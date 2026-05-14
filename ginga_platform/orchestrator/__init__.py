"""platform.orchestrator — workflow runner + meta integration + skill router.

Public sub-packages:
    runner            DSL parser, step dispatcher, state IO (jury-1 P0 唯一入口).
    meta_integration  guard_invoker / checker_invoker hooks.
    router            skill router (priority-based fan-out across skills).

See ARCHITECTURE.md §4.1 for the子层 split rationale (jury-1 P0 修订).
"""

__all__ = ["runner", "meta_integration", "router"]
