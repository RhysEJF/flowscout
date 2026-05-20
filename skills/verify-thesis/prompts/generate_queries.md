## Your task — Generate adversarial search queries

You are testing a research thesis against the open literature. Your job is to generate `{{N_QUERIES}}` search queries that will surface papers, articles, or other evidence that could **falsify, qualify, or confirm** the claim.

Good adversarial queries do NOT just paraphrase the thesis. They probe specific assumptions, look for counter-evidence under varied conditions, and target adjacent vocabulary the thesis itself wouldn't use.

## Inputs

**The thesis:**

- Title: {{THESIS_TITLE}}
- Claim (verbatim): {{THESIS_CLAIM}}
- Falsification design (verbatim): {{HOW_TO_FALSIFY}}
- Supporting papers (slugs): {{SUPPORTING_SLUGS}}
- Gap type(s): {{GAP_TYPE}}

## What to look for

Generate `{{N_QUERIES}}` queries spanning these intents (mix as appropriate):

1. **Direct support** — "research demonstrating that {{CLAIM_CORE}}". Use vocabulary the *opposing* school of thought would use, so a paper that explicitly addresses the claim from the other side is most likely to surface.
2. **Direct counter** — "research showing that NOT-{{CLAIM_CORE}}". Generate the strongest falsifier you can imagine, then search for it. If it exists, the thesis is in trouble.
3. **Conditional qualifier** — "studies on {{TOPIC}} under conditions {{X}} where {{CLAIM}} might break". Probe regime boundaries.
4. **Mechanism probe** — "papers testing whether {{MECHANISM}} is actually load-bearing". Only useful if the falsification design names a specific mechanism.

**Reject:**
- Queries that just paraphrase the thesis (will surface the supporting papers we already have).
- Vague queries ("agent memory architectures"). Be specific.
- Queries that can't be falsified in principle.

## Reframing for Exa

Each query gets reframed as an "describe the ideal page" prompt before searching, e.g.:
- ❌ "knowledge graph memory worse than verbatim"
- ✅ "arxiv research paper showing that knowledge-graph-based agent memory underperforms verbatim retrieval at scale on long-conversation benchmarks"

## Output format

JSON array. Each entry:

```json
{
  "query": "<the Exa-style 'describe the ideal page' query>",
  "intent": "support | counter | qualifier | mechanism",
  "rationale": "<one sentence on what the query is testing>"
}
```

If you cannot generate `{{N_QUERIES}}` distinct, falsifiable queries, output fewer rather than padding with weak ones. Empty list `[]` is valid but unusual — if the thesis really has zero testable angles, flag that in a single-element array with `{"query": null, "intent": null, "rationale": "untestable: <reason>"}`.
