# Prompt Taxonomy — Types, Fan-out Depth, and Generation Rules

Use this reference when morphiq-track generates prompts (via `create-prompts.py`) and when measuring share of voice. This document defines all prompt types, their fan-out depth profiles, tracking priority, and the rules for generating a balanced prompt set.

## Prompt Types

### Core Types (used in MORPHIQ-TRACKER.md)

These five types are the baseline prompt categories in the tracker:

| Type | Definition | Example |
|---|---|---|
| `brand` | Direct company name query | "what is Example Company" |
| `category` | Category/market query | "best widgets for teams" |
| `comparison` | Head-to-head comparison | "Example Company vs Competitor A" |
| `feature` | Specific feature/capability query | "widget automation features" |
| `use_case` | How-to or use case query | "how to implement a widget for remote teams" |

### Extended Types (from fan-out research)

These additional types capture prompt behaviors with distinct fan-out profiles:

| Type | Definition | Example |
|---|---|---|
| `technical_eval` | In-depth technical platform evaluation | "evaluate serverless GPU platforms for LLM inference" |
| `discovery` | Broad landscape/market exploration | "what AI startups are building data labeling tools" |
| `recommendation` | Seeking specific recommendations with criteria | "recommend a corporate card for a 50-person startup" |
| `problem_seeking` | Describing a problem, seeking solutions | "I need to automate expense reports for my team" |

---

## Fan-out Depth by Prompt Type (Cross-Model)

| Prompt Type | GPT-5.4 Avg | Claude Avg | Gemini Avg | Aggregate Priority |
|---|---|---|---|---|
| `technical_eval` | 11.0 | 2.0 | 8.0 | **Highest** — most visibility surface area |
| `discovery` | 7.5 | 2.0 | 5.5 | **High** — landscape-building, brand injection risk |
| `recommendation` | 5.8 | 1.0 | 5.5 | **Medium-high** — drives purchase decisions |
| `comparison` | 5.4 | 1.7 | 9.3 | **Medium-high** — always per-entity decomposition |
| `category` | ~5.0 | ~1.5 | ~5.0 | **Medium** — market landscape queries |
| `feature` | ~3.5 | ~1.5 | ~4.0 | **Medium** — feature verification |
| `problem_seeking` | 2.8 | 1.0 | 3.5 | **Medium** — solution landscape |
| `use_case` | 2.4 | N/A | N/A | **Lower** — focused, narrow lookup |
| `brand` | ~2.0 | ~1.0 | ~3.0 | **Lowest** — but essential baseline |

### Why fan-out depth matters for tracking

A `technical_eval` prompt with 11 sub-queries generates 11 opportunities for a brand to appear or be cited. A `brand` prompt with 2 sub-queries generates 2. Measuring them with equal weight skews SoV — a company could score 100% on brand queries but 0% on technical evaluations, giving a misleadingly high aggregate SoV.

**Tracking priority rule:** Weight high-fanout prompt types more heavily when generating prompt sets and calculating aggregate SoV. A citation won from a `technical_eval` prompt represents visibility across a larger sub-query surface than one from a `brand` prompt.

---

## Prompt Generation Rules

When `create-prompts.py` generates a prompt set, apply these rules:

### 1. Balanced type distribution

Generate prompts across all types, weighted toward high-fanout types:

| Type | Target % of Set | Rationale |
|---|---|---|
| `brand` | 10% | Baseline — low fanout but essential identity check |
| `category` | 15% | Market landscape visibility |
| `comparison` | 20% | Per-entity decomposition — high competitive signal |
| `feature` | 10% | Feature verification |
| `use_case` | 10% | Narrow but practical |
| `technical_eval` | 15% | Highest fanout — most visibility surface |
| `discovery` | 10% | Landscape building |
| `recommendation` | 5% | Purchase intent |
| `problem_seeking` | 5% | Solution landscape |

### 2. Temporal markers

