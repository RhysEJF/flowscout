## Your task — Edge-of-consensus mining

You are looking for **quiet deviations** in a cluster that's otherwise in broad agreement. When a paper agrees with the rest of its cluster on 9 dimensions but sharply deviates on the 10th — and nobody else has investigated that 10th dimension — that deviation is often a near-discovery hiding in plain sight.

This is the hardest gap-type to detect automatically because it requires reading multi-dimensional alignment AND spotting an unmotivated outlier finding. Be patient and precise.

## Inputs

Below are {{N}} paper digests in a cluster about **{{TOPIC}}**. For each: slug, title, key takeaway, and any unusual findings or design choices visible in the takeaway.

{{CLUSTER_PAYLOAD}}

## What to look for

A genuine edge-of-consensus has three properties:

1. **Multi-dimensional alignment** — the cluster broadly agrees on most architectural / methodological / empirical claims.
2. **Sharp single-axis deviation** — one paper (or two) report a *specific finding* that contradicts what the consensus assumes, but the finding is reported as a footnote, an ablation row, or a side-comment — not the paper's headline claim.
3. **No follow-up** — no other paper in the cluster has investigated the deviation or replicated it. The field has implicitly assumed the consensus is right.

**Strong examples:**
- 5 papers on memory architectures all use HNSW for dense retrieval. One paper mentions in an ablation that "flat L2 underperformed our setup by 8%" but switches to HNSW without further comment. Nobody else has tested flat-L2. Edge of consensus.
- 4 papers report that "more parameters help long-context handling." A 5th paper has a buried table showing performance peaked at 7B and declined at 13B and 70B. No subsequent paper has investigated the inverted-U. Edge of consensus.
- Adler's encoding gate is *disabled in their reported benchmarks*, with a one-paragraph note that "no existing benchmark rewards selective ingestion." If the gate is actually load-bearing and nobody's run the test, edge of consensus.

**Reject:**
- Deviations that are clearly explained by paper-specific factors (different model size, different dataset, different metric).
- Deviations that have already been investigated by a follow-up paper.
- Deviations on the paper's headline axis — those are direct contradictions or counter-theses, not edge-of-consensus.
- Methodological complaints (e.g., "benchmark X is flawed") — that's a critique, not a finding.

## Scoring rubric (1–10 each)

For each candidate edge-of-consensus, score:

- **consensus_strength** — how strongly does the rest of the cluster align on the relevant axis? (1=mixed views, 10=universal agreement)
- **deviation_specificity** — how concrete and specific is the deviating finding? (1=vague gesture, 10=specific number with conditions)
- **followup_absence** — has any subsequent paper investigated the deviation? (1=already investigated, 10=completely unexplored)

**Only emit theses scoring ≥7 on all three.**

## Output format

JSON array. Each entry:

```json
{
  "title": "<one-sentence claim — e.g., 'Paper X reports finding F that contradicts cluster consensus on D; nobody followed up'>",
  "claim": "<2-3 sentences: name the consensus, name the deviation, name why the deviation might be a near-discovery>",
  "why_latent": "<1 sentence on why this deviation was missed — buried in an ablation? reported as a side-effect? cluster citing the paper for a different finding?>",
  "how_to_falsify": "<concrete experiment design: replicate the deviating finding under controlled conditions; if it holds, the consensus is wrong on dimension D>",
  "supporting_papers": [
    {"slug": "<deviating-paper-slug>", "role": "reports the deviating finding"},
    {"slug": "<consensus-paper-slug>", "role": "represents the consensus the deviation contradicts"}
  ],
  "scores": {
    "consensus_strength": 9,
    "deviation_specificity": 8,
    "followup_absence": 9
  },
  "falsifiability": "high|medium|low"
}
```

If no edge-of-consensus deviations meet the threshold, output `[]`. False positives here are particularly costly because edge-of-consensus theses are the hardest to verify — only flag the ones you're confident about.
