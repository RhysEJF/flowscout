---
name: flow-frontier
description: Mine cross-paper insights from the papers wiki across five gap-types — convergence (N papers reach similar conclusions via different mechanisms), unstated-assumption (paper A assumes X, paper B tests/falsifies X), mechanism-gap (same effect, incompatible mechanisms), edge-of-consensus (paper deviates on one dimension while agreeing on others), and direct contradiction (paper A claims X, paper B claims ¬X). Emits falsifiable theses as markdown files for human review. Sits between /digest-paper (Layer 0: read) and /verify-thesis (Layer 2: verify via web search + experiment design). Incremental — runs cheap when no new papers in cluster. Trigger when user says `/flow-frontier --topic="..."` or asks to "find cross-paper insights", "mine theses from my wiki", "find convergences in my papers", "find contradictions", or "what is the latent question across these papers".
---

# /flow-frontier — Cross-paper thesis miner

> Layer 1 of the Flow Frontier research engine. Reads a topic cluster of paper digests, runs parallel gap-type sub-agents, emits falsifiable theses to `experiences/theses/`. Architecture plan: `experiences/plans/flow-frontier-architecture.md`.

## When to Use

- User says `/flow-frontier --topic="..."` (with optional `--slugs`, `--refresh`, `--gap-types`, etc.)
- User says `/flow-frontier --refresh` after digesting new papers, to update existing clusters incrementally
- User asks: "find cross-paper insights / find convergences / mine theses / what's latent across these papers"
- After a `/citation-walk` or batch of `/digest-paper` runs, when the wiki has new content worth mining

## Arguments

| Flag | Meaning |
|---|---|
| `--topic="..."` | Topic to cluster on. QMD pulls the top-`--max-papers` digests matching this query. Required unless `--slugs`, `--refresh`, or `--merge-clusters`. |
| `--slugs=a,b,c` | Explicit paper-slug set. Bypasses topic-based selection. Mutually exclusive with other modes. |
| `--refresh` | Walk all clusters in `_manifest.json`. Re-run only those whose paper-set has changed since last run. |
| `--merge-clusters=a,b,c` | **v2.** Treat the named clusters as a single merged cluster. Resolves to union of their papers, runs gap-types on the union, emits theses that survive dedup against all source clusters' existing theses. Source clusters are NOT modified. |
| `--gap-types=convergence,assumption,mechanism,edge,contradiction` | Which gap-types to run. Default: all five. Pass a subset to narrow scope or save cost. |
| `--max-papers=20` | How many papers to pull into the cluster (topic mode only). Default 20. |
| `--min-supporting=3` | Minimum supporting papers required for a convergence thesis to fire. Default 3. |
| `--min-falsifiability=medium` | Drop theses below this. Values: `low`, `medium`, `high`. Default `medium`. |
| `--overlap-threshold=0.80` | **v2.** When starting a fresh cluster, warn + exit if any existing cluster shares ≥ this fraction of papers. Override with `--force-new`. Default 0.80. |
| `--force-new` | **v2.** Skip the overlap check and proceed with the fresh cluster even if it overlaps heavily with an existing one. |
| `--cluster-name=<slug>` | Override the auto-generated cluster name. |
| `--force` | Re-run even if cluster paper-set is unchanged since last run. |
| `--no-cache` | **v2.** Skip the per-paper Pass A assumption cache (force re-extraction). Useful after a prompt change. |
| `--dry-run` | Resolve cluster + show what would run; do not emit theses. |

## Mutually exclusive modes

Exactly one of `--topic`, `--slugs`, `--refresh`, `--merge-clusters`. If none, error and prompt the user.

## Methodology

### Step 1 — Parse args + initialize state

1. Validate args (exactly one of `--topic` / `--slugs` / `--refresh`).
2. Compute the cluster name:
   - If `--cluster-name=<slug>` supplied → use it
   - Else if `--topic`: take the topic, lowercase, strip stopwords (a, an, the, of, in, on, for, to, vs, and, or, with, by, from, as), kebab-case the first 6 remaining content words, truncate to 60 chars. Example: `"agent memory write-time vs query-time"` → `agent-memory-write-time-query-time`.
   - Else if `--slugs`: use `adhoc-<YYYY-MM-DD>-<short-hash-of-sorted-slugs>`
   - Else (`--refresh`): no single cluster — the run iterates through all clusters in the manifest
