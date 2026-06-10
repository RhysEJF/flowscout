---
name: digest-paper
description: Given a URL to a scientific paper (arxiv/PDF/HTML), produce a structured, lens-tailored digest as a markdown file in the searchable papers wiki. Fan-out parallel analysis across 8 dimensions (TLDR, key takeaway, implications, method, best figure, extracted prompts, what experts overlook, citations), validates with a hallucination check, auto-links to related digests, and refreshes QMD search index. Trigger when user says `/digest-paper <url>`, asks to "digest this paper", "summarize this paper", or "add this paper to my wiki".
---

# /digest-paper — Scientific paper digester + searchable wiki

> Turns a paper URL into a structured, lens-tailored markdown digest that compounds into a Karpathy-style searchable wiki.

## When to Use

- User says `/digest-paper <url>` (with optional `--lens=<slug>`, `--new-lens`, or `--lens` alone for list mode)
- User pastes a paper URL and asks for a digest / summary / wiki entry
- User asks "what's interesting about this paper" with a URL

## Arguments

| Flag | Meaning |
|---|---|
| `<url>` (required) | arxiv.org / openreview / direct .pdf / any web page hosting the paper |
| `--corpus=<slug>` | Which research corpus this digest belongs to (see Step 0) |
| `--lens=<slug>` | Use an existing lens file at `skills/digest-paper/lenses/<slug>.md` |
| `--lens` (no value) | List all available lenses and ask user to pick |
| `--new-lens` | Interview user to define a new lens, save it, then use it |
| (no lens flag) | Default to `generic` lens |

## Methodology

### Step 0 — Resolve the corpus

A **corpus** is one body of research — a subdirectory `memory/knowledge-sources/papers/<corpus>/` with its own `INDEX.md`, figures, and viewer. Corpora keep unrelated research topics from mixing: seed-picking, canonical tallies, and browsing are all corpus-scoped, while paper dedup stays global.

Resolution order (same rule across all FlowScout commands):

1. `--corpus=<slug>` explicit flag
2. `FLOWSCOUT_CORPUS` environment variable
3. Exactly one corpus exists (one subdir with an `INDEX.md`) → use it silently
4. Otherwise → list the corpora from `memory/knowledge-sources/papers/corpora.md` and ask the user which to use (or whether to start a new one)

`python3 scripts/research-cycle-helpers.py list-corpora` prints the available corpora as JSON.

