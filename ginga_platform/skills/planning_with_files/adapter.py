"""Planning With Files — Adapter.

平台层与 planning-with-files skill 之间的双向 IO 转换。

职责：
    1. input_transform：把 runtime_state.workspace 三件套 + chapters + 资料库召回
       转成 skill 内部期望的输入格式（按思路 3 信息源优先级）
    2. output_transform：把 skill 输出（task_plan/findings/progress 增量 + 任务结果）
       转成 runtime_state.workspace.* 更新指令
    3. enter_immersive_mode / exit_immersive_mode：no-op（planning 不参与沉浸专线）
       保留 4 方法接口契约，与 dark-fantasy adapter 统一签名。

关键约束（forbidden_mutation 由 contract.yaml 声明）：
    - 不动 runtime_state.locked.*
    - 不动 runtime_state.entity_runtime.*（CHARACTER_STATE / RESOURCE_LEDGER 等）
    - 不动 chapter_text
    - 不动 meta 层（constitution / guards / checkers）

来源：ARCHITECTURE.md §4.3 / §6.3；scout-2-doctrine §思路 3；P-11c 任务定义。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from ginga_platform.orchestrator.runner.state_io import StateIO


class PlanningWithFilesAdapter:
    """planning-with-files skill 的双向 adapter。

    平台层调用顺序（典型规划维护任务）：
        adapter = PlanningWithFilesAdapter(state_io)
        skill_input = adapter.input_transform(runtime_state)
        skill_output = call_skill(skill_input)
        updates = adapter.output_transform(skill_output)
        for u in updates:
            state_io.apply(u)

    本 adapter 是 cross-cutting 工具型，不参与 dark-fantasy 的 immersive_mode；
    enter/exit_immersive_mode 实现为 no-op + audit_log 记录，保接口契约一致。
    """

    TASK_CATEGORIES: tuple = (
        "正文创作",
        "设定工作",
        "历史考据",
        "质量审查",
        "规划维护",
    )
    MODE_INCREMENTAL: str = "增量热更新"
    MODE_COLD_START: str = "全量冷启动"

    def __init__(self, state_io: "StateIO") -> None:
        """初始化 adapter。

        Args:
            state_io: 平台层唯一 state 读写入口（带事务 + audit_log）。
        """
        self.state_io: "StateIO" = state_io
        self._immersive_active: bool = False  # 始终 False；保字段为接口契约一致
        self._pending_updates: List[Dict[str, Any]] = []

    # ------------------------------------------------------------------
    # 输入转换：runtime_state → skill 内部期望的输入格式
    # ------------------------------------------------------------------
    def input_transform(self, runtime_state: Dict[str, Any]) -> Dict[str, Any]:
        """把 runtime_state 转成 planning-with-files skill 期望的输入格式。

        按思路 3 信息源优先级组织：
            1. 用户本轮明确要求与硬约束
            2. 用户本轮贴出的正文 / 片段 / 设定补丁 / 修改说明
            3. 最近相关的已存在正文章节或资料文件
            4. 本地规划文件 task_plan / findings / progress
            5. 本地参考资料与导入历史
            6. 联网核验结果
            7. 通用经验与类比

        Args:
            runtime_state: 平台层 runtime_state 完整快照。

        Returns:
            dict：skill 内部消费的输入结构，含 task_description / task_category /
            workspace（三件套）/ character_relationships / recent_chapters /
            references / user_guidance / mode。
        """
        workspace = runtime_state.get("workspace", {}) or {}
        retrieved = runtime_state.get("retrieved", {}) or {}
        chapter_meta = runtime_state.get("chapter_metadata", {}) or {}

        task_description = runtime_state.get("task_description", "")
        task_category = runtime_state.get("task_category", "规划维护")
        mode = runtime_state.get("mode") or self.MODE_INCREMENTAL

        return {
            "task_description": task_description,
            "task_category": task_category,
            "user_guidance": runtime_state.get("user_guidance", ""),
            "mode": mode,
            "workspace": {
                "task_plan": workspace.get("task_plan", ""),
                "findings": workspace.get("findings", ""),
                "progress": workspace.get("progress", ""),
                "character_relationships": workspace.get("character_relationships", ""),
            },
            "recent_chapters": self._slice_recent_chapters(
                runtime_state, mode=mode, requested=chapter_meta
            ),
            "references": retrieved.get("references", []),
            "chapter_metadata": chapter_meta,
            "constraints": {
                "no_fake_read": True,
                "no_chase_100_chapters": True,
                "no_web_abuse": True,
                "no_chain_of_thought_leak": True,
            },
        }

    # ------------------------------------------------------------------
    # 输出转换：skill 输出 → runtime_state 更新指令
    # ------------------------------------------------------------------
    def output_transform(self, skill_output: Dict[str, Any]) -> List[Dict[str, Any]]:
        """把 skill 输出转成 workspace.* 更新指令列表。

        skill_output 期望含字段：
            - self_check_table (dict, 可选)
            - task_plan_update (str, 可选)：task_plan.md 更新片段
            - findings_update (str, 可选)：findings.md 追加片段
            - progress_update (str, 可选)：progress.md 追加片段
            - result (str)：实际产出（正文 / 报告 / 清单 / 规划文件）

        Returns:
            list[dict]：每个 dict 是一个 state_io.apply 指令，形如
            {"op": "write_or_append" | "append", "path": <state_path>, "value": <...>}。

        forbidden_mutation 保护：本方法只针对 workspace.* 与 audit_log；
        正文 state（locked.* / entity_runtime.* / chapter_text）由 dark-fantasy
        或 default writer 通过它们各自的 adapter 处理。
        """
        updates: List[Dict[str, Any]] = []

        task_plan_update = skill_output.get("task_plan_update")
        if task_plan_update:
            updates.append({
                "op": "write_or_append",
                "path": "runtime_state.workspace.task_plan",
                "value": task_plan_update,
            })

        findings_update = skill_output.get("findings_update")
        if findings_update:
            updates.append({
                "op": "append",
                "path": "runtime_state.workspace.findings",
                "value": findings_update,
            })

        progress_update = skill_output.get("progress_update")
        if progress_update:
            updates.append({
                "op": "append",
                "path": "runtime_state.workspace.progress",
                "value": progress_update,
            })

        # 自检表记入 audit_log（不进 prompt，符合 jury-3 P1 "checker 输出不进 prompt"）
        self_check = skill_output.get("self_check_table")
        if self_check:
            updates.append({
                "op": "append",
                "path": "audit_log.entries",
                "value": {
                    "source": "planning-with-files.self_check",
                    "severity": "info",
                    "payload": self_check,
                },
            })

        return updates

    # ------------------------------------------------------------------
    # immersive_mode：no-op（planning 不参与沉浸专线，保接口契约一致）
    # ------------------------------------------------------------------
    def enter_immersive_mode(self) -> None:
        """no-op：planning-with-files 不参与 dark-fantasy 的沉浸专线。

        保留方法以满足 adapter 4 方法接口契约。
        触发时记 audit_log，便于运维排查（如果出现误调用）。
        """
        # 不修改 self._immersive_active；planning 状态机里它永远是 False
        self.state_io.audit(
            source="planning-with-files.adapter",
            severity="info",
            msg="enter_immersive_mode called on planning adapter (no-op by design)",
        )

    def exit_immersive_mode(self) -> Dict[str, Any]:
        """no-op：planning-with-files 不参与 dark-fantasy 的沉浸专线。

        Returns:
            dict：与 dark-fantasy adapter exit_immersive_mode 同 shape，
            applied_count / failed_count / last_error 全为 0 / None。
        """
        self.state_io.audit(
            source="planning-with-files.adapter",
            severity="info",
            msg="exit_immersive_mode called on planning adapter (no-op by design)",
        )
        return {"applied_count": 0, "failed_count": 0, "last_error": None}

    # ------------------------------------------------------------------
    # 内部辅助方法
    # ------------------------------------------------------------------
    def _slice_recent_chapters(
        self,
        runtime_state: Dict[str, Any],
        mode: str,
        requested: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """按思路 3 渐进式上下文加载切片最近章节。

        - 增量热更新模式：默认 3-10 章
        - 全量冷启动模式：返回全部（由调用方按拓扑再筛）
        - 长线伏笔 / 跨卷人物 / 重大伤势 / 长期交易链：扩 10-30
          （由 requested.scope=long_arc 触发）
        """
        chapters = runtime_state.get("chapters", []) or []
        if not chapters:
            return []
        if mode == self.MODE_COLD_START:
            return chapters
        # incremental 默认窗口
        window = 10
        scope = (requested or {}).get("scope")
        if scope == "long_arc":
            window = 30
        elif scope == "cross_volume":
            # 跨卷过渡点（如 020/021、040/041）：前后两个分卷
            window = 40
        return chapters[-window:]


__all__ = ["PlanningWithFilesAdapter"]