3. Create run directory: `experiences/flow-frontier/<cluster-name>-<YYYY-MM-DD>/`. For `--refresh`, use `refresh-<YYYY-MM-DD>/`.
4. Initialize `state.json`:
   ```json
   {
     "mode": "topic|slugs|refresh",
     "cluster_name": "...",
     "topic_query": "..." | null,
     "explicit_slugs": [...] | null,
     "gap_types": ["convergence", "assumption"],
     "min_supporting": 3,
     "min_falsifiability": "medium",
     "force": false,
     "started_at": "<ISO>",
     "cluster": [],          // resolved paper slugs
     "new_papers": [],       // papers added since last run
     "candidate_theses": [], // before dedup/rank
     "emitted_theses": [],
     "stale_theses": [],     // existing theses marked stale this run
     "skipped": [],
     "status": "running"
   }
   ```
5. Open `log.md` for human-readable progress.
6. If `--dry-run`: continue through Steps 2–3, print a preview table, exit before Step 4 (no agent calls, no writes).

### Step 2 — Resolve cluster (mode-specific)

**`--topic`:**
```bash
./vendor/qmd/bin/qmd query "<topic>" --json -n <max_papers + 10> \
  | jq '[.[] | select(.file | startswith("memory/knowledge-sources/papers/"))
              | select(.file | endswith(".md"))
              | select(.file | endswith("-notes.md") | not)
              | {slug: (.file | sub(".*/"; "") | sub(".md$"; "")), score}]
        | .[:<max_papers>]'
```
Filter out `-notes.md`, `INDEX.md`, anything not a digest. If fewer than 5 papers match, error and tell the user the topic is too narrow.

**`--slugs`:**
Split on commas. Validate each slug has `memory/knowledge-sources/papers/<slug>.md`. Error on the first missing.

**`--refresh`:**
Load `experiences/theses/_manifest.json`. For each cluster, re-resolve its current paper-set via the saved `topic_query`. Compute current `papers_sha = sha256(sorted(papers).join("\n"))`. Compare to manifest's stored `papers_sha`. If unchanged and `--force` not set: skip this cluster. If changed: queue it for re-run.

**`--merge-clusters=a,b,c`:** *(v2)*
Load `experiences/theses/_manifest.json`. Validate that each named cluster exists; error on first missing. Take the union of their `papers` arrays (preserving uniqueness). This becomes the new cluster's paper-set. Cluster name defaults to `merge-<sha1(sorted(source-cluster-names))[:8]>` unless `--cluster-name` is supplied. The source clusters are NOT modified — the merge cluster lives alongside them in the manifest. Skip the overlap-detection step (Step 3.5) for this mode since high overlap is intentional.

### Step 3 — Check manifest for delta

Skip this step for `--refresh` mode (already done in Step 2). For `--topic` / `--slugs` / `--merge-clusters`:

1. Load `experiences/theses/_manifest.json` (create empty if missing).
2. Look up `clusters[cluster_name]`.
3. If absent: this is a fresh cluster. `new_papers = cluster`. Proceed (and run Step 3.5 unless `--merge-clusters`).
4. If present: compute current `papers_sha`. Compare to manifest. If unchanged and not `--force`: exit cleanly with "Cluster unchanged since `<last_run>`; nothing to do."
5. Else: `new_papers = cluster - manifest.clusters[cluster_name].papers`. Proceed.

### Step 3.5 — Cluster-overlap detection *(v2)*

**Skip this step for `--refresh`, `--merge-clusters`, and existing clusters (Step 3 case 4).** Only runs for genuinely fresh clusters.

1. For each cluster `c` in `_manifest.json` (other than the new cluster itself):
   - Compute `overlap_fraction = |c.papers ∩ new.papers| / max(|c.papers|, |new.papers|)`
2. If any cluster has `overlap_fraction >= --overlap-threshold` (default 0.80) AND `--force-new` not set:
   - Print a warning listing each overlapping cluster with:
     - cluster name, last_run date, theses_generated count
     - overlap percentage
   - Suggest one of three actions:
     - `--refresh` if the user wants to incrementally update the existing cluster
     - `--force-new` to proceed with a fresh cluster anyway
     - `--merge-clusters=<old>,<new>` after this run completes, to consolidate
   - Exit cleanly with code 0 (no agents called, no writes).
3. Otherwise (no significant overlap, or `--force-new` set): continue to Step 4.

Implementation note: this check is cheap (O(N × M) string set operations where N is clusters and M is papers per cluster). Always runs before any agent is dispatched.

### Step 4 — Spawn gap-type sub-agents in parallel

Build the cluster payload — one block per paper:
```
SLUG: <slug>
TITLE: <title>
KEY_TAKEAWAY: <key_takeaway from frontmatter>
DOMINANT_VOCAB: <auto-extracted noun phrases from the takeaway, comma-separated>
```

