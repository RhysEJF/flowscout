## Your task — Synthesise the verdict on a thesis

Given the thesis claim + the scored evidence from searches, decide one of four verdicts and produce a structured output ready to write back into the thesis frontmatter and body.

## Inputs

**The thesis:**

- Title: {{THESIS_TITLE}}
- Claim: {{THESIS_CLAIM}}
- Falsification design: {{HOW_TO_FALSIFY}}
- Supporting papers: {{SUPPORTING_SLUGS}}

**Scored evidence** (list of `{url, title, label, quote, conditions, confidence, notes}`):

{{SCORED_JSON}}

**Whether to draft an experiment design**: {{DRAFT_EXPERIMENT}} (boolean — true when `--no-experiment` is not set)

## Verdict rubric

| Verdict | Required pattern in scored evidence |
|---|---|
| **`resolved-yes`** | ≥2 `supports` at `high` or `medium` confidence AND zero `contradicts` at `high` confidence. The literature confirms the claim. |
| **`resolved-no`** | ≥2 `contradicts` at `high` or `medium` confidence AND zero `supports` at `high` confidence. The literature falsifies the claim. |
| **`partially-resolved`** | At least one `qualifies` entry with clear regime/condition boundaries, AND the union of supports + qualifies covers most but not all of the claim's intended scope. |
| **`open`** | Everything else: empty search, weak evidence, evenly split, or the search did not surface the specific evidence the thesis's falsification design requires. |

**Default to `open` when uncertain.** False positives on `resolved-yes` / `resolved-no` are costly because they kill or canonise theses prematurely.

## What to produce

```json
{
  "verdict": "resolved-yes | resolved-no | partially-resolved | open",
  "verdict_sentence": "<one-sentence summary suitable for the frontmatter `verdict` field>",
  "rationale": "<one paragraph (3-5 sentences) explaining how the evidence led to this verdict — references specific scored entries by URL>",
  "verdict_evidence": [
    {
      "source": "<url>",
      "title": "<title>",
      "label": "supports | contradicts | qualifies",
      "quote": "<from the score step>",
      "conditions": "<from the score step>",
      "confidence": "high | medium | low"
    }
    // Include the TOP 3-6 most decisive entries. Drop irrelevant ones.
  ],
  "contradicting_papers": [
    // For wiki papers that contradict — slugs only.
    // For external contradicting sources — URLs.
    "<slug or url>"
  ],
  "experiment_design": {
    // Only populated when verdict is "open" or "partially-resolved" AND DRAFT_EXPERIMENT is true.
    // Otherwise null.
    "scenario": "<one paragraph: the real-world setting where this thesis would be tested>",
    "hypothesis": "<one sentence: what's being tested>",
    "method": [
      "<step 1>", "<step 2>", "..."
    ],
    "success_criteria": "<what result would confirm the thesis>",
    "failure_criteria": "<what result would falsify it>",
    "cost_estimate": "<rough dollar + wall-clock estimate, or 'unknown'>",
    "infrastructure": "<karpathy-autoresearch | flow-outcome | manual | other>"
  }
}
```

## Notes on quality

- The `verdict_evidence` list is what the user reads first. Pick entries that are most likely to change their mind, not the ones with the highest scores.
- The `rationale` should NAME specific sources by their host (e.g., "the arxiv:2510.05381 paper") — generic "the literature suggests…" is useless.
- The `experiment_design` should build on the thesis's existing falsification section, not invent a new one. The verifier's job is to *sharpen* the experiment based on what the literature gap revealed.

## When evidence is empty or all-irrelevant

If `scored_evidence` is empty or has only `irrelevant` entries:

```json
{
  "verdict": "open",
  "verdict_sentence": "Literature search returned no substantive evidence on this claim",
  "rationale": "All N candidate sources surfaced by the {{N_QUERIES}} adversarial queries scored as irrelevant or were not retrievable. This thesis has not been tested in publicly-indexed literature — making it a strong candidate for original experimentation rather than further verification.",
  "verdict_evidence": [],
  "contradicting_papers": [],
  "experiment_design": {...}  // if DRAFT_EXPERIMENT
}
```

This is a valid and useful outcome — empty literature = research opportunity.
