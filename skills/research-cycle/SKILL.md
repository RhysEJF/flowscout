---
name: research-cycle
description: Run one full cycle of /citation-walk across all four modes (broad → canonical → deep → orbit) plus a longitudinal meta-digest that compounds with every prior cycle. Designed for unattended overnight loops — `/loop /research-cycle "topic"` keeps growing your wiki and the cumulative narrative. Per-cycle yield ~30-75 papers, ~45-90 min wall-clock. Auto-picks the most-cross-referenced wiki digest as the seed for deep + orbit phases. Carries unrelated high-relevance candidates over to the next cycle's queue. Trigger when user says `/research-cycle "<topic>"`, asks to "run a research cycle", "loop the citation walker overnight", or "do a multi-phase walk on this topic".
---

# /research-cycle — Multi-phase citation-walking auto-loop

> Chains all four `/citation-walk` modes into one compounding cycle. Designed to be wrapped by `/loop` for hours-long unattended runs. Each cycle reads ALL prior cycle meta-digests so the cumulative narrative on a topic grows with every pass.

## When to Use

- User says `/research-cycle "<topic>" [...flags]`
- User asks to "run a research cycle on X", "loop the citation walker overnight", "do a multi-phase walk"
- User wraps it: `/loop /research-cycle "<topic>"` for unattended cycling
- After a few `/citation-walk --broad` runs have seeded a wiki and they're ready to start compounding

## Arguments

| Flag | Default | Meaning |
|---|---|---|
| `<topic>` (positional, required) | — | Sentence describing the topic. Used for all internal /citation-walk relevance scoring AND for picking the cycle dir name. |
| `--seeds=<slug1,slug2,...>` | auto | List of seed slugs for the broad phase. If omitted, auto-pick top-3 hub papers from the wiki (most-cross-referenced). |
| `--max-papers-per-mode=N` | 10 | Hard cap per phase. Total per cycle ≤ 4×N. |
| `--modes=broad,canonical,deep,orbit` | all four | Subset of phases to run. Useful for skipping when you know one mode won't yield (e.g. `--modes=broad,canonical` early on, before you have a great seed for orbit). |
| `--lens=<slug>` | `generic` | Passed through to every `/citation-walk` call. |
| `--cycle-num=N` | auto | Auto-detected from prior cycle dirs; only override if rebuilding. |
| `--dry-run` | off | Show the plan (which seeds, which modes, projected paper count) but don't fire any agents. ~10s. |

## Mode timing (with the 2-level architecture — measured per-paper costs)

| Phase | Wall-clock | Notes |
|---|---|---|
| 1. Broaden (10 papers across 3 seeds) | ~10 min | All N picked papers dispatched as parallel /digest-paper sub-agents |
| 2. Canonical (10 papers) | ~10 min | Single canonical-tally inline + N parallel /digest-paper |
| 3. Deep (5 hops) | ~25 min | Sequential by mode design, but each digest is ~5 min (fresh context) instead of ~14 min (inline) |
| 4. Orbit (10 papers) | ~12 min | One mutation+Exa sub-agent + N parallel /digest-paper |
| 5. Longitudinal meta-digest | ~5 min | One synthesis sub-agent reads all prior cycle digests + this cycle's new papers |
| **Total** | **~60-70 min** | ~7× faster than the old nested architecture (was 6-8 hours/cycle) |

For overnight via `/loop`, expect **7-10 cycles per 8-hour session = 200-400 new papers per night** at default budget.

The orchestrator-dispatches-directly pattern is what unlocks this — see "Architectural rule" section below.

## Methodology

### Step 1 — Parse args + resolve cycle number

```
1. Validate topic is non-empty.
2. Slugify topic: lowercase, kebab-case, max 40 chars. e.g. "AI agent memory" → "ai-agent-memory"
3. Detect cycle number:
   - Glob experiences/research-cycle/cycle-*-<topic-slug>-*/state.json
   - cycle_num = max(existing) + 1; if none exist, cycle_num = 1
4. Create run dir: experiences/research-cycle/cycle-<cycle_num>-<topic-slug>-<YYYY-MM-DD>/
5. Initialize state.json (see schema below)
6. If --dry-run, print plan and exit.
```

### Step 1.5 — Phase 0: BOOTSTRAP (cold-start handler, fires only on first cycle for a brand-new topic)

