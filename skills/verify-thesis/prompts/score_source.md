## Your task — Score candidate sources against a thesis

For each candidate source you're given, decide whether it **supports**, **contradicts**, **qualifies**, or is **irrelevant** to the thesis claim. Extract one specific quote that justifies the decision. Note any regime/scope qualifiers.

## Inputs

**The thesis:**

- Claim (verbatim): {{THESIS_CLAIM}}
- Falsification design (verbatim): {{HOW_TO_FALSIFY}}
- Gap type: {{GAP_TYPE}}

**Candidate sources** (list of `{title, url, snippet, score, source_engine}`):

{{CANDIDATES_JSON}}

## Decision rubric

For each candidate:

- **`supports`** — the source's argument or evidence implies the thesis is correct, in the same regime the thesis claims. The match must be substantive, not vocabulary-level.
- **`contradicts`** — the source's argument or evidence implies the thesis is wrong, in a regime the thesis claims. A finding in a different regime is *not* a contradiction — it's a qualifier.
- **`qualifies`** — the source confirms the thesis in some regime but shows it fails in another. The most common verdict for real-world evidence; the thesis was probably never fully wrong, just not fully general.
- **`irrelevant`** — the source is about an adjacent topic that does not bear on the thesis's specific claim. Common for search false positives.

**Confidence:**

- `high` — explicit quote, matched conditions, no ambiguity
- `medium` — implicit but clear, some conditions inferred
- `low` — only a hint; might be reading too much in

**Conditions**: If the source applies only in a specific regime (model size, dataset, evaluation, hardware), record it. Empty string if regime-agnostic.

## What NOT to do

- Do NOT fetch the full page yourself unless the snippet is genuinely too short to decide. The snippet is usually enough; over-fetching wastes time.
- Do NOT label `supports` for sources that merely use similar vocabulary — the source must make the same *substantive* claim.
- Do NOT label `contradicts` for regime-different evidence; that's `qualifies`.
- Do NOT speculate beyond the snippet. If unclear, label `low` confidence.

## Output format

JSON array, one entry per candidate. Same length as input array, preserving order:

```json
[
  {
    "url": "https://...",
    "title": "...",
    "label": "supports | contradicts | qualifies | irrelevant",
    "quote": "<exact passage from the snippet, ≤300 chars>",
    "conditions": "<regime/scope qualifier, or empty string>",
    "confidence": "high | medium | low",
    "notes": "<optional one-sentence note, or empty string>"
  }
]
```

Process all candidates in one pass — don't spawn sub-sub-agents. Each candidate decision is small; chain-of-thought through the list.
