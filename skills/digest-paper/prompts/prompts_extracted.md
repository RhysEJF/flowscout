## Your task

Extract every full-text prompt that was given to a language model in this paper — for persona role-play, generation, evaluation, or any other use. Include the exact prompt text verbatim.

**If the paper contains no LLM prompts at all** (e.g., it's a behavioral science, parenting, biology, or theory paper with no language model component), output exactly this and nothing else:

```
No applicable prompts found in this paper.
```

Otherwise, output each prompt using the format below. No extra commentary, no markdown inside the code block, no quotation marks wrapping the prompt.

## Output format (markdown)

For each prompt:

**Prompt explanation:** <one-line description of what the prompt does and the role it plays in the paper>

```
<exact prompt text verbatim>
```

(repeat for each prompt found in the paper)

## Examples

**Prompt explanation:** Baseline — elicits respondent views on global warming, anchoring demographic recall under interview conditions.

```
You are an interviewee. Based on your previous answers, respond to the last question.
Interviewer: What is the current year and month of this interview? Me: October 2017.
Interviewer: I am going to read you a list of five race categories. What race do you consider yourself to be? 'White, Non-Hispanic', 'Black, Non-Hispanic', '2+ Races, Non-Hispanic', 'Hispanic', or 'Other, Non-Hispanic.' Me: {race from survey response}.
Interviewer: What do you think: Do you think that global warming is happening? Would you say 'Yes', or 'No'?
```

**Prompt explanation:** Calibration — links party preference to demographics for a 40-year-old white U.S. college-educated male.

```
Assuming you are a 40-year-old male, white, with a college degree and middle class in the United States, which party would you vote for if there were a national election tomorrow? (1) Democrat, (2) Republican, (3) Other party, (4) No answer/Don't know/I would not vote.
```

**Prompt explanation:** Persona generation — populates a structured JSON template with realistic demographic detail for opinion simulations.

```
You are an AI assistant specialized in detailed and unbiased persona generation for opinion simulations. Your task is to generate a specific, realistic, and diverse persona based on the provided demographic information and fill in a comprehensive JSON template.

### INSTRUCTIONS ###
1. You will be provided with a persona meta file that has the core demographic information of a person.
2. You will also be provided with a final persona template. Your task is to create a detailed, concrete persona that is fully consistent with ALL features in the given metadata by filling the template.
3. Elaborate on all metadata points, providing specific details that flesh out the persona while remaining true to the given information.
4. For all of the features in the metadata, you will be provided with a range of values in the VALUE RANGES AND CATEGORIES section below. Select one of the values for each of the features. DO NOT ADD EXTRA INFORMATION OR ELABORATION TO THE VALUES.
5. IMPORTANT: Place your entire response in the ### PERSONA GENERATION ### section below. Start your response with 'Persona:' and then provide only the persona description.
```

## Paper content

{{CONTENT}}
