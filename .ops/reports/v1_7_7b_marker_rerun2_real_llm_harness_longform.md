# Longform Jiujiu Smoke Report

- dry_run: `False`
- passed: `False`
- endpoint: `久久`
- book_id: `v1-7-7b-marker-rerun2`
- requested_chapters: `4`
- completed_chapters: `2`
- word_target: `4000`
- topic: 玄幻黑暗 + 规则怪谈 + 末日多子多福
- drift_status: `stable`

## Drift

- low_anchor_chapters: `[]`
- forbidden_hit_chapters: `[]`
- short_chapters: `[]`
- missing_foreshadow_chapters: `[]`

## Production Policy

- recommended_batch_size: `4`
- upper_bound: `5`
- pressure_test_only_at_or_above: `6`

## Batches

- batch01: size=4, chapters=[1, 2, 3], completed=2, short=[], forbidden=[]

## Chapters

- ch001: ok, batch=1/4, chars=4416, zh=3611, foreshadow=1, forbidden={}
- ch002: ok, batch=1/4, chars=5204, zh=4455, foreshadow=1, forbidden={}
- ch003: failed, batch=1/4, chars=0, zh=0, foreshadow=0, forbidden={}