Before auto-picking seeds from the wiki, check whether the wiki has any topic-relevant papers at all. If not, bootstrap via Exa.

```python
# Detection: how many topic-relevant papers exist in the wiki right now?
relevant = subprocess.run(
    f"./vendor/qmd/bin/qmd vsearch '{state.topic}' --json -n 20",
    capture_output=True, shell=True
)
relevant_papers = [r for r in json.loads(relevant.stdout)
                   if r['file'].startswith('memory/knowledge-sources/papers/')
                   and r['file'].endswith('.md')
                   and r['score'] >= 0.5]

if len(relevant_papers) >= 3:
    # Enough wiki context exists — skip Phase 0, go directly to Step 2
    log("Phase 0 skipped: wiki has N topic-relevant papers")
    return
```

If fewer than 3 relevant papers exist, run bootstrap:

```python
log("Phase 0 BOOTSTRAP: wiki has <3 topic-relevant papers, seeding via Exa")

# 1. Exa search for seed candidates
exa_results = mcp__exa__web_search_exa(
    query=f"seminal research papers {state.topic}",
    numResults=15
)

# 2. Filter to fetchable academic sources
fetchable = []
for r in exa_results:
    url = r['url']
    if any(d in url for d in ['arxiv.org/abs/', 'arxiv.org/pdf/',
                              'openreview.net/forum', 'openreview.net/pdf']):
        fetchable.append(r)
    elif url.endswith('.pdf') and any(d in url for d in [
        '.edu/', '.ac.uk/', 'rctn.org', 'lesswrong.com', 'transformer-circuits.pub']
    ):
        fetchable.append(r)

# 3. Score top 8 with Haiku-judge for relevance (cheap)
scored = haiku_judge_relevance(fetchable[:8], state.topic)
scored.sort(key=lambda x: -x['score'])

# 4. Take top 3 with score >= 0.7 (if fewer, the topic may be too narrow — log and bail)
bootstrap_seeds = [s for s in scored if s['score'] >= 0.7][:3]
if not bootstrap_seeds:
    raise CycleAbort(
        f"Bootstrap could not find seed papers for topic '{state.topic}'. "
        f"Top Exa results: {[s['url'] for s in scored[:3]]}. "
        f"Try a more specific topic or pass --seeds=<url> explicitly."
    )

# 5. Fire parallel /digest-paper agents on the bootstrap seeds
parallel_dispatch([
    {"prompt": f"Execute /digest-paper {s['url']} --lens={state.lens}, sub-agent mode",
     "subagent_type": "general-purpose"}
    for s in bootstrap_seeds
])
# Wait for all to complete; collect their slugs

# 6. These slugs become Phase 1's seeds
state.bootstrap_seeds = [r.slug for r in completed]
state.phase0 = {
    "ran": True,
    "exa_query": f"seminal research papers {state.topic}",
    "candidates_considered": len(scored),
    "seeded_with": state.bootstrap_seeds
}
```

**Cost**: ~10-15 min wall-clock on first cycle for a new topic (Exa search ~5s + 3 parallel digests). Cycle 2+ skips Phase 0 because by then the wiki has 3+ topic-relevant papers.

**When Phase 0 picks weakly**: if all top-scored Exa results are below 0.7, bail with a helpful error rather than seed with low-quality picks. The user can then supply `--seeds=<url>` explicitly.

### Step 2 — Auto-pick seeds (if --seeds not given)

For the broad phase. The goal: pick papers that haven't been used as a broad-walk seed before AND have rich citation lists AND are central to the current cluster.

**If Phase 0 ran**, use `state.bootstrap_seeds` directly as Phase 1's seeds (they're freshly digested and on-topic by construction). Skip the centrality calculation below.

**If Phase 0 was skipped** (wiki already had topic-relevant papers), run the hub-paper detection:

