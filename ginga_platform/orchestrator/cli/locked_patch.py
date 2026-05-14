"""locked 域 patch CLI (ST-S2-S-MULTI-CHAPTER S-2).

用途：长篇 30 万字后修改 locked 域必须走 patch 流程，不许直接 state_io.apply 覆盖.
入口形态:

    python3 -m ginga_platform.orchestrator.cli.locked_patch \
        <book_id> --field locked.WORLD.factions \
        --reason "第25章扩出血雾教廷势力" \
        --new-value '[{"id":"F-001","name":"血雾教廷"}]'

或被 ginga wrapper 调（待 ginga CLI 主入口注册子命令）.

流程（按 foundation/schema/runtime_state.yaml locked_patch_flow 段）:
    1. 校验 field 必须在 locked 顶层域下
    2. 解析 new_value（支持 inline JSON / YAML）
    3. 生成 patch_id（P-<8 位随机>-<short-tag>）
    4. 写 meta/patches/<patch_id>.patch.yaml（含 ts / scope / reason / approval_required）
    5. 用 state_io.transaction 包裹整次 apply（异常自动 rollback）
    6. 写一条 audit_log severity=info source=cli.locked_patch
    7. 跑 R3 一致性 checker stub（mock：写 audit info；S3 替换真 character-iq + cool-point-payoff）
    8. 把 patch yaml 复制到 meta/patches/<patch_id>.applied.yaml（标记已应用）

关键：禁止绕过本 CLI 直接 state_io.apply({"locked.X": ...})：state_io 不强 enforce，
但本 CLI 的 audit_log 留迹是 P0 红线（jury-3 P1）.
"""
from __future__ import annotations

import argparse
import json
import secrets
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from ginga_platform.orchestrator.runner.state_io import StateIO


_DEFAULT_PATCHES_ROOT = Path("meta/patches")


class LockedPatchError(RuntimeError):
    """locked 域 patch 流程错误（field 越权 / new_value 无效 / 应用失败等）."""


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _gen_patch_id(short_tag: str) -> str:
    """生成 patch_id：P-<6 位 hex>-<sanitized-tag>."""
    tag = "".join(c if c.isalnum() or c == "-" else "-" for c in (short_tag or "").lower()).strip("-")
    tag = tag or "patch"
    return f"P-{secrets.token_hex(3)}-{tag[:40]}"


def _parse_new_value(raw: str) -> Any:
    """解析 --new-value 字符串：先试 JSON，再试 YAML."""
    if raw is None:
        raise LockedPatchError("new_value is required")
    # 容忍前后空白
    s = raw.strip()
    if not s:
        raise LockedPatchError("new_value is empty")
    try:
        return json.loads(s)
    except (ValueError, TypeError):
        pass
    try:
        return yaml.safe_load(s)
    except yaml.YAMLError as exc:
        raise LockedPatchError(f"new_value not parseable as JSON or YAML: {exc}") from exc


def _validate_field_in_locked(field: str) -> None:
    """field 必须形如 locked.XXX.YYY，禁止越权写其他域."""
    if not field or not isinstance(field, str):
        raise LockedPatchError(f"field must be non-empty str, got {field!r}")
    parts = field.split(".")
    if parts[0] != "locked" or len(parts) < 2:
        raise LockedPatchError(
            f"field must start with 'locked.', got {field!r}; use state_io.apply directly for non-locked domains"
        )


def _ensure_patches_dir(patches_root: Path) -> None:
    patches_root.mkdir(parents=True, exist_ok=True)


def _run_r3_consistency_checker_stub(sio: StateIO, *, patch_id: str, field: str) -> dict[str, Any]:
    """R3 一致性 checker stub.

    S2 mock：只写一条 audit info，假装跑了 character-iq + cool-point-payoff.
    S3 切真：调 ginga_platform.orchestrator.meta_integration.checker_invoker.invoke_checkers
    传 ["character-iq-checker", "cool-point-payoff-checker"] + 当前 state snapshot.
    """
    sio.audit(
        source="cli.locked_patch.r3_consistency_checker",
        severity="info",
        msg=f"R3 consistency checker stub passed for patch {patch_id} on field {field}",
        action="log",
        payload={"patch_id": patch_id, "field": field, "checkers": ["character-iq", "cool-point-payoff"]},
    )
    return {"ok": True, "checked_by": ["character-iq-stub", "cool-point-payoff-stub"]}