Spawn one Agent call per requested `gap-type`, in a single message (parallel). Prompts live at `skills/flow-frontier/prompts/<gap_type>.md` — see "Sub-agent prompts" section below for the v1 set.

**Convergence agent** — single call, full cluster in context.

**Unstated-assumption agent** — two-pass with per-paper cache:
- Pass A: for each paper, **check the cache at `experiences/theses/_cache/assumptions/<paper-slug>.json` first.** If the cache exists AND the cached `digest_sha` matches the current digest's SHA-256, use the cached assumptions (cache hit, no LLM call). Otherwise extract via `prompts/assumption_pass_a.md` and write the result to cache.
- Pass B: one cross-reference call using `prompts/assumption_pass_b.md`. Takes all Pass A outputs (cached + freshly extracted) + all takeaways. Identifies (assumption, papers-that-make-it, paper-that-tests-it) tuples.

The orchestrator does the two-pass coordination itself within the "unstated-assumption" Agent call. The cache is keyed by paper-slug and invalidated by digest content change; this means re-running on overlapping clusters reuses Pass A work and only pays for the cluster-specific Pass B cross-reference.

If `--no-cache` is set, all Pass A calls are forced fresh (useful after editing the Pass A prompt).

### Step 5 — Collect, dedupe, rank

1. Merge all candidate theses from the gap-type agents into a single list.
2. For each candidate:
   - Hash the `claim` text → `claim_hash` (lowercase, strip whitespace + punctuation, sha256-truncate to 16 hex).
   - If `claim_hash` matches any existing thesis in `experiences/theses/` → discard (already exists).
   - If `falsifiability` < `min_falsifiability` → discard to `state.skipped`.
3. Rank surviving candidates by:
   - `len(gap_types_that_fired)` DESC (theses surfaced by multiple gap-types rank first)
   - `len(supporting_papers)` DESC
   - `falsifiability` rank (high > medium > low)
4. Emit at most 10 per run by default (prevents thesis spam). Configurable later.

### Step 5.5 — Mark stale existing theses

