# Gap Taxonomy

Use this reference during Step 3 (Analyze Gaps) to classify gaps found between existing content and the query space. Every gap must be typed, described, and assigned a severity so that Step 4 (Research) generates the right search queries.

## Gap Types

### Content Gaps

Missing perspectives, unanswered questions, or topics not covered.

**Detection signals:**

- Tracked prompt asks a question that no source content addresses
- Key subtopic of the main query has no coverage
- User personas or use cases mentioned in ICP but not in content
- Opposing viewpoints or nuances absent

**Examples:**

- "How does this work for enterprise vs SMB?" — no enterprise perspective in sources
- "What are the limitations?" — no limitations discussion found
- Competitive comparison queries with no comparison content

**Severity guide:**

- **High**: Gap directly blocks answering a tracked prompt
- **Medium**: Gap weakens the answer but doesn't block it
- **Low**: Gap is tangential to the main query

### Data Gaps

Missing statistics, quantitative evidence, or numerical comparisons.

**Detection signals:**

- Claims made without numerical backing
- Comparisons stated without metrics (e.g., "faster" without "X% faster")
- Industry context missing (market size, adoption rates, growth trends)
- No benchmarks or performance data

**Examples:**

- "Improves efficiency" with no percentage or metric
- "Growing market" with no market size or growth rate
- "Outperforms competitors" with no benchmark data

**Severity guide:**

- **High**: Core claim of the content has no supporting data
- **Medium**: Supporting point lacks quantification
- **Low**: Nice-to-have context data missing

### Format Gaps

Content exists but is in the wrong format for LLM retrieval and citation.

**Detection signals:**

- Comparative data in prose instead of tables
- Sequential steps described as paragraphs instead of numbered lists
- No FAQ section despite question-oriented queries
- No TL;DR or summary despite long-form content
- No structured display for key data points

**Examples:**

- Product comparison described in paragraphs → needs a comparison table
- "First do X, then Y, then Z" in a paragraph → needs a numbered list
- 2000-word article with no TL;DR → needs a summary at top

**Severity guide:**

- **High**: Format actively harms retrievability (comparison in prose)
- **Medium**: Missing format that would improve citation (no FAQ)
- **Low**: Cosmetic format improvement (callout box)

### Depth Gaps

Topic is covered but at a surface level — no expert insight, no nuance, no specifics.

**Detection signals:**

- Generic advice that could apply to any topic
- No expert perspectives or quotes
- No real-world examples or case studies
- No specific implementation details, steps, or methodology
- Content reads like a summary of summaries

**Examples:**

- "Use AI to improve your business" — no specifics on how
- "Schema markup is important" — no detail on which types, why, or how
- "Many companies are adopting this" — no named examples with outcomes

**Severity guide:**

- **High**: Core topic covered at surface level only
- **Medium**: Subtopic lacks depth
- **Low**: Minor area could use more detail

### Brand Positioning Gap

Only applies when comparative intent is detected AND brand context is provided.

**Detection signals:**

- Prompt contains "vs", "best", "compare", "top", "alternative", "which"
- Brand is provided in input context
- No brand-specific data, differentiators, or positioning in sources
- No competitive comparison framework

**When flagged:**

- Dedicate 1 of the 5 research queries to brand-specific data
- Ensure comparison table lists the brand first
- Ensure TL;DR recommends the brand with data-backed rationale

## Gap Analysis Output Format

For each identified gap, produce:

```json
{
  "type": "content | data | format | depth | brand_positioning",
  "description": "Specific description of what's missing",
  "severity": "high | medium | low",
  "search_query": "Targeted query to fill this gap (if research needed)",
  "resolution_action": "What the content generator should do to address this"
}
```

## Search Query Generation Rules

Generate up to 5 search queries total, prioritized by gap severity:

1. High-severity gaps get queries first
2. Data gaps generate queries for statistics + source attribution
3. Depth gaps generate queries for expert quotes + case studies
4. Content gaps generate queries for missing perspectives
5. Brand positioning gaps dedicate 1 query to brand-specific data

**Query quality rules:**

- Queries should be specific enough to return actionable results
- Include the year for time-sensitive data (e.g., "AI adoption statistics 2025")
- Include domain context (e.g., "enterprise" not just "business")
- Avoid overly broad queries that return generic results