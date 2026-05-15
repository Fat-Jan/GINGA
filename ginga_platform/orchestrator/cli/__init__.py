"""ginga_platform.orchestrator.cli — Sprint 1 MVP CLI.

提供 init / run / status 三个子命令，端到端跑通"输入创意 → 输出第一章".

依赖：
    - ginga_platform.orchestrator.runner.state_io.StateIO（唯一 state 入口）
    - ask-llm（外部 CLI，用于 LLM 生成；默认端点为 久久 / qwen3.6-max-preview-nothinking）

约束：
    - 不直接读写 state 文件，全部经 StateIO
    - 不绕过 contract.yaml 的 forbidden_mutation 约束
    - LLM 调用集中在 demo_pipeline.run_chapter_draft
"""