For each thesis already in `experiences/theses/` whose `generated_from` overlaps with the current cluster's papers:
- If `new_papers` is non-empty AND any new paper's slug is NOT already in `generated_from`:
  - Set `status: stale-pending-review` (only if previous status was `open` or `partially-resolved` — don't downgrade `resolved-yes` / `resolved-no`)
  - Set `stale_reason: "New paper(s) added to cluster '<cluster-name>' on <date>: <comma-sep slugs>. Review whether they affect this thesis."`
  - Append to `state.stale_theses`

This is the contradiction-aware staleness signal. The user reviews stale theses via the viewer or by `/verify-thesis <slug>`. v1 does NOT auto-evaluate stale theses against new papers — that's a v2 sub-agent.

### Step 6 — Emit new artifacts

For each emitted thesis:

1. Generate slug from title (kebab, first ~6 content words after stopword strip).
2. Write `experiences/theses/<slug>.md` using the schema below.
3. Append row to `experiences/theses/INDEX.md` (create if missing — see template below).
4. Update `experiences/theses/_manifest.json`:
   ```json
   {
     "version": 1,
     "clusters": {
       "<cluster-name>": {
         "topic_query": "...",
         "papers": [...],
         "papers_sha": "...",
         "last_run": "<ISO>",
         "theses_generated": [...]  // append new slugs
       }
     },
     "theses_by_paper": {
       "<paper-slug>": ["thesis-slug-1", ...]  // append for each supporting paper
     }
   }
   ```

For each stale thesis: just rewrite its frontmatter with the new status. Don't touch the body.

### Step 7 — Refresh QMD

```bash
python3 scripts/with-lock.py /tmp/qmd-update.lock --timeout 120 -- ./vendor/qmd/bin/qmd update
python3 scripts/with-lock.py /tmp/qmd-embed.lock --timeout 300 -- ./vendor/qmd/bin/qmd embed
```

### Step 8 — Update state to completed

```json
"completed_at": "<ISO>",
"status": "completed"
```

Plus rewrite `log.md` with the final summary.

### Step 9 — Report to user

```
/flow-frontier complete  (<duration>s)
  Cluster: <cluster-name>  (<topic if topic-mode>)
  Papers in cluster: N    [new since last run: M]
  Gap-types run: convergence, assumption

  Theses emitted: K
    - [convergence]    <slug>  <title>
    - [assumption]     <slug>  <title>
    - [conv+assump]    <slug>  <title>   ← multi-gap-type
  Theses marked stale: J
    - <slug>   triggered by new paper [[<slug>]]
  Skipped (below threshold): L

  Read theses:  open experiences/theses/<slug>.md
                or  http://localhost:8000/viewer.html#theses
```

## Thesis file schema

```yaml
---
kind: thesis
slug: <kebab-slug>
title: "<one-sentence claim>"
gap_type:                          # array — supports multi-tag
  - convergence
  # - unstated-assumption          # add when multiple agents fire
gap_evidence:
  - type: convergence
    scores:
      vocabulary_distance: 8
      conclusion_similarity: 9
      naming_opportunity: 7
    notes: "..."
status: open                       # open | resolved-yes | resolved-no | partially-resolved | stale-pending-review
stale_reason: null
falsifiability: high               # high | medium | low
supporting_papers:
  - slug: <paper-slug>
    role: "what this paper contributes"
generated_from:                    # convenience: flat list of slugs (mirrors supporting_papers[].slug)
  - <paper-slug>
generated_date: "<ISO>"
generated_by:
  cluster: <cluster-name>
  gap_types_run: [convergence, assumption]
  flow_frontier_run: <run-dir>
verified_date: null
verdict: null
verdict_evidence: []
contradicting_papers: []           # populated by /verify-thesis
related_theses: []
---

# Thesis: <one-sentence claim>

## Claim
<2-3 sentences expanding the claim with specificity. Must be falsifiable.>

## Why this is latent
<1-2 sentences explaining what makes this a gap in the literature, not a known result. References the gap_type(s).>

## How to falsify
<Concrete experiment design — what to measure, what would prove the claim wrong, what success looks like.>

## Supporting papers
- [[<paper-slug>]] — <one-line role>

## Contradicting papers
[populated by /verify-thesis]

## Verification notes
[populated by /verify-thesis]
```

## INDEX.md template (for theses)

`experiences/theses/INDEX.md`:

```markdown
# Theses Wiki

> Falsifiable hypotheses mined from the papers wiki via `/flow-frontier`. Each thesis points at the originating papers and includes a falsification design. Verify with `/verify-thesis <slug>`.

**Search:** `./vendor/qmd/bin/qmd query "..." -n 5`

---

## Index

| Generated | Title | Gap-type | Status | Supporting | Falsif. | Cluster |
|---|---|---|---|---|---|---|
| _(no theses yet — run `/flow-frontier --topic="..."` to mine the first ones)_ | | | | | | |
```

Row format: `| {date} | [{title}]({slug}.md) | {gap_type_short} | {status} | {n_papers} | {falsif} | {cluster} |`
- `gap_type_short`: `conv` / `assump` / `conv+assump` / etc.
- `status`: emoji chip — 🟢 open · 🔵 verified · 🔴 falsified · ⚠️ stale

## Sub-agent prompts (all five gap-types)

These live at `skills/flow-frontier/prompts/<name>.md`:

- `prompts/convergence.md` — single-call agent: groups papers reaching similar conclusions via different vocabulary
- `prompts/assumption_pass_a.md` — per-paper assumption extraction (parallel)
- `prompts/assumption_pass_b.md` — cross-reference + thesis emission for unstated-assumption
- `prompts/mechanism.md` — single-call agent: finds N papers with similar effects but incompatible proposed mechanisms; emits ablation-ready theses
- `prompts/edge.md` — single-call agent: finds quiet deviations in otherwise-aligned clusters; rejects regime differences
- `prompts/contradiction.md` — single-call agent: finds directly opposing claims under matched conditions; conservative (requires `falsifiability: high`)

When the user passes `--gap-types`, only the named agents run. The orchestrator dispatches them in a single parallel batch (one Agent call per gap-type, plus Pass-A sub-sub-agents internally for the assumption two-pass).

## Manifest schema

`experiences/theses/_manifest.json`:

```json
{
  "version": 1,
  "clusters": {
    "<cluster-name>": {
      "topic_query": "<original --topic argument, null for slug clusters>",
      "papers": ["<slug-1>", "<slug-2>"],
      "papers_sha": "<sha256 of sorted slugs joined by newline>",
      "last_run": "<ISO>",
      "theses_generated": ["<thesis-slug-1>"],
      "source_kind": "topic | slugs | merge",
      "source_clusters": ["<a>", "<b>"]
    }
  },
  "theses_by_paper": {
    "<paper-slug>": ["<thesis-slug-1>", "<thesis-slug-2>"]
  }
}
```

`source_kind` and `source_clusters` are added for `--merge-clusters` outputs so a future run can trace provenance. `source_clusters` is omitted for non-merge runs.

## Pass A cache schema *(v2)*

`experiences/theses/_cache/assumptions/<paper-slug>.json`:

```json
{
  "slug": "adler-2026-storage-not-memory",
  "digest_sha": "<sha256 of the digest .md file content>",
  "extracted_at": "<ISO>",
  "extractor_version": "v1",
  "assumptions": [
    {
      "assumption": "<one sentence>",
      "load_bearing_evidence": "<which section/finding rests on it>",
      "falsifiability": "high|medium",
      "load_bearing": "high|medium"
    }
  ]
}
```

**Cache invalidation rule**: a cache entry is valid IFF its `digest_sha` matches the SHA-256 of the current `<paper-slug>.md` content. Computed cheaply with `shasum -a 256 < <path>` or Python's `hashlib`. Mismatch → re-extract and overwrite.

**`extractor_version`** is bumped when the Pass A prompt changes meaningfully. Cache entries with a stale `extractor_version` are also invalidated. Default: `v1`.

**Disk footprint**: each paper's cache is ~500–2000 bytes. 200 papers ≈ 200KB total. Safe to keep all cache entries forever; old papers' caches stay valid as long as the digest content is stable.

## Critical Rules

- **Modes are mutually exclusive.** Reject more than one of `--topic` / `--slugs` / `--refresh`.
- **Cluster < 5 papers is rejected.** Convergence is meaningless below this threshold; tell the user to broaden the topic or wait until more papers are digested.
- **Falsifiability gate is hard.** Theses below `--min-falsifiability` are dropped, not surfaced with a warning. The point is to keep the backlog actionable.
- **Never modify paper digests.** This skill writes only to `experiences/theses/` and `experiences/flow-frontier/<run-dir>/`. The reverse paper→thesis lookup lives in the manifest, not in paper frontmatter.
- **Dedupe by claim_hash.** Re-running on the same cluster (e.g., with `--force`) should not produce duplicate theses with slightly different wording — claim_hash collapses them.
- **Stale-mark, don't auto-mutate.** When a new paper joins a cluster, existing theses get `status: stale-pending-review` and a `stale_reason` field. The user re-verifies. Do NOT change the body of an existing thesis.
- **`kind: thesis` is load-bearing.** `/learn` skips on this field — theses are not session memories. `/verify-thesis` consumes them. The viewer renders them differently.
- **Always run `qmd update` + `qmd embed` at the end** — new theses aren't searchable until the index rebuilds.

## Verify

After running, confirm:
- [ ] `experiences/flow-frontier/<run-dir>/state.json` has `status: "completed"`
- [ ] Every slug in `state.emitted_theses` corresponds to a file at `experiences/theses/<slug>.md`
- [ ] `experiences/theses/INDEX.md` has a new row per emitted thesis
- [ ] `experiences/theses/_manifest.json` has the cluster updated and reverse-map entries added
- [ ] `qmd search "<thesis-title-fragment>"` returns the new thesis
- [ ] Stale theses (if any) have updated frontmatter only (body untouched)

## Forward compatibility

- **Stale-evaluation sub-agent (v2)**: when a thesis is marked stale, optionally run a sub-agent that reads the new paper(s) + the thesis and assesses `maybe-affected` / `likely-affected` / `confirmed-affected` to prioritize user review.
- **Auto-trigger on /digest-paper (v2)**: opt-in flag so `/digest-paper` fires `/flow-frontier --refresh` after digesting (only re-runs clusters the new paper joined).
- **Layer 2: `/verify-thesis`** consumes the thesis files, runs Exa + arxiv + web search to test the claim, decides `resolved-yes` / `resolved-no` / `partially-resolved` / `open`, writes verdict + evidence into the same thesis file. Builds the experiment design if status remains open.
- **Layer 3: `/experiment`** — eventual. Reads the falsification section + experiment design, hands off to Karpathy autoresearch (for ML experiments) or other infrastructure.

## Viewer changes (v1.5 — not required for v1)

When the user is ready, the papers viewer at `memory/knowledge-sources/papers/viewer.html` should be extended:

1. **Sidebar — Theses tab.** A second tab next to "Papers." Lists all theses from `experiences/theses/INDEX.md`. Status chips (🟢 open · 🔵 verified · 🔴 falsified · ⚠️ stale).
2. **Per-paper footer — "Theses involving this paper".** On each paper digest page, after the body, add a section listing all theses where this paper appears in `generated_from`. Lookup via `_manifest.json`'s `theses_by_paper` (fetched once on viewer load).
3. **Per-thesis detail page.** Custom layout for `kind: thesis` files: prominent claim, falsification section as a callout, supporting/contradicting papers as link chips, verification notes inline.

The viewer's static-server (`scripts/papers-server.py`) needs no changes — it serves `experiences/theses/` the same as `memory/knowledge-sources/papers/` once the URL paths are wired up.
