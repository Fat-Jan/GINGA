# v1.7-2 jury model probe notes

## ask-llm aliases

- `久久`: generation alias, default model `qwen3.6-max-preview-nothinking`, key stored in macOS Keychain.
- `jiujiu-jury`: jury-only alias, same base URL, default model `qwen3.6-max-preview-thinking`, key stored separately in macOS Keychain account `jiujiu-jury`.

## Probe result on 2026-05-15

- `qwen3.6-max-preview-thinking` returned a clean short Chinese review probe, so it is suitable for short reviewer questions.
- `GLM-5.1` repeatedly returned HTTP 504 on the short probe.
- `MiniMax-M2.7` returned content with visible `<think>` reasoning text, so it is not suitable as a clean reviewer default.
- `jiujiu-jury` returned HTTP 504 on the 132KB full queue packet, 22KB core packet, and 5.5KB P0 mini packet. It is therefore not in the default `ask-jury-safe` matrix.
- `wzw` returned an empty output file while the wrapper marked the cell OK; empty files must be treated as failed jury cells.

## Current routing decision

- Keep `久久` as the Chinese fiction generation main endpoint.
- Keep `jiujiu-jury` registered for manual short-input review probes.
- Keep `ask-jury-safe` default jurors as `ioll-grok,wzw`; manually inspect output size because `wzw` can produce empty files.
