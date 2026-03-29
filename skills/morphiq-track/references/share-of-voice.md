# Share of Voice — Measurement Methodology

Use this reference when morphiq-track calculates SoV metrics and when interpreting SoV data in the tracker. This document defines the SoV formulas, per-provider calculation, mention types, invisible SoV, and competitive tracking.

## Standard Share of Voice

### Formula

```
SoV = (company_mentions / total_mentions_across_all_responses) × 100
```

A "mention" is any instance where the company name, brand name, or domain URL appears in an AI model's response to a tracked prompt.

### Per-Provider SoV

Calculate SoV separately for each AI provider:

```
provider_SoV = (company_mentions_from_provider / total_mentions_from_provider) × 100
```

Providers: OpenAI (GPT-5.4), Gemini, Perplexity, Anthropic (Claude).

### Aggregate SoV

```
aggregate_SoV = mean(provider_SoVs)
```

Simple mean across all queried providers. If a provider is not queried in a run, exclude it from the mean.

---

## Mention Types

Not all mentions are equal. Track these separately:

| Mention Type | Definition | Weight |
|---|---|---|
| **Citation** | Company URL appears as a linked source in the response | 2.0 |
| **Named mention** | Company name appears in the response text | 1.0 |
| **Recommendation** | Company is explicitly recommended ("we recommend X", "X is the best") | 1.5 |
| **Passing reference** | Company is listed among others without emphasis | 0.5 |

### Weighted Mention Score

```
weighted_mentions = Σ(mention_count × mention_type_weight)
weighted_SoV = (weighted_company_mentions / weighted_total_mentions) × 100
```

The tracker records both raw SoV (all mentions equal) and weighted SoV (citations and recommendations count more).

---

## Fan-out-Weighted SoV

Standard SoV treats all prompt types equally. Fan-out-weighted SoV accounts for the fact that high-fanout prompt types generate more visibility surface area.

### Formula

```
fanout_weighted_SoV = Σ(prompt_type_SoV × prompt_type_fanout_weight) / Σ(prompt_type_fanout_weights)
```

Fanout weights by prompt type (from `prompt-taxonomy.md`):

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

### Why this matters

A company with 80% SoV on `brand` prompts but 10% SoV on `technical_eval` prompts has a misleadingly high standard SoV. Fan-out-weighted SoV surfaces this gap because technical evaluations represent 5x more sub-queries (and therefore 5x more citation opportunities) per prompt.

---

## Invisible SoV — Sub-Query Influence Tracking

### The Problem

Standard SoV only measures what appears in the model's final response. But research shows that brands influence AI responses at the sub-query level without appearing in the final citation list:

1. **GPT-5.4 injects brand names into sub-queries** even when the user never mentioned them. The model decides which brands to evaluate before the user sees results.
2. **`site:` queries access a brand's site** but the information may be synthesized without a visible citation — the brand influenced the answer without being credited.
3. **"Official docs" queries** pull authoritative content that gets synthesized into the response without verbatim citation.

### Invisible SoV Definition

Invisible SoV tracks whether the client's brand or domain appeared in the model's research process (sub-queries, retrieved pages) rather than just the final output.

### Detection Methods

| Model | Detection Method | Confidence |
|---|---|---|
| **GPT-5.4** | Responses API exposes `web_search` tool calls with all sub-queries visible | High — full sub-query visibility |
| **Claude** | Tool use results expose search queries when using web search tools | High — when tool use is visible |
| **Perplexity** | Shows sub-queries natively in some interfaces; API may provide `search_queries` | Medium — not always available |
| **Gemini** | Grounding metadata may expose search queries in some API configurations | Low-medium — inconsistent |

### Tracking Implementation

When sub-query data is available from the provider API response:

1. **Extract all sub-queries** from the provider response
2. **Check for brand presence** — does the client's company name, domain, or product name appear in any sub-query?
3. **Record sub-query mentions** separately from final-response mentions
4. **Calculate invisible SoV:**

```
invisible_SoV = (prompts_where_brand_appeared_in_subqueries / total_prompts) × 100
```

### Tracker Integration

The tracker's SoV section records three tiers of visibility:

| Metric | Definition |
|---|---|
| **Citation SoV** | Brand URL cited as a linked source in final response |
| **Mention SoV** | Brand named in final response text (standard SoV) |
| **Influence SoV** | Brand appeared in sub-queries during the model's research phase (invisible SoV) |