```python
# Hub-paper detection: count both inbound (how many other digests link here)
# AND outbound (how many citations this paper has) — sum, then pick top-K.

inbound = defaultdict(int)
outbound = defaultdict(int)
already_used_as_seed = set()  # read from prior cycle state.jsons

for digest_file in glob("memory/knowledge-sources/papers/*.md"):
    if not is_topic_relevant(digest_file, state.topic):  # via qmd vsearch
        continue
    fm = parse_frontmatter(digest_file)
    slug = fm["slug"]
    outbound[slug] = len(fm.get("citations", []))
    for related in fm.get("related_digests", []):
        inbound[related] += 1

centrality = {slug: inbound[slug] + (outbound[slug] / 10)  # outbound is bigger, downweight
              for slug in (inbound.keys() | outbound.keys())}

# Filter to topic-relevant + not-yet-seeded, sort by centrality desc
seeds = [slug for slug, _ in sorted(centrality.items(), key=lambda x: -x[1])
         if slug not in already_used_as_seed
         and is_topic_relevant(slug, state.topic)][:3]
```

If 0 candidate seeds (rare — usually only on cycle 1 of a brand-new topic), tell the user we need a seed URL and exit. Otherwise log the picked seeds + their centrality scores.

## Architectural rule — 2-level max (THIS IS THE KEY CONSTRAINT)

The orchestrator (this top-level session) **never** dispatches a `/citation-walk` sub-agent. Instead, it runs `/citation-walk`'s methodology inline (centrality, scoring, dedup, frontier management — all via `scripts/research-cycle-helpers.py` and inline Python) and dispatches `/digest-paper` sub-agents **directly**, in parallel batches.

**Why this matters:** Sub-agents cannot dispatch their own Agent tool calls. If `/research-cycle` dispatches `/citation-walk` (level 1) which then "dispatches" `/digest-paper` (level 2), the level-2 dispatch silently collapses to inline execution within the level-1 sub-agent's single shared context. Symptoms: ~14 min per paper instead of ~3, figures get skipped under context pressure, sub-agents stop after 1 paper instead of N.

**The fix:** Keep `/digest-paper` at level 1 always. The orchestrator (level 0) is the only thing that dispatches Agents. Each `/digest-paper` sub-agent gets its **own fresh 200K-token context** for just one paper → all 8 analyses + figure extraction complete reliably, and multiple sub-agents run in true parallel.

**Speed projection** (real per-paper costs measured in cycle 1+2):

| Phase | Old (nested) | New (flat) | Speedup |
|---|---|---|---|
| Broad (10 papers) | ~80 min sequential inline | ~8 min parallel | 10× |
| Canonical (10 papers) | ~2.4 hours sequential inline | ~8 min parallel | 18× |
| Deep (5 hops, sequential) | ~70 min | ~25 min (5 × 5 min) | 2.8× |
| Orbit (10 papers) | ~80 min sequential inline | ~10 min parallel | 8× |
| **Full cycle** | **~6-8 hours** | **~50-70 min** | **~7×** |

### Step 3 — Phase 1: BROADEN

For each picked seed in `state.seeds`, the orchestrator runs the methodology **inline**:

```bash
# 1. Read this seed's citations[] from frontmatter
python3 scripts/research-cycle-helpers.py read-citations <seed-slug> > /tmp/rc-cands-<seed>.json

# 2. Build wiki dedup set
python3 scripts/research-cycle-helpers.py wiki-keys | sort -u > /tmp/rc-wiki-keys.txt
```

Then inline Python (orchestrator runs via Bash heredoc): for each candidate in `/tmp/rc-cands-<seed>.json`, compute `make_keys(candidate)` and filter out any that intersect `/tmp/rc-wiki-keys.txt`. For surviving candidates with arxiv IDs, batch-fetch abstracts:

```bash
python3 scripts/research-cycle-helpers.py fetch-arxiv-batch <id1> <id2> ... > /tmp/rc-abstracts.json
```

**Score candidates with a single Haiku-judge sub-agent dispatch** (one Agent call per seed):

```
Agent(
  subagent_type="general-purpose",
  model="haiku",
  prompt="Score candidates against topic '<topic>' using
          skills/citation-walk/prompts/score_relevance.md template.
          Candidates in /tmp/rc-cands-with-abstracts-<seed>.json.
          Write JSON [{key, score}] to /tmp/rc-scores-<seed>.json"
)
```

Take top `max_papers_per_mode / num_seeds` (e.g., 4 per seed when budget=10, 3 seeds).

For each picked candidate, resolve URL:
- arxiv → `python3 scripts/research-cycle-helpers.py resolve-arxiv-url <id>`
- doi → `https://doi.org/<doi>` (best-effort)
- title-only → dispatch a separate `mcp__exa__web_search_exa` Agent call

