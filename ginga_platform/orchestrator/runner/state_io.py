"""State IO — runtime_state 的唯一读写入口 (jury-1 P0 强约束).

任何 workflow step / skill / guard / checker 要读写 runtime_state，必须经
``StateIO``；带事务、带 audit_log。其他模块直接 ``yaml.dump`` 写 state 文件
属于项目工程红线违规 (见 ARCHITECTURE.md §4.2).

State 落盘约定 (ARCHITECTURE.md §3.5)::

    foundation/runtime_state/<book_id>/
        locked.yaml           # STORY_DNA / PLOT_ARCHITECTURE / GENRE_LOCKED
        entity_runtime.yaml   # CHARACTER_STATE / RESOURCE_LEDGER / FORESHADOW_STATE / GLOBAL_SUMMARY
        workspace.yaml        # task_plan / findings / progress refs
        retrieved.yaml        # 每章 RAG 召回的 cards / methodology_refs
        audit_log.yaml        # checker / guard 的所有输出 (jury-1 P1 配套)

路径寻址 (read / apply key) 用点号分隔 (e.g. ``"locked.STORY_DNA.premise"``).
"""

from __future__ import annotations

import copy
import os
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Optional

import yaml


# state 文件按顶层域分文件，避免单文件巨大；同时与 §3.5 五个分域对应。
_TOP_DOMAINS: tuple[str, ...] = (
    "locked",
    "entity_runtime",
    "workspace",
    "retrieved",
    "audit_log",
)

# 默认 state 根目录（ARCHITECTURE 附录 A：foundation/runtime_state/<book_id>/）。
# 故意做成函数：避免"模块级常量被 mock.patch"诱导测试踩 Python 默认参数绑定陷阱
# （默认值在 import 时求值，patch 模块属性对已绑定的默认值无效）。测试要重定向请改
# _default_state_root 函数返回值（monkeypatch.setattr(state_io, "_default_state_root", lambda: tmp)）
# 或显式给 StateIO 传 state_root=... / CLI 传 --state-root。
def _default_state_root() -> Path:
    return Path("foundation/runtime_state")


class StateIOError(RuntimeError):
    """state_io 内部一致性错误（路径越界、域不存在等）."""


@dataclass(frozen=True)
class AuditEntry:
    """audit_log 单条记录 (ARCHITECTURE.md §3.5)."""

    ts: str
    source: str
    severity: str  # info / warn / error / block
    msg: str
    action: str = "log"  # log / patch / block / rollback
    payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ts": self.ts,
            "source": self.source,
            "severity": self.severity,
            "msg": self.msg,
            "action": self.action,
            "payload": dict(self.payload),
        }


