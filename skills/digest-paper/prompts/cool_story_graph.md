## Reader context (lens)

{{LENS}}

## Your task

Scan the paper and identify the figure or table that most clearly tells the paper's story in a single view — typically the one that contrasts the proposed method/finding with all baselines or comparison conditions (e.g., side-by-side charts, overlaid plots, confusion-matrix grids, before/after comparisons).

First, list the top three candidate figures with figure number and page, each on its own line, plus one sentence on why it's compelling.

Then choose the best figure and provide the items below.

**Output format (use exactly these headers, nothing else):**

```
Image Candidates:
Figure <number> (p. <page>): <one-sentence reason it's compelling>
Figure <number> (p. <page>): <one-sentence reason it's compelling>
Figure <number> (p. <page>): <one-sentence reason it's compelling>

Best Image:
Figure Name: Figure <number>: "<exact figure title>"
Figure Page: <integer page number where this figure appears in the PDF — REQUIRED, used by the skill to extract the image>
Slide Caption: <one-sentence caption suitable for use in a slide deck>
Description: <one concise paragraph describing what the figure shows, what comparison it makes, and why it matters>
```

Do not add any extra text before or after this block. The `Figure Page` line is mandatory — the skill parses it to call `pdftoppm` and extract the page as a PNG. If you cannot determine the page number with confidence, return your best estimate (still as a single integer) rather than skipping the line.

## Example

```
Image Candidates:
Figure 6 (p. 21): Overlays median forecasts from AI-simulated and human panels for key economic indicators across multiple forecast horizons.
Figure 7 (p. 23): Side-by-side density plots of forecast errors for individual AI and human forecasters across multiple periods.
Table 8 (p. 25): Grid comparing baseline AI accuracy to multiple stripped-down baselines, showing incremental contribution of each component.

Best Image:
Figure Name: Table 8: Relative accuracy of AI forecasts with fewer prompt inputs
Figure Page: 25
Slide Caption: Relative accuracy of AI forecasts with fewer prompt inputs.
Description: Table 8 presents a comprehensive matrix comparing the forecast accuracy of the proposed AI method — including all persona, real-time data, and historical survey inputs — against three key baselines: (1) generic AI with no persona, (2) no persona and no real-time data, and (3) no persona, no real-time data, and no historical survey data. Ratios above 1 indicate degradation in accuracy relative to the fully specified method. The grid demonstrates that forecast accuracy drops sharply as more context is removed, with the largest error increases seen when past survey data is omitted — highlighting the critical role of each input component.
```

## Paper content

{{CONTENT}}
