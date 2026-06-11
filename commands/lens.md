---
name: lens
description: Create, list, and inspect reading lenses (the reading-persona a paper is digested through). A lens defines who you are when you read a paper and what kind of takeaways matter — decoupled from any specific paper, so you can register one before you have a URL in hand.
---

# /lens — Reading-lens manager

The user invoked `/lens [new ["description"] | show <slug> | <no args>]`.

A **lens** is a reading persona: a ~150-word, second-person brief ("you are reading this paper as…") that steers every `/digest-paper` analysis toward the takeaways that matter to a particular reader. Lenses are global — one lens can be reused across any corpus — and live as plain markdown at `skills/digest-paper/lenses/<slug>.md`. The `generic` lens is the default; `memory-architect` is an example of a domain-specific one.

Pick the subcommand from the arguments:

## `/lens` (no args) — list

List every lens. Read each file in `skills/digest-paper/lenses/`, and for each show:

```
<slug>    <first ~12 words of the lens, as a one-line gist>
```

Then remind the user: `/lens new` to make one, or `/digest-paper <url> --lens=<slug>` to use one.

## `/lens show <slug>` — inspect

Print the full text of `skills/digest-paper/lenses/<slug>.md`. If it doesn't exist, say so and list the available lenses.

## `/lens new ["description"]` — create (no paper required)

This is the whole point of the standalone command: define a reading persona from a description alone.

1. **Get the description.**
   - If the user passed one inline (`/lens new "I build synthetic-user-testing products and care about when simulated users predict real behaviour"`), use it.
   - Otherwise ask: *"What's the lens? In 1–2 sentences: who are you when you read a paper in this field, and what kind of takeaways matter to you?"*

2. **Propose two things and show them:**
   - A **slug** auto-derived from the description (kebab-case, e.g. `synthetic-user-builder`). Keep it short and field-evocative.
   - A **~150-word lens text** expanding their sentence into the house format — declarative, second-person, opening with "You are reading this paper as…". Match the tone and shape of `skills/digest-paper/lenses/generic.md`: name the reader, state what they care about (evidence quality, methods, specific failure modes, the concrete questions they bring), and end with the two guardrails every lens carries — *prefer concrete facts/numbers/quotes over abstraction*, and *don't invent connections to fields the paper doesn't address; if something is unclear or under-evidenced, say so.*

3. **Ask the user to approve / edit / rename.** Iterate until they're happy.

4. **On approval, write** the lens text to `skills/digest-paper/lenses/<slug>.md` (only the lens prose — no frontmatter; that's the file format).

5. **Confirm** the path and show how to use it:
   - `/digest-paper <url> --lens=<slug>`
   - `/citation-walk <seed> --topic="…" --lens=<slug> --corpus=<corpus>`
   - `/research-cycle "<topic>" --lens=<slug> --corpus=<corpus>`

   Tip: a new field usually wants both a new lens *and* a new corpus — pair `--lens=<slug>` with `--corpus=<slug>` on the first run.

## Notes

- If the user asks to revise an existing lens, treat it as `/lens new` targeting that slug: read the current text, propose edits, overwrite on approval.
- Lenses are not corpus-scoped on disk. If you want a strict one-lens-per-corpus discipline, just name the lens after the corpus.
- `/digest-paper --new-lens` runs this same create flow inline and then immediately digests the paper — use it when you happen to already have a URL.
