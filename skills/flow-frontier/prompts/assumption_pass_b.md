## Your task — Pass B of unstated-assumption mining

You have implicit assumptions extracted from {{N}} papers in a cluster. Your job is to find cases where **one paper's untested assumption is directly tested (or falsified) by another paper in the same cluster**. Those (assumption, asserter, tester) tuples become falsifiable theses.

## Inputs

**Assumptions from Pass A** — one block per paper:

{{ASSUMPTIONS_FROM_PASS_A}}

**Key takeaways from all papers** (so you can identify potential testers):

{{TAKEAWAYS}}

## What to look for

For each assumption from Pass A:

1. Read the assumption and which paper made it.
2. Scan the takeaways of ALL OTHER papers in the cluster.
3. Does any other paper directly test, contradict, or partially-qualify that assumption?

**Strong matches:**
- Paper A assumes "more parameters → better long-context handling." Paper B's takeaway: "context length alone hurts performance 13.9–85% even with perfect retrieval." → contradicts.
- Paper A assumes "vector search retrieves what's relevant." Paper B's takeaway: "hybrid BM25+dense beats vector-only by 12 points." → qualifies.

**Reject weak matches:**
- Generic agreement/disagreement that doesn't directly bear on the assumption.
- Cases where Paper B operates in a different regime (e.g., different model size, different data type) and the connection requires a leap.
- Cases where the assumption was already a known open problem in the field.

## Output format

JSON array. Each entry becomes a thesis:

```json
{
  "title": "<one-sentence claim — e.g., 'Paper A's assumption X is contradicted by Paper B's finding Y'>",
  "claim": "<2-3 sentences. Name the assumption explicitly, name what tested it, state the falsifiable thesis that emerges.>",
  "why_latent": "<1 sentence on why this gap matters — what downstream work depends on the assumption that nobody has flagged>",
  "how_to_falsify": "<concrete experiment that would settle whether the assumption holds in regime A but not regime B, or whether the contradiction is real>",
  "supporting_papers": [
    {"slug": "<asserter-slug>", "role": "makes the implicit assumption"},
    {"slug": "<tester-slug>", "role": "tests/contradicts the assumption"}
  ],
  "match_strength": "strong|qualified",
  "falsifiability": "high|medium"
}
```

`match_strength: "qualified"` means the tester contradicts the assumption in some regime but not necessarily all. `match_strength: "strong"` means the contradiction is direct and regime-agnostic.

If no assumption→tester pairs meet the bar, output `[]`.

Be conservative — false positives here pollute the thesis backlog. A clean empty result is better than three weak theses.
