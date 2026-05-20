## Your task

Extract every reference cited in this paper's bibliography or references section. For each citation, return a structured JSON object. This output will be used to auto-link related papers and to seed future research loops.

## Output format

Return a single valid JSON array. No preamble, no markdown fence, no commentary — just the array. Each entry has the following fields (use `null` if a field is unknown):

```json
[
  {
    "title": "exact paper title",
    "authors": ["First Author", "Second Author"],
    "year": 2024,
    "venue": "journal or conference name, or 'preprint'",
    "doi": "10.xxxx/xxxxx or null",
    "url": "https://... or null",
    "arxiv_id": "2401.xxxxx or null"
  }
]
```

**Quality rules:**
- Authors as an array of strings, one entry per author. Use "First Last" format. Use first three authors followed by `"et al."` if there are more than three.
- Year as an integer. If only a date range or unclear, use `null`.
- Skip duplicate entries (same DOI or same title+first-author).
- If the paper has no references section, return an empty array `[]`.
- Do not invent DOIs or URLs — leave `null` if not present in the paper.
- If you find arxiv IDs in any form (`arXiv:2401.12345`, `arxiv.org/abs/2401.12345`), normalize to just the ID portion.

## Paper content

{{CONTENT}}