Then **across ALL seeds**, gather the full picked-URL list and dispatch `/digest-paper` sub-agents IN PARALLEL — single message with N parallel Agent tool calls:

```
# In ONE message, fire N Agent calls (one per paper):
for url, slug_guess in picked_papers:
    Agent(
      subagent_type="general-purpose",
      description=f"Digest {slug_guess}",
      prompt=f"Execute /digest-paper at /Users/.../skills/digest-paper/SKILL.md on:\n"
             f"  URL: {url}\n"
             f"  Lens: --lens={lens}\n\n"
             f"YOU ARE A TOP-LEVEL SUB-AGENT invoked by /research-cycle orchestrator.\n"
             f"Your inner 8-way analyses will collapse to inline (sub-agents can't\n"
             f"dispatch Agents) — that's expected. With your fresh 200K-token context\n"
             f"for just this one paper, all 8 sections + figure extraction will\n"
             f"complete reliably (we've measured this works at L1).\n\n"
             f"SKIP `qmd embed` (orchestrator handles at cycle end).\n"
             f"USE `python3 scripts/with-lock.py /tmp/papers-index.lock --timeout 60 -- ...`\n"
             f"for INDEX append. Use the same lock pattern for `qmd update`.\n\n"
             f"Report ONLY: slug, hallucination_severity, citations_count, figure_extracted."
    )
```

**Wait for ALL parallel digests to complete.** Each takes ~5-8 min, but they run in true parallel — total wall-clock ≈ slowest one.

After all return, reconcile INDEX (catches any sub-agent that skipped its append):

```bash
python3 scripts/research-cycle-helpers.py reconcile-index
```

Aggregate digested slugs into `state.phase1.digested` and `state.phase1.skipped`.

### Step 4 — Phase 2: CANONICAL

The orchestrator computes the canonical tally inline:

```bash
python3 scripts/research-cycle-helpers.py canonical-tally <min_count> <top_n> > /tmp/rc-canonical.json
# Default min_count=3, top_n=<max_papers_per_mode>
```

The helper does the heavy lifting: tallies citations across ALL wiki digests, dedups against wiki using multi-key matching, surfaces candidates cited by ≥ min_count distinct digests, returns top-N as JSON.

Read `/tmp/rc-canonical.json`. For each candidate, resolve URL (arxiv → direct, doi → doi.org, title-only → Exa via one batched Agent call).

Then dispatch up to `max_papers_per_mode` parallel `/digest-paper` sub-agents (single message, multiple Agent tool calls — same pattern as Step 3).

Wait, reconcile INDEX, aggregate `state.phase2.digested`.

**Skip rules**: if `canonical-tally` returns fewer than 3 qualified candidates, log "phase 2 skipped: insufficient signal" and move on. If the wiki has fewer than ~25 papers, skip with a note.

### Step 5 — Phase 3: DEEP

Inherently sequential (each hop's citation list comes from previous hop's digest). Pick the deep seed:

```bash
# Exclude prior deep seeds + Phase 1 broad seeds used in this cycle
python3 scripts/research-cycle-helpers.py pick-deep-seed <prior-seed-1> <prior-seed-2> ...
```

For each of `max_papers` hops (default 5):

1. Read current seed's citations + dedup against wiki (same inline pattern as Step 3)
2. Dispatch single Haiku-judge Agent to score
3. Pick top-1
4. Resolve URL
5. Dispatch ONE `/digest-paper` sub-agent at top level (fresh context, ~5-8 min)
6. Wait. New "current seed" = the digested slug
7. Loop

After all hops: reconcile INDEX. Record chain in `state.phase3.chain`.

### Step 6 — Phase 4: ORBIT

Pick the orbit seed:

```bash
python3 scripts/research-cycle-helpers.py pick-orbit-seed <prior-orbit-seed-1> ...
```

Orbit mode methodology (the orchestrator runs this):

