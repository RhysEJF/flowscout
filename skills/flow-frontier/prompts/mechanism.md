## Your task — Mechanism-gap mining

You are looking for cases where **multiple papers report similar effects but attribute them to different mechanisms**. This is the most ablation-productive gap-type: when three papers all improve a benchmark by 20–30 pp but each names a different "load-bearing primitive," the field has a hidden disagreement about *why* things work. A clean ablation would resolve it.

## Inputs

Below are {{N}} paper digests in a cluster about **{{TOPIC}}**. For each: slug, title, key takeaway, and the mechanism(s) the paper credits for its results.

{{CLUSTER_PAYLOAD}}

## What to look for

Identify groups of **≥3 papers** that:

1. Report **substantively similar effects** (similar magnitude of improvement, similar benchmark, similar problem).
2. Attribute those effects to **different mechanisms** (different "X is the secret sauce" claims).
3. **Have not been ablated against each other** — no paper has pinned which mechanism is actually doing the work.

**Strong examples:**
- Three papers all show "structured memory beats raw by ~25 pp on LoCoMo." Paper A credits typed routing. Paper B credits graph traversal. Paper C credits consolidation. None of them ablated the others' mechanisms. Mechanism gap.
- Two papers report 15% latency reductions in agent loops. One credits speculative execution. The other credits aggressive context compression. Neither tested the other. Mechanism gap (with min_supporting=2 if user lowered the threshold).

**Reject:**
- Papers whose mechanisms are clearly additive (paper A does X + Y, paper B does X + Z — overlap is the mechanism, not a gap).
- Effects in different problem domains (memory recall vs code generation — not the same effect).
- Cases where one paper has already ablated the others' mechanisms and reported negative results — the gap is already closed.
- Mechanisms that are obviously the same thing under different names (e.g., "typed routing" and "categorical indexing" in the same vocabulary space).

## Scoring rubric (1–10 each)

For each candidate mechanism gap, score:

- **effect_similarity** — how similar are the reported effects? (1=different things, 10=clearly the same effect)
- **mechanism_divergence** — how genuinely different are the proposed mechanisms? (1=same thing renamed, 10=causally distinct)
- **ablation_absence** — how much would a clean ablation move the field? (1=already done, 10=urgent open question)

**Only emit theses scoring ≥7 on all three.**

## Output format

JSON array. Each entry:

```json
{
  "title": "<one-sentence claim — e.g., 'The X effect is attributed to incompatible mechanisms M1/M2/M3 across N papers; ablation needed'>",
  "claim": "<2-3 sentences naming the shared effect, the divergent mechanisms, and what an ablation would settle>",
  "why_latent": "<1 sentence on why no paper has pinned the actual cause yet — what's blocking the ablation>",
  "how_to_falsify": "<concrete ablation experiment design: which mechanisms to factor, which variables to control, what would prove each one is/isn't load-bearing>",
  "supporting_papers": [
    {"slug": "<paper-slug>", "role": "credits mechanism M1 for effect E"},
    {"slug": "<paper-slug>", "role": "credits mechanism M2 for effect E"},
    {"slug": "<paper-slug>", "role": "credits mechanism M3 for effect E"}
  ],
  "scores": {
    "effect_similarity": 9,
    "mechanism_divergence": 8,
    "ablation_absence": 8
  },
  "falsifiability": "high|medium|low"
}
```

If no mechanism gaps meet the threshold, output `[]`. Mechanism-gap theses should almost always be `falsifiability: high` — if you can't propose a clean ablation, the gap isn't real, it's just disagreement.
