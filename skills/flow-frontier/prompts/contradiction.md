## Your task — Direct-contradiction mining

You are looking for pairs of papers in the cluster that make **directly opposing factual claims** about the same phenomenon under similar conditions. Direct contradictions are the sharpest gap-type but also the riskiest — most apparent contradictions dissolve on closer reading ("paper A measured X in regime R1, paper B measured X in regime R2"). Be conservative.

## Inputs

Below are {{N}} paper digests in a cluster about **{{TOPIC}}**. For each: slug, title, key takeaway, and any specific quantitative or qualitative claims visible in the takeaway.

{{CLUSTER_PAYLOAD}}

## What to look for

A genuine direct contradiction has four properties:

1. **Specific opposing claims** — paper A claims X; paper B claims ¬X (or claims a substantively incompatible result, e.g., effect goes the opposite direction).
2. **Same phenomenon** — both claims are about the same effect / setting / problem.
3. **Comparable conditions** — model sizes, evaluation methodologies, and data sources are similar enough that the contradiction can't be dismissed as a regime difference.
4. **Unresolved in the cluster** — no other paper in the cluster has explicitly adjudicated the contradiction.

**Strong examples:**
- Paper A: "Knowledge graphs improve multi-hop QA by 5%." Paper B: "Knowledge graphs hurt multi-hop QA by 3% under matched conditions." Same benchmark, same model class. Direct contradiction.
- Paper A: "Verbatim memory beats extracted memory at all scales we tested." Paper B: "Extracted memory beats verbatim memory at >1M-event scale." Different scale → not a contradiction (regime difference). Reject this one — it's a partial-resolution, not a direct contradiction.

**Reject:**
- Pairs where conditions differ meaningfully (different model size, different metric, different definition of "memory") — these are regime-disambiguation theses, not contradictions.
- Pairs where one paper has cited and addressed the other ("we explain the apparent contradiction with X").
- Pairs whose disagreement is methodological (e.g., "their benchmark is flawed") rather than empirical.
- Trivial measurement differences (5% vs 4% is not a contradiction; +5% vs -3% is).
- Cases where you'd need to read the full papers to confirm the contradiction — if the takeaways are ambiguous, don't speculate.

## Scoring rubric (1–10 each)

For each candidate contradiction pair, score:

- **claim_oppositeness** — how directly do the claims contradict each other? (1=adjacent disagreements, 10=mirror-image opposites)
- **condition_match** — how similar are the experimental conditions? (1=apples-to-oranges, 10=apples-to-apples)
- **unresolved_in_cluster** — has any other paper in the cluster adjudicated? (1=already resolved, 10=open in the literature)

**Only emit theses scoring ≥7 on all three. AND falsifiability must be `high`** — if you can't propose a clean replication experiment, the contradiction probably isn't real.

## Output format

JSON array. Each entry:

```json
{
  "title": "<one-sentence claim — e.g., 'Paper A claims X improves Y by N%; paper B claims X hurts Y by M%; resolution needed'>",
  "claim": "<2-3 sentences: name both claims, name the matched conditions, name what falsification would settle>",
  "why_latent": "<1 sentence on why this contradiction hasn't been resolved in the literature yet — papers ignoring each other? different research groups not citing? regime-disagreement assumed but not confirmed?>",
  "how_to_falsify": "<concrete replication experiment: same model, same benchmark, controlled conditions. Whichever direction the result lands resolves the contradiction.>",
  "supporting_papers": [
    {"slug": "<paper-A-slug>", "role": "claims X"},
    {"slug": "<paper-B-slug>", "role": "claims ¬X"}
  ],
  "scores": {
    "claim_oppositeness": 9,
    "condition_match": 8,
    "unresolved_in_cluster": 9
  },
  "falsifiability": "high"
}
```

If no direct contradictions meet the threshold, output `[]`. Especially be conservative here — direct contradictions in well-cited literature are usually already resolved or regime-dependent. Empty output is a perfectly valid result.
