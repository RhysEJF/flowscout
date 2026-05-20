You are writing the meta-digest for a citation-walk run. The user just had `/citation-walk` traverse the citation graph from a seed paper (or canonically across their wiki) and digest a cluster of N related papers. Your job is to synthesize what was learned across the cluster — patterns, threads, gaps — into a single readable document that helps the user navigate the cluster they just built.

## Run metadata

- **Mode:** {{MODE}} (broad | deep | canonical)
- **Topic:** {{TOPIC}}
- **Seed:** {{SEED}}
- **Papers digested this run:** {{DIGESTED_SLUGS}}
- **Skipped (with reasons):** {{SKIPPED}}

## Source material

Read each digest at `memory/knowledge-sources/papers/<slug>.md` for every slug in the digested list above. Use the Read tool. Look at TLDR, Key Takeaway, Implications, and What Experts Overlook sections — the headline findings, not the full method.

If `{{MODE}}` is `canonical`, ALSO read each of the pre-existing digests in the wiki that cited these papers — those tell you why these foundational works keep coming up.

## Output structure (markdown)

Write to `experiences/citation-walk/<run-dir>/meta-digest.md`. Use this exact structure:

```markdown
---
kind: cluster-meta-digest
run_dir: <run-dir>
seed: <seed-url-or-slug>
topic: "<topic>"
mode: <broad|deep|canonical>
papers_digested: <N>
created: <YYYY-MM-DD>
---

# Meta-digest — "{{TOPIC}}" cluster ({{MODE}} walk, {{N}} papers)

## In one paragraph

<3-5 sentence overview: what is this cluster about, what's the dominant narrative, what's the field's current state, who's leading. Plain English, no jargon-stuffing. Should land for someone who hasn't read any of the papers.>

## Timeline

<Chronological bullet list of papers in the cluster, oldest first. Each line:
- `**YYYY** — [[slug]] — One-sentence what-it-did/what-it-found.`
Aim for cluster narrative: how the thinking evolved year by year.>

## Consensus / canonical works

<Papers cited by multiple others in the cluster, OR papers that subsequent work clearly builds on. For each: which slug it is, and one sentence on what makes it foundational. If `{{MODE}}` is `canonical`, this section will be most of the document. If `--broad` or `--deep`, this might be 2-4 entries.>

## Thematic threads

<2-5 themes that emerged across the cluster. For each:
- **Theme name**: One paragraph describing the thread. Which papers contribute to it. What's the dominant view, what's contested.>

## Open questions / gaps

<3-5 things the cluster collectively DOESN'T resolve. These are the most useful insights for someone trying to do new work in this field — they point at research opportunities or product gaps. Be specific (not "more research is needed").>

## Recommended reading order

<If someone new to this topic wanted to read the cluster, what order would maximize understanding? 5-8 papers in a sequence. Each:
- `1. [[slug]] — Why this first / what it sets up.`
Order by pedagogical clarity, not chronology.>

## Surprising findings

<2-3 things that surprised you when reading across the cluster — counterintuitive results, contradictions between papers, methods that beat expectations. The kind of insight worth sharing in a single tweet or meeting comment. Be specific about which paper showed what.>

## What's NOT in this cluster

<One paragraph honestly noting what the walk didn't cover. E.g., "This walk stayed close to <topic-A> and didn't surface much on the adjacent <topic-B> literature" or "Only English-language papers / only ML papers / only post-2020 work." Helps the user decide whether to run another walk with a different seed.>
```

## Quality rules

- **Use `[[slug]]` wiki-link syntax** for every paper reference — the viewer.html and QMD both understand them.
- **Be specific over generic.** Don't write "this cluster covers various aspects of X" — write "this cluster shows that X benchmarks peaked in 2024 with the Y method, but no one has solved Z."
- **Don't invent connections that aren't in the digests.** If two papers seem related but neither cites the other and the digests don't draw the parallel, don't make one up. The synthesis should be grounded in what's actually in the source material.
- **Surprising findings should genuinely surprise.** Not "researchers used X technique to achieve Y%" (that's restatement). More like "the 2019 paper that everyone cites for foundational X actually didn't claim X — it was the 2021 follow-up that did, and the citation chain got corrupted."
- **Keep total length 800-1500 words.** Long enough to be useful, short enough to scan.
