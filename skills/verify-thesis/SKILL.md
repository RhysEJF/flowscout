---
name: verify-thesis
description: Layer 2 of the Flow Frontier research engine. Takes an open thesis from `experiences/theses/`, generates adversarial search queries to test the claim, runs Exa + WebSearch (+ arxiv), scores each candidate source as supports/contradicts/qualifies/irrelevant, synthesises a verdict (resolved-yes / resolved-no / partially-resolved / open), drafts an experiment design if the thesis remains open, and writes verdict + evidence + experiment back into the thesis file. Supports batch mode (`--all-open`) for unattended sweeps over the entire open backlog. Sits between `/flow-frontier` (Layer 1: synthesise theses) and `/experiment` (Layer 3: run experiments). Trigger when user says `/verify-thesis <slug>`, `/verify-thesis --all-open`, or asks to "verify a thesis", "check what the literature says about X", "see if anyone has tested Y".
---

# /verify-thesis — Falsifiable-claim verifier

> Layer 2 of the Flow Frontier research engine. Architecture plan: `experiences/plans/flow-frontier-architecture.md`.

## When to Use

- User says `/verify-thesis <slug>` — single-thesis verification
- User says `/verify-thesis --all-open` — sweep every open thesis in the backlog
- User says `/verify-thesis --status=<status>` — sweep theses with a specific status (e.g., `stale-pending-review` after a refresh)
- User asks: "verify a thesis" / "test this claim against the literature" / "is this resolved or still open?"
- After running `/flow-frontier` and producing a thesis backlog, when the user wants to triage which are already-resolved vs genuinely open

## Arguments

| Flag | Meaning |
|---|---|
| `<slug>` (positional) | Slug of a thesis in `experiences/theses/`. Mutually exclusive with `--all-open` / `--status`. |
| `--all-open` | Process every thesis where `status: open` or `status: partially-resolved`. Skips already-verified theses. |
| `--status=<value>` | Process every thesis matching this status. Useful for `--status=stale-pending-review` after a refresh. |
| `--max-batch=N` | When in batch mode, cap how many theses to process per run. Default 5. Prevents accidental $50 runs. |
| `--max-sources=N` | Max candidate sources to gather per thesis (Exa + WebSearch combined). Default 12. |
| `--gen-queries=N` | How many adversarial search queries to generate per thesis. Default 4. |
| `--no-experiment` | Skip the experiment-design draft even for theses that remain `open` or `partially-resolved`. Faster + cheaper. |
| `--force` | Re-verify even already-verified theses (overwrites previous verdict). |
| `--dry-run` | Show which theses would be processed + estimated cost; do not call agents or write. |

## Mutually exclusive modes

Exactly one of: positional `<slug>`, `--all-open`, `--status=<value>`. If none given, list open theses and ask the user to pick.

## Methodology

### Step 1 — Parse args + initialize state

1. Validate exclusivity (slug OR --all-open OR --status).
2. Resolve the thesis set:
   - Single slug: read `experiences/theses/<slug>.md` — error if missing.
   - `--all-open`: scan `experiences/theses/*.md` for `kind: thesis` AND `status: open|partially-resolved`. Skip `-notes.md` files.
   - `--status=X`: same scan, match `status: X`.
3. Apply `--max-batch` cap (default 5). If thesis set exceeds it, take the N with the earliest `generated_date` (oldest first — likely most ready for verification).
4. Create run dir: `experiences/verify-thesis/<run-id>/` where `<run-id>` is `<slug>-<YYYY-MM-DD>` for single mode, `batch-<YYYY-MM-DD>-<count>` for batch.
5. Initialize `state.json` with the resolved thesis list + flags.
6. Open `log.md` for human-readable progress.
7. If `--dry-run`: print the thesis list + estimated cost (~$0.50–1.50/thesis), exit cleanly.

### Step 2 — For each thesis in the batch (parallel up to 3)

For each thesis, dispatch ONE Agent call that runs the per-thesis pipeline (Steps 3–6 below) end-to-end and returns a structured result. The orchestrator can run up to 3 theses in parallel (more is risky — each thesis spawns its own sub-agents internally, and >9 concurrent network calls hits rate limits).

The per-thesis Agent gets:
- The thesis file path
- All five sub-step prompts (queries, score, synthesise, experiment)
- Instructions to write its outputs to a sub-dir under the run dir