The gap between Influence SoV and Citation SoV reveals **conversion potential** — the brand is influencing the model's research but not making it into the final answer. This is the highest-leverage optimization target: the model already knows about the brand and is actively looking at it, but something about the content prevents citation.

---

## Competitive SoV Tracking

### Competitor Identification

Track competitors identified during:
- Scan (from fan-out simulation — which brands GPT-5.4 injects into sub-queries)
- Track (from actual AI responses — which brands appear alongside the client)
- User input (manually specified competitors)

### Competitive Metrics

For each competitor, track:

| Metric | Formula |
|---|---|
| Competitor SoV | `(competitor_mentions / total_mentions) × 100` |
| SoV Gap | `competitor_SoV - client_SoV` |
| Trend | Direction of gap over last 3+ runs |
| Dominant Prompt Type | Which prompt type the competitor dominates |

### Competitive Displacement

When a competitor's SoV increases while the client's decreases on the same prompt type, flag as a **competitive displacement event** in `flagged_actions`:

```json
{
  "type": "competitor_gain",
  "summary": "Competitor A gained +5% SoV on comparison prompts while client lost -3%",
  "related_prompt_type": "comparison",
  "competitor": "Competitor A"
}
```

---

## SoV Delta Interpretation

### Healthy Signals
- Aggregate SoV increasing across 3+ consecutive runs
- Citation SoV growing faster than Mention SoV (more actual links, not just name-drops)
- Influence SoV and Citation SoV converging (research is converting to citations)
- SoV growth on high-fanout prompt types (`technical_eval`, `discovery`)

### Warning Signals
- Aggregate SoV declining for 2+ runs
- Influence SoV high but Citation SoV low (brand is researched but not cited — content quality or structure issue)
- SoV growth only on `brand` prompts (vanity metric — real visibility is on category/comparison prompts)
- Competitor SoV growing faster than client on shared prompt types

### Flagged Actions

Track generates `flagged_actions` in the delta report when:

| Trigger | Action Type | Feed to Rank? |
|---|---|---|
| Citation lost on a previously stable prompt | `citation_loss` | Yes — may create or escalate an issue |
| SoV dropped >5% on a prompt type | `sov_drop` | Yes — triggers re-prioritization |
| Competitor gained >5% on a shared prompt | `competitor_gain` | Yes — may create a fanout issue |
| Influence SoV > Citation SoV by >20 points | `conversion_gap` | Yes — content quality or structure issue |
| New citation gained | `citation_opportunity` | No — positive signal, track only |

---

## Three Tracking Levels

SoV is tracked at three granularity levels:

### 1. Per-Prompt

For each tracked prompt, record:
- Did the brand appear in this response?
- Which competitors appeared?
- Was the brand cited (URL linked) or just mentioned?
- What position was the brand in any ranked list?

### 2. Per-Category

Aggregate mention rates within each GEO category (Organic, Competitor, How-to, Brand-Specific, FAQ) and each pipeline prompt type:

```
category_SoV = (brand_mentions_in_category / total_mentions_in_category) × 100
```

This reveals WHERE the brand is strong or weak. A brand might have 80% SoV on brand queries but 5% on organic queries.

### 3. Aggregate

Overall SoV across all prompts and providers:

```
aggregate_SoV = (total_brand_mentions / total_mentions_across_all_responses) × 100
```

---

## Competitive Metrics Shape

For each competitor tracked, maintain this data structure:

```json
{
  "name": "CompetitorX",
  "visibility": 45,
  "position": 2.3,
  "sentiment": "Positive",
  "mentions": 23,
  "isYou": false
}
```

| Field | Definition |
|---|---|
| `name` | Normalized competitor name |
| `visibility` | Mention rate % across all prompts |
| `position` | Average ranking in responses where listed (1 = first) |
| `sentiment` | Dominant sentiment (Positive, Neutral, Negative, Mixed) |
| `mentions` | Total mention count across all responses |
| `isYou` | Whether this entry represents the tracked brand |

---

## Time-Series Tracking

Daily aggregation into VisibilityDataPoint:

```json
{
  "date": "2026-03-26",
  "you": 62,
  "competitors": {
    "CompetitorA": 48,
    "CompetitorB": 31
  },
  "totalResponses": 280
}
```

This structure feeds the SoV Trend section in MORPHIQ-TRACKER.md and enables visualization of competitive positioning over time. Git commits on the tracker file provide the historical audit trail.
