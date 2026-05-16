"""Tests for project-local LLM config loading and ask-llm fallback calls."""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock


class LlmConfigTest(unittest.TestCase):
    def test_load_config_from_project_root(self) -> None:
        from ginga_platform.orchestrator.cli.llm_config import load_config

        config = load_config()

        self.assertEqual(config["version"], "1.0")
        self.assertEqual(config["defaults"]["endpoint"], "久久")
        self.assertEqual(config["roles"]["prose_writer"]["primary"], "久久")

    def test_load_config_missing_file_returns_defaults(self) -> None:
        from ginga_platform.orchestrator.cli.llm_config import load_config

        with tempfile.TemporaryDirectory() as tmp:
            config = load_config(Path(tmp) / "missing.yaml")

        self.assertEqual(config["defaults"]["endpoint"], "久久")
        self.assertEqual(config["defaults"]["max_tokens"], 4096)
        self.assertEqual(config["defaults"]["timeout"], 300)

    def test_resolve_role_prose_writer(self) -> None:
        from ginga_platform.orchestrator.cli.llm_config import load_config, resolve_role

        role = resolve_role("prose_writer", load_config())

        self.assertEqual(
            role,
            {
                "endpoint": "久久",
                "max_tokens": 12000,
                "timeout": 300,
                "fallback": ["ioll-mix"],
            },
        )

    def test_resolve_role_unknown_falls_back_to_defaults(self) -> None:
        from ginga_platform.orchestrator.cli.llm_config import resolve_role

        role = resolve_role(
            "unknown",
            {
                "defaults": {
                    "endpoint": "default-endpoint",
                    "max_tokens": 123,
                    "timeout": 45,
                }
            },
        )

        self.assertEqual(
            role,
            {
                "endpoint": "default-endpoint",
                "max_tokens": 123,
                "timeout": 45,
                "fallback": [],
            },
        )

    def test_call_llm_with_fallback_primary_success(self) -> None:
        from ginga_platform.orchestrator.cli import llm_config

        completed = subprocess.CompletedProcess(
            args=["ask-llm"],
            returncode=0,
            stdout="primary output",
            stderr="",
        )
        with mock.patch.object(llm_config, "load_config", return_value=_sample_config()):
            with mock.patch.object(llm_config.subprocess, "run", return_value=completed) as run:
                output = llm_config.call_llm_with_fallback("prompt", role="prose_writer")

        self.assertEqual(output, "primary output")
        self.assertEqual(run.call_count, 1)
        self.assertEqual(run.call_args.args[0][1], "primary")
        self.assertEqual(run.call_args.kwargs["timeout"], 30)

    def test_call_llm_with_fallback_primary_fails_uses_fallback(self) -> None:
        from ginga_platform.orchestrator.cli import llm_config

        primary = subprocess.CompletedProcess(
            args=["ask-llm"],
            returncode=1,
            stdout="",
            stderr="gateway timeout",
        )
        fallback = subprocess.CompletedProcess(
            args=["ask-llm"],
            returncode=0,
            stdout="fallback output",
            stderr="",
        )
        with mock.patch.object(llm_config, "load_config", return_value=_sample_config()):
            with mock.patch.object(llm_config.subprocess, "run", side_effect=[primary, fallback]) as run:
                output = llm_config.call_llm_with_fallback("prompt", role="prose_writer")

        self.assertEqual(output, "fallback output")
        self.assertEqual([call.args[0][1] for call in run.call_args_list], ["primary", "fallback-a"])

    def test_call_llm_with_fallback_all_fail_raises(self) -> None:
        from ginga_platform.orchestrator.cli import llm_config

        failures = [
            subprocess.CompletedProcess(args=["ask-llm"], returncode=1, stdout="", stderr="bad primary"),
            subprocess.CompletedProcess(args=["ask-llm"], returncode=0, stdout="   ", stderr=""),
        ]
        with mock.patch.object(llm_config, "load_config", return_value=_sample_config()):
            with mock.patch.object(llm_config.subprocess, "run", side_effect=failures):
                with self.assertRaises(RuntimeError) as ctx:
                    llm_config.call_llm_with_fallback("prompt", role="prose_writer")

        message = str(ctx.exception)
        self.assertIn("primary", message)
        self.assertIn("fallback-a", message)
        self.assertIn("bad primary", message)
        self.assertIn("empty output", message)


def _sample_config() -> dict:
    return {
        "roles": {
            "prose_writer": {
                "primary": "primary",
                "fallback": ["fallback-a"],
                "max_tokens": 99,
                "timeout": 30,
            }
        },
        "defaults": {
            "endpoint": "default",
            "max_tokens": 10,
            "timeout": 5,
        },
    }


if __name__ == "__main__":
    unittest.main()
