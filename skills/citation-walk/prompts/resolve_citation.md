You are resolving a paper citation to a fetchable URL. The citation has title + authors + year but no DOI or arxiv ID. Your job is to find where this paper actually lives online so it can be downloaded for digestion.

## The citation

{{CITATION}}

## Process

1. Use the `mcp__exa__web_search_exa` tool to search for the paper. Construct the query as:
   ```
   "<exact title>" <first_author_lastname> <year>
   ```

2. Review the top 5 results. Prefer in this order:
   - **arxiv.org** (direct PDF preferred: `arxiv.org/pdf/<id>.pdf`)
   - **openreview.net** (direct PDF)
   - **acm.org / acl-anthology / ieee** (publisher PDF if accessible)
   - **A `.pdf` URL hosted on the author's personal/university page**
   - **semanticscholar.org page** (last resort — links to PDF but adds a hop)

3. Verify the match is the right paper:
   - Title matches (allow minor punctuation differences)
   - At least one author last name matches
   - Year matches (allow ±1 — preprint vs publication year drift is common)

4. Reject if no result meets the verification bar. Better to skip a paper than to digest the wrong one.

## Output format

Return ONLY a single JSON object, no preamble:

```json
{
  "resolved": true,
  "url": "https://arxiv.org/pdf/2407.17387.pdf",
  "confidence": "high",
  "source": "arxiv"
}
```

Or, if no good match:

```json
{
  "resolved": false,
  "reason": "no_confident_match",
  "attempted_queries": ["..."]
}
```

`confidence` values: `"high"` (exact title + author + year match), `"medium"` (close title + author match with year drift), `"low"` (best-effort, may be wrong — orchestrator may choose to skip these).
