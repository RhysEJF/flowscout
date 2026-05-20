---
name: citation-walk
description: Walk the citation graph from a seed paper (URL or already-digested slug) to build coverage on a topic. Four modes — --broad (cover all citations widely), --deep (follow the most-relevant thread to the cutting edge), --canonical (surface foundational papers cited by multiple already-digested works), --orbit (lateral discovery — generates mutated takeaways from the seed and uses Exa to find papers in different vocabulary subgraphs that no citation walk would reach). Internally calls /digest-paper on each visited paper, deduplicates against the wiki, scores candidate relevance, checkpoints state, and produces a final meta-digest synthesizing the cluster. Trigger when user says `/citation-walk <seed> --topic="..."` or asks to "find related papers", "build coverage on this topic", "walk citations from this paper", "find papers that everyone cites", or "find papers connected by idea not by citation".
---

# /citation-walk — Citation-graph walker

> Compounds your papers wiki by walking the citation graph from a seed paper, with topic-relevance scoring and a hard budget so it doesn't drift or run forever.

## ⚠️ Architectural rule — invoke at top level only

`/citation-walk` MUST be invoked directly by the user (top level) — NOT dispatched as a sub-agent by another skill like `/research-cycle`.

If `/research-cycle` (or any other orchestrator) needs `/citation-walk`'s functionality, it must run **this skill's methodology inline** (read its steps and execute them itself) and dispatch `/digest-paper` directly. See `/research-cycle/SKILL.md` "Architectural rule" section.

**Why**: sub-agents cannot dispatch Agent tool calls. If `/citation-walk` runs as a sub-agent, its inner `/digest-paper` dispatches silently collapse to inline execution in the `/citation-walk` sub-agent's single shared context. Result: ~14 min per paper instead of ~3 min, figures get skipped under context pressure, sub-agent stops after 1 paper instead of N.

When invoked at top level (the normal user path), this skill dispatches `/digest-paper` sub-agents at level 1 — each gets its own fresh 200K-token context, all run in parallel, ~10 min wall-clock for 10 papers.

## When to Use

- User says `/citation-walk <seed-url-or-slug> --topic="..."` (with optional `--broad` / `--deep` / `--canonical`)
- User asks to "find related papers" / "build coverage on this topic" / "walk citations from this paper" / "find papers that everyone cites"
- User has just run `/digest-paper` on a seed paper and wants to expand into the cluster around it
- User wants to find the foundational works in a field they're already partially digesting (`--canonical`)

## Arguments

| Flag | Meaning |
|---|---|
| `<seed-url-or-slug>` (required, except for `--canonical`) | URL of a paper to seed from, OR slug of an already-digested paper in `memory/knowledge-sources/papers/`. Slug-vs-URL detection: if starts with `http://` / `https://` or contains `/`, treat as URL; otherwise slug. |
| `--topic="..."` (required) | Short sentence describing the topic you want coverage on. Used for relevance scoring. Example: `"synthetic AI personas for market research"`. |
| `--broad` | (default mode) Digest ALL of the seed's citations (1-hop completeness), then optionally extend to 2-hop on the most-relevant candidates. Wide coverage, shallow depth. |
| `--deep` | Pick the **single most relevant** citation, digest it, pick the most relevant from ITS citations, digest, repeat. Thin chain through the graph following the topic thread. |
| `--canonical` | No seed required. Scan all already-digested papers' citations, find the ones cited by ≥ `--min-canonical-count` distinct digests but not yet digested themselves. Digest the top N. |
| `--orbit` | **Lateral discovery — does NOT walk citations.** Reads the seed's `key_takeaway`, spawns 4 parallel sub-agents that each mutate it through a different lens (counter-thesis / push-to-limit / two adjacent-field translations), runs Exa semantic search with each mutation, aggregates by cross-pattern frequency, and digests the top N candidates. Surfaces papers connected by *shape* rather than by citation — work in different vocabulary subgraphs that a citation walk would never reach. Seed must be an already-digested slug. `--topic` is optional (the takeaway IS the topic). |
| `--max-papers=N` | Hard cap on total NEW papers digested per run. Default: 15. |
| `--max-depth=N` | Hop limit from seed. Default: 3. Ignored for `--canonical`. |
| `--min-relevance=0.5` | Float 0-1. Candidates scoring below this don't enter the frontier. Default: 0.5. Ignored for `--canonical`. |
| `--min-canonical-count=3` | Used only with `--canonical`. Minimum number of distinct already-digested papers that must cite a candidate for it to qualify. Default: 3. |
| `--lens=<slug>` | Lens passed through to `/digest-paper` for every paper visited. Default: `generic`. |
| `--dry-run` | Compute the frontier and rank candidates, but DO NOT fire any `/digest-paper` agents and DO NOT write to the wiki. Output a preview table to stdout so the user can sanity-check what would be digested before committing to the run. ~10-30 seconds. |