class StateIO:
    """runtime_state 的唯一读写入口 + 事务上下文 + audit_log.

    Usage::

        sio = StateIO(book_id="demo-001")
        premise = sio.read("locked.STORY_DNA.premise")
        with sio.transaction() as tx:
            tx.apply({"entity_runtime.RESOURCE_LEDGER.particles": 42})
            tx.audit("step_dispatch", severity="info", msg="step G done")
        # commit on context exit; rollback on exception.
    """

    def __init__(
        self,
        book_id: str,
        state_root: Path | str | None = None,
        *,
        autoload: bool = True,
    ) -> None:
        if not book_id or "/" in book_id or ".." in book_id:
            raise StateIOError(f"invalid book_id: {book_id!r}")
        self.book_id: str = book_id
        if state_root is None:
            state_root = _default_state_root()
        self.state_dir: Path = Path(state_root) / book_id
        # in-memory 真值（dict-of-dict），按 top domain 分桶。
        self._state: dict[str, dict[str, Any]] = {d: {} for d in _TOP_DOMAINS}
        # audit_log 单独抽出来直读直写，避免 ``audit_log.entries`` 嵌套层级。
        self.audit_log: list[dict[str, Any]] = []
        # 事务深度，>0 时禁止重入嵌套 commit。
        self._tx_depth: int = 0
        # 事务期 snapshot（用于 rollback）。
        self._tx_snapshot: Optional[tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]] = None
        if autoload:
            self._load_from_disk()

    # -- public read ---------------------------------------------------------

    def read(self, path: str, default: Any = None) -> Any:
        """读 state 字段，路径形如 ``locked.STORY_DNA.premise``.

        路径不存在返回 ``default``；顶层域必须在 ``_TOP_DOMAINS`` 内.
        """
        domain, rest = self._split_path(path)
        node: Any = self._state[domain]
        for seg in rest:
            if not isinstance(node, dict) or seg not in node:
                return default
            node = node[seg]
        return copy.deepcopy(node)

    # -- public write --------------------------------------------------------

    def apply(self, update: dict[str, Any], *, source: str = "unknown") -> None:
        """应用 state 更新 + 记 audit_log.

        ``update`` 是 ``{"locked.STORY_DNA.premise": "...", ...}`` 形式的扁平 dict，
        值为 ``None`` 表示删除该键。每次 apply 都会自动写 ``audit_log`` 一条 ``info``.
        """
        if not isinstance(update, dict):
            raise StateIOError(f"apply expects dict, got {type(update).__name__}")
        applied_paths: list[str] = []
        for path, value in update.items():
            self._write_path(path, value)
            applied_paths.append(path)
        self._append_audit(
            AuditEntry(
                ts=self._now_iso(),
                source=source,
                severity="info",
                msg=f"applied {len(applied_paths)} update(s)",
                action="log",
                payload={"paths": applied_paths},
            )
        )
        if self._tx_depth == 0:
            # 非事务上下文，直接落盘。
            self._flush_to_disk()

    def audit(
        self,
        source: str,
        *,
        severity: str = "info",
        msg: str = "",
        action: str = "log",
        payload: Optional[dict[str, Any]] = None,
    ) -> None:
        """显式追加一条 audit_log entry（checker / guard / step_dispatch 公用）."""
        self._append_audit(
            AuditEntry(
                ts=self._now_iso(),
                source=source,
                severity=severity,
                msg=msg,
                action=action,
                payload=dict(payload or {}),
            )
        )
        if self._tx_depth == 0:
            self._flush_audit_only()

    def write_artifact(
        self,
        name: str,
        content: str,
        *,
        source: str,
        artifact_type: str,
        payload: Optional[dict[str, Any]] = None,
    ) -> Path:
        """Write a non-state artifact under this book's state directory.

        YAML state domains still must be changed via ``apply`` / ``audit``. This
        helper exists for chapter artifacts such as ``chapter_01.md`` so their
        boundary is explicit and audit-visible.
        """
        if not name or not isinstance(name, str):
            raise StateIOError(f"artifact name must be non-empty str, got {name!r}")
        rel = Path(name)
        if rel.is_absolute() or ".." in rel.parts:
            raise StateIOError(f"artifact path must stay under state_dir, got {name!r}")
        if rel.name in {f"{domain}.yaml" for domain in _TOP_DOMAINS}:
            raise StateIOError(
                f"{rel.name} is a runtime_state domain file; use StateIO.apply/audit instead"
            )
        if rel.suffix in {".yaml", ".yml"}:
            raise StateIOError(
                f"YAML artifacts are not allowed through write_artifact: {name!r}"
            )
        artifact_path = self.state_dir / rel
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_text(content, encoding="utf-8")
        artifact_payload = dict(payload or {})
        artifact_payload.update(
            {
                "artifact_type": artifact_type,
                "path": str(artifact_path),
                "bytes": artifact_path.stat().st_size,
            }
        )
        self.audit(
            source=source,
            severity="info",
            msg=f"artifact written: {name}",
            action="log",
            payload=artifact_payload,
        )
        return artifact_path

    # -- transaction ---------------------------------------------------------

    @contextmanager
    def transaction(self) -> Iterator["StateIO"]:
        """事务上下文：异常 rollback，正常 commit + 落盘.

        嵌套事务（深度 >0）共享同一份 snapshot，只在最外层 commit/落盘.
        """
        outer = self._tx_depth == 0
        if outer:
            self._tx_snapshot = (copy.deepcopy(self._state), copy.deepcopy(self.audit_log))
        self._tx_depth += 1
        try:
            yield self
        except Exception:
            # rollback：恢复 snapshot，不落盘。
            if outer and self._tx_snapshot is not None:
                self._state, self.audit_log = self._tx_snapshot
                self._append_audit(
                    AuditEntry(
                        ts=self._now_iso(),
                        source="state_io.transaction",
                        severity="warn",
                        msg="transaction rolled back",
                        action="rollback",
                    )
                )
            raise
        else:
            if outer:
                self._flush_to_disk()
        finally:
            self._tx_depth -= 1
            if outer:
                self._tx_snapshot = None

    # -- internal: path & write ----------------------------------------------

    @staticmethod
    def _split_path(path: str) -> tuple[str, list[str]]:
        if not path or not isinstance(path, str):
            raise StateIOError(f"path must be non-empty str, got {path!r}")
        parts = path.split(".")
        domain = parts[0]
        if domain not in _TOP_DOMAINS:
            raise StateIOError(
                f"unknown top-level state domain {domain!r}; expected one of {_TOP_DOMAINS}"
            )
        if domain == "audit_log":
            raise StateIOError(
                "audit_log is append-only; use StateIO.audit(...) instead of apply(...)"
            )
        return domain, parts[1:]

    def _write_path(self, path: str, value: Any) -> None:
        domain, rest = self._split_path(path)
        if not rest:
            # 整域替换。
            if value is None:
                self._state[domain] = {}
            elif isinstance(value, dict):
                self._state[domain] = copy.deepcopy(value)
            else:
                raise StateIOError(
                    f"top-level domain {domain!r} must be dict, got {type(value).__name__}"
                )
            return
        node = self._state[domain]
        for seg in rest[:-1]:
            if seg not in node or not isinstance(node[seg], dict):
                node[seg] = {}
            node = node[seg]
        last = rest[-1]
        if value is None:
            node.pop(last, None)
        else:
            node[last] = copy.deepcopy(value)

    # -- internal: audit -----------------------------------------------------

    def _append_audit(self, entry: AuditEntry) -> None:
        self.audit_log.append(entry.to_dict())

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat(timespec="seconds")

    # -- internal: persistence ----------------------------------------------

    def _load_from_disk(self) -> None:
        if not self.state_dir.exists():
            return
        for domain in _TOP_DOMAINS:
            fp = self.state_dir / f"{domain}.yaml"
            if not fp.exists():
                continue
            try:
                raw = yaml.safe_load(fp.read_text(encoding="utf-8")) or {}
            except yaml.YAMLError as exc:
                raise StateIOError(f"failed to parse {fp}: {exc}") from exc
            if domain == "audit_log":
                if isinstance(raw, dict):
                    entries = raw.get("entries", [])
                else:
                    entries = raw
                if not isinstance(entries, list):
                    raise StateIOError(f"audit_log entries must be list, got {type(entries).__name__}")
                self.audit_log = list(entries)
            else:
                if not isinstance(raw, dict):
                    raise StateIOError(
                        f"{fp.name} must be a mapping, got {type(raw).__name__}"
                    )
                self._state[domain] = raw

    def _flush_to_disk(self) -> None:
        """落盘 5 个分域文件 (atomic write per file)."""
        self.state_dir.mkdir(parents=True, exist_ok=True)
        for domain in _TOP_DOMAINS:
            fp = self.state_dir / f"{domain}.yaml"
            if domain == "audit_log":
                payload: Any = {"entries": self.audit_log}
            else:
                payload = self._state[domain]
            self._atomic_write_yaml(fp, payload)

    def _flush_audit_only(self) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        fp = self.state_dir / "audit_log.yaml"
        self._atomic_write_yaml(fp, {"entries": self.audit_log})

    @staticmethod
    def _atomic_write_yaml(fp: Path, payload: Any) -> None:
        # tempfile + os.replace 保证原子；防止崩溃留半截。
        fd, tmp = tempfile.mkstemp(prefix=fp.name + ".", dir=str(fp.parent))
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                yaml.safe_dump(
                    payload,
                    fh,
                    allow_unicode=True,
                    sort_keys=False,
                    default_flow_style=False,
                )
            os.replace(tmp, fp)
        except Exception:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise

    # -- convenience ---------------------------------------------------------

    @property
    def state(self) -> dict[str, dict[str, Any]]:
        """只读视图（返回 deep copy 避免外部直改）."""
        return copy.deepcopy(self._state)

    def snapshot(self) -> dict[str, Any]:
        """整体 snapshot（含 audit_log），调试用."""
        return {
            "book_id": self.book_id,
            "state": copy.deepcopy(self._state),
            "audit_log": copy.deepcopy(self.audit_log),
        }


__all__ = ["StateIO", "StateIOError", "AuditEntry"]
