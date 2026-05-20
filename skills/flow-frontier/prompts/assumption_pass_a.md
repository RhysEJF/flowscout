## Your task — Pass A of unstated-assumption mining

You are analyzing a single paper digest. Your job is to identify what the paper **requires to be true but never tests** — its implicit, load-bearing assumptions. These are the foundations a future paper could falsify.

## Cache contract *(v2)*

Before extracting assumptions, **check the cache** at `experiences/theses/_cache/assumptions/{{SLUG}}.json`:

1. If the file exists AND its `digest_sha` matches the SHA-256 of the current digest file content (compute with `shasum -a 256 < <digest-path>` or `python3 -c "import hashlib; print(hashlib.sha256(open(p,'rb').read()).hexdigest())"`) AND its `extractor_version == "v1"` → **return the cached assumptions array** (no LLM call needed for this paper).
2. Otherwise: extract fresh per the instructions below, then **write the cache entry** with:
   - `slug`, `digest_sha`, `extracted_at` (current ISO), `extractor_version: "v1"`, and the `assumptions` array.

The cache lives at `experiences/theses/_cache/assumptions/` (the orchestrator ensures this directory exists). Always read+write through this path.

If `{{NO_CACHE}}` is truthy (orchestrator passes `--no-cache`), skip the cache check and always re-extract, but DO still write the new cache entry.

## Inputs

The paper digest is at: **{{DIGEST_PATH}}**

Read the digest in full before answering. Use the Read tool with `offset`/`limit` if it's long.

## What to look for

For each implicit assumption:

- It must be something the paper's central claim REQUIRES to be true (not a peripheral aside).
- It must be UNTESTED in this paper — neither directly evaluated nor cited to another paper that evaluated it.
- It must be FALSIFIABLE in principle — a counterexample could exist.

**Examples of good implicit assumptions** (from real papers):
- "If retrieval finds the right chunk, the model will use it correctly." (Assumed by every RAG paper that benchmarks retrieval recall separately from QA accuracy.)
- "Long-conversation memory transfers to long-document memory." (Assumed by papers that benchmark on chat data but pitch enterprise document use cases.)
- "Token cost scales linearly with conversation length." (Assumed by cost-comparison tables that ignore caching, prompt sharing, and KV-cache eviction.)

**Reject:**
- Assumptions the paper explicitly tests (e.g., they ran an ablation on it).
- Assumptions the paper acknowledges as a limitation in its discussion section.
- Vague philosophical premises that aren't falsifiable ("attention is all you need" is not an unstated assumption — it's the paper's thesis).
- Tautologies or definitional choices.

## Scoring

For each assumption you identify, score:

- **falsifiability** — would a clear counterexample disprove the paper's central claim? `high` / `medium` / `low`. Default to `low` if unsure.
- **load_bearing** — how central is this assumption to the paper's argument? `high` (paper collapses without it) / `medium` (some claims weaken) / `low` (peripheral).

Only return assumptions where **both** scores are `medium` or `high`. Low-falsifiability or low-load-bearing assumptions add noise.

## Output format

JSON array. Each entry:

```json
{
  "assumption": "<one-sentence implicit assumption>",
  "load_bearing_evidence": "<which paper section/finding rests on this assumption>",
  "falsifiability": "high|medium",
  "load_bearing": "high|medium"
}
```

Cap at 3 assumptions per paper. Pick the most interesting ones.

If you cannot identify a useful unstated assumption that meets the bar, output an empty array `[]`. Better to emit nothing than padding.