## Mutually exclusive modes

Exactly one of `--broad`, `--deep`, `--canonical`, `--orbit` may be set. If none given, default to `--broad`. If multiple given, error out and tell the user to pick one.

## Methodology

### Step 1 — Parse args + initialize state

```
1. Validate args: exactly one of (--broad, --deep, --canonical). Topic required
   unless --canonical (which uses the wiki as its topic by definition).
2. If seed is a slug → check memory/knowledge-sources/papers/<slug>.md exists.
   If seed is a URL → no preflight check (the digest step will handle it).
3. Create run directory: experiences/citation-walk/<seed-slug-or-canonical>-<YYYY-MM-DD>/
4. Initialize state.json:
   {
     "mode": "broad|deep|canonical",
     "topic": "...",
     "lens": "...",
     "max_papers": 15,
     "max_depth": 3,
     "min_relevance": 0.5,
     "min_canonical_count": 3,
     "seed": {"type": "slug|url", "value": "..."},
     "frontier": [],          # [{"url": "...", "depth": 1, "score": 0.7, "title": "...", "source_citation": {...}}, ...]
     "seen": [],              # [{"key": "doi:10.../arxiv:.../title:normalized"}, ...] — dedup set
     "digested": [],          # [<slug>, ...] — slugs of papers digested THIS run
     "skipped": [],           # [{"reason": "below_threshold|no_url|already_digested|fetch_failed", "candidate": {...}}, ...]
     "budget_used": 0,
     "started_at": "<ISO-8601>",
     "completed_at": null,
     "status": "running"
   }
5. Open log.md and start writing human-readable progress.
6. If `--dry-run` was passed, set state.status = "dry-run" and continue through Steps 2–4 (seed frontier, score, resolve URLs) — but STOP before Step 5 (the main loop). After Step 4, print a preview table to stdout summarizing what would have been digested:

   ```
   /citation-walk DRY-RUN — <mode>, topic="<topic>"
   Existing wiki: N papers digested already (won't be re-digested)
   Frontier (top <max_papers> by score) — these WOULD be digested:
     <score>  <url>  <title>  (depth=<d>)  [arxiv|exa|already-found]
     ...
   Skipped (not entering frontier):
     <reason>  <count>  e.g. "no_url: 12", "below_threshold (<0.3): 5"
   Estimated wall-clock: ~<N>×<3-8>min in parallel batches of 5
   Estimated cost: <N> × /digest-paper calls (~1-2 cents each)

   Re-run without --dry-run to execute.
   ```

   Then exit cleanly. Do NOT fire any `/digest-paper` agents, do NOT write to `memory/knowledge-sources/papers/`.
```

### Step 2 — Seed the frontier (mode-specific)

**Mode: `--broad` or `--deep`**

```
1. If seed is a URL:
   - Call /digest-paper <url> --lens=<lens> via Agent tool
   - On completion, get back the slug + the digest's frontmatter.citations[]
   - Add slug to state.digested, budget_used += 1
   - Add normalized key to state.seen
2. If seed is a slug:
   - Read memory/knowledge-sources/papers/<slug>.md
   - Extract frontmatter.citations[]
   - Add slug to state.seen (but NOT to state.digested — it was pre-existing)
3. For each citation in the seed's citations[]:
   - Normalize: key = doi || arxiv_id || normalize_title(title, first_author, year)
   - If key in state.seen, skip
   - Score relevance against state.topic (see Step 3)
   - If score >= min_relevance, push to frontier with depth=1
   - Mark key as seen
```

**Mode: `--canonical`**

```
1. Read all existing memory/knowledge-sources/papers/*.md (skip INDEX.md, viewer.html, figures/)
2. For each existing digest:
   - Parse frontmatter.citations[]
   - For each citation:
     - Normalize key
     - If key matches the slug of an already-digested paper, skip
     - tally[key] = tally.get(key, 0) + 1
     - Store the most complete metadata seen for this citation
3. Sort tally desc by count. Filter to count >= min_canonical_count.
4. For the top N (where N = max_papers), populate frontier:
   - Each entry: {"url": resolved_url, "depth": 0, "score": count_as_proxy, ...}
   - Use Exa/arxiv-API to resolve URL if the citation only has title+authors (see Step 3.5)
   - Add to skipped if URL can't be resolved
5. No need for further relevance scoring — citation frequency IS the signal.
```

**Mode: `--orbit` (lateral discovery via mutated takeaways)**

This mode does NOT walk the citation graph. It generates mutated key-takeaways from the seed and uses Exa to find papers in different vocabulary subgraphs — papers connected by *shape*, not by citation. Validated experimentally: from one seed (Adler 2026) under the `memory-architect` lens, three mutations surfaced ~18 new papers, only ~3 of which a forward/backward citation walk would have reached.

```
1. Seed must be an already-digested slug. If a URL was supplied, first call
   /digest-paper on it, then proceed with the resulting slug.

2. Read the seed's frontmatter:
   - key_takeaway   (REQUIRED — must exist and be non-empty)
   - lens           (used to choose adjacent fields for translation patterns)

3. Pick adjacent fields for translation patterns based on lens:
   - memory-architect    → FIELD_A=operating systems / virtual memory
                           FIELD_B=cognitive psychology / hippocampal memory
   - synthetic-personas  → FIELD_A=ethnographic market research
                           FIELD_B=evolutionary game theory
   - generic             → FIELD_A=physics / information theory
                           FIELD_B=biology / evolution
   - any other lens      → read skills/digest-paper/lenses/<lens>.md and infer
                           two adjacent fields from its content; if unclear,
                           fall back to (operating systems, cognitive psychology)

4. Spawn 4 parallel sub-agents (single message, 4 Agent calls), one per pattern.
   Each receives only the seed's key_takeaway and outputs exactly one sentence.

   PATTERN 1 — Counter-thesis:
     "Given this paper's key takeaway: '{takeaway}' — generate ONE sentence
      that states the OPPOSITE thesis as if it were the takeaway of a paper
      arguing against this one. Use vocabulary the original paper would not
      use. Be specific and falsifiable. Output ONLY the one sentence — no
      preamble, no explanation."

   PATTERN 2 — Push-to-limit:
     "Given this paper's key takeaway: '{takeaway}' — assume it is correct,
      then push the claim to its extreme. What would the takeaway of a paper
      that pushed this idea to extreme scale or extreme generality say?
      Name what would break, or what would emerge, at that limit. Output
      ONLY one sentence."

   PATTERN 3 — Adjacent-field translation (FIELD_A):
     "Given this paper's key takeaway: '{takeaway}' — restate the same
      underlying idea in the vocabulary of {FIELD_A}. Use that field's
      standard terminology and concepts. Output ONE sentence as if it were
      the takeaway of a paper in that field. Output ONLY one sentence."

   PATTERN 4 — Adjacent-field translation (FIELD_B):
     Same as Pattern 3 but with {FIELD_B}.

5. Reframe each mutation as an Exa "ideal page" query by prepending a
   research-paper frame:
     "arxiv research paper that argues/proposes/shows that {mutation}"

6. Run 4 parallel mcp__exa__web_search_exa calls (numResults=8 each).
   Total candidates: up to 32 raw results.

7. Aggregate + filter:
   a) Normalize each result: arxiv_id (preferred) || url || title-hash
   b) Drop the seed itself (if it surfaced) and the seed's notes sidecar
   c) Drop hits that are already in state.seen (existing wiki digests)
   d) For each unique candidate, record:
        { url, title, arxiv_id?, patterns: [list of pattern numbers that
          surfaced it], max_score: max of Exa scores }
   e) Rank by (len(patterns) DESC, max_score DESC). Cross-pattern hits
      always rank above single-pattern hits — a paper that hits both the
      counter-thesis and a field-translation is high-confidence interesting.

8. Push top max_papers entries to state.frontier with:
     depth=1,
     score = min(0.99, 0.6 + 0.1 * len(patterns)),
     source_citation = {patterns: [...], mutations: {pattern_idx: query}}

9. Skip Step 3 (Haiku relevance scoring) for --orbit. Exa's semantic
   reranking + cross-pattern frequency IS the signal. If --topic was
   provided, optionally re-rank candidates within each (patterns, max_score)
   tier by topic-similarity — but do NOT drop below max_papers.

10. Persist the four mutated takeaways to the run dir at
    `experiences/citation-walk/<run-dir>/orbit-mutations.md` so the user can
    inspect WHAT was searched. Format:

      # Orbit mutations for {seed-slug}

      Generated from seed key_takeaway:
      > {takeaway}

      ## Pattern 1 — Counter-thesis
      {generated sentence}

      ## Pattern 2 — Push-to-limit
      {generated sentence}

      ## Pattern 3 — Adjacent-field translation ({FIELD_A})
      {generated sentence}

      ## Pattern 4 — Adjacent-field translation ({FIELD_B})
      {generated sentence}

    This makes the discovery audit-trail explicit. If a pattern is producing
    weak hits, the user can edit this file and re-run with --resume (v2).
```

### Step 3 — Score relevance of a candidate against the topic

Used in `--broad` and `--deep` modes (skipped for `--canonical`).

**For candidates that are ALREADY digested** (rare during walk, but happens with cross-cluster citations):

Run once at start of each batch:
```bash
./vendor/qmd/bin/qmd vsearch "<state.topic>" --json -n 100 \
  | jq '[.[] | select(.file | startswith("memory/knowledge-sources/papers/"))
              | select(.file | endswith(".md"))
              | {slug: (.file | sub(".*/"; "") | sub(".md$"; "")), score}]'
```

This gives you a relevance score (cosine similarity) for every digested paper relative to your topic. Cache the result; reuse for the batch.

**For NEW candidates (not yet digested)** — use Haiku-judge:

```
For each candidate batch (up to 20 candidates per Agent call):
  Launch Agent(
    subagent_type="general-purpose",
    description="relevance scoring",
    prompt=<see prompts/score_relevance.md, with {{TOPIC}} and {{CANDIDATES}} filled in>
  )
  Parse JSON response: [{"key": "...", "score": 0.0-1.0}, ...]
```

Why Haiku-judge and not QMD vectors for these: QMD's embedding model (`embeddinggemma-300M` by default, configurable via `QMD_EMBED_MODEL`) runs in node-llama-cpp and is not exposed for ad-hoc text→vector conversion outside the index. Adding `sentence-transformers` as a Python dep to bridge this would be a ~1GB install. Haiku-judge:
- Already set up (uses the same Claude API everything else uses)
- ~$0.0005 per scoring decision
- Higher quality than title-only vector similarity (Haiku understands paper context, knows what "PERSONA" means in a 2024 AI paper, etc.)
- Negligible cost: max 15 papers × ~20 candidates × $0.0005 = $0.15 per max-budget run

### Step 3.5 — Resolve candidate URL when missing

Most citations from `/digest-paper` already have `doi`, `arxiv_id`, or `url`. For those that don't:

```
For citation with title + authors + year but no URL:
  Use Exa MCP (mcp__exa__web_search_exa) with query:
    "<title>" <first_author> <year>
  Filter results: prefer arxiv.org, openreview.net, .pdf links, semanticscholar.org
  Pick top match if confidence is high (title close enough)
  If no good match, mark as skipped with reason="no_url" and move on
```

For arxiv-IDed citations: construct URL as `https://arxiv.org/abs/<arxiv_id>`.
For DOI-only citations: try `https://doi.org/<doi>` — many resolve to publisher PDFs.

### Step 4 — Lightweight metadata fetch (title + abstract) for new candidates

Before scoring, we need the abstract to give Haiku-judge a strong signal. Fetch via:

```
For arxiv candidates:
  curl -s "http://export.arxiv.org/api/query?id_list=<arxiv_id>" \
    | (parse Atom XML for <summary>)
  ~200ms, free, no API key needed

For DOI candidates:
  curl -s "https://api.openalex.org/works/doi:<doi>" \
    | jq '.abstract_inverted_index | (deinvert)'
  ~300ms, free, no API key needed

For unknown candidates:
  Use Exa to fetch a snippet of the paper page (title + abstract usually visible)
```

If abstract fetch fails for a candidate, score on title alone — accept the weaker signal, don't fail the whole run.

### Step 5 — Main loop (mode-specific)

**Mode: `--broad`**

```
while frontier non-empty AND budget_used < max_papers:
    # Take a batch of the top-K highest-scoring candidates with depth <= max_depth
    batch_size = min(5, max_papers - budget_used)
    batch = pop_top_n(frontier, batch_size, filter: depth <= max_depth)

    # Dispatch parallel digests
    Send ONE message with batch_size Agent calls, each running:
      "Execute /digest-paper for <url> with --lens=<lens>. Follow
       skills/digest-paper/SKILL.md exactly. After completion, report:
         slug, frontmatter.citations[], hallucination_severity."

    Wait for all to complete.

    For each result:
      append slug to state.digested
      budget_used += 1
      append normalized key to state.seen

      For each cit in result.citations:
        norm_key = normalize(cit)
        if norm_key in state.seen: continue
        state.seen.append(norm_key)

        url = cit.url || resolve_url(cit)  # Step 3.5
        if not url:
          state.skipped.append({"reason": "no_url", "candidate": cit}); continue

        meta = fetch_abstract(cit)  # Step 4 — falls back to title-only on failure
        score = score_relevance(meta, state.topic)  # Step 3
        if score < state.min_relevance:
          state.skipped.append({"reason": "below_threshold", "candidate": cit, "score": score}); continue

        frontier.push({"url": url, "depth": result.depth + 1, "score": score, ...})

    checkpoint state.json + log.md
```

**Mode: `--deep`**

Same as broad, but `batch_size = 1` (always single-paper batches) and after each digest only the **top-1 most-relevant citation** is pushed to the frontier. This produces a thin chain rather than a fan-out tree.

**Mode: `--canonical`**

The frontier is populated once in Step 2; no new citations get added (canonical is a one-shot survey of what's already in your wiki). The loop just iterates the pre-populated frontier:

```
while frontier non-empty AND budget_used < max_papers:
    batch = pop_top_n(frontier, 5)  # by citation_count, descending
    Dispatch parallel digests (same as broad)
    For each result: append slug to state.digested, budget_used += 1
    (No relevance scoring, no new citations pushed.)
    checkpoint state.
```

**Mode: `--orbit`**

Same shape as `--canonical` — the frontier was populated once in Step 2, the loop just drains it:

```
while frontier non-empty AND budget_used < max_papers:
    batch = pop_top_n(frontier, 5)  # by (patterns_count, max_score), descending
    Dispatch parallel digests via /digest-paper, passing through --lens=<seed-lens>
    For each result:
        append slug to state.digested
        budget_used += 1
        record source_citation.patterns so the meta-digest can attribute
        which mutation surfaced this paper
    (No new candidates pushed — orbit is a one-shot mutation pass.)
    checkpoint state.
```

### Step 6 — Synthesize the final meta-digest

After the loop exits, run ONE Agent call with `prompts/synthesize_cluster.md`. Inputs:
- The seed (URL or slug)
- The topic
- The mode
- The full list of digested slugs (this run + the pre-existing wiki entries that were used for canonical or that the walk touched)
- The skipped list with reasons

The synthesis prompt produces a markdown meta-digest:
- Cluster overview (what's the field about, in one paragraph)
- Timeline of papers in the cluster (chronological, with brief one-liners)
- Most-cited / consensus papers (the "must read" subset)
- Thematic threads (what subtopics emerge)
- Gaps / open questions (what the cluster doesn't answer)
- Recommended reading order (best path through the cluster for someone new to it)

Write to `experiences/citation-walk/<run-dir>/meta-digest.md`.

### Step 6.5 — Reconcile INDEX.md (post-run)

Some sub-agents may have skipped their `INDEX.md` append for concurrency safety (the lock might have timed out, or the agent self-aborted the row write). Before declaring the run complete, scan every slug in `state.digested` and ensure each has a row in `memory/knowledge-sources/papers/INDEX.md`. Add any missing rows.

```python
import re, yaml
INDEX = "memory/knowledge-sources/papers/INDEX.md"
with open(INDEX) as f: idx = f.read()
existing_slugs = set(re.findall(r'\]\(([\w\-]+)\.md\)', idx))
for slug in state["digested"]:
    if slug in existing_slugs:
        continue
    # Read the digest's frontmatter to construct the row
    with open(f"memory/knowledge-sources/papers/{slug}.md") as f:
        meta = yaml.safe_load(f.read().split("---")[1])
    row = f"| {meta['digested_date']} | [{meta['title']}]({slug}.md) | " \
          f"{meta['authors'][0].split(',')[0]} et al. | {meta['year']} | " \
          f"`{meta['lens']}` | {meta['key_takeaway']} |"
    idx = re.sub(r'(\|---\|---\|---\|---\|---\|---\|\n)', r'\1' + row + '\n', idx, count=1)
with open(INDEX, "w") as f: f.write(idx)
```

This is cheap and idempotent — running it on a fully-consistent INDEX is a no-op.

### Step 7 — Update state to completed + refresh QMD

```bash
# Mark run done
update state.json: status="completed", completed_at=<now>

# Reindex so the new digests + the meta-digest are searchable
# Use the lock helper since other sessions / future digest calls may also be reindexing.
python3 scripts/with-lock.py /tmp/qmd-update.lock --timeout 120 -- ./vendor/qmd/bin/qmd update
python3 scripts/with-lock.py /tmp/qmd-embed.lock --timeout 300 -- ./vendor/qmd/bin/qmd embed
```

### Step 8 — Report to user

Single message summarizing:
- Mode + topic
- N papers digested this run (with slugs)
- N candidates skipped (with reasons)
- Most surprising finding (pull from the meta-digest's "key insight")
- Path to the meta-digest file
- Suggested next move: open `viewer.html` to browse, or `/citation-walk --canonical` to find foundational works now that the wiki has grown

## State + checkpointing

All state lives at `experiences/citation-walk/<run-dir>/state.json` and is rewritten after every batch. If a run is interrupted (token budget, crash, user stops it), you can inspect the state and resume by re-invoking with `--resume=<run-dir>` (defer the resume flag to v2 — for v1, interrupted runs just leave partial state behind, which is fine: the digests written so far ARE the wiki).

## Critical Rules

- **Modes are mutually exclusive.** Reject any invocation with more than one of `--broad` / `--deep` / `--canonical`.
- **Always update state.json after every batch.** If a run dies mid-flight, the next session can pick up by reading state.
- **Always run `qmd update` + `qmd embed` at the end** — the new digests aren't searchable until the index rebuilds.
- **Deduplication is on normalized key, not raw title.** Different papers can have the same first word; same paper can have minor title variants across citation styles. Normalize to lowercase, strip punctuation, take first 60 chars + first author lastname + year as the dedup key.
- **Never invoke `/citation-walk` recursively.** This skill calls `/digest-paper`, not itself. No reentrancy.
- **Respect the budget hard.** Even if relevance scores are sky-high, stop at `max_papers`. The user can re-invoke if they want more.
- **`--canonical` requires a non-trivial wiki.** If fewer than ~5 already-digested papers exist, warn the user — canonical signal is too weak and you'll get noise. Suggest running `--broad` a couple times first.

## Paper-digest invocation pattern

Each `/digest-paper` call from within `/citation-walk` happens via Agent tool. The prompt template:

```
You are executing the /digest-paper skill defined in skills/digest-paper/SKILL.md
on the paper at <URL>.

Follow that SKILL.md end-to-end. Use --lens=<LENS>.

When complete, report back ONLY:
  - slug: <kebab-slug-of-digest>
  - hallucination_severity: <Clean|Minor fact tweak|Urgent rewrite needed>
  - citations_count: <N>
  - figure_extracted: <true|false>

Do not include the full digest in your response — it's already on disk.
```

This keeps the orchestrator's context lean.

## Verify

After running the skill, confirm:
- [ ] `experiences/citation-walk/<run-dir>/state.json` exists with `status: "completed"`
- [ ] `experiences/citation-walk/<run-dir>/meta-digest.md` exists
- [ ] `experiences/citation-walk/<run-dir>/log.md` exists with batch-by-batch progress
- [ ] Every slug in `state.digested` corresponds to a real file under `memory/knowledge-sources/papers/`
- [ ] `qmd search "<topic-fragment>"` returns the new digests + the meta-digest
- [ ] If mode was `--canonical`, confirm every digested paper was indeed cited by ≥ min_canonical_count distinct pre-existing digests

## Auto-research hook (forward compatibility)

This skill IS the "auto-research" the user was thinking about (not to be confused with Karpathy's `autoresearch` which is for ML training experiments). Future expansions:

- `--resume=<run-dir>` flag: pick up an interrupted run from its checkpointed state. Especially useful for `--orbit` where the user might want to edit the persisted mutations and re-search.
- `--orbit-hybrid` mode: combine `--orbit` and `--broad`. Run orbit first (lateral discovery), then for each new paper digested, also walk its 1-hop citations (filling in the citation-graph neighborhood around the laterally-discovered work).
- Scheduled mode: `/schedule weekly /citation-walk --canonical --max-papers=5` — passive growth of the wiki as new papers cite older work.
