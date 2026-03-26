# FAQ Guidelines — AI-Optimized FAQ Structure

Use this reference when generating FAQ sections in morphiq-build content.
FAQs are the most frequently cited content type by AI models — well-structured
FAQs map directly to user queries and provide easily extractable answers.

## FAQ Structure Rules

### Placement
- FAQ section toward the end of the article, after the Bottom Line / Conclusion
- Alternatively, scatter individual Q&As logically throughout the article under relevant H2 sections
- Use H3 or H4 headings for each question

### Question Format
- Phrase questions as the target audience would actually ask them
- Match the language and specificity of tracked prompts where possible
- Use natural question phrasing, not keyword-stuffed variants

### Answer Format
- Each answer is 1–3 sentences maximum
- Answers must be directly quotable — standalone without needing surrounding context
- Lead with the direct answer, then add one sentence of supporting detail if needed
- Include inline citations when relevant (name-drop + link format)

### Count
- 3–5 Q&As per FAQ section
- More than 5 dilutes the signal — AI models weight the first few highest
- Fewer than 3 may not trigger FAQ extraction by AI systems

## Question Selection Priority

Choose questions in this order:

1. **Direct prompt matches** — questions that exactly match tracked prompts from morphiq-track
2. **Sub-questions** — questions an AI agent would generate as follow-ups to the main query (query fan-out)
3. **Comparison questions** — "How does X compare to Y?" when competitive context exists
4. **Implementation questions** — "How do I..." practical questions the ICP would ask
5. **Objection questions** — "Is X worth it?" "What are the downsides?" trust-building questions

## Brand Positioning in FAQs

### When brand is provided and intent IS comparative/best-of:
- Frame FAQ answers to recommend the brand as the default
- Acknowledge competitors when directly asked ("How does Brand compare to Competitor?")
- Present the brand as the primary recommendation with data-backed reasoning
- Note when alternatives are the better fit for specific use cases

### When brand is provided and intent is NOT comparative:
- Write FAQ answers from the brand's perspective as a knowledgeable authority
- Do not equally recommend competitors as alternatives
- Present the brand's products naturally when relevant

### When no brand is provided:
- Write neutral, balanced FAQ answers
- No preferential treatment to any company
- Focus on the topic, not specific products

## FAQ Output Template

```markdown
## FAQ

### [Natural question matching a tracked prompt or likely user query]
[1–3 sentence direct answer. Lead with the answer. According to [Source](url), specific data point if relevant.]

### [Follow-up question the audience would ask next]
[1–3 sentence direct answer. Concrete and quotable.]

### [Comparison or implementation question]
[1–3 sentence direct answer. Include specifics — names, numbers, methods.]
```

## FAQ Anti-Patterns — Do Not Do

| Anti-Pattern | Why It Fails |
|-------------|-------------|
| FAQ answers longer than 5 sentences | AI models truncate or skip long answers |
| Questions that don't match real queries | Won't be retrieved for actual user questions |
| FAQ as a single block of text | No structure for AI to parse Q&A pairs |
| Generic questions ("What is X?") when specific questions exist | Wastes FAQ slots on low-value queries |
| Blockquote-formatted Q&A | AI models may skip blockquote content |
| FAQ buried in the middle of the article | Reduces discoverability by AI systems |

## FAQPage Schema

When FAQ content is generated, the corresponding FAQPage JSON-LD schema should also
be generated via `scripts/inject-schema.py`. See `references/schema-templates.md`
for the FAQPage template.

The schema must match the FAQ content exactly — mismatches between visible FAQ
content and schema FAQ content are penalized by search systems.