### Step 3 — Generate adversarial search queries (per thesis)

The sub-agent reads the thesis (claim, falsification design, supporting papers) and generates `--gen-queries` (default 4) search queries designed to **falsify, qualify, or confirm** the claim.

Query templates (the agent picks the appropriate one per query):

- **Direct support**: "research papers that argue {paraphrase of claim}"
- **Direct counter**: "research papers that show {opposite of claim}"
- **Conditional qualifier**: "studies on {topic} under conditions where {claim} might break"
- **Mechanism probe**: "papers testing whether {specific mechanism named in falsification design} is load-bearing"

Each query is reframed in Exa "describe the ideal page" form, e.g., "arxiv research paper demonstrating that..."

Output: JSON array of `{query, intent: support|counter|qualifier|mechanism, rationale}` written to `experiences/verify-thesis/<run-id>/<slug>/queries.json`.

Prompt: `skills/verify-thesis/prompts/generate_queries.md`.

### Step 4 — Run searches (per thesis)

For each query, run in parallel:
1. `mcp__exa__web_search_exa` with `numResults=4`
2. `WebSearch` (general fallback for non-arxiv content)
3. Optional arxiv API direct fetch if the query has an obvious arxiv-id

Aggregate. Dedupe by URL. Cap at `--max-sources` (default 12) total candidates per thesis, ranked by Exa score where available.

Output: `experiences/verify-thesis/<run-id>/<slug>/candidates.json` — list of `{title, url, snippet, score, source_engine}`.

### Step 5 — Score each candidate source (per thesis)

For each candidate, spawn a small sub-agent that:
1. Reads the thesis claim + falsification design
2. Reads the candidate's snippet (and optionally fetches the full page if snippet is too short)
3. Decides: `supports` / `contradicts` / `qualifies` / `irrelevant`
4. Extracts one specific quote that justifies the decision
5. Notes any regime/condition info that limits applicability (e.g., "only at scale >1M tokens")

For batch efficiency, the scoring can be done by ONE sub-agent processing all candidates in a single chain-of-thought pass rather than N parallel sub-agents — candidates are small.

Output: `experiences/verify-thesis/<run-id>/<slug>/scored.json` — list of `{url, title, label, quote, conditions, confidence}`.

Prompt: `skills/verify-thesis/prompts/score_source.md`.

### Step 6 — Synthesise verdict (per thesis)

One sub-agent reads:
- The thesis claim + falsification design + supporting papers
- All scored candidates from Step 5

It produces:
1. **Verdict**: one of `resolved-yes` / `resolved-no` / `partially-resolved` / `open`
   - `resolved-yes` requires ≥2 strong supporting sources AND no strong contradictions
   - `resolved-no` requires ≥2 strong contradicting sources AND no equally-strong supports
   - `partially-resolved` when the literature settles the claim in *some* regimes but not others
   - `open` when the search came back empty, weak, or evenly split
2. **One-paragraph rationale** explaining the verdict
3. **`verdict_evidence` list** — top 3-6 sources, each tagged supports/contradicts/qualifies with the quote from Step 5
4. **`contradicting_papers` list** — slugs from the wiki that contradict (if any), plus URLs of external contradicting sources
5. If `--no-experiment` is NOT set AND verdict is `open` or `partially-resolved`: an **experiment design** based on the thesis's existing "How to falsify" section, sharpened with the conditional gaps the search revealed.

Output: `experiences/verify-thesis/<run-id>/<slug>/verdict.json` + an updated copy of the thesis frontmatter ready to write back.

Prompt: `skills/verify-thesis/prompts/synthesize_verdict.md`.

### Step 7 — Write verdict back into the thesis file

Read the original `experiences/theses/<slug>.md`. Update:

- **Frontmatter**:
  - `status`: new verdict value
  - `verified_date`: ISO timestamp
  - `verdict`: one-sentence summary
  - `verdict_evidence`: structured list from Step 6
  - `contradicting_papers`: list of slugs/URLs

- **Body**:
  - Replace `## Contradicting papers` placeholder with the actual list (with quotes)
  - Replace `## Verification notes` placeholder with the rationale paragraph + evidence summary
  - If experiment was drafted, append a `## Experiment design` section

