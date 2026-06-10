#!/usr/bin/env bash
# FlowScout installer
# Usage: from the root of your Claude Code project, run:
#   curl -sSL https://raw.githubusercontent.com/RhysEJF/flowscout/main/install.sh | bash
# Or:
#   ./install.sh [--force]

set -euo pipefail

FORCE=false
if [[ "${1:-}" == "--force" ]]; then
  FORCE=true
fi

# Step 0: verify we're in a Claude Code project
if [[ ! -d ".claude" && ! -f "CLAUDE.md" ]]; then
  echo "Error: this does not look like a Claude Code project."
  echo "Run install.sh from the root of your second brain (the directory containing .claude/ or CLAUDE.md)."
  exit 1
fi

echo "Installing FlowScout into $(pwd)"
echo ""

# Step 1: create directories
mkdir -p .claude/commands
mkdir -p skills
mkdir -p scripts
mkdir -p memory/knowledge-sources/papers
mkdir -p experiences/citation-walk
mkdir -p experiences/theses
mkdir -p experiences/research-cycle
mkdir -p experiences/flow-frontier
mkdir -p experiences/verify-thesis

# Step 2: fetch FlowScout to a temp directory
TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT

echo "Fetching FlowScout..."
git clone --depth 1 --quiet https://github.com/RhysEJF/flowscout.git "$TMPDIR/flowscout"

# Step 3: install commands
echo ""
echo "Installing slash commands..."
for cmd in digest-paper citation-walk research-cycle flow-frontier verify-thesis; do
  src="$TMPDIR/flowscout/commands/$cmd.md"
  dst=".claude/commands/$cmd.md"
  if [[ -f "$dst" && "$FORCE" != true ]]; then
    echo "  - /$cmd already exists (use --force to overwrite)"
  else
    cp "$src" "$dst"
    echo "  + /$cmd"
  fi
done

# Step 4: install skills
echo ""
echo "Installing skills..."
for skill in digest-paper citation-walk research-cycle flow-frontier verify-thesis; do
  src="$TMPDIR/flowscout/skills/$skill"
  dst="skills/$skill"
  if [[ -d "$dst" && "$FORCE" != true ]]; then
    echo "  - skills/$skill already exists (use --force to overwrite)"
  else
    rm -rf "$dst"
    cp -R "$src" "$dst"
    echo "  + skills/$skill"
  fi
done

# Step 5: install helper scripts
echo ""
echo "Installing helper scripts..."
for script in with-lock.py papers-server.py research-cycle-helpers.py; do
  src="$TMPDIR/flowscout/scripts/$script"
  dst="scripts/$script"
  if [[ -f "$dst" && "$FORCE" != true ]]; then
    echo "  - scripts/$script already exists (use --force to overwrite)"
  else
    cp "$src" "$dst"
    chmod +x "$dst"
    echo "  + scripts/$script"
  fi
done

# Step 6: prerequisites check
echo ""
echo "Checking prerequisites..."
if ! command -v python3 >/dev/null 2>&1; then
  echo "  ! python3 not found. The helper scripts (locking, viewer server, /research-cycle bookkeeping) need it."
else
  echo "  + python3 found"
  if python3 -c "import yaml" >/dev/null 2>&1; then
    echo "  + PyYAML installed"
  else
    echo "  ! PyYAML not installed. /research-cycle needs it: pip3 install pyyaml"
  fi
fi

if [[ -z "${EXA_API_KEY:-}" ]]; then
  echo "  ! EXA_API_KEY not set. /citation-walk --orbit and /verify-thesis will be limited."
  echo "    Get a key at https://exa.ai then: export EXA_API_KEY=..."
else
  echo "  + EXA_API_KEY set"
fi

if [[ -x "./vendor/qmd/bin/qmd" ]]; then
  echo "  + QMD detected at ./vendor/qmd/bin/qmd"
else
  echo "  ! QMD not detected. --canonical mode will fall back to grep (still works, less precise)."
fi

# Done
echo ""
echo "FlowScout installed."
echo ""
echo "Try it:"
echo "  /digest-paper https://arxiv.org/abs/2109.02157"
echo ""
echo "Docs: https://github.com/RhysEJF/flowscout"
