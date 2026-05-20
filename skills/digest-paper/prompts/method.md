## Reader context (lens)

{{LENS}}

## Your task

Translate this paper's method or experimental design into step-by-step instructions someone could actually run themselves, applied to a realistic scenario relevant to the reader's lens above. Match it to an authentic real-world use case the reader would actually care about — not a contrived academic example.

The instructions should be scannable for a non-technical reader (who needs to understand roughly what's happening) AND clear enough for a technical reader to execute. Include any prompt templates, formulas, or specific procedures the paper requires. No time limits, no costs.

## Output format (markdown)

**Scenario:** <One-paragraph realistic business or research scenario the reader's lens would care about, that this method could be applied to.>

**Steps:**

1. **<Step name>**: <What to do, what to check, what tools to use.>
2. **<Step name>**: <...>
3. ...

(Where a step requires a prompt template, include it as a fenced code block underneath the step.)

**Expected outcome:** <One paragraph describing what the reader will end up with — what insights, artifacts, or decisions they can make from the result.>

## Example (format reference — adapt scenario and steps to the actual paper and the reader's lens)

**Scenario:** A consumer tech company wants to test public reactions to a new wearable health device before launching. They want to understand how different customer segments might respond to its features, pricing, and messaging.

**Steps:**

1. **Define the key audience segments**: Choose 4–8 customer segments based on real attributes — age, income, lifestyle, health habits, tech usage, geography (e.g., "Urban Gen Z tech adopters," "Retired rural users with chronic health issues," "Middle-income suburban parents focused on fitness").

2. **Create structured persona profiles**: For each segment, define a short profile using a consistent format:

   ```
   Name: Mark
   Age: 45
   Occupation: Construction Manager
   Location: Texas
   Health Status: Pre-diabetic, trying to lose weight
   Tech Comfort: Moderate
   Goals: Wants to manage health better but skeptical of new gadgets
   Income: $60K/year
   Values: Practicality, value for money, simplicity
   ```

3. **Develop a product description prompt** that stays consistent across all personas:

   ```
   Imagine you are learning about a new product: "VitalBand." A wearable
   wristband that tracks heart rate, blood pressure, sleep, hydration, and
   sends alerts to your phone. $129, 14-day battery, connects to an app.
   ```

4. **Design the evaluation prompt**:

   ```
   You are [persona description]. You just read the product overview below.
   PRODUCT: [Insert product prompt]
   QUESTION: What is your honest reaction? What do you like or dislike?
   Would you consider buying this product? Why or why not? Be specific and
   stay in character.
   ```

5. **Run the prompt for each persona** using a language model (GPT-4 or similar). Sample 3–5 responses per persona for varied perspectives.

6. **Analyze the results by persona**: Tag themes like "price concern," "trust in health tracking," "interest in improvement," "doubt about usefulness." Summarize common reactions and highlight differences across segments.

7. **Optional validation pass**: Modify the product description based on feedback (e.g., emphasize affordability), rerun with the same personas, compare reactions.

**Expected outcome:** Detailed, persona-specific feedback about the product's appeal, objections, and perceived value — without needing human participants. Helps identify which segments are most receptive, which need tailored messaging, and whether pricing or features might be barriers before launch.

## Paper content

{{CONTENT}}