**If the resolved corpus is new** (its directory doesn't exist yet): create `memory/knowledge-sources/papers/<corpus>/` with an empty-table `INDEX.md`, and append a row to the registry `memory/knowledge-sources/papers/corpora.md` (`| <slug> | <one-line description — ask the user if not obvious> | <YYYY-MM-DD> |`). Create `corpora.md` with a header + table if it doesn't exist.

**Legacy flat layout** (digests directly in the papers root, no corpus subdirs): keep operating on the root and suggest the user migrate — see the README's "Multiple corpora" section.

Every path below written as `papers/<corpus>/...` means `memory/knowledge-sources/papers/<corpus>/...`.

### Step 1 — Resolve the lens

Determine which lens content to inject into the prompt templates as `{{LENS}}`.

```
if --new-lens:
    Ask user: "What's the lens? Describe in 1-2 sentences: who are you when
              reading this paper, and what kind of takeaways matter?"
    Take their answer, propose:
      - A slug (auto-derived from the description, e.g. "venture-builder")
      - A ~150-word full lens text (expand their sentence to match the
        format of lenses/generic.md — declarative, second-person "you are
        reading this paper as...")
    Show both, ask user to approve / edit / rename.
    On approval, write to skills/digest-paper/lenses/<slug>.md.
    Use the new content as {{LENS}}.

elif --lens with no value:
    List files in skills/digest-paper/lenses/. Show user as a numbered menu.
    Ask which to use. Load the chosen file as {{LENS}}.

elif --lens=<slug>:
    Read skills/digest-paper/lenses/<slug>.md as {{LENS}}.
    If the file doesn't exist, tell user, list available, and offer --new-lens.

else (no flag):
    Read skills/digest-paper/lenses/generic.md as {{LENS}}.
```

### Step 2 — Fetch the paper

Route based on URL pattern:

```
if URL matches arxiv.org/abs/<id> OR arxiv.org/pdf/<id>:
    Normalize to https://arxiv.org/pdf/<id>.pdf
    curl -L -o /tmp/digest-paper/<slug>/paper.pdf "<url>"

elif URL ends in .pdf OR is openreview.net/pdf?id=...:
    curl -L -o /tmp/digest-paper/<slug>/paper.pdf "<url>"

else:
    Use Exa MCP (mcp__exa__web_fetch_exa) to fetch full page content.
    Save extracted text to /tmp/digest-paper/<slug>/paper.txt
```

Where `<slug>` is initially `tmp-<8-char-hash-of-url>` (will be renamed to the proper paper slug after `paper_details` runs in Step 3).

If `paper.pdf` was downloaded, convert to plain text for subagent consumption:
- If `pdftotext` is available on the system, run `pdftotext -layout paper.pdf paper.txt`
- Otherwise, use the Read tool on the PDF (iterating with the `pages` parameter for documents longer than 10 pages) and concatenate the extracted text into `paper.txt`

After this step, the canonical file for subagents is `/tmp/digest-paper/<slug>/paper.txt`.

### Step 3 — Fan-out parallel analysis (8 sub-agents in ONE message)

Send a single message with 8 parallel `Agent` tool calls. Each subagent gets a prompt built from a template + substitutions:

```
For each template_name in [
    paper_details, tldr, cool_story_graph, implications,
    method, key_takeaway, prompts_extracted, what_experts_overlook
]:
    template = read skills/digest-paper/prompts/<template_name>.md
    prompt = template
        .replace("{{LENS}}", lens_content)
        .replace("{{CONTENT}}",
            "The paper text is in the file at <absolute_path>/paper.txt.\n"
            "Read it in full before answering. Use the Read tool with the\n"
            "`offset` and `limit` parameters if the file is very long."
        )
    Launch Agent(
        subagent_type="general-purpose",
        description="<template_name> analysis",
        prompt=prompt
    )
```

All 8 calls in **the same message** so they run truly in parallel. Wait for all to complete before proceeding.

**When invoked as a level-1 sub-agent** (the standard case for orchestrated runs from `/research-cycle` or top-level `/citation-walk`): the Agent tool is unavailable to you (sub-agents cannot dispatch their own Agent calls). Perform the 8 analyses **inline** by reading the paper text once and analyzing each section sequentially in your own context. Use the same prompt templates from `skills/digest-paper/prompts/`. This is the EXPECTED path under the 2-level architecture — your fresh 200K-token context for one paper has plenty of budget for all 8 sequential analyses + figure extraction. Do NOT skip any of the 8 analyses, do NOT skip figure extraction (Step 5.5). Process them serially; ~5-8 min wall-clock per paper.

**Crucially**: this only works because you are at LEVEL 1 (orchestrator → you = level 1). If you find yourself at level 2 (orchestrator → /citation-walk → you), the call stack is wrong — the orchestrator should be running /citation-walk methodology inline and dispatching you at level 1 instead. Report the wrong nesting to the orchestrator if you can detect it.

The parallel-Agent path (8 analyses fired in parallel as sub-sub-agents) is only available when this skill runs at level 0 (user invokes `/digest-paper <url>` directly). Almost always you'll be running inline at level 1 — that's fine and expected.

### Step 4 — Determine the paper slug + rename temp dir

Parse `paper_details` output. Construct the canonical paper slug:

```
slug = "<first-author-lastname>-<year>-<2-3-word-title-summary>"
       all lowercase, kebab-case, ASCII only
       e.g. "castricato-2024-persona-testbed"
            "salganik-2006-music-market"
```

Rename `/tmp/digest-paper/tmp-<hash>/` → `/tmp/digest-paper/<slug>/` so subsequent steps are easier to trace.

### Step 5 — Extract citations (sequential sub-agent)

Run one more Agent call with the `citations.md` template. This is sequential (not in the parallel batch) because:
- Its output is structured JSON, not narrative — different handling
- Often the longest/heaviest analysis, so isolating it avoids dragging out the parallel batch

Parse the returned JSON. Validate it's a well-formed array. If parsing fails, retry once with an explicit "Return only valid JSON, no other text" instruction. If it still fails, store `citations: []` and add a note in the digest body that citation extraction failed.

### Step 5.5 — Extract the best figure as a cropped image

Two passes: render the page as a high-resolution PNG, then visually crop to just the figure + caption region (not the surrounding body text).

**Pass A — render the page**

Parse the `Figure Page: <N>` line from the `cool_story_graph` output (this field is mandatory in the prompt template — if missing, fall back by greping the paper text for the figure caption and counting form-feed (`\f`) characters to estimate the page).

If the paper was fetched as a PDF (`/tmp/digest-paper/<slug>/paper.pdf` exists), render the page to a temp PNG:

```bash
pdftoppm -f <N> -l <N> -r 150 -png \
    /tmp/digest-paper/<slug>/paper.pdf \
    /tmp/digest-paper/<slug>/page
# Produces /tmp/digest-paper/<slug>/page-<N>.png
```

**Pass B — vision-driven crop to the figure region**

The main orchestrator session uses the `Read` tool on the temp PNG (Claude can read PNGs natively). Visually identify the bounding box of the figure block — the figure panels AND its caption — and choose pixel coordinates `(left, top, right, bottom)` that:

- Include all panels of the figure (single or multi-panel)
- Include the figure caption ("Figure N: ..." text underneath)
- Include the panel-description blocks ("(a) ...", "(b) ...") if present
- Exclude page header/footer, page number, surrounding body text, neighboring figures
- Leave ~10-20px padding on each side for visual breathing room

Then crop using Python PIL (standard with Python 3 distros):

```bash
mkdir -p memory/knowledge-sources/papers/<corpus>/figures
python3 <<EOF
from PIL import Image
src = "/tmp/digest-paper/<slug>/page-<N>.png"
dst = "memory/knowledge-sources/papers/<corpus>/figures/<slug>-fig.png"
crop = Image.open(src).crop((left, top, right, bottom))
crop.save(dst)
EOF
```

After saving, the orchestrator should `Read` the cropped image to verify the figure is fully captured (caption not cut off, panels not clipped). If the crop is wrong, retry with adjusted coordinates — don't ship a bad image.

Then in Step 6, embed the cropped image at the top of the `## Best Figure` section as:

```markdown
![Figure <num> — <title> (page <N>)](figures/<slug>-fig.png)
```

**Fallback paths:**

- If the paper was HTML-fetched (no PDF), skip both passes. Add a note in the Best Figure section: `_(figure not extracted — paper was fetched as HTML, no source PDF available)_`.
- If `pdftoppm` is not installed, log a warning and skip. Install: `brew install poppler` on macOS, `apt install poppler-utils` on Linux.
- If Python PIL is missing (unusual — it ships with most Python 3 distros), save the full page as the figure rather than failing — a less-tight image is better than no image. Install: `pip3 install --break-system-packages Pillow`.

### Step 6 — Compose the draft digest

Assemble a single markdown file with the structure below (see "Paper frontmatter schema" further down for the full frontmatter spec):

```markdown
---
[frontmatter — see schema below]
---

# {{paper_title}}

**Authors:** {{authors}}
**Published:** {{publication_date}} · [Source]({{source_url}})
**Lens:** `{{lens_slug}}` · **Digested:** {{digested_date}}

## TLDR

{{tldr_output}}

## Key Takeaway

{{key_takeaway_output}}

## Implications

{{implications_output}}

## How to Apply It (method)

{{method_output}}

## Best Figure

![Figure {{fig_num}} — {{fig_title}} (page {{fig_page}})](figures/{{slug}}-fig.png)

{{cool_story_graph_output}}

## What Experts Overlook

{{what_experts_overlook_output}}

## Extracted Prompts

{{prompts_extracted_output}}

## Citations

{{citations_summary — first 10 entries as bullets, rest in frontmatter as JSON}}

## Related Digests

[populated in Step 8]

## Reviewer Notes

[populated in Step 7]
```

Write this draft to `memory/knowledge-sources/papers/<corpus>/<slug>.md`.

**Also create an empty notes sidecar** at `memory/knowledge-sources/papers/<corpus>/<slug>-notes.md` so the viewer's annotation backend has somewhere to write. Content:

```markdown
---
kind: paper-notes
digest: <slug>
title: "Notes — <paper title>"
---

# Notes — <paper title>

Notes and highlights on [[<slug>]].

_No notes yet. Highlight text in the digest to add one._
```

The bundled `scripts/papers-server.py` server appends/removes note blocks in this file as the user annotates in the viewer. QMD indexes it like any other markdown file, and session-memory extractors (like Flow OS's `/learn`) skip it on the `kind: paper-notes` discriminator.

### Step 7 — Hallucination check (sequential)

Run one Agent call with the `hallucination_check.md` template. The `{{CONTENT}}` substitution points to the paper text file as before; the `{{DIGEST}}` placeholder is replaced with the **full text of the draft digest written in Step 6** (read it back via Read tool, or pass the file path with an instruction to Read it).

Take the reviewer's output and write it into the digest's `## Reviewer Notes` section, replacing the placeholder. If the overall severity is `Urgent rewrite needed`, surface this to the user as a warning at the end — they may want to manually edit before relying on the digest.

### Step 8 — Cross-paper linking

Find related digests already in the wiki using QMD:

```bash
# Build a query from the new paper's topics + tags
QUERY="<comma-separated topics> <comma-separated tags>"

./vendor/qmd/bin/qmd query "$QUERY" --json -n 10 \
    | jq '[.[] | select(.file | startswith("memory/knowledge-sources/papers/<corpus>/"))
                | select(.file != "memory/knowledge-sources/papers/<corpus>/<slug>.md")
                | {file, score}]'
```

Related-digest links are corpus-scoped (the `startswith` filter above) — papers in other corpora are different research threads, so don't cross-link them even when QMD scores them as similar.

Take the top 3-5 hits (score > 0.5). For each:
1. Read the related file's frontmatter to extract its `slug` and `title`
2. Add to the new digest's frontmatter `related_digests:` list
3. Append a `## Related Digests` body section with `[[slug]]` wiki-links and one-line titles, e.g.:

```markdown
## Related Digests

- [[castricato-2024-persona-testbed]] — PERSONA: A reproducible testbed for synthetic persona evaluation
- [[salganik-2006-music-market]] — Experimental study of inequality and unpredictability in an artificial cultural market
```

### Step 9 — Update INDEX.md

Append a new row to `memory/knowledge-sources/papers/<corpus>/INDEX.md`'s table, **serialized with a file lock** so concurrent sub-agent runs don't race and lose rows. Read the file inside the lock, edit, write back. The lockfile is per-corpus (`/tmp/papers-index-<corpus>.lock`) so parallel runs on different corpora don't serialize against each other.

Row format:
```
| {{digested_date}} | [{{paper_title}}]({{slug}}.md) | {{first_author}} et al. | {{year}} | `{{lens_slug}}` | {{key_takeaway_first_sentence}} |
```

Wrap the read-modify-write in `scripts/with-lock.py`. The simplest pattern is a one-shot Python snippet executed under the lock:

```bash
python3 scripts/with-lock.py /tmp/papers-index-<corpus>.lock --timeout 60 -- \
  python3 -c '
import re
path = "memory/knowledge-sources/papers/<corpus>/INDEX.md"
new_row = "| <date> | [<title>](<slug>.md) | <author> et al. | <year> | `<lens>` | <takeaway> |"
with open(path) as f: content = f.read()
# Insert new row right after the table separator line `|---|---|...`
content = re.sub(r"(\\|---\\|---\\|---\\|---\\|---\\|---\\|\\n)", r"\\1" + new_row + "\\n", content, count=1)
with open(path, "w") as f: f.write(content)
'
```

Why the lock matters: in `/citation-walk` runs, 5–15 sub-agents may call `/digest-paper` concurrently. Without the lock, two appends can interleave and one row gets lost (we observed this on the first real broad-walk — Lewis 2020 row was dropped). The lock serializes the read-modify-write so each append sees the prior one.

### Step 10 — Update viewer.html (only if first run, or if it doesn't exist)

If `memory/knowledge-sources/papers/<corpus>/viewer.html` exists, do nothing — it auto-reads INDEX.md and the individual markdown files at view time. If it doesn't exist (this is the first paper digested into this corpus), copy the template from `skills/digest-paper/viewer-template.html` (created on skill install) to that path. Each corpus gets its own viewer page; the viewer's relative fetches resolve within the corpus directory.

### Step 11 — Refresh QMD index

Both steps must be serialized with a file lock, because concurrent `qmd embed` invocations corrupt each other's index writes (observed on the first real broad-walk — 5+ sub-agents called embed simultaneously and several reported crashes).

```bash
python3 scripts/with-lock.py /tmp/qmd-update.lock --timeout 120 -- \
  ./vendor/qmd/bin/qmd update          # BM25 / keyword reindex (fast, ~1-2s per new file)

python3 scripts/with-lock.py /tmp/qmd-embed.lock --timeout 300 -- \
  ./vendor/qmd/bin/qmd embed           # Vector embeddings (slower, but needed for semantic search)
```

**If you are running inside an orchestrator** (e.g., this `/digest-paper` is being called by `/citation-walk` as one of N parallel sub-agents): **skip the `qmd embed` step entirely**. The orchestrator will run a single `qmd embed` after all sub-agents return, which is faster and avoids contention. Still run `qmd update` (it's cheap and the lock handles concurrency fine).

You can tell you're inside an orchestrator if your prompt instructions came from another skill or if the prompt mentions other concurrent agents. When in doubt, run both (the lock prevents crashes either way).

### Step 12 — Report to user

Tell the user:
- File written: `memory/knowledge-sources/papers/<corpus>/<slug>.md`
- Reviewer severity (if not Clean, call it out)
- Number of related digests linked
- Number of citations extracted (this is the auto-research hook — future `/auto-research` skill will walk these)
- How to browse: run `python3 scripts/papers-server.py` and open `http://localhost:8000/<corpus>/viewer.html` (enables the annotation + theses features; an Obsidian vault pointed at the papers root also renders everything natively)
- Suggest next actions: `/digest-paper <next-url>` to grow the wiki, or `qmd query "..."` to search across all digested papers

## Paper frontmatter schema

Every digest file at `memory/knowledge-sources/papers/<corpus>/<slug>.md` MUST have this frontmatter. Field order matters for readability — keep it consistent:

```yaml
---
kind: paper-digest                     # marks this as NOT a v2 session memory
corpus: <corpus>                       # which research corpus this belongs to
slug: <slug>                           # e.g. castricato-2024-persona-testbed
title: "<full paper title>"
authors:                               # array of strings, "First Last" format
  - "Castricato, L."
  - "..."
year: 2024                             # integer
publication_date: "2024-07"            # string, YYYY-MM if known else YYYY
venue: "arXiv preprint"                # journal/conf/preprint
source_url: "https://arxiv.org/abs/2407.17387"
doi: null                              # or "10.xxxx/xxxxx"
arxiv_id: "2407.17387"                 # or null
lens: synthetic-personas               # slug of lens used
digested_date: "2026-05-19"            # ISO date this digest was generated
key_takeaway: "<first sentence of key_takeaway section>"   # for the INDEX
topics:                                # array of free-form topic slugs (used by QMD)
  - synthetic-personas
  - llm-evaluation
  - market-research
tags:                                  # array of free-form tags (used by QMD)
  - paper
  - ai-personas
  - benchmark
entities:                              # array of slugs for QMD entity linking
  - castricato-louis                   # author slugs in firstname-lastname form
related_digests:                       # auto-populated from QMD in Step 8
  - other-paper-slug
citations:                             # full JSON array from citations subagent
  - title: "..."
    authors: ["..."]
    year: 2023
    doi: "..."
    url: "..."
    arxiv_id: null
hallucination_severity: "Clean"        # or "Minor fact tweak" / "Urgent rewrite needed"
best_figure:                           # extracted in Step 5.5; null if no PDF or pdftoppm missing
  number: 3
  title: "Cost-accuracy and oracle-ceiling analysis on LoCoMo"
  page: 10
  image_path: "figures/<slug>-fig.png"
---
```

**Why this schema** (and why it's not the v2 memory schema):
- `kind: paper-digest` distinguishes these files from extracted session memories — session-memory extractors (like Flow OS's `/learn`) check for this and skip them
- `topics`, `tags`, `entities` use the same field names as v2 so QMD's existing tag/entity search works across both
- Wiki-link `[[slug]]` references in body activate QMD's WikiWord cross-referencing

## Critical Rules

- **Run all 8 main analyses in parallel** (single message, 8 Agent calls). Sequential chaining was a legacy workaround for old context limits and is dramatically slower with no quality benefit on modern models.
- **Never invent connections to fields the paper doesn't address.** If the lens asks for "implications for X" and the paper genuinely has none, say so — don't manufacture takeaways.
- **The hallucination check runs AFTER the digest is drafted** and edits it in place. Don't skip it — it's the only thing standing between you and shipping a wrong fact into your wiki.
- **The `kind: paper-digest` frontmatter field is load-bearing.** It prevents session-memory extractors (like Flow OS's `/learn`) from trying to re-extract these as session memories.
- **Always run `qmd update` + `qmd embed` at the end.** Without it, the new digest is invisible to next session's search.
- **One paper per run.** Don't batch multiple URLs in one invocation — each gets its own slug, frontmatter, and QMD pass.
- **Figure extraction requires `pdftoppm`** (from poppler-utils). If unavailable, the digest still ships — just without an embedded figure image. Don't fail the run over a missing figure.
- **Dedup is global, writes are corpus-scoped.** Before digesting, check `python3 scripts/research-cycle-helpers.py wiki-keys` (all corpora). If the paper already exists in ANOTHER corpus, don't re-digest — add a pointer row to this corpus's INDEX.md (`| <date> | [<title>](../<other-corpus>/<slug>.md) | ... | (in <other-corpus>) |`) and tell the user.

## Verify

After running the skill, confirm:
- [ ] `memory/knowledge-sources/papers/<corpus>/<slug>.md` exists with full frontmatter (including `corpus:`)
- [ ] `memory/knowledge-sources/papers/<corpus>/INDEX.md` has a new row for it
- [ ] `memory/knowledge-sources/papers/corpora.md` lists the corpus
- [ ] `./vendor/qmd/bin/qmd search "<paper-title-fragment>"` returns the new file
- [ ] If `related_digests` is non-empty, the body contains `[[slug]]` wiki-links
- [ ] If `hallucination_severity != "Clean"`, the `## Reviewer Notes` section is populated
- [ ] If the paper was a PDF, `memory/knowledge-sources/papers/<corpus>/figures/<slug>-fig.png` exists and the digest body references it with a markdown image tag

## Auto-research hook (forward compatibility)

The `citations[]` array in frontmatter is the structured hook for a future `/auto-research <topic>` skill. That skill will:
1. Start from a seed digest (or a user-supplied URL)
2. Walk the seed's `citations[]` via Exa to find PDFs
3. Call `/digest-paper` recursively on each
4. After N hops or M papers, synthesize a meta-digest of the cluster

By keeping citations as structured JSON (not free-form prose), the loop can iterate cleanly without re-parsing.
