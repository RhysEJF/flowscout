#!/usr/bin/env python3
"""
Papers wiki server.

Serves the static files in memory/knowledge-sources/papers/ AND a small
notes API that reads/writes sidecar markdown files at <slug>-notes.md.

Notes are stored as structured markdown so they remain Markdown SSOT —
QMD indexes them, Obsidian renders them, /learn can read them.

Endpoints
---------
GET    /                       → viewer.html
GET    /<file>                 → static
GET    /api/notes/<slug>       → JSON list of notes on that digest
POST   /api/notes/<slug>       → append a note; body = JSON {prefix, exact, suffix, note}
DELETE /api/notes/<slug>/<id>  → remove a note

Run
---
    python3 scripts/papers-server.py [--port 8000]

Then open http://localhost:8000/viewer.html
"""

import argparse
import json
import os
import random
import re
import socket
import string
import sys
from datetime import datetime, timezone
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PAPERS_DIR = os.path.join(REPO_ROOT, "memory", "knowledge-sources", "papers")
THESES_DIR = os.path.join(REPO_ROOT, "experiences", "theses")

NOTE_ID_ALPHABET = string.ascii_lowercase + string.digits
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9\-]{1,100}$")
NOTE_ID_RE = re.compile(r"^n_[a-z0-9]{8,16}$")


def new_note_id() -> str:
    return "n_" + "".join(random.choices(NOTE_ID_ALPHABET, k=10))


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# Notes file read/write
# ---------------------------------------------------------------------------

NOTES_HEADER_TMPL = (
    "---\n"
    "kind: paper-notes\n"
    "digest: {slug}\n"
    "title: \"Notes — {title}\"\n"
    "---\n"
    "\n"
    "# Notes — {title}\n"
    "\n"
    "Notes and highlights on [[{slug}]].\n"
    "\n"
)


def notes_path_for(slug: str) -> str:
    if not SLUG_RE.match(slug):
        raise ValueError(f"invalid slug: {slug!r}")
    return os.path.join(PAPERS_DIR, f"{slug}-notes.md")


def digest_title(slug: str) -> str:
    """Best-effort lookup of the paper title from the digest's frontmatter."""
    digest_path = os.path.join(PAPERS_DIR, f"{slug}.md")
    if not os.path.exists(digest_path):
        return slug
    try:
        with open(digest_path, "r", encoding="utf-8") as f:
            head = f.read(4096)
        m = re.search(r"^title:\s*\"?(.+?)\"?\s*$", head, re.MULTILINE)
        if m:
            return m.group(1).strip()
    except OSError:
        pass
    return slug


# A note section in the file looks like:
#
#     ## Note n_xxxxxxx {#n_xxxxxxx}
#
#     ```json
#     {"prefix": "...", "exact": "...", "suffix": "...", "created": "..."}
#     ```
#
#     User's note text in markdown.
#
#     ---
#
# We use this exact shape so the file is human-editable, Obsidian-friendly,
# and trivially parseable here.

NOTE_BLOCK_RE = re.compile(
    r"^##\s+Note\s+(n_[a-z0-9]+)\s*\{#\1\}\s*\n+"
    r"```json\s*\n(\{.*?\})\s*\n```\s*\n+"
    r"(.*?)"
    r"(?=^##\s+Note\s+n_|\Z)",
    re.MULTILINE | re.DOTALL,
)

EMPTY_PLACEHOLDER_RE = re.compile(
    r"\n_No notes yet\. Highlight text in the digest to add one\._\n",
    re.MULTILINE,
)


def read_notes(slug: str) -> list[dict]:
    path = notes_path_for(slug)
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    notes = []
    for m in NOTE_BLOCK_RE.finditer(text):
        nid = m.group(1)
        try:
            meta = json.loads(m.group(2))
        except json.JSONDecodeError:
            continue
        body = m.group(3).strip()
        # Strip trailing "---" separator if present
        body = re.sub(r"\n+---\s*$", "", body).strip()
        notes.append({
            "id": nid,
            "prefix": meta.get("prefix", ""),
            "exact": meta.get("exact", ""),
            "suffix": meta.get("suffix", ""),
            "created": meta.get("created", ""),
            "note": body,
        })
    return notes


def ensure_notes_file(slug: str) -> None:
    """Create the notes file with a stub header if it doesn't exist."""
    path = notes_path_for(slug)
    if os.path.exists(path):
        return
    title = digest_title(slug)
    content = NOTES_HEADER_TMPL.format(slug=slug, title=title)
    content += "_No notes yet. Highlight text in the digest to add one._\n"
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def append_note(slug: str, prefix: str, exact: str, suffix: str, note: str) -> dict:
    ensure_notes_file(slug)
    path = notes_path_for(slug)
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    # Drop the placeholder line if present
    text = EMPTY_PLACEHOLDER_RE.sub("\n", text)
    if not text.endswith("\n"):
        text += "\n"
    nid = new_note_id()
    created = now_iso()
    meta = {
        "prefix": prefix,
        "exact": exact,
        "suffix": suffix,
        "created": created,
    }
    block = (
        f"\n## Note {nid} {{#{nid}}}\n\n"
        f"```json\n{json.dumps(meta, ensure_ascii=False)}\n```\n\n"
        f"{note.strip()}\n\n---\n"
    )
    text += block
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return {
        "id": nid,
        "prefix": prefix,
        "exact": exact,
        "suffix": suffix,
        "created": created,
        "note": note.strip(),
    }