def apply_patch_to_book(
    book_id: str,
    *,
    field: str,
    reason: str,
    new_value: Any,
    affected_chapters: str = "unknown",
    approval_required: bool = True,
    author: str = "cli.locked_patch",
    short_tag: str = "patch",
    state_root: Path | str | None = None,
    patches_root: Path | str = _DEFAULT_PATCHES_ROOT,
    dry_run: bool = False,
) -> dict[str, Any]:
    """对 book 应用一次 locked 域 patch.

    返回 dict：``{patch_id, applied: bool, patch_path, r3_result}``.
    任何步骤失败抛 LockedPatchError；state_io.transaction 包裹 apply，异常 rollback.
    """
    _validate_field_in_locked(field)
    if not reason or not isinstance(reason, str):
        raise LockedPatchError(f"reason must be non-empty str, got {reason!r}")

    patches_root_path = Path(patches_root)
    _ensure_patches_dir(patches_root_path)

    # 1. 准备 patch 文档
    patch_id = _gen_patch_id(short_tag)
    ts = _now_iso()
    patch_doc: dict[str, Any] = {
        "patch_id": patch_id,
        "ts": ts,
        "author": author,
        "book_id": book_id,
        "reason": reason,
        "scope": [field],
        "affected_chapters": affected_chapters,
        "approval_required": approval_required,
        "new_value": {field: new_value},
        "post_apply": ["run_r3_consistency_checker", "audit_log_record", "persist_patch_yaml"],
        "on_failure": {"rollback_strategy": "snapshot_revert", "alert_severity": "error"},
    }
    patch_path = patches_root_path / f"{patch_id}.patch.yaml"
    # 落盘 patch yaml
    patch_path.write_text(
        yaml.safe_dump(patch_doc, allow_unicode=True, sort_keys=False, default_flow_style=False),
        encoding="utf-8",
    )

    # 2. dry-run：只写 patch yaml，不动 state
    if dry_run:
        return {
            "patch_id": patch_id,
            "applied": False,
            "patch_path": str(patch_path),
            "r3_result": None,
            "note": "dry_run only; state not modified",
        }

    # 3. approval_required = True 且 author 不在白名单时拒绝
    # 简化：CLI 直接通过 --approve 才往下走（cli_main 处理）；
    # 这里函数级假设 caller 自己 ACK 过.

    # 4. 加载 state_io + 应用（事务）
    sio_kwargs: dict[str, Any] = {"autoload": True}
    if state_root is not None:
        sio_kwargs["state_root"] = state_root
    sio = StateIO(book_id, **sio_kwargs)

    try:
        with sio.transaction() as tx:
            tx.apply({field: new_value}, source=f"cli.locked_patch.{patch_id}")
            tx.audit(
                source="cli.locked_patch",
                severity="info",
                msg=f"locked patch applied: id={patch_id} field={field} reason={reason[:80]}",
                action="patch",
                payload={
                    "patch_id": patch_id,
                    "field": field,
                    "affected_chapters": affected_chapters,
                    "approval_required": approval_required,
                    "patch_path": str(patch_path),
                },
            )
    except Exception as exc:
        sio.audit(
            source="cli.locked_patch",
            severity="error",
            msg=f"patch {patch_id} apply failed: {exc}",
            action="rollback",
            payload={"patch_id": patch_id, "field": field},
        )
        raise LockedPatchError(f"apply patch {patch_id} failed: {exc}") from exc

    # 5. post_apply：跑 R3 一致性 checker stub
    r3_result = _run_r3_consistency_checker_stub(sio, patch_id=patch_id, field=field)

    # 6. patch.applied.yaml 标记
    applied_path = patches_root_path / f"{patch_id}.applied.yaml"
    applied_doc = dict(patch_doc)
    applied_doc["applied_at"] = _now_iso()
    applied_doc["r3_result"] = r3_result
    applied_path.write_text(
        yaml.safe_dump(applied_doc, allow_unicode=True, sort_keys=False, default_flow_style=False),
        encoding="utf-8",
    )

    return {
        "patch_id": patch_id,
        "applied": True,
        "patch_path": str(patch_path),
        "applied_path": str(applied_path),
        "r3_result": r3_result,
    }


# ---------- CLI entry ---------------------------------------------------------


def cli_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="ginga patch",
        description="locked 域 patch CLI（修改 locked 域必走本流程，留 audit + meta/patches 痕迹）",
    )
    parser.add_argument("book_id", help="书 id（runtime_state 目录名）")
    parser.add_argument("--field", required=True, help="要改的 locked 域 dotted path（如 locked.WORLD.factions）")
    parser.add_argument("--reason", required=True, help="改的原因（一句话）")
    parser.add_argument(
        "--new-value",
        required=True,
        help="新值，JSON 字符串优先；JSON 不可解析时按 YAML 处理",
    )
    parser.add_argument("--affected-chapters", default="unknown", help="影响章节区间，如 25-40")
    parser.add_argument("--approval-required", default="true", choices=["true", "false"], help="是否需要 approve")
    parser.add_argument("--short-tag", default="patch", help="patch_id 短标签（生成文件名用）")
    parser.add_argument("--author", default="cli.user", help="patch 作者")
    parser.add_argument(
        "--approve",
        action="store_true",
        help="若 --approval-required=true，必须显式带本 flag 才会真应用",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只写 patch yaml 不动 state（默认 false）",
    )
    parser.add_argument(
        "--patches-root",
        default=str(_DEFAULT_PATCHES_ROOT),
        help="meta/patches/ 根路径（默认按工作目录解析）",
    )
    parser.add_argument(
        "--state-root",
        default=None,
        help="state 根路径（默认 foundation/runtime_state；测试时可指向 tmp dir）",
    )

    args = parser.parse_args(argv)

    try:
        new_value = _parse_new_value(args.new_value)
    except LockedPatchError as exc:
        print(f"❌ {exc}", file=sys.stderr)
        return 2

    approval_required = args.approval_required.lower() == "true"
    if approval_required and not args.approve and not args.dry_run:
        print(
            "❌ approval_required=true 但未带 --approve；请确认改动正确后追加 --approve 重试",
            file=sys.stderr,
        )
        return 3

    try:
        result = apply_patch_to_book(
            args.book_id,
            field=args.field,
            reason=args.reason,
            new_value=new_value,
            affected_chapters=args.affected_chapters,
            approval_required=approval_required,
            author=args.author,
            short_tag=args.short_tag,
            patches_root=Path(args.patches_root),
            state_root=(Path(args.state_root) if args.state_root else None),
            dry_run=args.dry_run,
        )
    except LockedPatchError as exc:
        print(f"❌ patch failed: {exc}", file=sys.stderr)
        return 4

    print(
        f"✅ patch_id={result['patch_id']} applied={result['applied']} "
        f"patch_yaml={result['patch_path']}"
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(cli_main())


__all__ = [
    "LockedPatchError",
    "apply_patch_to_book",
    "cli_main",
]
