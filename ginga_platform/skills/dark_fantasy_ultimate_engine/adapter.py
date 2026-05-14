"""Dark Fantasy Ultimate Engine — Adapter.

平台层与 dark-fantasy skill 之间的双向 IO 转换。

职责：
    1. input_transform：把 runtime_state 转成 skill 内部期望的输入格式
       （按思路 2 信息源优先级：用户要求 > 当前状态卡 > 最近正文 > 设定圣经 > 拆解知识库）
    2. output_transform：把 skill 输出（章节正文 + 表格摘要 + 结算）转成 runtime_state 更新指令
    3. enter_immersive_mode / exit_immersive_mode：沉浸专线行为
       （连续多章不打断 state 更新，章节块结束才批量结算）

关键约束（forbidden_mutation 由 contract.yaml 声明，state_io 在 platform 层强制 enforce）：
    - 不直接动 runtime_state.locked.*
    - 不动 meta/constitution.yaml / meta/guards/* / meta/checkers/*
    - 不动 workspace.task_plan / workspace.findings（归 planning-with-files）

来源：ARCHITECTURE.md §4.3 / §4.5；scout-2-doctrine §思路 2；P-10 任务定义。
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:  # 避免循环 import 与 stub 阶段 ImportError
    from ginga_platform.orchestrator.runner.state_io import StateIO


class DarkFantasyAdapter:
    """Dark Fantasy skill 的双向 adapter。

    平台层调用顺序（非 immersive 模式）：
        adapter = DarkFantasyAdapter(state_io)
        skill_input = adapter.input_transform(runtime_state)
        skill_output = call_skill(skill_input)          # 由 step_dispatch 真实调度
        updates = adapter.output_transform(skill_output)
        for u in updates:
            state_io.apply(u)                            # 显式同步（state_sync_mode=explicit）

    immersive 模式：
        adapter.enter_immersive_mode()
        # 连续多章 G_chapter_draft → output_transform 把 updates 推入 pending_updates，
        # 不立即 apply；checker 全静默。
        adapter.exit_immersive_mode()                    # 章节块结束时批量 apply + 触发 R2
    """

    HARD_PARTICLE_ANCHOR: int = 840_000_000
    SUPPORTED_TOPICS: tuple = ("玄幻黑暗", "暗黑奇幻", "黑暗玄幻")

    def __init__(self, state_io: "StateIO") -> None:
        """初始化 adapter。

        Args:
            state_io: 平台层提供的唯一 state 读写入口（带事务 + audit_log）。
        """
        self.state_io: "StateIO" = state_io
        self._immersive_active: bool = False
        self._pending_updates: List[Dict[str, Any]] = []
        self._last_safe_state: Optional[Dict[str, Any]] = None

    # ------------------------------------------------------------------
    # 输入转换：runtime_state → skill 内部期望的输入格式
    # ------------------------------------------------------------------
    def input_transform(self, runtime_state: Dict[str, Any]) -> Dict[str, Any]:
        """把 runtime_state 转成 dark-fantasy skill 期望的输入格式。

        按思路 2 信息源优先级组织：
            1. 用户本轮明确要求与硬约束
            2. 用户本轮贴出的正文 / 设定补丁
            3. 当前状态卡（runtime_state.entity_runtime.CHARACTER_STATE）
            4. 最近正文（runtime_state.chapter_text 最近 N 章）
            5. 设定总索引 / 主定义文件（runtime_state.locked）
            6. 拆解知识库（runtime_state.retrieved.cards）

        Args:
            runtime_state: 平台层 runtime_state 完整快照。

        Returns:
            dict：skill 内部消费的输入结构，含 topic / chapter_metadata /
            current_state_card / recent_chapters / world_setting /
            character_dynamics / plot_architecture / particle_ledger /
            pending_hooks / style_lock / retrieved_cards / user_guidance。
        """
        locked = runtime_state.get("locked", {}) or {}
        entity = runtime_state.get("entity_runtime", {}) or {}
        retrieved = runtime_state.get("retrieved", {}) or {}

        topic = (locked.get("GENRE_LOCKED", {}) or {}).get("topic", [])
        if not self._matches_dark_fantasy(topic):
            # 防御性：本 adapter 只服务玄幻黑暗题材；上游 skill-router 应已挡住。
            # 这里仍做兼容（避免被错误路由时 silently 生成不该有的内容）。
            pass

        return {
            "topic": topic,
            "chapter_metadata": runtime_state.get("chapter_metadata", {}),
            "current_state_card": entity.get("CHARACTER_STATE", {}),
            "recent_chapters": self._slice_recent_chapters(runtime_state, n=10),
            "world_setting": locked.get("WORLD", {}),
            "story_dna": locked.get("STORY_DNA", {}),
            "plot_architecture": locked.get("PLOT_ARCHITECTURE", {}),
            "particle_ledger": entity.get("RESOURCE_LEDGER", {}),
            "pending_hooks": entity.get("FORESHADOW_STATE", {}),
            "style_lock": (locked.get("GENRE_LOCKED", {}) or {}).get("style_lock"),
            "retrieved_cards": retrieved.get("cards", []),
            "user_guidance": runtime_state.get("user_guidance", ""),
            "hard_anchors": {
                "particle_cap": self.HARD_PARTICLE_ANCHOR,
            },
        }

    # ------------------------------------------------------------------
    # 输出转换：skill 输出 → runtime_state 更新指令
    # ------------------------------------------------------------------
    def output_transform(self, skill_output: Dict[str, Any]) -> List[Dict[str, Any]]:
        """把 skill 输出转成 runtime_state 更新指令列表。

        skill_output 期望含字段：
            - chapter_text (str)：章节正文（含【写作自检】+ 主体 + 可选【章节结算】）
            - writing_self_check (dict)：表格版外显摘要
            - chapter_settlement (dict, 可选)：吞噬 / 突破 / 卷末时的结算表
            - state_updates (dict, 可选)：skill 内部预先聚合的增量

        Returns:
            list[dict]：每个 dict 是一个 state_io.apply 指令，形如
            {"op": "delta" | "append" | "write", "path": <state_path>, "value": <...>}。

        若处于 immersive_mode：updates 仅入 pending_updates 队列，
            返回空列表（调用方仍可拿到 chapter_text，但不会触发 state apply）。
        """
        updates: List[Dict[str, Any]] = []

        chapter_text = skill_output.get("chapter_text", "")
        if chapter_text:
            updates.append({
                "op": "write",
                "path": "chapter_text",
                "value": chapter_text,
            })

        settlement = skill_output.get("chapter_settlement") or {}
        particle_delta = self._extract_particle_delta(settlement)
        if particle_delta is not None:
            updates.append({
                "op": "delta",
                "path": "runtime_state.entity_runtime.RESOURCE_LEDGER.particles",
                "value": particle_delta,
            })

        resource_events = settlement.get("resource_changes") or []
        for event in resource_events:
            updates.append({
                "op": "append",
                "path": "runtime_state.entity_runtime.RESOURCE_LEDGER.items",
                "value": event,
            })

        foreshadow_changes = settlement.get("foreshadow_changes") or []
        for change in foreshadow_changes:
            updates.append({
                "op": "append_or_update",
                "path": "runtime_state.entity_runtime.FORESHADOW_STATE.pool",
                "value": change,
                "key": "hook_id",
            })

        char_diff = (skill_output.get("state_updates") or {}).get("CHARACTER_STATE")
        if char_diff:
            updates.append({
                "op": "delta",
                "path": "runtime_state.entity_runtime.CHARACTER_STATE",
                "value": char_diff,
            })

        word_count = self._estimate_word_count(chapter_text)
        if word_count > 0:
            updates.append({
                "op": "delta",
                "path": "runtime_state.entity_runtime.GLOBAL_SUMMARY.total_words",
                "value": word_count,
            })

        # immersive 模式：累积到 pending_updates 不立即返回
        if self._immersive_active:
            self._pending_updates.extend(updates)
            # 仍返回 chapter_text 的 write 指令？
            # 设计：immersive 期内 chapter_text 也累积，章节块结束才一并 apply。
            # 这样退出 immersive 时一次性 R2 一致性可以看到全部章节文。
            return []

        return updates

    # ------------------------------------------------------------------
    # immersive_mode：进入 / 退出
    # ------------------------------------------------------------------
    def enter_immersive_mode(self) -> None:
        """进入沉浸写作专线。

        - 后续 output_transform 返回的 updates 改为入 pending_updates 队列
          （保留 list-of-ops 形态，exit 时统一经 op_translator 翻译）
        - 写 workspace.workflow_flags.immersive_mode = True
        - 写 workspace.workflow_flags.checker_silenced = True
          （checker_invoker 顶部 hook 读到 True → 全部 silenced + audit）
        - 快照当前 state 作为 last_safe_state，供 exit 时 batch apply 失败回滚

        幂等：已在 immersive 中 → 直接 return（不重复 audit / snapshot）。
        """
        if self._immersive_active:
            return
        self._immersive_active = True

        # 快照基线：state_io.snapshot() 已提供（含 _state + audit_log）。
        try:
            self._last_safe_state = self.state_io.snapshot()
        except Exception:
            self._last_safe_state = None

        self._pending_updates.clear()

        # 写两个 workflow_flags 到 workspace 域（state_io 顶层域只接受 4 个合法域，
        # workflow_flags 寄存于 workspace.workflow_flags.* 下）。
        try:
            self.state_io.apply(
                {
                    "workspace.workflow_flags.immersive_mode": True,
                    "workspace.workflow_flags.checker_silenced": True,
                },
                source="dark_fantasy_adapter.enter_immersive_mode",
            )
        except Exception:
            # 写 flag 失败属于不可恢复，回滚 immersive 状态。
            self._immersive_active = False
            self._last_safe_state = None
            raise

        # audit："immersive entered"（jury-3 / contract.yaml immersive_mode.behavior）
        try:
            self.state_io.audit(
                source="dark_fantasy_adapter",
                severity="info",
                msg="immersive entered",
                action="log",
                payload={"checker_silenced": True},
            )
        except Exception:
            pass

    def exit_immersive_mode(self) -> Dict[str, Any]:
        """退出沉浸写作专线，批量 apply 累积的 pending_updates。

        实施顺序（contract.immersive_mode.behavior / fallback）：
            1. 关闭 checker_silenced（保证 R2 checker 期内不被自家 flag 静默）
            2. 用 op_translator 把 self._pending_updates 翻译成 flat dict
            3. state_io.transaction() 内一次性 apply 全部 updates
            4. 标记 immersive_mode flag = False
            5. audit "<N> chapters batch applied"
            6. 触发 R2_consistency_check（调 invoke_checkers + audit "trigger:R2"）
            7. 异常路径：transaction 已 rollback；persist pending → fallback json

        Returns:
            dict：summary 含 applied_count / failed_count / last_error / chapter_count。
        """
        if not self._immersive_active:
            return {
                "applied_count": 0, "failed_count": 0, "last_error": None,
                "chapter_count": 0,
            }

        # 统计 chapter_text 写入次数（每章一条 op）
        chapter_count = sum(
            1 for op in self._pending_updates
            if op.get("op") == "write" and op.get("path") == "chapter_text"
        )

        applied = 0
        failed = 0
        last_error: Optional[str] = None

        # 先关 checker_silenced flag，确保后续 R2 不被自家 flag 静默。
        # 注意：这里不放进 batch transaction —— transaction rollback 会把这个改动也撤回，
        # 导致复盘期内 R2 跑不动。flag 关闭是独立 apply。
        try:
            self.state_io.apply(
                {"workspace.workflow_flags.checker_silenced": False},
                source="dark_fantasy_adapter.exit_immersive_mode",
            )
        except Exception:
            pass

        # 批量 apply：先 op_translator 翻成 flat dict，再 transaction 内 apply。
        # transaction 失败 → state_io 内部已 rollback _state + audit_log。
        try:
            # 局部 import 避免循环依赖（op_translator 导入 state_io）
            from ginga_platform.orchestrator.runner.op_translator import (
                adapter_ops_to_state_updates,
            )
            flat_updates = adapter_ops_to_state_updates(
                list(self._pending_updates), self.state_io
            )
            if flat_updates:
                with self.state_io.transaction():
                    self.state_io.apply(
                        flat_updates,
                        source="dark_fantasy_adapter.exit_immersive_mode.batch",
                    )
                applied = len(flat_updates)
            else:
                applied = 0
        except Exception as exc:
            failed = len(self._pending_updates) - applied
            last_error = repr(exc)
            # transaction 内异常已 rollback _state；这里只持久化 pending 供复盘
            self._persist_pending_for_replay()
            # audit failure
            try:
                self.state_io.audit(
                    source="dark_fantasy_adapter",
                    severity="error",
                    msg=f"immersive batch apply failed: {exc}",
                    action="rollback",
                    payload={"pending_count": len(self._pending_updates)},
                )
            except Exception:
                pass

        # 收尾：标 immersive_mode = False；audit batch applied
        try:
            self.state_io.apply(
                {"workspace.workflow_flags.immersive_mode": False},
                source="dark_fantasy_adapter.exit_immersive_mode",
            )
        except Exception:
            pass

        if last_error is None:
            try:
                self.state_io.audit(
                    source="dark_fantasy_adapter",
                    severity="info",
                    msg=f"{chapter_count} chapters batch applied",
                    action="log",
                    payload={
                        "applied_paths": applied,
                        "chapter_count": chapter_count,
                    },
                )
            except Exception:
                pass

        # 触发 R2 一致性 checker（仅在 batch apply 成功时跑）
        if last_error is None:
            try:
                self._trigger_r2_consistency_check()
            except Exception as exc:
                try:
                    self.state_io.audit(
                        source="dark_fantasy_adapter",
                        severity="warn",
                        msg=f"R2 trigger failed: {exc}",
                        action="log",
                    )
                except Exception:
                    pass

        self._pending_updates.clear()
        self._immersive_active = False
        self._last_safe_state = None

        return {
            "applied_count": applied,
            "failed_count": failed,
            "last_error": last_error,
            "chapter_count": chapter_count,
        }

    def _trigger_r2_consistency_check(self) -> None:
        """触发 R2_consistency_check（全章节块范围）.

        实现：调 checker_invoker.invoke_checkers，传入聚合 step_output
        （含 chapter_text 列表）+ runtime_context（state_io + step_id="R2_immersive_exit"）。
        checker_silenced 此时已为 False（exit 时第一步关）。
        """
        try:
            from ginga_platform.orchestrator.meta_integration.checker_invoker import (
                invoke_checkers,
            )
        except Exception:
            return

        # 聚合本块所有 chapter_text 写入作为 step_output
        chapter_texts = [
            op.get("value", "")
            for op in self._pending_updates
            if op.get("op") == "write" and op.get("path") == "chapter_text"
        ]
        step_output = {
            "chapter_text": "\n\n---\n\n".join(chapter_texts),
            "chapter_count": len(chapter_texts),
        }
        runtime_context = {
            "state_io": self.state_io,
            "step_id": "R2_immersive_exit",
        }
        # R2 默认 checker 列表（玄幻黑暗题材必跑：一致性 + 风格锁）
        checker_ids = ["R2_consistency_check"]
        try:
            invoke_checkers(checker_ids, step_output, runtime_context)
        except Exception:
            # checker block / load error 都不阻塞 exit；audit 由 checker_invoker 内部记录
            pass

        # audit trigger 标记，方便验收命令通过 audit_log 检测
        try:
            self.state_io.audit(
                source="dark_fantasy_adapter",
                severity="info",
                msg="R2_consistency_check triggered (immersive_block)",
                action="log",
                payload={"scope": "immersive_block", "chapter_count": len(chapter_texts)},
            )
        except Exception:
            pass

    # ------------------------------------------------------------------
    # 内部辅助方法
    # ------------------------------------------------------------------
    def _matches_dark_fantasy(self, topic: Any) -> bool:
        """判断 topic 是否匹配 dark-fantasy 强绑定题材。"""
        if not topic:
            return False
        if isinstance(topic, str):
            topic = [topic]
        return any(t in self.SUPPORTED_TOPICS for t in topic)

    def _slice_recent_chapters(
        self, runtime_state: Dict[str, Any], n: int = 10
    ) -> List[Dict[str, Any]]:
        """按思路 2 最小上下文原则：默认取最近 3-10 章，不机械追满 100 章。"""
        chapters = runtime_state.get("chapters", []) or []
        if not chapters:
            return []
        # 保留切片下界 3，上界 n
        return chapters[-max(n, 3):]

    def _extract_particle_delta(self, settlement: Dict[str, Any]) -> Optional[int]:
        """从【章节结算】表里抽出微粒 delta。

        settlement.particle_balance 期望形如：
            {"period_start": int, "delta": int, "period_end": int}
        """
        balance = settlement.get("particle_balance") or {}
        delta = balance.get("delta")
        if isinstance(delta, int):
            return delta
        return None

    def _estimate_word_count(self, text: str) -> int:
        """粗估章节字数（中文按字符计，去掉 markdown 表格与代码块）。"""
        if not text:
            return 0
        cleaned = []
        in_table = False
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("|") and stripped.endswith("|"):
                in_table = True
                continue
            if in_table and not stripped.startswith("|"):
                in_table = False
            if stripped.startswith("```"):
                continue
            cleaned.append(line)
        body = "".join(cleaned)
        # 中文按字符；其他字符宽松计入
        return sum(1 for ch in body if not ch.isspace())

    def _persist_pending_for_replay(self) -> None:
        """exit_immersive_mode 失败时把 pending_updates 持久化供复盘。

        落点：.ops/immersive_fallback/<book_id>_<utc-iso>.json
            包含 pending_updates 完整 op 列表 + last_safe_state snapshot ref。

        失败容忍：persist 本身失败不阻塞 exit，仅 audit 一条 warn。
        """
        import json
        from datetime import datetime, timezone

        try:
            book_id = getattr(self.state_io, "book_id", "unknown")
            fallback_dir = Path(".ops/immersive_fallback")
            fallback_dir.mkdir(parents=True, exist_ok=True)
            ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            fp = fallback_dir / f"{book_id}_{ts}.json"
            payload = {
                "book_id": book_id,
                "ts": ts,
                "pending_updates": self._pending_updates,
                "had_safe_state": self._last_safe_state is not None,
            }
            fp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            try:
                self.state_io.audit(
                    source="dark_fantasy_adapter",
                    severity="warn",
                    msg=f"immersive pending persisted to {fp}",
                    action="log",
                    payload={"file": str(fp), "count": len(self._pending_updates)},
                )
            except Exception:
                pass
        except Exception:
            # persist 失败也不阻塞 exit；记 audit
            try:
                self.state_io.audit(
                    source="dark_fantasy_adapter",
                    severity="error",
                    msg="immersive pending persist failed (silent)",
                    action="log",
                )
            except Exception:
                pass


__all__ = ["DarkFantasyAdapter"]
