"""Asset-backed capability providers for the P2-7 platform runner.

Providers are deterministic and offline-safe. They never mutate ``StateIO``
directly; they return ``state_updates`` for ``step_dispatch`` to whitelist and
apply through ``StateIO``.
"""

from __future__ import annotations

import re
from copy import deepcopy
from pathlib import Path
from typing import Any, Callable, Dict, Mapping

import yaml


CapabilityFn = Callable[[Mapping[str, Any], Mapping[str, Any]], Dict[str, Any]]

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_ASSETS_ROOT = _REPO_ROOT / "foundation" / "assets" / "capabilities"

A_BRAINSTORM_ID = "base-methodology-creative-brainstorm"
B_STORY_DNA_ID = "base-template-story-dna"
C_WORLDVIEW_ID = "base-template-worldview"
D_PROTAGONIST_ID = "base-template-protagonist"
E_OUTLINE_ID = "base-template-outline"
F_STATE_INIT_ID = "base-template-state-init"
G_CHAPTER_DRAFT_ID = "base-card-chapter-draft"
H_CHAPTER_SETTLE_ID = "base-template-chapter-settle"
R1_STYLE_POLISH_ID = "base-methodology-style-polish"
R2_CONSISTENCY_CHECK_ID = "base-methodology-consistency-check"
R3_FINAL_PACK_ID = "base-methodology-final-pack"
V1_RELEASE_CHECK_ID = "base-checker-dod-final"

_ALL_CAPABILITY_IDS: tuple[str, ...] = (
    A_BRAINSTORM_ID,
    B_STORY_DNA_ID,
    C_WORLDVIEW_ID,
    D_PROTAGONIST_ID,
    E_OUTLINE_ID,
    F_STATE_INIT_ID,
    G_CHAPTER_DRAFT_ID,
    H_CHAPTER_SETTLE_ID,
    R1_STYLE_POLISH_ID,
    R2_CONSISTENCY_CHECK_ID,
    R3_FINAL_PACK_ID,
    V1_RELEASE_CHECK_ID,
)

_REQUIRED_LOCKED_DOMAINS = ("STORY_DNA", "WORLD", "PLOT_ARCHITECTURE")
_REQUIRED_ENTITY_DOMAINS = (
    "CHARACTER_STATE",
    "RESOURCE_LEDGER",
    "FORESHADOW_STATE",
    "GLOBAL_SUMMARY",
)
_BLOCKING_AUDIT_SEVERITIES = {"error", "block"}
_BLOCKING_AUDIT_ACTIONS = {"block", "rollback"}

_HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
_FORESHADOW_RE = re.compile(
    r"<!--\s*foreshadow:\s*id=(?P<id>[\w\-]+)\s+"
    r"planted_ch=(?P<planted_ch>\d+)\s+"
    r"expected_payoff=(?P<expected_payoff>\d+)\s+"
    r"summary=(?P<summary>.+?)\s*-->",
    re.IGNORECASE,
)


def build_asset_capability_providers(
    assets_root: Path | str = _DEFAULT_ASSETS_ROOT,
) -> dict[str, CapabilityFn]:
    """Return all MVP 12-step capability handlers backed by asset cards."""

    root = Path(assets_root)
    manifests = {capability_id: _load_manifest(root, capability_id) for capability_id in _ALL_CAPABILITY_IDS}
    builders: dict[str, Callable[[Mapping[str, Any], Mapping[str, Any], Mapping[str, Any]], dict[str, Any]]] = {
        A_BRAINSTORM_ID: _provide_brainstorm,
        B_STORY_DNA_ID: _provide_story_dna,
        C_WORLDVIEW_ID: _provide_worldview,
        D_PROTAGONIST_ID: _provide_character_seed,
        E_OUTLINE_ID: _provide_outline,
        F_STATE_INIT_ID: _provide_state_init,
        G_CHAPTER_DRAFT_ID: _provide_chapter_draft,
        H_CHAPTER_SETTLE_ID: h_chapter_settle_provider,
        R1_STYLE_POLISH_ID: r1_style_polish_provider,
        R2_CONSISTENCY_CHECK_ID: r2_consistency_check_provider,
        R3_FINAL_PACK_ID: r3_final_pack_provider,
        V1_RELEASE_CHECK_ID: v1_release_check_provider,
    }
    return {
        capability_id: _wrap_provider(manifests[capability_id], builders[capability_id])
        for capability_id in _ALL_CAPABILITY_IDS
    }


def _wrap_provider(
    manifest: Mapping[str, Any],
    builder: Callable[[Mapping[str, Any], Mapping[str, Any], Mapping[str, Any]], dict[str, Any]],
) -> CapabilityFn:
    def _handler(inputs: Mapping[str, Any], ctx: Mapping[str, Any]) -> dict[str, Any]:
        out = deepcopy(builder(inputs, ctx, manifest))
        out.setdefault("provider", "asset-backed")
        out["asset_ref"] = _asset_ref(manifest)
        out.setdefault("state_updates", {})
        return out

    return _handler


def _load_manifest(root: Path, capability_id: str) -> dict[str, Any]:
    for suffix in (".md", ".yaml"):
        path = root / f"{capability_id}{suffix}"
        if not path.exists():
            continue
        if suffix == ".md":
            raw = _read_frontmatter(path)
        else:
            raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if not isinstance(raw, dict):
            raise ValueError(f"capability manifest must be a mapping: {path}")
        if raw.get("id") != capability_id:
            raise ValueError(f"capability manifest id mismatch: {path}")
        raw["_asset_path"] = str(path.relative_to(_REPO_ROOT))
        return raw
    raise FileNotFoundError(f"capability asset not found: {root / capability_id}")