def delete_note(slug: str, nid: str) -> bool:
    if not NOTE_ID_RE.match(nid):
        raise ValueError(f"invalid note id: {nid!r}")
    path = notes_path_for(slug)
    if not os.path.exists(path):
        return False
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    # Pattern that captures the entire block for this nid, including the trailing ---
    block_re = re.compile(
        r"\n##\s+Note\s+" + re.escape(nid) + r"\s*\{#" + re.escape(nid) + r"\}\s*\n"
        r".*?(?:\n---\s*\n|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    new_text, n = block_re.subn("\n", text, count=1)
    if n == 0:
        return False
    # If no notes left, re-add the placeholder
    if not NOTE_BLOCK_RE.search(new_text):
        if not new_text.endswith("\n"):
            new_text += "\n"
        new_text += "_No notes yet. Highlight text in the digest to add one._\n"
    with open(path, "w", encoding="utf-8") as f:
        f.write(new_text)
    return True


# ---------------------------------------------------------------------------
# HTTP handler
# ---------------------------------------------------------------------------


class PapersHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=PAPERS_DIR, **kwargs)

    # Virtual mount: /theses/* serves from experiences/theses/
    def translate_path(self, path):
        # Strip query string + fragment before path-mapping
        if "?" in path:
            path = path.split("?", 1)[0]
        if "#" in path:
            path = path.split("#", 1)[0]
        if path.startswith("/theses/"):
            rel = path[len("/theses/"):]
            # Reject traversal
            if ".." in rel.split("/"):
                return os.path.join(THESES_DIR, "__rejected__")
            return os.path.join(THESES_DIR, rel)
        return super().translate_path(path)

    # Quieter logging — one line per request, no terminal noise
    def log_message(self, fmt, *args):
        sys.stderr.write(f"[{self.log_date_time_string()}] {self.address_string()} {fmt % args}\n")

    # ---- routing ---------------------------------------------------------

    def do_GET(self):  # noqa: N802
        path = urlparse(self.path).path
        m = re.fullmatch(r"/api/notes/([a-z0-9][a-z0-9\-]{1,100})", path)
        if m:
            self._api_list_notes(m.group(1))
            return
        super().do_GET()

    def do_POST(self):  # noqa: N802
        path = urlparse(self.path).path
        m = re.fullmatch(r"/api/notes/([a-z0-9][a-z0-9\-]{1,100})", path)
        if m:
            self._api_create_note(m.group(1))
            return
        self._send_json(404, {"error": "not found"})

    def do_DELETE(self):  # noqa: N802
        path = urlparse(self.path).path
        m = re.fullmatch(r"/api/notes/([a-z0-9][a-z0-9\-]{1,100})/(n_[a-z0-9]+)", path)
        if m:
            self._api_delete_note(m.group(1), m.group(2))
            return
        self._send_json(404, {"error": "not found"})

    # ---- handlers --------------------------------------------------------

    def _api_list_notes(self, slug: str):
        try:
            notes = read_notes(slug)
        except ValueError as e:
            self._send_json(400, {"error": str(e)})
            return
        self._send_json(200, {"slug": slug, "notes": notes})

    def _api_create_note(self, slug: str):
        try:
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length) if length else b""
            data = json.loads(raw.decode("utf-8") or "{}")
        except (ValueError, json.JSONDecodeError) as e:
            self._send_json(400, {"error": f"bad json: {e}"})
            return
        prefix = (data.get("prefix") or "").strip()
        exact = (data.get("exact") or "").strip()
        suffix = (data.get("suffix") or "").strip()
        note = (data.get("note") or "").strip()
        if not exact:
            self._send_json(400, {"error": "exact is required"})
            return
        # Sanity caps to keep frontmatter readable
        if len(exact) > 4000 or len(prefix) > 500 or len(suffix) > 500 or len(note) > 8000:
            self._send_json(400, {"error": "field too long"})
            return
        try:
            created = append_note(slug, prefix, exact, suffix, note)
        except ValueError as e:
            self._send_json(400, {"error": str(e)})
            return
        self._send_json(201, created)

    def _api_delete_note(self, slug: str, nid: str):
        try:
            ok = delete_note(slug, nid)
        except ValueError as e:
            self._send_json(400, {"error": str(e)})
            return
        if not ok:
            self._send_json(404, {"error": "note not found"})
            return
        self.send_response(204)
        self.end_headers()

    # ---- helpers ---------------------------------------------------------

    def _send_json(self, status: int, payload: dict):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)


class DualStackServer(HTTPServer):
    """Listens on both IPv4 and IPv6 so `localhost` resolves cleanly
    regardless of whether the browser prefers ::1 or 127.0.0.1."""
    address_family = socket.AF_INET6

    def server_bind(self):
        try:
            self.socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
        except (AttributeError, OSError):
            pass  # IPv4-only system; falls back to that
        super().server_bind()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--host", default="::1",
                        help="bind address (default loopback; pass '::' to expose on your LAN)")
    args = parser.parse_args()
    try:
        server = DualStackServer((args.host, args.port), PapersHandler)
    except OSError:
        # Fallback to IPv4-only if the system has no IPv6
        server = HTTPServer(("127.0.0.1", args.port), PapersHandler)
    print(f"Papers wiki  →  http://localhost:{args.port}/viewer.html")
    print(f"Serving from {PAPERS_DIR}")
    print("Ctrl+C to stop.\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")


if __name__ == "__main__":
    main()
