---
name: Morphiq Track
description: This skill should be used when the user asks to "run a tracking cycle", "measure AI visibility", "check share of voice", "run Morphiq Track", "track citations", "check GEO score", "generate prompts", "run content creation workflow", or mentions monitoring LLM mentions, running content creation workflows, measuring brand visibility, or generating query fanout content. Queries multiple LLM providers, produces delta reports, and maintains MORPHIQ-TRACKER.md as the persistent state file for the entire pipeline.
version: 0.1.0
---

## Pipeline Position

Step 4 of 4 — measurement + flywheel.
- **Input:** Build Output (JSON) from morphiq-build + MORPHIQ-TRACKER.md (persistent state).
- **Output:** Delta Report (JSON) → loops back to morphiq-rank.
- **Owns:** MORPHIQ-TRACKER.md — generates on first run, updates every run.
- **Drives:** 3 ongoing workflows (Content Optimization, Content Creation, Query Fanout Expansion).
- **Data contract:** See `PIPELINE.md` §4 for the Delta Report and §5 for MORPHIQ-TRACKER.md.

## Purpose

Morphiq Track is the measurement and flywheel skill. It queries AI providers to measure brand visibility, computes GEO scores and Share of Voice, tracks deltas over time, and drives three ongoing workflows that feed back into the pipeline.

## Workflow

### Step 1: Generate or Load Prompts

**First run:** Generate 70 prompts across 6 GEO categories:

| Category | Share | Brand Name? |
|---|---|---|
| Organic | 40% | No |
| Competitor | 8–12% | Mixed |
| How-to | 12% | No |
| Generic | 10% | No |
| Brand-Specific | 11% | Yes |
| FAQ | 15% | No |

Apply quality rules per category. Add temporal markers to 70%+ prompts. Include entities in comparison/technical prompts.

**Subsequent runs:** Load from MORPHIQ-TRACKER.md. Generate 20 recommendations if 7-day cooldown elapsed.

For taxonomy, fanout profiles, and generation rules, read `references/prompt-taxonomy.md`.

### Step 2: Query AI Providers

Distribute prompts evenly across 4 providers:

| Provider | Model | Concurrency |
|---|---|---|
| OpenAI | gpt-4o | Full |
| Perplexity | sonar-pro | 2 concurrent |
| Anthropic | claude-sonnet-4-5 | Serialized |
| Gemini | gemini-3-flash-preview | 3 concurrent |

Model names reflect recommended defaults. Use the latest available version of each provider's model at runtime. The agent executes queries using its built-in web search and API tools — `scripts/run-queries.py` provides the orchestration plan and result structuring, not the API calls themselves.

For provider config and response pipeline, read `references/provider-strategies.md`.
For selection rules and distribution, read `references/query-targets.md`.

### Step 3: Analyze Responses

5-step pipeline: extract raw response/citations/sub-queries → structured analysis (using the agent's reasoning capabilities) → brand mention validation (exact → TLD → LLM judge) → competitor filtering → entity normalization.

### Step 4: Compute GEO Score

```
GEO = mean(provider_scores)
Weighted GEO = (Organic × 0.40) + (Competitor × 0.20) + (How-to × 0.20) + (Generic × 0.10) + (Brand × 0.10)
```

Thresholds: ≥60 Excellent, ≥40 Good, ≥20 Fair, ≥10 Poor, <10 Very Poor.

For GEO methodology, read `references/query-targets.md`.

### Step 5: Compute Share of Voice

Three SoV tiers:

| Metric | What It Measures |
|---|---|
| **Mention SoV** | Brand name in final responses |
| **Fanout-Weighted SoV** | Weighted by prompt type fan-out depth |
| **Influence SoV** | Brand presence in sub-queries (invisible influence) |

Track **Conversion Gap** = Influence SoV − Citation SoV.

For SoV methodology, read `references/share-of-voice.md`.

### Step 6: Compute Deltas

Compare against previous snapshot. Flag changes >5 points. Generate flagged actions for regressions, losses, displacement, and conversion gaps.

For delta methodology, read `references/delta-scoring.md`.

### Step 7: Update MORPHIQ-TRACKER.md

Update all 14 sections: Score Summary, Score Breakdown, Open/Resolved Issues, SoV (3-tier), SoV Trend, Citations, Prompts, Competitors, Per-Page, Content Performance, Fanout Coverage, Creation Queue, Run History.

For tracker specification, read `references/tracker-spec.md`.

### Step 8: Produce Delta Report

Assemble JSON (`PIPELINE.md` §4): SoV metrics, citations, per-provider data, competitors, flagged actions, content queue. Loops back to morphiq-rank.

## Three Ongoing Workflows

### Workflow A: Content Optimization

1. Identify pages with declining SoV or lost citations
2. Feed to morphiq-build (existing content path)
3. Re-track to measure impact

### Workflow B: Content Creation

1. Collect prompts where brand is absent
2. Identify competitor citation sources
3. Generate content briefs for missing coverage
4. Feed to morphiq-build (new content path)

### Workflow C: Query Fanout Expansion

1. Analyze sub-queries from provider responses
2. Identify sub-queries with no matching site content
3. Generate briefs for unanswered sub-queries
4. Prioritize by citation weight (citation-producing 1.5x, `site:` 2x)

## Reference Files

| File | Purpose |
|---|---|
| `references/prompt-taxonomy.md` | Prompt types, GEO categories, fanout depth, generation rules |
| `references/share-of-voice.md` | SoV formulas, mention types, invisible SoV, competitive tracking |
| `references/provider-strategies.md` | Provider config, models, response analysis pipeline |
| `references/query-targets.md` | Provider selection, distribution, citation categories, GEO score |
| `references/delta-scoring.md` | Delta calculation, significance thresholds, flagged actions |
| `references/tracker-spec.md` | Full MORPHIQ-TRACKER.md specification (14 sections) |
