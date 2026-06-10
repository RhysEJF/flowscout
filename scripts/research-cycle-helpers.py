#!/usr/bin/env python3
"""
research-cycle-helpers.py — bookkeeping helpers for /research-cycle orchestrator.

The orchestrator (top-level Claude session) calls these from Bash to do all the
bookkeeping (centrality, dedup, frontier mgmt, INDEX reconciliation) BETWEEN
parallel /digest-paper dispatches. By keeping this logic in Python rather than
inside a sub-agent, the orchestrator can dispatch /digest-paper directly at
top-level — which means each paper gets its own fresh 200K-token sub-agent
context, instead of N papers sharing one sub-agent's context.

Corpus scoping:
  Every subcommand accepts --corpus=<slug> (or the FLOWSCOUT_CORPUS env var) and
  operates on memory/knowledge-sources/papers/<corpus>/. Resolution order:
  --corpus= > FLOWSCOUT_CORPUS > sole existing corpus > legacy flat root.
  Reads that pick seeds/canonicals/centrality are corpus-scoped (research topics
  must not bleed into each other); dedup (wiki-keys) is deliberately global.

Subcommands:
  list-corpora                 — list corpus subdirs (+ legacy-root flag) as JSON
  centrality                   — print top-N hub papers in the wiki by (inbound + 0.1*outbound)
  dedup-keys SLUG              — print all multi-keys for a digest (for dedup checks)
  wiki-keys                    — print all dedup-keys for every wiki paper (one per line)
  read-citations SLUG          — print frontmatter.citations[] of a digest as JSON
  canonical-tally MIN_COUNT    — tally citations across wiki, surface count>=MIN_COUNT
  reconcile-index              — append INDEX rows for any digest missing from INDEX.md
  fetch-arxiv-batch IDS...     — batch-fetch abstracts from arxiv API
  resolve-arxiv-url ID         — canonical arxiv PDF URL for an ID
  init-cycle TOPIC             — create new cycle dir + state.json (auto cycle_num)
  topic-relevant-count TOPIC   — qmd vsearch count above 0.5 (for Phase 0 detection)
  pick-deep-seed               — most-cross-referenced unused digest (for Phase 3)
  pick-orbit-seed              — digest with longest key_takeaway not yet used as orbit seed

All output goes to stdout as JSON or plain lines depending on subcommand;
errors to stderr; exits non-zero on failure.
"""
import json
import os
import re
import subprocess
import sys
import urllib.request
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import datetime, timezone
from glob import glob

try:
    import yaml
except ImportError:
    sys.exit(
        "research-cycle-helpers.py requires PyYAML to parse digest frontmatter.\n"
        "Install it with:  pip3 install pyyaml"
    )

PAPERS = "memory/knowledge-sources/papers"
RESEARCH_CYCLE = "experiences/research-cycle"

# Set by __main__ via _resolve_corpus(). None means legacy flat layout
# (digests directly in PAPERS root, pre-corpus installs).
CORPUS = None


def _list_corpora():
    """Corpus slugs = subdirectories of PAPERS that contain an INDEX.md."""
    if not os.path.isdir(PAPERS):
        return []
    return sorted(
        d for d in os.listdir(PAPERS)
        if os.path.isdir(os.path.join(PAPERS, d))
        and d != "figures"
        and os.path.exists(os.path.join(PAPERS, d, "INDEX.md"))
    )


def _root_has_legacy_digests():
    """True if digests sit directly in the PAPERS root (pre-corpus flat layout)."""
    if not os.path.isdir(PAPERS):
        return False
    return any(
        fn.endswith(".md") and not fn.endswith("-notes.md")
        and fn not in ("INDEX.md", "corpora.md")
        for fn in os.listdir(PAPERS)
    )


