---
name: flow-frontier
description: Mine cross-paper theses from the papers wiki across five gap-types — convergence, unstated-assumption, mechanism-gap, edge-of-consensus, and direct contradiction. Emits falsifiable theses to experiences/theses/. Layer 1 of the Flow Frontier research engine — sits between /digest-paper and /verify-thesis.
---

# /flow-frontier — Cross-paper thesis miner

The user invoked `/flow-frontier [--topic="..." | --slugs=a,b,c | --refresh] [--gap-types=convergence,assumption,mechanism,edge,contradiction] [--max-papers=20] [--min-supporting=3] [--min-falsifiability=medium] [--cluster-name=<slug>] [--force] [--dry-run]` (or asked to "find cross-paper insights", "mine theses from my wiki", "find convergences", "find contradictions", "what's latent across these papers").

The full skill methodology lives at `skills/flow-frontier/SKILL.md`. Read that file in full and follow it end-to-end. The sub-agent prompts live at `skills/flow-frontier/prompts/`.

**Required:** exactly one of:
- `--topic="..."` — fresh cluster from a topic
- `--slugs=a,b,c` — explicit paper-slug set
- `--refresh` — incremental update across all existing clusters
- `--merge-clusters=a,b,c` — union of named clusters' papers as a new merged cluster (v2)

**Optional flags:**
- `--gap-types=convergence,assumption,mechanism,edge,contradiction` — which gap-types to run. Default: all five. Pass a subset to narrow scope or save cost.
- `--max-papers=20` — cluster size cap (topic mode)
- `--min-supporting=3` — min papers for convergence
- `--min-falsifiability=medium` — drop theses below this
- `--overlap-threshold=0.80` — fresh-cluster overlap guard (v2). Warns + exits if any existing cluster shares ≥ this fraction of papers.
- `--force-new` — bypass overlap guard (v2). Use when you really do want a fresh cluster despite overlap.
- `--no-cache` — bypass Pass A assumption cache (v2). Force fresh extraction. Useful after prompt edits.
- `--cluster-name=<slug>` — override auto-generated cluster name
- `--corpus=<slug>` — research corpus to mine (theses + reads scoped to it)
- `--force` — re-run even if cluster unchanged
- `--dry-run` — preview without writing

**Outputs:**
- `experiences/theses/<corpus>/<slug>.md` — one file per new thesis, with frontmatter + falsification section
- `experiences/theses/<corpus>/INDEX.md` — appended rows
- `experiences/theses/_manifest.json` — cluster tracking + reverse map (papers → theses)

Modes are mutually exclusive — reject invocations with more than one of `--topic` / `--slugs` / `--refresh`.

If the user did not pass any of the three required mode flags, ask which they want: a fresh topic search, an explicit slug set, or a refresh of existing clusters.

If a cluster resolves to fewer than 5 papers, error and tell the user the cluster is too small for convergence to be meaningful.
