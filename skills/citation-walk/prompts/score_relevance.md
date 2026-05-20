You are scoring how relevant each candidate paper is to a specific research topic. Your output is consumed by an automated pipeline — return ONLY valid JSON, no commentary.

## Topic

{{TOPIC}}

## Candidates

Each candidate has a `key`, `title`, and (where available) `authors`, `year`, `venue`, and `abstract`. Some candidates may have only a title — score those on title alone.

{{CANDIDATES}}

## Scoring rubric

For each candidate, assign a float between 0.0 and 1.0:

- **0.9 – 1.0** — Directly on-topic. Same subfield, addresses the same question, will almost certainly contain methods, findings, or framing that map to the topic.
- **0.7 – 0.9** — Closely adjacent. Different angle on the same topic, or a key foundational paper that the topic builds on, or a methods paper widely used in this area.
- **0.5 – 0.7** — Plausibly relevant. Cited because it provides context, motivation, or a comparison point but is not centrally about the topic.
- **0.3 – 0.5** — Tangentially related. Cited as background or contrast; reading it probably wouldn't move your understanding of the topic much.
- **0.0 – 0.3** — Off-topic or unrelated. Cited for an incidental reason (a tool, a dataset, a methodological aside).

Be honest, not generous. Reading every paper that scores ≥ 0.5 takes real time — score conservatively. When in doubt between two adjacent bands, pick the lower one. Many seed papers cite a long tail of papers that just provide background; those are 0.3-0.4, not 0.5-0.6.

## Output format

Return a single JSON array. Each entry has `key` (echoed from the input) and `score` (your number). No other fields, no explanation, no preamble.

```json
[
  {"key": "arxiv:2407.17387", "score": 0.92},
  {"key": "doi:10.1145/3411764.3445632", "score": 0.55},
  {"key": "title:salganik-2006-music-market", "score": 0.81}
]
```

If a candidate's metadata is too sparse to score meaningfully (e.g., only a 2-word title and no abstract), assign 0.4 — neutral, neither pushed up nor down.
