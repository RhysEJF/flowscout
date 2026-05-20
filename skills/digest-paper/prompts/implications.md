## Reader context (lens)

{{LENS}}

## Your task

What are the practical implications of this paper's findings for someone matching the reader context above? Produce 5-8 brief bullet points. Each bullet starts with a bold imperative or insight (the "headline"), then explains in one or two sentences what it means and what action the reader could take. Keep it concrete, specific, and grounded in what the paper actually shows. Don't repeat the same point in different wording.

## Output format (markdown)

- **<Bold headline imperative or insight>**: <One or two sentences explaining what the paper shows and what the reader can do about it.>
- **<Bold headline>**: <Explanation.>
- ...

No preamble, no outro. Just the bullet list.

## Examples (format reference — adapt content to the actual paper and the reader's lens)

### Example 1
- **Ground your simulated audience in real-world data wherever possible**: Studies that used actual population data (like surveys or census records) produced more accurate and credible results than those relying only on randomization or fixed values.
- **Avoid defaulting to random or constant values for personas**: Over 70% of published simulations simply assigned random or fixed attributes to agents, but this shortcut risks missing important diversity and reduces predictive value.
- **Use established techniques for building synthetic populations**: Methods like "synthetic reconstruction" or "combinatorial optimization" blend statistical data and sampling to create more representative virtual audiences.

### Example 2
- **Prompt design matters more than the AI model used**: The way you ask questions has a bigger impact on response quality than which language model you use. Invest time in better prompt wording before paying for more expensive models.
- **AI personas struggle with short or factual queries**: Simulated audiences are less accurate on terse, fact-based questions ("What is X?"). Avoid relying on simulations for these use cases.
- **Use persona summarization before asking questions**: First ask the persona to identify which parts of their background are relevant to the question, then generate the response. This single technique improved accuracy across all models tested.
- **Avoid chain-of-thought prompting for personas**: Counter-intuitively, asking AI personas to "think through" their responses made them worse at mimicking human preferences. Keep responses direct and immediate.
- **Validate synthetic results with small human samples**: Since AI personas achieved substantial agreement with humans, run large synthetic studies and validate findings with smaller, targeted human samples rather than expensive large-scale human research upfront.

### Example 3
- **Large-scale group dynamics only emerge with enough agents**: Polarization, social contagion, and cultural diffusion only appeared in simulations with at least 50–1000 agents. For trend or opinion-spread studies, use larger audiences.
- **Role diversity improves realism**: Agents with distinct social roles (builder, trader, leader) behaved more like real people. Assign personas specific goals or professions.
- **Coherent agents avoid contradictions**: Simulations were more accurate when agents used a centralized decision process to align speech and actions. Don't let your personas "say one thing and do another."
- **Longitudinal simulations uncover richer patterns**: Running agents over longer simulated time revealed realistic shifts in opinions and alliances. Use multi-step or sequential simulations instead of one-off surveys.
- **Influencers and norms shape behavior**: Introducing "influencer" personas or shared rules led to measurable behavior changes. Test how brand ambassadors or policies might affect customers by seeding influencers or rule changes.

## Paper content

{{CONTENT}}