def _resolve_corpus(explicit):
    """--corpus= beats FLOWSCOUT_CORPUS beats sole-corpus beats legacy root."""
    corpora = _list_corpora()
    corpus = explicit or os.environ.get("FLOWSCOUT_CORPUS")
    if corpus:
        if corpus not in corpora:
            sys.exit(f"unknown corpus: {corpus!r} — available: {', '.join(corpora) or 'none'}")
        return corpus
    if len(corpora) == 1:
        return corpora[0]
    if not corpora and _root_has_legacy_digests():
        print("note: flat pre-corpus layout detected — operating on the papers root. "
              "See README 'Multiple corpora' to migrate.", file=sys.stderr)
        return None
    sys.exit(
        "--corpus=<slug> required (or set FLOWSCOUT_CORPUS). "
        f"Available: {', '.join(corpora) or 'none — run /digest-paper with --corpus=<slug> to start one'}"
    )


def corpus_dir():
    return os.path.join(PAPERS, CORPUS) if CORPUS else PAPERS


def cycle_root():
    return os.path.join(RESEARCH_CYCLE, CORPUS) if CORPUS else RESEARCH_CYCLE


def _normalize_title(t):
    return re.sub(r'[^a-z0-9]+', ' ', (t or '').lower()).strip()[:60]


def make_keys(c):
    """Multi-key dedup: returns all possible identity keys for a citation/digest dict."""
    keys = set()
    if c.get('arxiv_id'):
        keys.add(f"arxiv:{c['arxiv_id']}")
    if c.get('doi'):
        keys.add(f"doi:{c['doi']}")
    title = c.get('title') or ''
    if title:
        nt = _normalize_title(title)
        keys.add(f"title-only:{nt}")
        authors = c.get('authors') or ['unknown']
        first_author = (authors[0] if authors else 'unknown')
        fa_last = first_author.split(',')[0].split(' ')[-1].lower()
        keys.add(f"t:{nt}|{fa_last}|{c.get('year') or 'na'}")
    return keys


def _digest_path(slug):
    """Find a digest by slug — current corpus first, then root, then all corpora.
    Slugs are globally unique across corpora, so first hit wins."""
    candidates = [os.path.join(corpus_dir(), f"{slug}.md"),
                  os.path.join(PAPERS, f"{slug}.md")]
    candidates += sorted(glob(os.path.join(PAPERS, "*", f"{slug}.md")))
    for p in candidates:
        if os.path.exists(p):
            return p
    return None


def _load_digest(slug):
    """Load a digest's frontmatter dict. Returns None if file missing or unparseable."""
    path = _digest_path(slug)
    if not path:
        return None
    try:
        with open(path) as f:
            content = f.read()
        if '---' not in content:
            return None
        return yaml.safe_load(content.split('---')[1]) or None
    except Exception:
        return None


def _iter_digests(root=None):
    """Yield (slug, frontmatter_dict) for every digest in one directory.
    Defaults to the active corpus — keeps seed-picking, centrality, and
    canonical tallies from bleeding across research topics."""
    root = root or corpus_dir()
    if not os.path.isdir(root):
        return
    for fn in sorted(os.listdir(root)):
        if not fn.endswith('.md') or fn.endswith('-notes.md') \
                or fn in ('INDEX.md', 'corpora.md'):
            continue
        slug = fn[:-3]
        fm = _load_digest_at(os.path.join(root, fn))
        if fm:
            yield slug, fm


def _load_digest_at(path):
    """Frontmatter dict for an exact file path (no slug search)."""
    try:
        with open(path) as f:
            content = f.read()
        if '---' not in content:
            return None
        return yaml.safe_load(content.split('---')[1]) or None
    except Exception:
        return None


def _iter_all_digests():
    """Yield (slug, frontmatter) across the root AND every corpus.
    Used for dedup — a paper digested in any corpus should never be
    re-digested, whichever corpus is active."""
    roots = [PAPERS] + [os.path.join(PAPERS, c) for c in _list_corpora()]
    for root in roots:
        yield from _iter_digests(root)