Do NOT modify the original claim, falsification design, or supporting-papers sections. Those are immutable historical record.

### Step 8 — Update INDEX.md + manifest

For each verified thesis:
1. Update `experiences/theses/INDEX.md`: replace the status chip in the thesis's row (🟢 open → 🔵 verified / 🔴 falsified / 🟡 partial / 🟢 still open).
2. No manifest changes needed — verification doesn't alter cluster membership.

### Step 9 — Refresh QMD

```bash
python3 scripts/with-lock.py /tmp/qmd-update.lock --timeout 120 -- ./vendor/qmd/bin/qmd update
python3 scripts/with-lock.py /tmp/qmd-embed.lock --timeout 300 -- ./vendor/qmd/bin/qmd embed
```

### Step 10 — Report to user

```
/verify-thesis complete (<duration>s)
  Theses processed: K / requested N
  Verdicts:
    🔵 resolved-yes:  X    e.g., <slug> — <one-line verdict>
    🔴 resolved-no:   Y
    🟡 partial:       Z
    🟢 still open:    W   (experiment design drafted: ...)
  Skipped (over batch cap): Q
  Cost: ~$<estimate>
  Wall-clock: <Ns>

  Read: open experiences/theses/<slug>.md, or http://localhost:8000/viewer.html#<slug>
```

## File schema additions

The thesis file's frontmatter gains these populated fields after verification:

```yaml
status: resolved-yes | resolved-no | partially-resolved | open
verified_date: "<ISO>"
verdict: "<one-sentence summary of the verdict>"
verdict_evidence:
  - source: "https://arxiv.org/abs/..."
    title: "..."
    label: supports | contradicts | qualifies
    quote: "<exact passage from the source>"
    conditions: "<regime/scope qualifier or null>"
    confidence: high | medium | low
contradicting_papers:
  - slug-in-wiki  # if it's a paper already digested
  - "https://..."  # if external
```

And the body gains:

- `## Contradicting papers` (was placeholder) — now populated with quotes
- `## Verification notes` (was placeholder) — rationale paragraph + summary
- `## Experiment design` (new section, only if status is `open` or `partially-resolved` and `--no-experiment` not set)

## Critical Rules

- **Never modify the original claim / falsification / supporting-papers sections.** Those are historical record. Only fill the placeholder sections + frontmatter.
- **Batch mode default is 5.** Prevents accidental $25-50 runs. User can `--max-batch=20` for full sweeps with explicit intent.
- **Resolved-yes requires ≥2 strong supporting sources AND no strong contradictions.** Single-source confirmations get downgraded to `open` with a "promising but unconfirmed" verdict.
- **Resolved-no requires ≥2 strong contradictions AND no equally-strong supports.** Conservative — don't kill a thesis on weak evidence.
- **Experiment design is mandatory for `open` verdicts** unless `--no-experiment` is passed. Open without experiment design is half-finished.
- **Status downgrade rule**: a thesis with `status: resolved-yes` should NOT be auto-re-verified by `--all-open`. Use `--force` to override.
- **Always run `qmd update` + `qmd embed` at the end** — the updated theses need to re-index for `verified` chips to show in viewer searches.

## Verify

After running, confirm:
- [ ] `experiences/verify-thesis/<run-id>/state.json` has `status: "completed"`
- [ ] Every processed thesis has updated `status` + `verified_date` frontmatter
- [ ] Every processed thesis has populated `## Contradicting papers` and `## Verification notes` body sections (not the placeholder text)
- [ ] `experiences/theses/INDEX.md` rows show the new status chips
- [ ] `qmd search "<thesis-title-fragment>"` returns the updated digest

## Forward compatibility

- **v2 — `--rebut` mode**: for a `resolved-no` verdict, draft a "the field thought X but Y" Cognitive Shift post from the falsification evidence. Saves the user time when killing a thesis cleanly is useful as content.
- **v2 — `--depth=N` recursive verification**: when a verdict cites a paper not yet in the wiki, optionally fire `/digest-paper` on it then re-verify with the new digest as a supporting source.
- **Layer 3: `/experiment`**: consumes thesis files with `status: open` and a non-empty `## Experiment design` section. Hands the design to whatever infrastructure fits (Karpathy autoresearch for ML training experiments, Flow outcome for manual experiments, etc.).