Add year markers ("2026", "latest") to at least 70% of prompts. Research shows GPT-5.4 triggers web search 92% of the time, but the 8% that skips search are queries without temporal markers. Adding the year ensures search is triggered.

### 3. Entity inclusion

For comparison and technical_eval prompts, include 2–3 specific entities (the client company + top competitors). This triggers the per-entity decomposition pattern across all models.

### 4. Competitor coverage

For every competitor tracked in the tracker, generate at least:
- 1 direct comparison prompt ("Client vs Competitor")
- 1 category prompt where the competitor would naturally appear
- 1 "alternative to [Competitor]" prompt (to measure Gemini's alternative exploration behavior)

### 5. Fan-out trigger optimization

Avoid generating prompts that are too generic to trigger search:
- Include at least one specific entity or product name per prompt
- Include temporal markers when the topic is time-sensitive
- Use specific use-case framing rather than abstract category names

---

## Prompt Type Detection Rules

When classifying an incoming prompt or existing tracked prompt:

| Signal | Detected Type |
|---|---|
| Contains company name only, no other entities | `brand` |
| Contains "vs", "versus", "compared to", "or" between entities | `comparison` |
| Contains "best", "top", "leading" + category noun | `category` |
| Contains specific feature names or capability keywords | `feature` |
| Contains "how to", "implement", "set up", "configure" | `use_case` |
| Contains "evaluate", "assess", "benchmark", "which platform" | `technical_eval` |
| Contains "what [category] companies/tools/startups" | `discovery` |
| Contains "recommend", "suggest", "should I use" | `recommendation` |
| Describes a problem without naming solutions | `problem_seeking` |

If multiple signals match, prefer the higher-fanout type (it generates more visibility surface).

---

## Per-Model Decomposition Patterns

How each model decomposes a comparison prompt ("A vs B vs C for [use case]"):

| Step | GPT-5.4 | Claude | Gemini | Perplexity |
|---|---|---|---|---|
| 1 | Broad: "A vs B vs C [use case] [year]" | Bundled: "A vs B vs C [use case] [year]" | Broad: "A vs B vs C [year]" | Opaque (single internal search) |
| 2 | Per-entity: "A features pricing official" | Contextual: related event/news | Per-entity features: "A features [year]" | — |
| 3 | Per-entity: "B features pricing official" | (stops at 2–3) | Per-entity features: "B features [year]" | — |
| 4 | Per-entity: "C features pricing official" | | Per-entity features: "C features [year]" | — |
| 5 | `site:a.com` pricing official | | Per-entity review: "A review [year]" | — |
| 6 | `site:b.com` pricing official | | Per-entity review: "B review [year]" | — |
| 7 | `site:c.com` pricing official | | Per-entity review: "C review [year]" | — |
| 8+ | More `site:` deep dives | | "best [category] [year]" | — |
| 9+ | | | Per-entity pricing: "A pricing [year]" | — |
| 10+ | | | Per-entity alternatives: "A alternatives [year]" | — |

How each model decomposes a discovery prompt ("Best [category] for [use case] [year]"):

| Step | GPT-5.4 | Claude | Gemini | Perplexity |
|---|---|---|---|---|
| 1 | Broad with brand names injected | Single keyword extraction query | Broad category search | Opaque |
| 2 | `site:` per known player | (sometimes a 2nd angle) | Per-platform search | — |
| 3–8 | More `site:` verification | | Variations (trends, reviews, alternatives) | — |

---

## Weighted SoV Calculation

To account for fan-out depth when calculating SoV, use fan-out weights per prompt type:

### Standard SoV (current formula)

```
SoV = (company_mentions / total_mentions) × 100
```

### Fan-out-weighted SoV

```
weighted_SoV = Σ(prompt_type_SoV × prompt_type_weight) / Σ(prompt_type_weights)
```

Where `prompt_type_weight` is proportional to average fan-out depth:

| Type | Weight |
|---|---|
| `technical_eval` | 3.0 |
| `discovery` | 2.5 |
| `recommendation` | 2.0 |
| `comparison` | 2.0 |
| `category` | 1.5 |
| `feature` | 1.0 |
| `problem_seeking` | 1.0 |
| `use_case` | 0.8 |
| `brand` | 0.5 |

A 40% SoV on `technical_eval` prompts contributes more to aggregate SoV than a 40% SoV on `brand` prompts because technical evaluations represent 5x more sub-queries per prompt.

The tracker records both standard and weighted SoV.

For full SoV methodology including mention types and invisible SoV, read `share-of-voice.md`.

---

## GEO Prompt Categories (5 Categories)

The GEO scoring system uses a 5-category prompt taxonomy that maps to the 9 pipeline types above. This taxonomy covers the full spectrum of how a potential customer might discover a brand through AI:

| Category | Share | Count (of 50) | Brand Name? | What It Tests |
|---|---|---|---|---|
| Organic | 45% | ~23 | No | Unprompted discovery — does AI recommend without being asked? |
| Competitor | 11% | ~6 | Mixed | Competitive positioning — "alternatives to X" |
| How-to Guides | 14% | ~7 | No | Solution discovery — tool-seeking problem queries |
| Brand-Specific | 13% | ~7 | Yes | Direct brand knowledge — does AI know who you are? |
| FAQ | 17% | ~9 | No | Educational/learning context — "how/what/why" queries |

### GEO Category → Pipeline Type Mapping

| GEO Category | Pipeline Prompt Types |
|---|---|
| Organic | `category`, `discovery`, `recommendation` |
| Competitor | `comparison` |
| How-to | `use_case`, `problem_seeking` |
| Brand-Specific | `brand` |
| FAQ | `use_case`, `problem_seeking` |

### GEO Category Quality Rules

| Category | Rules |
|---|---|
| **Organic** | <120 chars, concise (<20 words), 10–35% start with "Best", must express buying/evaluation intent |
| **Competitor** | 70% discovery ("alternatives to X"), 30% direct comparison ("[Brand] vs X") — NEVER "Competitor A vs Competitor B" without brand |
| **How-to** | Must include tool-seeking phrase ("what tools help with this?", "what platforms do people recommend?") |
| **FAQ** | Must start with question word (How, What, Why, Can, Is, Does, Which) |
| **Brand-Specific** | Must contain brand name |

---

## Intent-Weighted GEO Score

Beyond the simple average mention rate, the GEO scoring applies intent weights to each category:

```
Weighted GEO = (Organic × 0.45) + (Competitor × 0.22) + (How-to × 0.22) + (Brand × 0.11)
```

### Why These Weights

- **Organic at 45%:** Unprompted discovery is the hardest and most valuable signal. If AI recommends a brand without being asked, it has earned genuine authority.
- **Competitor at 22%:** Head-to-head competitive positioning — does the brand win comparisons?
- **How-to at 22%:** Solution context — is the brand recommended when users solve problems?
- **Brand-Specific at 11%:** Should be high for any real brand. A sanity check, not a differentiator.

FAQ category excluded from the weighted score (uses standard average only).

### GEO Score Thresholds

| Score | Rating | Color |
|---|---|---|
| ≥ 60 | Excellent | Green |
| ≥ 40 | Good | Blue |
| ≥ 20 | Fair | Yellow |
| ≥ 10 | Poor | Orange |
| < 10 | Very Poor | Red |

### Relationship: Fan-out Weights vs. Intent Weights

These are two different weighting systems:

| System | Operates On | Purpose |
|---|---|---|
| **Fan-out weights** (above) | 9 pipeline prompt types | Weights SoV by sub-query surface area per prompt |
| **Intent weights** (this section) | 5 GEO categories | Weights GEO score by discovery intent value |

Both are valid perspectives. Fan-out weights answer "how much visibility surface does each prompt type create?" Intent weights answer "how valuable is each type of discovery for the brand?" The tracker records both.