def cmd_centrality(args):
    """Print top-N hub papers by (inbound related_digests count) + (0.1 * outbound citations)."""
    n = int(args[0]) if args else 10
    exclude = set(args[1:]) if len(args) > 1 else set()
    inbound = defaultdict(int)
    outbound = defaultdict(int)
    for slug, fm in _iter_digests():
        outbound[slug] = len(fm.get('citations') or [])
        for r in (fm.get('related_digests') or []):
            if isinstance(r, str):
                inbound[r] += 1
    centrality = {
        s: inbound[s] + outbound[s] * 0.1
        for s in set(list(inbound.keys()) + list(outbound.keys()))
        if s not in exclude
    }
    top = sorted(centrality.items(), key=lambda x: -x[1])[:n]
    print(json.dumps([
        {"slug": s, "centrality": round(c, 2),
         "inbound": inbound[s], "outbound": outbound[s]}
        for s, c in top
    ], indent=2))


def cmd_wiki_keys(args):
    """Print all multi-keys for all wiki digests (one key per line). For dedup checks.
    Deliberately global across every corpus — never re-digest a known paper."""
    seen = set()
    for slug, fm in _iter_all_digests():
        for k in make_keys({
            'arxiv_id': fm.get('arxiv_id'), 'doi': fm.get('doi'),
            'title': fm.get('title'), 'authors': fm.get('authors') or [],
            'year': fm.get('year')
        }):
            if k not in seen:
                seen.add(k)
                print(k)


def cmd_read_citations(args):
    """Print frontmatter.citations[] of a digest as JSON."""
    if not args:
        sys.exit("usage: read-citations SLUG")
    fm = _load_digest(args[0])
    if not fm:
        sys.exit(f"digest not found: {args[0]}")
    print(json.dumps(fm.get('citations') or [], indent=2))


def cmd_dedup_keys(args):
    """Print all multi-keys for a single digest. For verifying dedup logic."""
    if not args:
        sys.exit("usage: dedup-keys SLUG")
    fm = _load_digest(args[0])
    if not fm:
        sys.exit(f"digest not found: {args[0]}")
    keys = make_keys({
        'arxiv_id': fm.get('arxiv_id'), 'doi': fm.get('doi'),
        'title': fm.get('title'), 'authors': fm.get('authors') or [],
        'year': fm.get('year')
    })
    print(json.dumps(sorted(keys), indent=2))


def cmd_canonical_tally(args):
    """
    Tally citations across all wiki digests, surface candidates cited by ≥ MIN_COUNT
    distinct digests but NOT already in the wiki. Print top N as JSON.
    """
    min_count = int(args[0]) if args else 3
    top_n = int(args[1]) if len(args) > 1 else 20

    # Already-digested check is global (any corpus); the tally itself is
    # corpus-scoped so a young corpus isn't drowned out by a mature one.
    digested_keys = set()
    for slug, fm in _iter_all_digests():
        digested_keys |= make_keys({
            'arxiv_id': fm.get('arxiv_id'), 'doi': fm.get('doi'),
            'title': fm.get('title'), 'authors': fm.get('authors') or [],
            'year': fm.get('year')
        })

    tally = defaultdict(lambda: {"count": 0, "cited_by": [], "best_meta": None})
    for slug, fm in _iter_digests():
        for cit in (fm.get('citations') or []):
            keys = make_keys(cit)
            if keys & digested_keys:
                continue
            # Pick a stable primary key for tally aggregation
            if cit.get('arxiv_id'):
                pk = f"arxiv:{cit['arxiv_id']}"
            elif cit.get('doi'):
                pk = f"doi:{cit['doi']}"
            else:
                pk = f"title-only:{_normalize_title(cit.get('title',''))}"
            tally[pk]["count"] += 1
            tally[pk]["cited_by"].append(slug)
            prev = tally[pk]["best_meta"]
            if prev is None or (cit.get('arxiv_id') and not prev.get('arxiv_id')):
                tally[pk]["best_meta"] = cit

    qualified = [
        {"primary_key": k, **v}
        for k, v in tally.items()
        if v["count"] >= min_count
    ]
    qualified.sort(key=lambda x: -x["count"])
    print(json.dumps(qualified[:top_n], indent=2))


