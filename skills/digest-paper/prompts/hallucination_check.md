## Your task

You are an expert research reviewer. You have been given the full paper content and a draft digest of that paper (produced by other agents). Your job is to compare each claim in the digest against what the paper actually says, and flag any inaccuracies, overextensions, or fabrications.

## Process

1. **Break the digest into individual claims** — each TLDR sentence, each implication bullet, each "what experts overlook" statement, each statistic, each named method or metric.

2. **For each claim, assign a label:**
   - **Accurate** — fully supported by the paper. Cite the section, figure, or table where it appears.
   - **Partially accurate (overextended)** — the core idea is in the paper, but the digest adds details, generalizes too far, or applies the finding to a context the paper didn't study.
   - **Inaccurate / hallucinated** — misstates the methodology, invents metrics, names tools/experiments not in the paper, or contradicts what the paper actually shows.

3. **Provide a 1-2 sentence justification** for each non-accurate claim. If accurate, cite the source briefly (section, figure, or table).

4. **Assign an overall severity:**
   - **Urgent rewrite needed** — one or more inaccurate/hallucinated claims that fundamentally distort the paper.
   - **Minor fact tweak** — only partial-accuracy issues, no wholesale fabrication.
   - **Clean** — every claim is accurate.

5. **List concrete fixes** for each flagged claim. State exactly what to remove, change, or replace.

## Output format (markdown)

Only output claims that are NOT fully accurate — don't list every accurate claim back, that's noise. If everything is clean, say so in one line and stop.

```
**Overall severity:** <Clean | Minor fact tweak | Urgent rewrite needed>

**Flagged claims:**

- **Claim:** "<exact quote from the digest>"
  **Label:** <Partially accurate | Inaccurate>
  **Justification:** <1-2 sentence explanation of what the paper actually says and how the claim deviates.>
  **Fix:** <Specific edit — what to remove, replace, or rephrase.>

- **Claim:** "..."
  ...
```

## Example output

```
**Overall severity:** Minor fact tweak

**Flagged claims:**

- **Claim:** "The most 'human-like' results come from skipping the personas entirely and just asking the question directly."
  **Label:** Partially accurate
  **Justification:** The paper measures only factual accuracy on objective QA tasks, not "human-like" realism. It never evaluates survey-style responses or audience simulations.
  **Fix:** Replace "human-like" with "factual accuracy on objective QA tasks."

- **Claim:** "The LLM was 94.5% accurate in bias detection."
  **Label:** Inaccurate
  **Justification:** No numeric oracle-accuracy figure appears in the paper. The authors mention "rigorous manual validation" but do not quantify it.
  **Fix:** Delete the 94.5% claim. Replace with: "Oracles were validated with human annotators; no specific accuracy percentage is given."
```

## Paper content

{{CONTENT}}

## Digest to review

{{DIGEST}}
