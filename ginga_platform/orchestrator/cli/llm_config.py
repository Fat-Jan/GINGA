"""LLM 配置加载 + fallback 调用封装。

配置文件路径：项目根 llm_config.yaml
调用方式：
    from ginga_platform.orchestrator.cli.llm_config import load_config, call_llm_with_fallback

    # 按 role 调用（自动 fallback）
    text = call_llm_with_fallback(prompt, role="prose_writer")

    # 按显式 endpoint 调用（不 fallback，向后兼容）
    text = call_llm_with_fallback(prompt, endpoint="久久", max_tokens=8000)
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import yaml


_HARDCODED_DEFAULTS: dict[str, Any] = {
    "version": "fallback",
    "roles": {},
    "defaults": {
        "endpoint": "久久",
        "max_tokens": 4096,
        "timeout": 300,
        "max_retries": 1,
    },
}


def load_config(config_path: Path | None = None) -> dict:
    """Load project llm_config.yaml, falling back to defaults if absent."""
    path = config_path or _find_project_config_path()
    if path is None or not path.exists():
        return _copy_defaults()
    loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(loaded, dict):
        return _copy_defaults()
    return loaded


def resolve_role(role: str, config: dict | None = None) -> dict:
    """Resolve an LLM role to endpoint, token, timeout, and fallback settings."""
    cfg = config or load_config()
    defaults = cfg.get("defaults", {}) if isinstance(cfg.get("defaults", {}), dict) else {}
    role_cfg = {}
    roles = cfg.get("roles", {})
    if isinstance(roles, dict):
        candidate = roles.get(role)
        if isinstance(candidate, dict):
            role_cfg = candidate

    return {
        "endpoint": str(role_cfg.get("primary") or defaults.get("endpoint") or "久久"),
        "max_tokens": int(role_cfg.get("max_tokens") or defaults.get("max_tokens") or 4096),
        "timeout": int(role_cfg.get("timeout") or defaults.get("timeout") or 300),
        "fallback": _string_list(role_cfg.get("fallback")),
    }


def call_llm_with_fallback(
    prompt: str,
    *,
    role: str | None = None,
    endpoint: str | None = None,
    max_tokens: int | None = None,
    timeout: int | None = None,
) -> str:
    """Call ask-llm with optional role-based fallback on failures or empty output."""
    config = load_config()
    if endpoint is not None:
        defaults = config.get("defaults", {}) if isinstance(config.get("defaults", {}), dict) else {}
        resolved_endpoint = endpoint
        resolved_max_tokens = max_tokens or int(defaults.get("max_tokens") or 4096)
        resolved_timeout = timeout or int(defaults.get("timeout") or 300)
        fallbacks: list[str] = []
    else:
        resolved = resolve_role(role or "", config)
        resolved_endpoint = resolved["endpoint"]
        resolved_max_tokens = max_tokens or resolved["max_tokens"]
        resolved_timeout = timeout or resolved["timeout"]
        fallbacks = resolved["fallback"] if role is not None else []

    attempts = [resolved_endpoint, *fallbacks]
    errors: list[str] = []
    for candidate in attempts:
        try:
            return _call_ask_llm(
                prompt,
                endpoint=candidate,
                max_tokens=resolved_max_tokens,
                timeout=resolved_timeout,
            )
        except RuntimeError as exc:
            errors.append(f"{candidate}: {exc}")
    raise RuntimeError("ask-llm failed for all endpoints: " + " | ".join(errors))


def _call_ask_llm(prompt: str, *, endpoint: str, max_tokens: int, timeout: int) -> str:
    cmd = [
        "ask-llm",
        endpoint,
        "--max-tokens",
        str(max_tokens),
        "-s",
    ]
    proc = subprocess.run(
        cmd,
        input=prompt,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"ask-llm {endpoint} failed (exit={proc.returncode}): {proc.stderr[:500]}"
        )
    if not proc.stdout.strip():
        raise RuntimeError(f"ask-llm {endpoint} returned empty output")
    return proc.stdout


def _find_project_config_path() -> Path | None:
    for parent in [Path.cwd(), *Path.cwd().parents]:
        config_path = parent / "llm_config.yaml"
        if config_path.exists():
            return config_path
        if (parent / "AGENTS.md").exists():
            return config_path
    module_path = Path(__file__).resolve()
    for parent in module_path.parents:
        config_path = parent / "llm_config.yaml"
        if config_path.exists():
            return config_path
        if (parent / "AGENTS.md").exists():
            return config_path
    return None


def _copy_defaults() -> dict:
    return {
        "version": _HARDCODED_DEFAULTS["version"],
        "roles": dict(_HARDCODED_DEFAULTS["roles"]),
        "defaults": dict(_HARDCODED_DEFAULTS["defaults"]),
    }


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if isinstance(item, str) and item]
