You are writing the **longitudinal cycle meta-digest** for `/research-cycle`. This is a cumulative knowledge-building artifact — not just a snapshot of this cycle's papers, but a running narrative across ALL prior cycles on this topic. Future cycles will read this and the prior ones, so the chain compounds.

## Inputs

### Cycle metadata

- **Cycle number:** {{CYCLE_NUM}}
- **Topic:** {{TOPIC}}
- **Started:** {{STARTED_AT}}
- **Completed:** {{COMPLETED_AT}}
- **Papers digested this cycle:** {{NEW_PAPER_SLUGS}}
- **Modes run this cycle:** {{MODES_RUN}}  (e.g. broad, canonical, deep, orbit)
- **Bootstrapped (cold start)?** {{BOOTSTRAPPED}}  (true if Phase 0 fired — wiki had no topic-relevant papers and Exa-discovered seeds were used). If true, mention this once in the opening paragraph so the narrative starts honestly ("This cluster was bootstrapped from Exa search; cycle 2+ extends from the resulting wiki state").

### Prior cycle meta-digests on this topic

A chronological list of prior cycle digest paths (oldest first):

{{PRIOR_CYCLE_PATHS}}

Read each one in full using the Read tool. Pay particular attention to:
- The "Running narrative" section (where prior cycles tracked the evolving understanding)
- The "Open questions" section (which of those did this cycle answer? Which remain?)
- The "What's still missing" section (did this cycle fill any of those gaps?)

If `{{CYCLE_NUM}}` is 1 (no priors), skip this block — you're starting the narrative.

### This cycle's new digests

A list of digest file paths at `memory/knowledge-sources/papers/<slug>.md` for each slug in `{{NEW_PAPER_SLUGS}}`. Read each — focus on TLDR, Key Takeaway, Implications, What Experts Overlook.

### Wiki state for context

Total wiki size: {{WIKI_SIZE}} papers. Topic-relevant subset (from QMD search): {{TOPIC_RELEVANT_COUNT}}.

## Output structure

Write to `experiences/research-cycle/cycle-{{CYCLE_NUM}}-{{TOPIC_SLUG}}-{{DATE}}/cycle-digest.md`. Use this exact structure:

```markdown
---
kind: cycle-meta-digest
cycle_num: {{CYCLE_NUM}}
topic: "{{TOPIC}}"
papers_added_this_cycle: {{N}}
wiki_size_after: {{WIKI_SIZE}}
modes_run: [broad, canonical, deep, orbit]
prior_cycles_referenced: [{{PRIOR_CYCLE_NUMS}}]
created: {{DATE}}
---

# Cycle {{CYCLE_NUM}} meta-digest — "{{TOPIC}}"

## In one paragraph

<3-5 sentences. What was this cycle's main contribution to understanding the topic? Did it confirm prior patterns, surface contradictions, open new threads, or fill specific gaps? Reference prior cycles by number if relevant ("Cycle 2 established X; this cycle extends that to Y by adding [[paper-slug]]").>

## Running narrative (cumulative across all cycles)

<Write the current state of the topic as a narrative arc. This is the section that COMPOUNDS — each cycle extends it. Roughly: where does our understanding stand NOW? What's the central tension/debate? What are the main camps? What's the empirical consensus?>

<For cycle 1: write the narrative fresh based on this cycle's papers + any pre-existing wiki context.>
<For cycle 2+: read the prior cycle's narrative section, then EXTEND it. Mark new contributions clearly (e.g. "Cycle 3 added evidence that..." or "[[new-paper-slug]] complicates the cycle-2 conclusion by..."). Don't just rewrite from scratch — show the evolution.>

## What this cycle added

For each of the {{N}} new papers, one line:
- `[[slug]]` (mode: broad/canonical/deep/orbit) — One-sentence what-it-contributed-to-the-cluster.

## Convergence vs divergence (across cycles)

<2-4 bullets about patterns that REPEAT across cycles (convergence — these are real signals) vs claims that get CONTRADICTED or COMPLICATED in subsequent cycles (divergence — these mark live debates). Examples:
- **Convergent**: Every cycle's papers converge on the same retrieval-pipeline recipe (dense + BM25 + RRF + cross-encoder). 8 of the last 12 papers added.
- **Divergent**: Cycle 1 said write-time intelligence loses; cycle 3 added [[paper-X]] which finds write-time wins on specific question types.>

## Open questions / gaps (carried forward)

<Track open questions across cycles. For each, note status:
- Original cycle that raised it
- Status (still open / partially answered by [[paper]] / closed by [[paper]])
- If still open: what kind of paper would resolve it?

This list shrinks as cycles close gaps. New cycles add new entries.>

## What's NOT yet in this cluster (still missing)

<Honest list of adjacent literature this cluster still doesn't cover. The next cycle's `--broad` or `--orbit` phase should target one of these. Examples: "Cognitive-science roots (Bartlett, Tulving)", "Commercial closed competitors", "Pre-2020 mechanistic-interp lineage".>

## Recommended next-cycle move

<One sentence: based on what THIS cycle revealed, what should the next cycle focus on? Pick a mode + a seed/topic. Examples:
- "Run --deep from [[slug-X]] — its citations suggest a still-unexplored chain into [topic]."
- "Run --orbit from [[slug-Y]] — its key takeaway is shape-distinctive enough to surface a different vocabulary subgraph."
- "Run --broad from [[slug-Z]] — it's the hub paper of this cycle's results and its citations likely include the next batch of canonicals.">

## Surprising findings (this cycle only)

<2-3 things that surprised you when reading the new papers. Be specific. Reference paper slugs.>

## Carry-over for next cycle

<If this cycle's modes hit budget but high-relevance candidates remained, list them so next cycle's `--broad` can pick them up. Format:
- `<title>` — [arxiv:ID or needs-exa] — relevance ~<score> — surfaced by [mode] in cycle {{CYCLE_NUM}}>
```

## Quality rules

- **Use `[[slug]]` wiki-link syntax** for every paper reference — viewer.html + QMD both understand them.
- **Reference prior cycle digests explicitly** by their cycle number when extending their claims. E.g. "Cycle 2 established that... Cycle 3 added [[paper-X]] which..."
- **The Running Narrative section is the load-bearing one.** It's the artifact that compounds. Keep it coherent across cycles — if a prior cycle said X, either confirm it, extend it, or complicate it. Don't silently drop it.
- **Be specific. Don't write "more research is needed."** Write "no paper in the cluster has tested whether <specific mechanism> survives <specific condition>; a likely seed is <slug>."
- **Length: 1500-2500 words** for cycle 1 (need to set the stage). 1200-2000 for subsequent cycles (extending an existing narrative).
- **Don't repeat content from individual digests.** This is a CLUSTER document — paper-level details belong in the individual digests; this artifact synthesizes.
