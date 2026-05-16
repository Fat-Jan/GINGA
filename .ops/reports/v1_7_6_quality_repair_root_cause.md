# v1.7-6 Quality Repair Root Cause

- generated_at: `2026-05-16`
- scope: offline diagnosis from committed v1.7-6 harness artifacts; no new real LLM calls
- related status: `v1.7-6 Longform Quality Repair Follow-up` remains `observation`

## Evidence

- `v1-7-6-quality-repair-4000-failfast`: fail-fast at chapter 1 after repair, `3265 < 3500` Chinese chars, with opening-loop score 3.
- `v1-7-6-quality-repair-4000-origin-ok`: fail-fast at chapter 1 after repair, `3313 < 3500` Chinese chars.
- `v1-7-6-quality-repair-4000-retry2`: fail-fast at chapter 1 after repair, `2941 < 3500` Chinese chars, with opening-loop score 4.
- Earlier `v1-7-6-quality-repair-4000` produced chapter files before fail-fast tightening, but chapter body counts were still below the 3500 Chinese-character gate:
  - chapter 1: total chars 3625, total Chinese chars 3001, body Chinese chars 2854, opening-loop score 4.
  - chapter 2: total chars 3358, total Chinese chars 2745, body Chinese chars 2626, opening-loop score 1.
  - chapter 3: total chars 4038, total Chinese chars 3310, body Chinese chars 3221, opening-loop score 2.

## Boundary Checks

- `word_target=4000` maps to `max_tokens=8800`, so the observed 2941-3313 Chinese-char outputs are not explained by the current token cap alone.
- Rebuilt chapter-1 prompt length from the failed isolated states is about 2354 chars / 1134 Chinese chars.
- Rebuilt repair prompt length with a 3000+ Chinese-char problem draft is about 4512 chars / 3154 Chinese chars.
- The prompt already contains both `目标字数 4000 字` and the hard floor `不得低于 3600 个中文汉字` / `不得低于 3500 个中文汉字`.

## Root Cause Hypothesis

The failure is primarily an instruction/measurement mismatch, not a process crash:

1. The model appears to satisfy something close to the visible `4000 字` total-output target, where markdown table, title, punctuation, comments, and non-CJK characters count toward perceived length.
2. The gate measures stricter body-quality evidence: Chinese Han characters, with effective body Chinese chars often 2600-3221.
3. The repair prompt appends a large problem draft. That keeps context under the token budget, but it gives the model a strong compression/editing anchor and still produces a revised short chapter rather than a clearly expanded replacement.
4. Opening-loop repair is secondary here. The most stable blocker is short Chinese-body output; opening-loop scores appear in two runs, but `origin-ok` still failed purely on length.

## Next Minimal Repair

Do not run another real batch before changing the prompt contract.

Suggested next slice:

1. Add an offline prompt-contract test that asserts the generation prompt says the table/title/comment do not count toward the Chinese-body floor.
2. Change the base prompt from generic `目标字数 4000 字` to a single unambiguous metric: `正文汉字数 3800-4200，表格、标题、注释、标点不计入`.
3. Change the repair prompt so it does not paste the full short draft by default; include a short failure summary plus a short excerpt only, and instruct a full rewrite with 7-10 substantial scene beats.
4. Keep fail-fast. If the model still produces below 3500 Chinese body chars after the prompt-contract fix, run a single-chapter isolated real probe before any 4-chapter batch.

## Non-Goals

- Do not lower the 3500 Chinese-character gate to make v1.7-6 pass.
- Do not mark v1.7-6 done from dry-run or mock tests.
- Do not expand real batch size until a single isolated chapter clears the body-length gate and review remains non-blocking.