def cmd_reconcile_index(args):
    """Append INDEX rows for any digest missing from the corpus INDEX.md. Idempotent."""
    INDEX_PATH = os.path.join(corpus_dir(), "INDEX.md")
    with open(INDEX_PATH) as f:
        idx = f.read()
    indexed = set(re.findall(r'\]\(([\w\-]+)\.md\)', idx))
    digest_slugs = set(s for s, _ in _iter_digests())
    missing = sorted(digest_slugs - indexed)
    if not missing:
        print(json.dumps({"reconciled": 0, "missing": []}))
        return
    for slug in missing:
        fm = _load_digest(slug)
        if not fm:
            continue
        author = (fm.get('authors') or ['?'])[0].split(',')[0]
        title = fm.get('title', slug)
        year = fm.get('year', '?')
        lens = fm.get('lens', 'generic')
        kt = (fm.get('key_takeaway') or '').replace('|', '\\|')
        date = fm.get('digested_date', '2026-05-19')
        row = (f"| {date} | [{title}]({slug}.md) | {author} et al. | "
               f"{year} | `{lens}` | {kt} |")
        idx = re.sub(r'(\|---\|---\|---\|---\|---\|---\|\n)',
                     r'\1' + row + '\n', idx, count=1)
    with open(INDEX_PATH, "w") as f:
        f.write(idx)
    print(json.dumps({"reconciled": len(missing), "missing": missing}))


def cmd_fetch_arxiv_batch(args):
    """Batch-fetch abstracts from arxiv API for a list of arxiv IDs."""
    if not args:
        sys.exit("usage: fetch-arxiv-batch ID1 ID2 ...")
    ids = args
    url = (f"http://export.arxiv.org/api/query?id_list={','.join(ids)}"
           f"&max_results={len(ids)}")
    req = urllib.request.Request(url, headers={"User-Agent": "research-cycle/1.0"})
    out = {}
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            xml_data = resp.read().decode()
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        for entry in ET.fromstring(xml_data).findall('atom:entry', ns):
            m = re.search(r'arxiv\.org/abs/([\d.v]+)',
                          entry.find('atom:id', ns).text)
            if m:
                aid = m.group(1).split('v')[0]
                summary = re.sub(r'\s+', ' ',
                                 entry.find('atom:summary', ns).text.strip())
                out[aid] = summary
    except Exception as e:
        sys.exit(f"arxiv fetch failed: {e}")
    print(json.dumps(out, indent=2))


def cmd_resolve_arxiv_url(args):
    """Canonical arxiv PDF URL for an ID."""
    if not args:
        sys.exit("usage: resolve-arxiv-url ID")
    aid = args[0]
    print(f"https://arxiv.org/pdf/{aid}.pdf")


def cmd_init_cycle(args):
    """Create a new cycle dir + initial state.json. Auto-detects cycle_num."""
    if not args:
        sys.exit("usage: init-cycle TOPIC [--max=N] [--lens=L]")
    topic = args[0]
    max_papers = 10
    lens = "generic"
    for a in args[1:]:
        if a.startswith("--max="):
            max_papers = int(a.split("=", 1)[1])
        elif a.startswith("--lens="):
            lens = a.split("=", 1)[1]
    topic_slug = re.sub(r'[^a-z0-9]+', '-', topic.lower()).strip('-')[:60]
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    existing = glob(f"{cycle_root()}/cycle-*-{topic_slug}-*")
    cycle_num = 1
    for d in existing:
        m = re.search(r'cycle-(\d+)-', d)
        if m:
            cycle_num = max(cycle_num, int(m.group(1)) + 1)
    run_dir = f"{cycle_root()}/cycle-{cycle_num}-{topic_slug}-{date}"
    os.makedirs(run_dir, exist_ok=True)
    state = {
        "cycle_num": cycle_num,
        "corpus": CORPUS,
        "topic": topic,
        "topic_slug": topic_slug,
        "max_papers_per_mode": max_papers,
        "modes_planned": ["broad", "canonical", "deep", "orbit"],
        "lens": lens,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": None,
        "status": "running",
        "phase0": {"status": "pending"},
        "phase1": {"mode": "broad", "status": "pending"},
        "phase2": {"mode": "canonical", "status": "pending"},
        "phase3": {"mode": "deep", "status": "pending"},
        "phase4": {"mode": "orbit", "status": "pending"},
        "phase5": {"status": "pending"},
    }
    with open(f"{run_dir}/state.json", "w") as f:
        json.dump(state, f, indent=2)
    print(json.dumps({"run_dir": run_dir, "cycle_num": cycle_num}, indent=2))