def _read_frontmatter(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError(f"capability asset missing YAML frontmatter: {path}")
    end = text.find("\n---\n", 4)
    if end == -1:
        raise ValueError(f"capability asset has unterminated YAML frontmatter: {path}")
    raw = yaml.safe_load(text[4:end]) or {}
    if not isinstance(raw, dict):
        raise ValueError(f"capability asset frontmatter must be mapping: {path}")
    return raw


def _asset_ref(manifest: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "id": str(manifest.get("id", "")),
        "path": str(manifest.get("_asset_path", "")),
        "version": str(manifest.get("version", "")),
        "title": str(manifest.get("title", "")),
    }


def _asset_ref_path_for_id(capability_id: str) -> str:
    for suffix in (".md", ".yaml"):
        path = _DEFAULT_ASSETS_ROOT / f"{capability_id}{suffix}"
        if path.exists():
            return str(path.relative_to(_REPO_ROOT))
    return str(_DEFAULT_ASSETS_ROOT / f"{capability_id}.md")


def _provider_output(
    capability_id: str,
    manifest: Mapping[str, Any] | None,
    *,
    result: Any,
    state_updates: Mapping[str, Any],
    audit_intents: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "provider": "asset-backed",
        "capability_id": capability_id,
        "asset_ref": _asset_ref(manifest) if manifest is not None else _asset_ref_path_for_id(capability_id),
        "result": deepcopy(result),
        "state_updates": deepcopy(dict(state_updates)),
        "audit_intents": deepcopy(list(audit_intents or [])),
    }


# ---------------------------------------------------------------------------
# A-F setup providers
# ---------------------------------------------------------------------------


def _provide_brainstorm(
    inputs: Mapping[str, Any],
    ctx: Mapping[str, Any],
    manifest: Mapping[str, Any],
) -> dict[str, Any]:
    params = _params(ctx)
    seed_text = _seed_text(inputs, params)
    topic = _topic(params, seed_text)
    premise = str(params.get("premise") or params.get("idea") or params.get("seed") or seed_text).strip()
    if not premise:
        premise = "一个主角被迫面对失控秩序，并用代价换取自由"
    protagonist = _protagonist_from_text(seed_text)
    antagonist = _antagonist_from_text(seed_text)
    motif = _motif_from_text(seed_text)
    core_idea = f"{topic}：{_shorten(premise, 64)}"
    payload = {
        "asset_ref": _asset_ref(manifest),
        "seed_input": seed_text,
        "topic": topic,
        "core_idea": core_idea,
        "protagonist_seed": protagonist,
        "antagonist_seed": antagonist,
        "central_motif": motif,
        "conflict_candidates": [
            f"{protagonist} vs {antagonist}",
            f"{motif}的代价 vs {protagonist}的自由",
            f"{topic}秩序 vs 个体选择",
        ],
        "tone_candidates": _tones_for_topic(topic, seed_text),
        "raw_seeds": _keywords(seed_text, topic),
    }
    return {
        "result": {"asset_ref": payload["asset_ref"], "summary": core_idea},
        "state_updates": {"retrieved.brainstorm": payload},
    }


def _provide_story_dna(
    inputs: Mapping[str, Any],
    ctx: Mapping[str, Any],
    manifest: Mapping[str, Any],
) -> dict[str, Any]:
    brainstorm = _mapping(inputs.get("retrieved.brainstorm"))
    params = _params(ctx)
    topic = str(brainstorm.get("topic") or _topic(params, _seed_text(inputs, params)))
    seed = _seed_text(inputs, params) + " " + str(brainstorm.get("core_idea", ""))
    protagonist = str(brainstorm.get("protagonist_seed") or _protagonist_from_text(seed))
    antagonist = str(brainstorm.get("antagonist_seed") or _antagonist_from_text(seed))
    motif = str(brainstorm.get("central_motif") or _motif_from_text(seed))
    explicit_premise = str(params.get("premise") or "").strip()
    if explicit_premise:
        premise = explicit_premise if topic in explicit_premise else f"{topic}中，{explicit_premise}"
    else:
        premise = (
            f"{topic}中，{protagonist}发现{motif}正在被{antagonist}垄断，"
            f"必须用一次不可逆的选择夺回自我与真相。"
        )
    conflict_engine = f"{protagonist}的自由意志 vs {antagonist}掌控的{motif}秩序"
    payload = {
        "asset_ref": _asset_ref(manifest),
        "premise": premise,
        "core_conflict": conflict_engine,
        "conflict_engine": conflict_engine,
        "payoff_promise": f"逐步揭开{motif}真相、兑现反抗代价，并把开局钩子推向可持续升级。",
        "audience": _audience_for_topic(topic),
        "topic": topic,
        "source_brainstorm_ref": _mapping(brainstorm.get("asset_ref")),
        "word_target": _int_param(params, "word_target", 500_000),
    }
    return {
        "result": {"asset_ref": payload["asset_ref"], "premise": premise},
        "state_updates": {"locked.STORY_DNA": payload},
    }


def _provide_worldview(
    inputs: Mapping[str, Any],
    ctx: Mapping[str, Any],
    manifest: Mapping[str, Any],
) -> dict[str, Any]:
    story_dna = _mapping(inputs.get("locked.STORY_DNA"))
    params = _params(ctx)
    seed = _seed_text(inputs, params) + " " + str(story_dna.get("premise", ""))
    topic = _topic(params, seed)
    motif = _motif_from_text(seed)
    protagonist = _protagonist_from_text(seed)
    antagonist = _antagonist_from_text(seed)
    genre = {
        "asset_ref": _asset_ref(manifest),
        "topic": [topic],
        "style_lock": {
            "tone": _tones_for_topic(topic, seed),
            "forbidden_styles": ["都市腔", "游戏系统播报腔", "轻小说吐槽腔"],
            "anchor_phrases": _keywords(seed, topic)[:4],
        },
    }
    world = {
        "asset_ref": _asset_ref(manifest),
        "power_system": f"{motif}以债、誓约和记忆为媒介运转；越接近真相，代价越具体。",
        "physical": f"{topic}舞台围绕{motif}异常区展开，边界会吞没未完成的承诺。",
        "social": f"{antagonist}控制解释权，普通人用沉默换取生存，{protagonist}被迫成为裂缝。",
        "metaphor": f"{motif}不是装饰，而是角色选择留下的账本。",
        "factions": [
            {"id": "order", "name": antagonist, "role": "压迫性秩序"},
            {"id": "undercurrent", "name": f"{protagonist}的临时同盟", "role": "高风险协助者"},
        ],
        "geography": f"{topic}核心场景：{_place_from_text(seed)}",
        "history": f"{motif}在旧时代被封存，如今因{protagonist}的选择重新显影。",
        "taboos": [f"不得公开质疑{motif}来源", "不得跳过代价直接获得力量"],
    }
    return {
        "result": {"asset_ref": _asset_ref(manifest), "world_axis": [world["physical"], world["social"]]},
        "state_updates": {"locked.GENRE_LOCKED": genre, "locked.WORLD": world},
    }


def _provide_character_seed(
    inputs: Mapping[str, Any],
    ctx: Mapping[str, Any],
    manifest: Mapping[str, Any],
) -> dict[str, Any]:
    story_dna = _mapping(inputs.get("locked.STORY_DNA"))
    world = _mapping(inputs.get("locked.WORLD"))
    params = _params(ctx)
    seed = _seed_text(inputs, params) + " " + str(story_dna.get("premise", "")) + " " + str(world.get("power_system", ""))
    protagonist_name = _protagonist_from_text(seed)
    antagonist = _antagonist_from_text(seed)
    motif = _motif_from_text(seed)
    payload = {
        "asset_ref": _asset_ref(manifest),
        "protagonist": {
            "id": _slugify(protagonist_name),
            "name": protagonist_name,
            "drives": [f"查清{motif}真相", f"摆脱{antagonist}的定义", "保护一个会让自己付出代价的人或承诺"],
            "inventory": [{"item": f"{motif}残片", "count": 1}],
            "abilities": [{"skill": f"{motif}感知", "level": 1, "cooldown": 0}],
            "body": {"hp": 100, "mp": 50, "status": ["未稳定", "被追踪"]},
            "psyche": {"mood": "警觉", "beliefs": ["真相必须带着代价验证"], "traumas": [f"曾被{antagonist}改写选择"]},
            "relations": [{"target": "order", "type": "enemy", "score": -80}],
            "events": [],
            "iq_level": "adaptive",
        },
        "supporting": [{"id": "witness", "name": f"{motif}见证者", "role": "提供线索但隐藏代价"}],
        "relationship_edges": [
            {"from": _slugify(protagonist_name), "to": "order", "type": "hunted_by"},
            {"from": _slugify(protagonist_name), "to": "witness", "type": "uses_and_doubts"},
        ],
    }
    return {
        "result": {"asset_ref": payload["asset_ref"], "protagonist": protagonist_name},
        "state_updates": {"entity_runtime.CHARACTER_STATE": payload},
    }


def _provide_outline(
    inputs: Mapping[str, Any],
    ctx: Mapping[str, Any],
    manifest: Mapping[str, Any],
) -> dict[str, Any]:
    story_dna = _mapping(inputs.get("locked.STORY_DNA"))
    world = _mapping(inputs.get("locked.WORLD"))
    char_state = _mapping(inputs.get("entity_runtime.CHARACTER_STATE"))
    protagonist = _mapping(char_state.get("protagonist")).get("name") or _protagonist_from_text(str(story_dna))
    motif = _motif_from_text(str(world.get("power_system", "")) + " " + str(story_dna.get("premise", "")))
    acts = [
        {"name": "第一幕：触发与追猎", "chapters": "1-30", "goal": f"{protagonist}理解{motif}的第一层代价"},
        {"name": "第二幕：同盟与反噬", "chapters": "31-150", "goal": "把个人危机扩展成秩序裂缝"},
        {"name": "第三幕：改写与偿还", "chapters": "151-300", "goal": f"用最终选择重写{motif}规则"},
    ]
    pivots = [
        {"ch": 1, "type": "起", "beat": f"{protagonist}在{_place_from_text(str(world))}遭遇{motif}异常。"},
        {"ch": 30, "type": "转", "beat": f"第一次证明{motif}背后有可被利用的漏洞。"},
        {"ch": 150, "type": "破", "beat": "同盟代价爆发，主角必须牺牲一条原计划。"},
        {"ch": 300, "type": "合", "beat": f"{protagonist}偿还代价并改写核心规则。"},
    ]
    foreshadows = [
        {"id": "FH-001", "planted_ch": 1, "expected_payoff": 30, "summary": f"{motif}残片只对{protagonist}响应"},
        {"id": "FH-002", "planted_ch": 3, "expected_payoff": 90, "summary": "见证者隐瞒了第一次失败的真相"},
    ]
    payload = {
        "asset_ref": _asset_ref(manifest),
        "acts": acts,
        "pivot_points": pivots,
        "foreshadows": foreshadows,
        "chapter_runway": [
            {"ch": 1, "intent": "开局钩子 + 代价显影"},
            {"ch": 2, "intent": "追猎压力 + 第一个选择"},
            {"ch": 3, "intent": "同盟登场 + 隐瞒伏笔"},
        ],
    }
    return {
        "result": {"asset_ref": payload["asset_ref"], "acts": [act["name"] for act in acts]},
        "state_updates": {"locked.PLOT_ARCHITECTURE": payload},
    }


def _provide_state_init(
    inputs: Mapping[str, Any],
    ctx: Mapping[str, Any],
    manifest: Mapping[str, Any],
) -> dict[str, Any]:
    locked = _mapping(inputs.get("locked"))
    char_state = _mapping(inputs.get("entity_runtime.CHARACTER_STATE"))
    story_dna = _mapping(locked.get("STORY_DNA"))
    plot = _mapping(locked.get("PLOT_ARCHITECTURE"))
    topic = _topic(_params(ctx), str(story_dna.get("premise", "")))
    foreshadows = plot.get("foreshadows") if isinstance(plot.get("foreshadows"), list) else []
    if not foreshadows:
        foreshadows = [{"id": "FH-001", "planted_ch": 1, "expected_payoff": 30, "summary": "开局核心异常待兑现"}]
    normalized_pool = []
    for item in foreshadows:
        if not isinstance(item, Mapping):
            continue
        hook_id = str(item.get("id") or item.get("hook_id") or f"FH-{len(normalized_pool) + 1:03d}")
        normalized_pool.append(
            {
                "id": hook_id,
                "hook_id": hook_id,
                "planted_ch": _as_int(item.get("planted_ch"), 1),
                "expected_payoff": _as_int(item.get("expected_payoff"), 30),
                "status": str(item.get("status") or "open"),
                "summary": str(item.get("summary") or ""),
                "asset_ref": _asset_ref(manifest),
            }
        )
    workspace_ref = _asset_ref(manifest)
    protagonist = _mapping(char_state.get("protagonist")).get("name") or "主角"
    state_updates = {
        "entity_runtime.RESOURCE_LEDGER": {"asset_ref": workspace_ref, "particles": 0, "currency": 0, "items": []},
        "entity_runtime.FORESHADOW_STATE": {"asset_ref": workspace_ref, "pool": normalized_pool},
        "entity_runtime.GLOBAL_SUMMARY": {"asset_ref": workspace_ref, "total_words": 0, "arc_summaries": []},
        "workspace.task_plan": {
            "asset_ref": workspace_ref,
            "mode": "planning_with_files",
            "items": [
                {"id": "plan-001", "status": "todo", "task": "完成第 1 章开局钩子与状态自检"},
                {"id": "plan-002", "status": "todo", "task": "保持 STORY_DNA / WORLD / CHARACTER_STATE 对齐"},
                {"id": "plan-003", "status": "todo", "task": "每章至少推进或校验一个伏笔"},
            ],
        },
        "workspace.findings": {
            "asset_ref": workspace_ref,
            "notes": [f"题材入口：{topic}", f"主角状态入口：{protagonist}", f"核心承诺：{story_dna.get('payoff_promise', '')}"],
        },
        "workspace.progress": {
            "asset_ref": workspace_ref,
            "current_phase": f"{topic} runtime initialized",
            "completed_steps": ["A_brainstorm", "B_premise_lock", "C_world_build", "D_character_seed", "E_outline"],
            "next_step": "G_chapter_draft",
        },
    }
    return {
        "result": {"asset_ref": _asset_ref(manifest), "workspace": "initialized"},
        "state_updates": state_updates,
    }


def _provide_chapter_draft(
    inputs: Mapping[str, Any],
    ctx: Mapping[str, Any],
    manifest: Mapping[str, Any],
) -> dict[str, Any]:
    locked = _mapping(inputs.get("locked"))
    entity = _entity_runtime(inputs)
    story_dna = _mapping(locked.get("STORY_DNA"))
    protagonist = _mapping(_mapping(entity.get("CHARACTER_STATE")).get("protagonist"))
    name = str(protagonist.get("name") or _protagonist_from_text(str(story_dna)) or "未命名主角")
    premise = str(story_dna.get("premise") or "主角被迫用代价换取第一章行动资格")
    chapter_no = _chapter_no(ctx)
    chapter_text = (
        "| 写作自检 | 内容 |\n|---|---|\n"
        f"| 当前锚定 | {premise} |\n"
        "| 当前微粒 | 0 |\n"
        "| 预计微粒变化 | +0 |\n"
        "| 主要冲突 | 个体选择 / 旧秩序 / 可追踪代价 |\n\n"
        f"# 第{chapter_no}章 · 代价开场\n\n"
        f"{name}停在裂隙边缘，终于明白这不是一次普通开局。{_shorten(premise, 96)}。"
        "他没有得到解释，只得到一个必须立刻偿还的选择。\n"
        f"<!-- foreshadow: id=FH-{chapter_no:03d} planted_ch={chapter_no} "
        f"expected_payoff={chapter_no + 29} summary=代价开场的旧秩序痕迹 -->\n"
    )
    return {
        "result": {"asset_ref": _asset_ref(manifest), "chapter_chars": len(chapter_text)},
        "state_updates": {"workspace.chapter_text": chapter_text},
    }


# ---------------------------------------------------------------------------
# H/R/V providers
# ---------------------------------------------------------------------------


def h_chapter_settle_provider(
    inputs: Mapping[str, Any],
    ctx: Mapping[str, Any],
    manifest: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    chapter_text = _chapter_text_from_inputs(inputs)
    chapter_no = _chapter_no(ctx)
    entity = _entity_runtime(inputs)
    character_state = deepcopy(_mapping(entity.get("CHARACTER_STATE")))
    resource_ledger = deepcopy(_mapping(entity.get("RESOURCE_LEDGER")))
    foreshadow_state = deepcopy(_mapping(entity.get("FORESHADOW_STATE")))

    particle_delta = _particle_delta_from_text(chapter_text)
    resource_ledger["particles"] = _as_int(resource_ledger.get("particles"), 0) + particle_delta
    items = list(resource_ledger.get("items") or [])
    if particle_delta:
        items.append({"type": "particles", "delta": particle_delta, "from": f"ch{chapter_no}", "source": "asset_provider:H_chapter_settle"})
    resource_ledger["items"] = items

    new_hooks = _foreshadows_from_text(chapter_text)
    pool = _merge_foreshadow_pool(foreshadow_state.get("pool") or [], new_hooks, chapter_no)
    foreshadow_state["pool"] = pool

    protagonist = character_state.setdefault("protagonist", {})
    if not isinstance(protagonist, dict):
        protagonist = {}
        character_state["protagonist"] = protagonist
    events = list(protagonist.get("events") or [])
    events.append({"ch": chapter_no, "type": "settle", "impact": _text_summary(chapter_text)})
    protagonist["events"] = events
    protagonist.setdefault("psyche", {"mood": "警觉"})

    progress = f"# Progress\n\n- 第 {chapter_no} 章结算：{_text_summary(chapter_text)}"
    progress += f"；微粒变化 {particle_delta:+d}"
    if new_hooks:
        progress += f"；新增伏笔 {', '.join(hook['id'] for hook in new_hooks)}"
    progress += "\n"
    return _provider_output(
        H_CHAPTER_SETTLE_ID,
        manifest,
        result={"pass": True, "chapter_no": chapter_no, "particle_delta": particle_delta, "new_hook_ids": [h["id"] for h in new_hooks]},
        state_updates={
            "entity_runtime.CHARACTER_STATE": character_state,
            "entity_runtime.FORESHADOW_STATE": foreshadow_state,
            "entity_runtime.RESOURCE_LEDGER": resource_ledger,
            "workspace.progress": progress,
        },
    )


def r1_style_polish_provider(
    inputs: Mapping[str, Any],
    ctx: Mapping[str, Any],  # noqa: ARG001
    manifest: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    chapter_text = _chapter_text_from_inputs(inputs)
    locked = _locked_state(inputs)
    polished = _polish_preserving_comments(chapter_text)
    polished = _ensure_style_anchors(polished, _style_anchor_phrases(locked))
    return _provider_output(
        R1_STYLE_POLISH_ID,
        manifest,
        result={"changed": polished != chapter_text, "chars": len(polished)},
        state_updates={"workspace.chapter_text": polished},
    )


def r2_consistency_check_provider(
    inputs: Mapping[str, Any],
    ctx: Mapping[str, Any],
    manifest: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    chapter_text = _chapter_text_from_inputs(inputs)
    locked = _locked_state(inputs)
    entity = _entity_runtime(inputs)
    issues: list[dict[str, Any]] = []
    checked = _chapter_quality_details(chapter_text, locked)
    for marker in _forbidden_markers(locked):
        if marker and marker in chapter_text:
            issues.append({"code": "forbidden_style_marker", "severity": "warn", "marker": marker})
    protagonist = _mapping(_mapping(entity.get("CHARACTER_STATE")).get("protagonist"))
    name = str(protagonist.get("name") or protagonist.get("id") or "")
    if name and name not in chapter_text:
        issues.append({"code": "missing_character_anchor", "severity": "warn", "name": name})
    world_anchors = checked["world_anchors"]
    if world_anchors and not checked["has_world_anchor"]:
        issues.append({"code": "missing_world_anchor", "severity": "warn", "anchors": world_anchors[:5]})
    if checked["foreshadow_count"] == 0:
        issues.append({"code": "missing_foreshadow_annotation", "severity": "warn"})
    if checked["particle_delta"] is None:
        issues.append({"code": "particle_delta_unparseable", "severity": "info"})
    report = {
        "pass": not issues,
        "chapter_no": _chapter_no(ctx),
        "issues": issues,
        "summary": _quality_summary(issues, checked),
        "recommendations": _recommendations_for_issues(issues),
        "consistency_report": {
            "checked": ["workspace.chapter_text", "locked", "entity_runtime"],
            "checked_details": {
                "body_paragraph_count": checked["body_paragraph_count"],
                "foreshadow_count": checked["foreshadow_count"],
                "has_world_anchor": checked["has_world_anchor"],
                "particle_delta": checked["particle_delta"],
                "world_anchors": world_anchors[:5],
            },
            "issue_count": len(issues),
        },
    }
    report["readability_report"] = _readability_report(issues, checked, chapter_text)
    return _provider_output(
        R2_CONSISTENCY_CHECK_ID,
        manifest,
        result=report,
        state_updates={},
        audit_intents=[
            {
                "source": "asset_provider:R2_consistency_check",
                "severity": "info" if report["pass"] else "warn",
                "msg": f"R2 consistency {'PASS' if report['pass'] else 'WARN'}: {len(issues)} issue(s)",
                "action": "log",
                "payload": {"consistency_report": report},
            }
        ],
    )


def r3_final_pack_provider(
    inputs: Mapping[str, Any],
    ctx: Mapping[str, Any],
    manifest: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    chapter_text = _chapter_text_from_inputs(inputs)
    global_summary = _global_summary(inputs)
    words = _count_text_words(chapter_text)
    arcs = list(global_summary.get("arc_summaries") or [])
    arcs.append({"chapter": _chapter_no(ctx), "summary": _text_summary(chapter_text), "words": words})
    global_summary["total_words"] = _as_int(global_summary.get("total_words"), 0) + words
    global_summary["arc_summaries"] = arcs
    return _provider_output(
        R3_FINAL_PACK_ID,
        manifest,
        result={
            "pass": True,
            "chapter_no": _chapter_no(ctx),
            "words": words,
            "summary": arcs[-1]["summary"],
            "summary_source": "workspace.chapter_text",
            "input_summary": _text_summary(chapter_text, limit=120),
            "uncovered_boundaries": [
                "not_real_llm_quality_gate",
                "not_multi_chapter_continuity_gate",
            ],
        },
        state_updates={"entity_runtime.GLOBAL_SUMMARY": global_summary},
    )


def v1_release_check_provider(
    inputs: Mapping[str, Any],
    ctx: Mapping[str, Any],
    manifest: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    report = build_v1_release_report(inputs, ctx)
    if manifest is not None:
        report["asset_ref"] = _asset_ref(manifest)
    return _provider_output(V1_RELEASE_CHECK_ID, manifest, result=report, state_updates={})


def build_v1_release_report(inputs: Mapping[str, Any], ctx: Mapping[str, Any] | None = None) -> dict[str, Any]:
    ctx = ctx or {}
    chapter_text = _chapter_text_from_inputs(inputs)
    locked = _locked_state(inputs)
    entity = _entity_runtime(inputs)
    audit_log = inputs.get("audit_log")
    audit_entries = list(audit_log) if isinstance(audit_log, list) else []
    issues: list[dict[str, Any]] = []
    checked = _chapter_quality_details(chapter_text, locked)

    if not chapter_text.strip():
        issues.append({"code": "chapter_text_empty", "severity": "error", "path": "workspace.chapter_text"})
    elif len(chapter_text.strip()) < 180:
        issues.append(
            {
                "code": "chapter_text_too_short",
                "severity": "warn",
                "path": "workspace.chapter_text",
                "chars": len(chapter_text.strip()),
                "min_chars": 180,
            }
        )
    if checked["body_paragraph_count"] < 2:
        issues.append(
            {
                "code": "body_paragraphs_too_few",
                "severity": "warn",
                "count": checked["body_paragraph_count"],
                "min": 2,
            }
        )
    if checked["foreshadow_count"] == 0:
        issues.append({"code": "foreshadow_annotation_missing", "severity": "warn"})
    locked_present: list[str] = []
    for key in _REQUIRED_LOCKED_DOMAINS:
        if _present(locked.get(key)):
            locked_present.append(key)
        else:
            issues.append({"code": "locked_domain_missing", "severity": "error", "path": f"locked.{key}"})
    locked_present.sort()

    entity_present: list[str] = []
    for key in _REQUIRED_ENTITY_DOMAINS:
        if _present(entity.get(key)):
            entity_present.append(key)
        else:
            issues.append({"code": "entity_runtime_domain_missing", "severity": "error", "path": f"entity_runtime.{key}"})
    entity_present.sort()

    blocking = []
    for entry in audit_entries:
        if not isinstance(entry, Mapping):
            continue
        severity = str(entry.get("severity", "")).lower()
        action = str(entry.get("action", "")).lower()
        if severity in _BLOCKING_AUDIT_SEVERITIES or action in _BLOCKING_AUDIT_ACTIONS:
            blocking.append(entry)
            code = "audit_log_error_entry" if severity == "error" else "audit_log_blocking_entry"
            issues.append(
                {
                    "code": code,
                    "severity": "error",
                    "source": entry.get("source", ""),
                    "audit_severity": entry.get("severity", ""),
                    "audit_action": entry.get("action", ""),
                }
            )
    report = {
        "pass": not issues,
        "provider": "asset-backed",
        "asset_ref": _asset_ref_path_for_id(V1_RELEASE_CHECK_ID),
        "book_id": ctx.get("book_id"),
        "summary": {
            "issue_count": len(issues),
            "blocking_audit_count": len(blocking),
            "chapter_text_chars": len(chapter_text.strip()),
            "body_paragraph_count": checked["body_paragraph_count"],
            "foreshadow_count": checked["foreshadow_count"],
            "world_anchor_count": len(checked["matched_world_anchors"]),
        },
        "inputs_checked": {
            "chapter_text": "present" if chapter_text.strip() else "missing",
            "locked": locked_present,
            "entity_runtime": entity_present,
            "audit_log_entries": len(audit_entries),
            "quality": {
                "body_paragraphs": checked["body_paragraph_count"],
                "foreshadow_count": checked["foreshadow_count"],
                "matched_world_anchors": checked["matched_world_anchors"][:5],
            },
        },
        "issues": issues,
    }
    report["context_snapshot"] = _provider_context_snapshot(
        report,
        ctx,
        checked,
        chapter_text,
        locked_present,
        entity_present,
    )
    report["gap_report"] = _provider_gap_report(report)
    report["residual_risk"] = _provider_residual_risk(ctx)
    report["quality_summary"] = _provider_quality_summary(report)
    return report


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _params(ctx: Mapping[str, Any]) -> dict[str, Any]:
    params = ctx.get("params") if isinstance(ctx, Mapping) else None
    return dict(params) if isinstance(params, Mapping) else {}


def _mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _seed_text(inputs: Mapping[str, Any], params: Mapping[str, Any]) -> str:
    parts = []
    for key in ("topic", "premise", "idea", "seed", "prompt", "user_input"):
        value = params.get(key)
        if value:
            parts.append(str(value))
    for key in ("input", "user_input", "prompt", "seed"):
        value = inputs.get(key)
        if value:
            parts.append(str(value))
    brainstorm = _mapping(inputs.get("retrieved.brainstorm"))
    for key in ("seed_input", "core_idea"):
        value = brainstorm.get(key)
        if value:
            parts.append(str(value))
    return " ".join(part.strip() for part in parts if part and str(part).strip()).strip()


def _chapter_text_from_inputs(inputs: Mapping[str, Any]) -> str:
    for key in ("workspace.chapter_text", "chapter_text"):
        value = inputs.get(key)
        if isinstance(value, str):
            return value
    workspace = _mapping(inputs.get("workspace"))
    value = workspace.get("chapter_text")
    return value if isinstance(value, str) else ""


def _entity_runtime(inputs: Mapping[str, Any]) -> dict[str, Any]:
    entity = _mapping(inputs.get("entity_runtime"))
    for key in _REQUIRED_ENTITY_DOMAINS:
        dotted = inputs.get(f"entity_runtime.{key}")
        if isinstance(dotted, Mapping):
            entity[key] = dict(dotted)
    return deepcopy(entity)


def _locked_state(inputs: Mapping[str, Any]) -> dict[str, Any]:
    locked = _mapping(inputs.get("locked"))
    for key in (*_REQUIRED_LOCKED_DOMAINS, "GENRE_LOCKED"):
        dotted = inputs.get(f"locked.{key}")
        if isinstance(dotted, Mapping):
            locked[key] = dict(dotted)
    return deepcopy(locked)


def _global_summary(inputs: Mapping[str, Any]) -> dict[str, Any]:
    value = inputs.get("entity_runtime.GLOBAL_SUMMARY")
    if isinstance(value, Mapping):
        return deepcopy(dict(value))
    return deepcopy(_mapping(_entity_runtime(inputs).get("GLOBAL_SUMMARY")))


def _chapter_no(ctx: Mapping[str, Any]) -> int:
    raw = ctx.get("chapter_no")
    params = _params(ctx)
    if raw is None:
        raw = params.get("chapter_no")
    return max(_as_int(raw, 1), 1)


def _particle_delta_from_text(text: str) -> int:
    if not text:
        return 0
    for pattern in (
        r"(?:预计微粒变化|当前微粒)\s*\|\s*\+?(-?\d+)",
        r"微粒\s*(?:delta|结算|变化)\s*[:=]\s*([+-]?\d+)",
    ):
        match = re.search(pattern, text)
        if match:
            return _as_int(match.group(1), 0)
    return 0


def _foreshadows_from_text(text: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for match in _FORESHADOW_RE.finditer(text):
        hook_id = match.group("id")
        out.append(
            {
                "id": hook_id,
                "hook_id": hook_id,
                "planted_ch": _as_int(match.group("planted_ch"), 1),
                "expected_payoff": _as_int(match.group("expected_payoff"), 30),
                "status": "open",
                "summary": match.group("summary").strip(),
            }
        )
    return out


def _merge_foreshadow_pool(pool_now: Any, new_hooks: list[dict[str, Any]], chapter_no: int) -> list[Any]:
    rolled: list[Any] = []
    if isinstance(pool_now, list):
        for entry in pool_now:
            if not isinstance(entry, Mapping):
                rolled.append(deepcopy(entry))
                continue
            new_entry = deepcopy(dict(entry))
            expected = new_entry.get("expected_payoff")
            if isinstance(expected, int) and chapter_no >= expected and new_entry.get("status", "open") == "open":
                new_entry["status"] = "tickled"
                new_entry["tickled_at_ch"] = chapter_no
            rolled.append(new_entry)
    existing = {_foreshadow_key(entry) for entry in rolled if isinstance(entry, Mapping)}
    for hook in new_hooks:
        key = _foreshadow_key(hook)
        if key not in existing:
            rolled.append(deepcopy(hook))
            existing.add(key)
    return rolled


def _foreshadow_key(entry: Mapping[str, Any]) -> Any:
    return entry.get("id") or entry.get("hook_id")


def _polish_preserving_comments(text: str) -> str:
    parts: list[str] = []
    cursor = 0
    for match in _HTML_COMMENT_RE.finditer(text):
        parts.append(_polish_plain_text(text[cursor:match.start()]))
        parts.append(match.group(0))
        cursor = match.end()
    parts.append(_polish_plain_text(text[cursor:]))
    return "".join(parts)


def _polish_plain_text(text: str) -> str:
    replacements = (
        ("他感到无比震惊和愤怒", "他指节一紧，怒意压进喉间"),
        ("她感到无比震惊和愤怒", "她指节一紧，怒意压进喉间"),
        ("突然之间", "下一息"),
        ("感到无比", ""),
        ("无比", ""),
        ("非常", ""),
        ("不禁", ""),
        ("可以说", ""),
        ("仿佛就像", "像"),
    )
    out = text
    for old, new in replacements:
        out = out.replace(old, new)
    return out


def _style_anchor_phrases(locked: Mapping[str, Any]) -> list[str]:
    genre = _mapping(locked.get("GENRE_LOCKED"))
    style_lock = _mapping(genre.get("style_lock"))
    anchors = [str(item).strip() for item in style_lock.get("anchor_phrases") or [] if str(item).strip()]
    return _dedupe(anchors)


def _ensure_style_anchors(text: str, anchors: list[str]) -> str:
    missing = [anchor for anchor in anchors if anchor and anchor not in text]
    if not missing:
        return text
    anchor_line = "、".join(missing[:3])
    comment_matches = list(_HTML_COMMENT_RE.finditer(text))
    insertion = f"\n{anchor_line}在暗处回响，像一枚尚未结清的债。\n"
    if comment_matches:
        first = comment_matches[0]
        return text[: first.start()].rstrip() + insertion + "\n" + text[first.start():]
    return text.rstrip() + insertion


def _forbidden_markers(locked: Mapping[str, Any]) -> list[str]:
    genre = _mapping(locked.get("GENRE_LOCKED"))
    style_lock = _mapping(genre.get("style_lock"))
    markers = ["系统提示", "恭喜获得", "叮", "游戏面板", "任务完成"]
    markers.extend(str(item) for item in style_lock.get("forbidden_styles") or [] if item)
    return _dedupe(markers)


def _count_text_words(text: str) -> int:
    cjk = sum(1 for ch in text if "\u4e00" <= ch <= "\u9fff")
    ascii_words = len(re.findall(r"[A-Za-z0-9_]+", text))
    return cjk + ascii_words


def _text_summary(text: str, limit: int = 80) -> str:
    body = _clean_chapter_body(text)
    body = " ".join(body.split())
    return body[:limit] if body else "empty chapter"


def _clean_chapter_body(text: str) -> str:
    body = _HTML_COMMENT_RE.sub("", text)
    kept: list[str] = []
    in_table = False
    for raw_line in body.splitlines():
        line = raw_line.strip()
        if not line:
            in_table = False
            continue
        if line.startswith("|"):
            in_table = True
            continue
        if in_table and re.fullmatch(r"[:\-\s|]+", line):
            continue
        in_table = False
        if line.startswith("#"):
            continue
        kept.append(line)
    return "\n".join(kept)


def _body_paragraphs(text: str) -> list[str]:
    body = _clean_chapter_body(text)
    paragraphs = [" ".join(part.split()) for part in re.split(r"\n\s*\n|(?<=[。！？])\s*\n", body)]
    return [part for part in paragraphs if part]


def _world_anchor_terms(locked: Mapping[str, Any]) -> list[str]:
    world = _mapping(locked.get("WORLD"))
    terms: list[str] = []

    def collect(value: Any) -> None:
        if isinstance(value, Mapping):
            for sub in value.values():
                collect(sub)
        elif isinstance(value, list):
            for sub in value:
                collect(sub)
        elif isinstance(value, str):
            for word in re.findall(r"[A-Za-z0-9]+|[\u4e00-\u9fff]{2,8}", value):
                if len(word) >= 2 and word not in {"一个", "可以", "必须", "通过", "媒介", "规则"}:
                    terms.append(word)

    collect(world)
    return _dedupe(terms)


def _chapter_quality_details(chapter_text: str, locked: Mapping[str, Any]) -> dict[str, Any]:
    anchors = _world_anchor_terms(locked)
    matched = [anchor for anchor in anchors if anchor in chapter_text]
    particle_delta = None if _particle_delta_from_text(chapter_text) == 0 and "预计微粒变化" not in chapter_text else _particle_delta_from_text(chapter_text)
    paragraphs = _body_paragraphs(chapter_text)
    return {
        "body_paragraph_count": len(paragraphs),
        "foreshadow_count": len(_foreshadows_from_text(chapter_text)),
        "world_anchors": anchors,
        "matched_world_anchors": matched,
        "has_world_anchor": bool(matched) if anchors else True,
        "particle_delta": particle_delta,
    }


def _quality_summary(issues: list[dict[str, Any]], checked: Mapping[str, Any]) -> str:
    if not issues:
        return (
            f"离线一致性检查通过：正文段落 {checked['body_paragraph_count']}，"
            f"伏笔标注 {checked['foreshadow_count']}。"
        )
    return f"离线一致性检查发现 {len(issues)} 个需关注项，先处理高影响锚点和伏笔追踪。"


def _recommendations_for_issues(issues: list[dict[str, Any]]) -> list[str]:
    mapping = {
        "forbidden_style_marker": "删除游戏化或禁用文风标记，改成场景动作与代价表达。",
        "missing_character_anchor": "补回主角名字或稳定代称，避免章节游离于角色状态之外。",
        "missing_world_anchor": "把世界观锚点写入具体动作、代价或场景物件中。",
        "missing_foreshadow_annotation": "追加可机读的 foreshadow HTML 注释，保持后续回收可追踪。",
        "particle_delta_unparseable": "在写作自检或章节结算中给出可解析的微粒变化。",
    }
    out = [mapping.get(str(issue.get("code")), "保留该问题的上下文，进入人工复核。") for issue in issues]
    return _dedupe(out)


def _readability_report(
    issues: list[dict[str, Any]],
    checked: Mapping[str, Any],
    chapter_text: str,
) -> dict[str, Any]:
    action_items = []
    recommendations = _recommendations_for_issues(issues)
    for idx, issue in enumerate(issues):
        action_items.append(
            {
                "code": str(issue.get("code", "unknown")),
                "severity": str(issue.get("severity", "info")),
                "action": recommendations[idx] if idx < len(recommendations) else "进入人工复核。",
            }
        )
    headline = (
        "章节一致性可进入下一步"
        if not issues
        else f"章节仍有 {len(issues)} 个可读性 / 连续性缺口"
    )
    return {
        "headline": headline,
        "action_items": action_items,
        "evidence": {
            "body_paragraph_count": checked.get("body_paragraph_count", 0),
            "foreshadow_count": checked.get("foreshadow_count", 0),
            "matched_world_anchors": list(checked.get("matched_world_anchors", []))[:5],
            "chapter_excerpt": _text_summary(chapter_text, limit=120),
        },
    }


def _provider_context_snapshot(
    report: Mapping[str, Any],
    ctx: Mapping[str, Any],
    checked: Mapping[str, Any],
    chapter_text: str,
    locked_present: list[str],
    entity_present: list[str],
) -> dict[str, Any]:
    return {
        "book_id": ctx.get("book_id"),
        "execution_mode": ctx.get("execution_mode") or ctx.get("mode") or "unknown",
        "chapter_no": _chapter_no(ctx),
        "chapter_text_chars": len(chapter_text.strip()),
        "body_paragraph_count": checked.get("body_paragraph_count", 0),
        "foreshadow_count": checked.get("foreshadow_count", 0),
        "world_anchor_count": len(checked.get("matched_world_anchors", [])),
        "locked_domains_present": list(locked_present),
        "entity_domains_present": list(entity_present),
        "audit_log_entries": _mapping(report.get("inputs_checked")).get("audit_log_entries", 0),
    }


def _provider_gap_report(report: Mapping[str, Any]) -> dict[str, Any]:
    open_gaps = []
    for issue in report.get("issues", []):
        if not isinstance(issue, Mapping):
            continue
        open_gaps.append(
            {
                "code": str(issue.get("code", "unknown")),
                "severity": str(issue.get("severity", "info")),
                "detail": str(issue.get("path") or issue.get("marker") or issue.get("name") or issue.get("source") or ""),
            }
        )
    open_gaps.append(
        {
            "code": "production_quality_not_proven",
            "severity": "warn",
            "detail": "V1 provider is deterministic report-only evidence, not real long-form production proof.",
        }
    )
    return {"status": "needs_review" if open_gaps else "clear", "open_gaps": open_gaps}


def _provider_residual_risk(ctx: Mapping[str, Any]) -> list[dict[str, Any]]:
    mode = str(ctx.get("execution_mode") or ctx.get("mode") or "unknown")
    risks = [
        {
            "code": "single_step_report_scope",
            "severity": "medium",
            "mitigation": "pair V1 report with harness and real demo sidecar before claiming production readiness.",
        },
        {
            "code": "real_llm_quality_variability",
            "severity": "medium" if mode == "real_llm_demo" else "low",
            "mitigation": "store endpoint/scope in the real demo report and review chapter artifact manually.",
        },
        {
            "code": "mock_harness_boundary",
            "severity": "medium",
            "mitigation": "mock harness proves StateIO/workflow boundaries only.",
        },
    ]
    return risks


def _provider_quality_summary(report: Mapping[str, Any]) -> str:
    summary = _mapping(report.get("summary"))
    issue_count = _as_int(summary.get("issue_count"), 0)
    if issue_count:
        return f"V1 检查发现 {issue_count} 个缺口，需先处理 gap_report 中的开放项。"
    return "V1 deterministic 检查通过；仍需结合 real_llm_demo sidecar 判断真实章节质量。"


def _present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, (str, bytes, list, tuple, set, dict)):
        return len(value) > 0
    return True


def _topic(params: Mapping[str, Any], seed_text: str) -> str:
    explicit = params.get("topic") or params.get("genre")
    if explicit:
        return str(explicit).strip()
    if "赛博" in seed_text:
        return "赛博奇幻"
    if "宫廷" in seed_text or "摄政" in seed_text:
        return "宫廷权谋"
    if "海" in seed_text or "鲸" in seed_text:
        return "深海奇幻"
    if "玄幻" in seed_text or "修真" in seed_text:
        return "玄幻黑暗"
    return "玄幻黑暗"


def _protagonist_from_text(text: str) -> str:
    for pattern in (
        r"([\u4e00-\u9fff]{2,8})(?:在|用|因|被|发现|寻找|试图)",
        r"(潜水员|替身公主|刺客|少年|少女|公主|猎人|术士|修士|账房)",
    ):
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    return "未命名主角"


def _antagonist_from_text(text: str) -> str:
    if "摄政王" in text:
        return "摄政王"
    if "AI" in text or "ai" in text:
        return "AI遗骨议会"
    if "海沟" in text:
        return "海沟神权"
    if "宫廷" in text:
        return "宫廷旧秩序"
    if "血" in text:
        return "血誓寡头"
    return "垄断真相的旧秩序"


def _motif_from_text(text: str) -> str:
    for word in ("AI鲸骨", "鲸骨", "账本", "海沟", "微粒", "天堑", "记忆", "血雾", "契约", "王座"):
        if word in text:
            return word
    keywords = _keywords(text, "核心")
    return keywords[0] if keywords else "真相"


def _place_from_text(text: str) -> str:
    for word in ("海沟", "宫廷", "废都", "天堑", "鲸骨神殿", "王城", "矿井"):
        if word in text:
            return word
    return "边境裂隙"


def _tones_for_topic(topic: str, seed_text: str) -> list[str]:
    tones = ["紧张", "高压", "代价明确"]
    if "黑" in topic or "血" in seed_text:
        tones.extend(["暗黑", "压抑"])
    if "宫廷" in topic:
        tones.extend(["克制", "权谋"])
    if "赛博" in topic or "AI" in seed_text:
        tones.extend(["冷硬", "异质"])
    if "海" in topic or "鲸" in seed_text:
        tones.extend(["深水窒息感", "神秘"])
    return _dedupe(tones)


def _audience_for_topic(topic: str) -> str:
    if "宫廷" in topic:
        return "偏好权谋反转与关系张力的长篇读者"
    if "赛博" in topic:
        return "偏好异质设定与升级代价的类型读者"
    return "偏好暗黑升级、强冲突和持续伏笔兑现的类型读者"


def _keywords(text: str, topic: str) -> list[str]:
    words = re.findall(r"[A-Za-z0-9]+|[\u4e00-\u9fff]{2,8}", text)
    stop = {"一个", "发现", "必须", "正在", "中的", "用户", "输入", "故事", "核心"}
    out = [topic]
    for word in words:
        if word in stop or len(word) < 2:
            continue
        out.append(word)
    return _dedupe(out)[:8]


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            out.append(value)
    return out


def _shorten(text: str, limit: int) -> str:
    text = " ".join(str(text).split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _slugify(text: str) -> str:
    ascii_slug = re.sub(r"[^a-zA-Z0-9]+", "_", text).strip("_").lower()
    if ascii_slug:
        return ascii_slug
    codepoints = "_".join(f"{ord(ch):x}" for ch in text[:6])
    return f"char_{codepoints}" if codepoints else "char_unknown"


def _int_param(params: Mapping[str, Any], key: str, default: int) -> int:
    return _as_int(params.get(key), default)


def _as_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


__all__ = [
    "H_CHAPTER_SETTLE_ID",
    "R1_STYLE_POLISH_ID",
    "R2_CONSISTENCY_CHECK_ID",
    "R3_FINAL_PACK_ID",
    "V1_RELEASE_CHECK_ID",
    "build_asset_capability_providers",
    "build_v1_release_report",
    "h_chapter_settle_provider",
    "r1_style_polish_provider",
    "r2_consistency_check_provider",
    "r3_final_pack_provider",
    "v1_release_check_provider",
]
