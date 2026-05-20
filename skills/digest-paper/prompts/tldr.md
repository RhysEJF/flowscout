## Reader context (lens)

{{LENS}}

## Your task

Produce a single-paragraph TLDR of the paper that an intelligent layperson can scan in 30 seconds and walk away with the actionable findings and statistics. Do not use flowery language. Do not start with "This paper..." templated openings — get into the substance. Include concrete numbers (sample sizes, effect sizes, percentage gains, model names) wherever the paper provides them. End with the most useful takeaway. Single paragraph only — no headings, no bullets.

## Examples of great TLDRs (format reference — adapt content to the actual paper's domain)

### Example 1
This 2006 study by Salganik, Dodds, and Watts created an artificial music market with 14,341 participants to test how social influence affects market outcomes. They divided participants into conditions where some could see others' choices (social influence) and some couldn't (independent). The researchers found social influence significantly increased both inequality (popular items became disproportionately more popular) and unpredictability (the same item could succeed in one environment but fail in another with identical starting conditions). Success was only partly determined by quality — the best songs rarely failed completely and the worst rarely succeeded greatly, but anything in between was possible. When social signals were strengthened (by sorting songs by popularity in experiment 2), these effects intensified. This demonstrates that market outcomes are inherently unpredictable when social influence is present.

### Example 2
The authors built PERSONA, a freely-available testbed that turns 1,586 synthetic U.S. personas — sampled from American Community Survey microdata and enriched with Big-Five traits, values and quirks — into a 317k-pair preference dataset covering 3,868 controversial prompts; when language models answer questions "in character," GPT-4's responses match human raters imitating the same persona 60-80% of the time (Cohen's κ ≈ 0.6-0.8), while a model given no persona context scores only ~5% accuracy. Key design lessons: (1) sample personas directly from census-level microdata, then fill gaps procedurally and filter for self-consistency with an LLM; (2) feed the persona to the model but summarize the relevant traits first — this simple step beats both raw persona conditioning and chain-of-thought prompting across 700 questions; (3) no single demographic field drives preferences — effect is holistic — so deleting one attribute barely moves κ; (4) pass-at-k tests show open-weights models like Llama-3-70B can overtake GPT-4 when you sample multiple times, suggesting ensemble-style querying can raise fidelity.

### Example 3
OASIS is an open-source simulator that plugs large-language-model "users" into a Twitter- or Reddit-style sandbox: it gives each agent a realistic profile, a dynamically changing follow network, a content-based recommender (TwHIN-BERT worked best), and 21 native actions (post, comment, follow, mute, refresh feed, etc.), then lets up to 1 million of them interact in parallel. When benchmarked against 198 real Twitter cascades the model reproduced propagation scale, depth and breadth with mean normalised RMSE under 0.2 — provided both the recommender and real-hourly activity curves were kept; removing either feature severely dampened reach. Several phenomena emerged only at scale: below 10k agents herd behaviour was absent, but at 10k–1M users down-voted posts rapidly lost support while up-voted ones snowballed, and groups gradually corrected counterfactual claims over 30 simulated timesteps. A 1M-user run (10 timesteps) needed 27 A100 GPUs and ~18h per step; 100k users ran on 5 GPUs in 3h, so sizing matters.

## Paper content

{{CONTENT}}