def cmd_topic_relevant_count(args):
    """qmd vsearch count above 0.5 (for Phase 0 cold-start detection)."""
    if not args:
        sys.exit("usage: topic-relevant-count TOPIC")
    topic = args[0]
    try:
        result = subprocess.run(
            ["./vendor/qmd/bin/qmd", "vsearch", topic, "--json", "-n", "30"],
            capture_output=True, text=True, timeout=30
        )
        hits = json.loads(result.stdout) if result.stdout.strip() else []
    except Exception:
        hits = []
    relevant = [
        h for h in hits
        if h.get('file', '').startswith(corpus_dir() + '/')
        and h.get('file', '').endswith('.md')
        and not h.get('file', '').endswith('-notes.md')
        and 'INDEX.md' not in h.get('file', '')
        and h.get('score', 0) >= 0.5
    ]
    print(json.dumps({"count": len(relevant), "top": relevant[:5]}, indent=2))


def cmd_pick_deep_seed(args):
    """Most-cross-referenced wiki digest not yet used as a deep seed."""
    exclude = set(args)
    inbound = defaultdict(int)
    for slug, fm in _iter_digests():
        for r in (fm.get('related_digests') or []):
            if isinstance(r, str):
                inbound[r] += 1
    candidates = [
        (s, c) for s, c in sorted(inbound.items(), key=lambda x: -x[1])
        if s not in exclude
    ]
    if not candidates:
        sys.exit("no candidates")
    print(json.dumps({"slug": candidates[0][0], "inbound": candidates[0][1]}, indent=2))


def cmd_pick_orbit_seed(args):
    """Digest with the longest key_takeaway not yet used as an orbit seed."""
    exclude = set(args)
    best = None
    best_len = 0
    for slug, fm in _iter_digests():
        if slug in exclude:
            continue
        kt = fm.get('key_takeaway') or ''
        if len(kt) > best_len:
            best_len = len(kt)
            best = slug
    if not best:
        sys.exit("no candidates")
    print(json.dumps({"slug": best, "takeaway_length": best_len}, indent=2))


def cmd_list_corpora(args):
    """List corpora (subdirs of the papers root with an INDEX.md) as JSON."""
    print(json.dumps({
        "corpora": _list_corpora(),
        "legacy_root_digests": _root_has_legacy_digests(),
    }, indent=2))


COMMANDS = {
    "centrality": cmd_centrality,
    "list-corpora": cmd_list_corpora,
    "dedup-keys": cmd_dedup_keys,
    "wiki-keys": cmd_wiki_keys,
    "read-citations": cmd_read_citations,
    "canonical-tally": cmd_canonical_tally,
    "reconcile-index": cmd_reconcile_index,
    "fetch-arxiv-batch": cmd_fetch_arxiv_batch,
    "resolve-arxiv-url": cmd_resolve_arxiv_url,
    "init-cycle": cmd_init_cycle,
    "topic-relevant-count": cmd_topic_relevant_count,
    "pick-deep-seed": cmd_pick_deep_seed,
    "pick-orbit-seed": cmd_pick_orbit_seed,
}


if __name__ == "__main__":
    _explicit_corpus = None
    _argv = []
    for _a in sys.argv[1:]:
        if _a.startswith("--corpus="):
            _explicit_corpus = _a.split("=", 1)[1]
        else:
            _argv.append(_a)
    if not _argv or _argv[0] not in COMMANDS:
        print(__doc__, file=sys.stderr)
        print(f"\nKnown commands: {sorted(COMMANDS.keys())}", file=sys.stderr)
        sys.exit(2)
    if _argv[0] != "list-corpora":
        CORPUS = _resolve_corpus(_explicit_corpus)
    COMMANDS[_argv[0]](_argv[1:])