1. Read seed's `key_takeaway` from frontmatter
2. Dispatch ONE Agent to mutate the takeaway 4 ways (counter-thesis, push-to-limit, 2 adjacent-field translations) AND run 4 Exa searches (one per mutation) AND return ranked candidates (this is one Agent call doing all 4 mutations + 4 searches sequentially in its own context — it's a SUB-agent so it can't fan out further, but it's just text manipulation + Exa MCP calls, not parallel-needing)
3. Receive ranked candidates as JSON
4. Dedup against wiki (inline Python via helpers)
5. Take top `max_papers`
6. Resolve URLs (arxiv URL is usually in Exa results directly)
7. Dispatch up to `max_papers` parallel `/digest-paper` sub-agents (same pattern as Step 3)

Wait, reconcile INDEX, aggregate.

### Step 7 — Phase 5: Longitudinal cycle meta-digest

This is the compounding artifact. Cycle N reads cycles 1..N-1's meta-digests + this cycle's new papers, and writes a digest that extends the running narrative.

```
1. Find all prior cycle meta-digests on this topic:
   prior_paths = sorted(glob("experiences/research-cycle/cycle-*-<topic-slug>-*/cycle-digest.md"))
   (Sort by cycle number, oldest first.)

2. Aggregate this cycle's new papers across all 4 phases:
   new_papers = state.phase1.digested + state.phase2.digested + state.phase3.digested + state.phase4.digested
   (Dedup — a paper may appear in multiple phases via citation overlap.)

3. Compute carry-over queue: high-scoring candidates not digested due to budget caps.
   carry_over = union of phase{1,2,3,4}.skipped where reason == "budget_exceeded" and score > 0.7

4. Launch ONE Agent with skills/research-cycle/prompts/cycle_meta_digest.md:
   - Pass CYCLE_NUM, TOPIC, NEW_PAPER_SLUGS, MODES_RUN, STARTED_AT, COMPLETED_AT
   - Pass PRIOR_CYCLE_PATHS as a list (subagent will Read each)
   - Pass WIKI_SIZE, TOPIC_RELEVANT_COUNT (one qmd query call)
   - Subagent writes to experiences/research-cycle/cycle-<N>-<topic-slug>-<DATE>/cycle-digest.md

5. After subagent returns, write carry-over to state.carry_over_for_next_cycle.
```

### Step 8 — Update state to completed + refresh QMD

```bash
# Mark cycle done
# state.json -> status: completed, completed_at: <now>, papers_added_this_cycle: <N>

# One final reindex so cycle-digest is searchable
python3 scripts/with-lock.py /tmp/qmd-update.lock --timeout 120 -- ./vendor/qmd/bin/qmd update
python3 scripts/with-lock.py /tmp/qmd-embed.lock --timeout 300 -- ./vendor/qmd/bin/qmd embed
```

### Step 9 — Report to user

Brief output for human (and for `/loop` to log):

```
Cycle <N> complete on "<topic>" (<wall-clock>)
  Phase 1 broaden:    +<n> papers (seeds: <slug1>, <slug2>, <slug3>)
  Phase 2 canonical:  +<n> papers
  Phase 3 deep:       +<n> papers (seed: <slug>, chain: <slug> → <slug> → ...)
  Phase 4 orbit:      +<n> papers (seed: <slug>)
  Phase 5 digest:     experiences/research-cycle/cycle-<N>-<topic>-<date>/cycle-digest.md
  Wiki: <before> → <after> papers
  Carry-over for cycle <N+1>: <n> candidates queued

Top surprise this cycle:
  <pull from cycle-digest "Surprising findings">

Next-cycle recommendation:
  <pull from cycle-digest "Recommended next-cycle move">
```

## State schema (state.json)

```json
{
  "cycle_num": 3,
  "topic": "AI agent memory architecture and retrieval",
  "topic_slug": "ai-agent-memory-architecture-and-retrieval",
  "max_papers_per_mode": 10,
  "modes_planned": ["broad", "canonical", "deep", "orbit"],
  "lens": "memory-architect",
  "started_at": "<ISO-8601>",
  "completed_at": null,
  "status": "running",
  "seeds": ["latimer-2025-hindsight-memory", "rasmussen-2025-zep-temporal-kg"],
  "phase1": {
    "mode": "broad",
    "status": "completed",
    "digested": ["...", "..."],
    "skipped": [{"reason": "below_threshold", "key": "...", "score": 0.25}]
  },
  "phase2": {"mode": "canonical", "status": "skipped", "reason": "wiki_too_small"},
  "phase3": {
    "mode": "deep",
    "status": "completed",
    "seed": "latimer-2025-hindsight-memory",
    "chain": ["...", "...", "..."]
  },
  "phase4": {
    "mode": "orbit",
    "status": "completed",
    "seed": "adler-2026-storage-not-memory",
    "digested": ["...", "..."]
  },
  "phase5_meta_digest_path": "experiences/research-cycle/cycle-3-ai-agent-memory-architecture-and-retrieval-2026-05-20/cycle-digest.md",
  "papers_added_this_cycle": 27,
  "carry_over_for_next_cycle": [
    {"title": "...", "score": 0.82, "from_phase": "broad", "source_url": "https://..."}
  ]
}
```

## Critical Rules

- **NEVER dispatch a `/citation-walk` sub-agent.** The orchestrator runs `/citation-walk` methodology inline using `scripts/research-cycle-helpers.py`. This is the load-bearing architectural rule — see "Architectural rule" section above. Violating it causes the entire cycle to silently collapse to ~7× slower nested-inline execution.
- **`/digest-paper` is ALWAYS dispatched at level 1** (directly by orchestrator). Never as a level-2 sub-sub-agent. This guarantees fresh context per paper, all 8 inner analyses complete, figures always extract.
- **Parallel dispatch within a phase.** Phases 1, 2, 4 each fire N parallel `/digest-paper` sub-agents in a single message. Wall-clock for the phase ≈ slowest single digest, NOT N × slowest. This is why the new architecture is ~7× faster.
- **One topic per cycle, one cycle per invocation.** Don't try to multiplex topics — each gets its own cycle dir + meta-digest chain.
- **Phases run sequentially.** Phase 2 can't start until phase 1 finishes (it scans the wiki including phase-1's additions). Phase 5 needs all four prior phases done.
- **Phase 5 reads ALL prior cycle meta-digests on this topic, in order.** This is what makes the knowledge compound. Do not skip this read.
- **Skip phases gracefully.** If canonical has < 3 qualifying candidates, log "skipped: insufficient signal" and move on. Don't fail the cycle.
- **Auto-pick seeds never reuse a seed** across phases of the same cycle OR across cycles. Track prior seeds in `state.prior_seeds[phase]` (read across all prior cycle state.jsons).
- **Reconcile INDEX after every phase.** `python3 scripts/research-cycle-helpers.py reconcile-index` is idempotent — catches any sub-agent that skipped its INDEX append under context pressure (rare with fresh-context architecture but still possible).
- **Run `qmd update + qmd embed` ONLY at cycle end** (Step 8). Sub-agents skip these to avoid concurrent corruption — orchestrator does one consolidated reindex.

