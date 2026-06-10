---
name: verify-thesis
description: Verify a thesis (or all open theses) against the open literature. Generates adversarial search queries, runs Exa + WebSearch, scores each candidate as supports/contradicts/qualifies/irrelevant, synthesises a verdict (resolved-yes/resolved-no/partially-resolved/open), drafts an experiment design if the thesis remains open, and writes verdict + evidence back into the thesis file. Layer 2 of the Flow Frontier research engine.
---

# /verify-thesis — Falsifiable-claim verifier

The user invoked `/verify-thesis <slug>` or `/verify-thesis --all-open` (or `--status=<value>`), with optional flags: `--max-batch=N`, `--max-sources=N`, `--gen-queries=N`, `--no-experiment`, `--force`, `--dry-run`.

The full skill methodology lives at `skills/verify-thesis/SKILL.md`. Read that file in full and follow it end-to-end. The sub-agent prompts live at `skills/verify-thesis/prompts/`.

**Required:** exactly one of:
- `<slug>` (positional) — verify a single thesis
- `--all-open` — sweep every `open` or `partially-resolved` thesis
- `--status=<value>` — sweep theses matching a specific status (e.g., `--status=stale-pending-review`)

**Optional flags:**
- `--max-batch=5` — cap on theses processed per run (batch modes only). Default 5.
- `--max-sources=12` — max candidate sources per thesis
- `--gen-queries=4` — adversarial queries to generate per thesis
- `--no-experiment` — skip experiment-design draft for `open` verdicts
- `--force` — re-verify already-verified theses
- `--dry-run` — preview without calling agents

**Outputs:**
- Updated `experiences/theses/<slug>.md` files: frontmatter (`status`, `verified_date`, `verdict`, `verdict_evidence`, `contradicting_papers`), populated `## Contradicting papers` and `## Verification notes` body sections, optional `## Experiment design` section.
- `experiences/verify-thesis/<run-id>/state.json` — full run state.

Modes are mutually exclusive — reject invocations with more than one of `<slug>` / `--all-open` / `--status`. If none, list open theses and ask the user to pick.
