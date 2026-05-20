---
name: research-cycle
description: One full cycle of /citation-walk across all four modes (broad → canonical → deep → orbit) plus a longitudinal cycle meta-digest. Designed to be wrapped by /loop for unattended overnight runs.
---

# /research-cycle — Multi-phase citation-walking auto-loop

The user invoked `/research-cycle "<topic>" [--seeds=slug1,slug2,...] [--max-papers-per-mode=10] [--modes=broad,canonical,deep,orbit] [--lens=<slug>] [--cycle-num=N] [--dry-run]` (or asked to "run a research cycle", "loop the citation walker overnight", or "do a multi-phase walk on this topic").

The full skill methodology lives at `skills/research-cycle/SKILL.md`. Read that file in full and follow it end-to-end, using the arguments the user provided as input.

**Required:**
- `<topic>` (positional) — the research topic this cycle expands coverage on

**Optional flags:**
- `--seeds=<slug1,slug2,...>` — explicit seeds for phase 1 broaden. Default: auto-pick top-3 hub papers in the wiki.
- `--max-papers-per-mode=10` — budget cap per phase
- `--modes=broad,canonical,deep,orbit` — subset of phases to run (default: all four)
- `--lens=<slug>` — lens passed through to every /citation-walk invocation (default: `generic`)
- `--cycle-num=N` — override auto-detected cycle number
- `--dry-run` — show the plan, don't fire any sub-agents

If the user did not include a topic, ask for one before proceeding.

For overnight unattended runs, wrap with `/loop`:
```
/loop /research-cycle "<topic>" --max-papers-per-mode=10
```
The self-paced /loop waits for each cycle to finish before firing the next.