## Loop compatibility

Designed to be wrapped:

```bash
# Self-paced — model decides when previous cycle finished + next is ready
/loop /research-cycle "AI agent memory architecture" --max-papers-per-mode=10

# Time-paced — every 90 min, even if previous didn't finish (overlap is fine, cycles are independent)
/loop 90m /research-cycle "AI agent memory architecture" --max-papers-per-mode=10
```

Self-paced is the right default. The model checks if there's a running cycle (state.status == "running" in the newest dir); if so, waits for it; if not, fires the next.

## Verify

After a cycle completes:
- [ ] `experiences/research-cycle/cycle-<N>-<topic>-<date>/state.json` has `status: "completed"`
- [ ] `experiences/research-cycle/cycle-<N>-<topic>-<date>/cycle-digest.md` exists
- [ ] All slugs in `state.papers_added_this_cycle` correspond to real digest files
- [ ] Cycle-digest's frontmatter `prior_cycles_referenced` matches the actual prior cycle nums
- [ ] `qmd search "<topic-fragment>"` returns this cycle's digests + meta-digest
- [ ] Centrality auto-pick didn't reuse a seed from a prior cycle (cross-check `state.prior_seeds` aggregation)

## Wrapping with /loop — recipe for overnight

```
1. Decide budget: --max-papers-per-mode=10 gives ~30-40 papers/cycle, 6-10 cycles/night.
2. Pick topic: should be specific enough that relevance scoring works
   (e.g. "AI agent memory architecture" not "AI").
3. Fire:
   /loop /research-cycle "<topic>" --max-papers-per-mode=10
4. Close laptop. Come back in 8 hours.
5. Read the most recent cycle-digest first — it summarizes everything that's evolved
   across all cycles. Then drill into individual paper digests as needed.
```

The newest cycle-digest is always the single document that tells you the running state of your understanding on that topic. Read it; everything else is supporting material.
