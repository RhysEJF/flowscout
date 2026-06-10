---
name: digest-paper
description: Given a paper URL, produce a structured lens-tailored digest in the searchable papers wiki
---

# /digest-paper — Scientific paper digester

The user invoked `/digest-paper <url> [--corpus=<slug>] [--lens=<slug>] [--new-lens] [--lens]` (or asked you to digest / summarize / wiki-fy a paper given its URL).

The full skill methodology lives at `skills/digest-paper/SKILL.md`. Read that file in full and follow it end-to-end, using the arguments the user provided as input.

**Required argument:** the paper URL.
**Optional flags:**
- `--corpus=<slug>` — which research corpus (subdirectory of the papers wiki) to write into; resolution rule in the SKILL.md Step 0
- `--lens=<slug>` — use an existing lens (see `skills/digest-paper/lenses/`)
- `--lens` (no value) — list available lenses and let the user pick
- `--new-lens` — interview the user to create a new lens, save it, then use it
- (no flag) — default to the `generic` lens

If the user did not include a URL, ask for one before proceeding.
