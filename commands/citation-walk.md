---
name: citation-walk
description: Walk the citation graph from a seed paper to build coverage on a topic. Modes: --broad (cover all), --deep (follow the thread), --canonical (foundational works in the wiki), --orbit (lateral discovery via mutated takeaways — finds papers connected by idea, not by citation).
---

# /citation-walk — Citation-graph walker

The user invoked `/citation-walk <seed-url-or-slug> --topic="..." [--broad | --deep | --canonical | --orbit] [--max-papers=N] [--max-depth=N] [--min-relevance=0.5] [--min-canonical-count=3] [--lens=<slug>]` (or asked you to walk citations from a paper / find related papers / build coverage on a topic / find canonical works / find papers connected by idea not by citation).

The full skill methodology lives at `skills/citation-walk/SKILL.md`. Read that file in full and follow it end-to-end, using the arguments the user provided as input.

**Required:**
- `--topic="..."` — required for `--broad`, `--deep`, `--canonical`. **Optional for `--orbit`** (the seed's key_takeaway IS the topic).
- `<seed-url-or-slug>` — required for `--broad`, `--deep`, `--orbit`. Not needed for `--canonical`. For `--orbit`, the seed must be an already-digested slug (or supply a URL and the skill will digest it first).

**Optional flags:**
- `--broad` (default) — wide coverage, all citations from the seed
- `--deep` — thin chain, most-relevant citation at each step
- `--canonical` — find papers cited by ≥3 already-digested wiki entries
- `--orbit` — lateral discovery: mutate the seed's key takeaway 4 ways (counter-thesis / push-to-limit / two adjacent-field translations), search Exa with each, rank by cross-pattern frequency
- `--max-papers=15` — hard cap on new papers digested
- `--max-depth=3` — hop limit from seed (ignored for `--canonical` and `--orbit`)
- `--min-relevance=0.5` — drift guard (ignored for `--canonical` and `--orbit`)
- `--min-canonical-count=3` — canonical threshold
- `--lens=<slug>` — passed through to /digest-paper for each visited paper

Modes are mutually exclusive — reject invocations with more than one of `--broad` / `--deep` / `--canonical` / `--orbit`.

If the user did not include a topic (and mode is not `--canonical` or `--orbit`), ask for one before proceeding. If they did not include a seed (and mode is not `--canonical`), ask for the URL or slug.
