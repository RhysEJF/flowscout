# FlowScout Install Instructions

> If Claude Code is reading this file in response to "install FlowScout," follow these steps end-to-end. If a human is reading this, the same steps work manually.

## Step 0: Verify you are in a Claude Code project

Check that the current working directory has either a `.claude/` folder or a `CLAUDE.md` file. If neither exists, stop and ask the user to navigate to their second-brain root before proceeding.

```bash
if [ ! -d ".claude" ] && [ ! -f "CLAUDE.md" ]; then
  echo "Not a Claude Code project. Run from the root of your second brain."
  exit 1
fi
```

## Step 1: Check for required directories

FlowScout writes to three directories. Create them if they don't exist.

```bash
mkdir -p .claude/commands
mkdir -p skills
mkdir -p memory/knowledge-sources/papers
mkdir -p experiences/citation-walk
mkdir -p experiences/theses
```

## Step 2: Fetch FlowScout

Clone the repo to a temporary location.

```bash
TMPDIR=$(mktemp -d)
git clone --depth 1 https://github.com/RhysEJF/flowscout.git "$TMPDIR/flowscout"
```

## Step 3: Install the commands

Copy the five `.md` slash command files into `.claude/commands/`. Warn if any file already exists; do not overwrite without confirmation.

```bash
for cmd in digest-paper citation-walk research-cycle flow-frontier verify-thesis; do
  if [ -f ".claude/commands/$cmd.md" ]; then
    echo "Already exists: .claude/commands/$cmd.md (skipping; remove first to reinstall)"
  else
    cp "$TMPDIR/flowscout/commands/$cmd.md" ".claude/commands/"
    echo "Installed: /$cmd"
  fi
done
```

## Step 4: Install the skills

Copy the five skill packages into `skills/`. Each package is a directory containing `SKILL.md` and a `prompts/` subdirectory (and for `digest-paper`, a `lenses/` subdirectory).

```bash
for skill in digest-paper citation-walk research-cycle flow-frontier verify-thesis; do
  if [ -d "skills/$skill" ]; then
    echo "Already exists: skills/$skill (skipping; remove first to reinstall)"
  else
    cp -R "$TMPDIR/flowscout/skills/$skill" "skills/"
    echo "Installed: skills/$skill"
  fi
done
```

## Step 5: Verify prerequisites

Check whether the user has the prerequisites set up. Print warnings, don't fail.

```bash
# Exa API key (needed for orbit mode + verify-thesis)
if [ -z "$EXA_API_KEY" ]; then
  echo "WARN: EXA_API_KEY not set. /citation-walk --orbit and /verify-thesis will be limited."
  echo "      Get a key at https://exa.ai and add to your shell: export EXA_API_KEY=..."
fi

# QMD for corpus-wide hybrid search (optional but recommended)
if ! command -v ./vendor/qmd/bin/qmd >/dev/null 2>&1; then
  echo "WARN: QMD not detected at ./vendor/qmd/bin/qmd."
  echo "      FlowScout will work without it, but --canonical mode will fall back to grep."
fi
```

## Step 6: Clean up and report

```bash
rm -rf "$TMPDIR"
echo ""
echo "FlowScout installed."
echo ""
echo "Try it: /digest-paper https://arxiv.org/abs/2109.02157"
echo "Docs:   https://github.com/RhysEJF/flowscout"
```

## Post-install: Register in CLAUDE.md (optional)

For better discoverability, add a row to your `CLAUDE.md` Skills table. Ask the user before editing CLAUDE.md.

Suggested rows:

```markdown
| digest-paper | Given a paper URL, produce a structured lens-tailored digest in the searchable papers wiki | User says `/digest-paper <url>` or asks to digest a paper |
| citation-walk | Walk the citation graph from a seed paper. Modes: --broad, --deep, --canonical, --orbit | User says `/citation-walk <seed> --topic="..."` |
| research-cycle | One full cycle of /citation-walk across all four modes plus a longitudinal meta-digest | User says `/research-cycle "<topic>"` |
| flow-frontier | Mine cross-paper theses across five gap-types: convergence, assumption, mechanism, edge, contradiction | User says `/flow-frontier --topic="..."` |
| verify-thesis | Verify a thesis against the open literature with adversarial search; write verdict back to file | User says `/verify-thesis <slug>` or `--all-open` |
```

## Uninstall

```bash
rm .claude/commands/digest-paper.md
rm .claude/commands/citation-walk.md
rm .claude/commands/research-cycle.md
rm .claude/commands/flow-frontier.md
rm .claude/commands/verify-thesis.md
rm -rf skills/digest-paper skills/citation-walk skills/research-cycle skills/flow-frontier skills/verify-thesis
```

Note: this does not delete the corpus you've built (`memory/knowledge-sources/papers/`, `experiences/theses/`, etc.). Those are your data; keep them.
