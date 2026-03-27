# Query Fanout — Simulation Framework

Use this reference during the query fanout evaluation in a morphiq-scan audit. This document defines how AI models decompose user prompts into sub-queries, how to simulate that decomposition for a given domain, and how to score coverage against the 10-point fanout rubric.

## Core Concept

AI models do not simply search for the exact text a user types. When processing a query that requires web research, models decompose the prompt into multiple sub-queries — a process called **query fan-out** — and research the topic across multiple angles before synthesizing an answer.

A single user prompt like "best corporate cards for startups 2026" can trigger 5–14 sub-queries across landscape scans, per-entity deep dives, pricing lookups, and review aggregation. If the audited site has no content answering a sub-query, that gap becomes a citation suppression point — the model cites a competitor instead.

Scan's job is to simulate this fan-out for the audited domain and check whether the site can answer each sub-query.

---

## Per-Model Simulation Rules

Each major AI model has a distinct search architecture. Simulate fan-out using the model-specific rules below.

### GPT-5.4 — Two-Phase Research Agent

**Strategy:** Broad landscape scan followed by per-entity `site:` verification.

**Signature behaviors:**
- Operates in two phases: 1–3 broad keyword queries, then targeted `site:domain.com` deep dives
- Appends "official docs" or "official" to ~85% of sub-queries
- Uses `site:` operator in ~46% of all sub-queries to target specific company websites
- Injects brand names preemptively — even when the user prompt mentions no brands, GPT-5.4 adds known competitors to its searches
- Produces the longest, most keyword-dense sub-queries (avg 69 chars, ~10 words)
- Adds temporal markers ("2026", "latest") to ~74% of queries
- Triggers web search 92% of the time; the 8% that skips search are generic/timeless queries without temporal markers

**Simulation rule:** For each topic the site covers, generate:
1. One broad landscape query with the topic + year + "official"
2. One `site:domain.com` query per key product/page on the audited site
3. One per-competitor `site:` query for the top 2–3 competitors

**Critical implication:** GPT-5.4 will literally search `site:theauditedsitehere.com [topic]`. If the site has no page matching that query, it is an explicit, observable gap.

### Claude — Focused Searcher

**Strategy:** Minimal, targeted queries with high citation density per search.

**Signature behaviors:**
- Maximum 3 search calls per prompt, regardless of complexity
- Returns ~10 citations per search call — remarkably consistent
- Strips natural language to clean keyword extractions (avg 48 chars, ~7 words)
- Never uses `site:` operator — relies on general search quality
- Adds year markers to ~85% of queries
- Bundles comparison queries as a single search ("A vs B vs C [use case] [year]") rather than splitting per entity
- Uniquely issues contextual queries based on business intelligence (e.g., surfacing a relevant acquisition event rather than mechanically searching per entity)

**Simulation rule:** For each topic, generate:
1. One bundled keyword query covering the main topic + entities + year
2. One contextual query if there are relevant industry events or news

**Critical implication:** Claude's low fan-out but high citation density means each search is high-stakes. If the site does not rank well for the single bundled query, it may not appear at all — there are no follow-up deep dives to catch it.

### Gemini 2.5 Flash — Systematic Enumerator

**Strategy:** Exhaustive per-entity x per-angle enumeration.

**Signature behaviors:**
- Produces the highest fan-out on comparison queries (up to 14 sub-queries)
- Decomposes into a per-entity x per-angle matrix: features, reviews, pricing, alternatives for each entity
- Uses short, natural-language queries (avg 43 chars, ~6.4 words) — the most human-readable
- Never uses `site:` or quote operators
- Generates the highest citation volume (avg 20.6 citations per prompt — 3x GPT-5.4)
- Uniquely issues "what is X" concept clarification queries before answering
- Uniquely searches "[Brand] alternatives [year]" for every entity in a comparison

**Simulation rule:** For each topic involving multiple entities, generate:
1. One broad comparison query
2. One per-entity features query
3. One per-entity review query
4. One per-entity pricing query
5. One per-entity "alternatives" query
6. One "best [category] [year]" query

**Critical implication:** Gemini's "alternatives" searches mean competitor alternative-to pages can capture Gemini traffic. The audited site needs "alternative to [competitor]" content to defend against this.

### Perplexity Sonar Pro — Black Box

**Strategy:** Completely opaque search — zero visible fan-out.

**Signature behaviors:**
- Exposes no sub-queries in its API response
- Always produces citations (avg 7.5 per query, consistent across all prompt types)
- Fastest responses (5–8 seconds vs 20–60s for other models)
- Fan-out behavior can only be inferred from citation patterns, not observed directly

**Simulation rule:** Perplexity cannot be directly simulated via sub-query generation. Instead, evaluate coverage by checking whether the site appears in Perplexity citations for tracked prompts (handled by morphiq-track's measurement loop, not by Scan's simulation).

**Critical implication:** For Perplexity, citation optimization matters more than query coverage — optimize to be cited rather than predicting what it will search.

---

## Fan-out by Prompt Type

Prompt type determines fan-out depth. Use these averages to estimate how many sub-queries a topic will generate:

| Prompt Type | GPT-5.4 Avg | Claude Avg | Gemini Avg | Visibility Surface |
|---|---|---|---|---|
| `technical_eval` | 11.0 | 2.0 | 8.0 | Highest — per-platform verification |
| `discovery` | 7.5 | 2.0 | 5.5 | High — landscape building |
| `recommendation` | 5.8 | 1.0 | 5.5 | Medium-high — alternatives exploration |
| `comparison` | 5.4 | 1.7 | 9.3 | Medium-high — per-entity decomposition |
| `problem_seeking` | 2.8 | 1.0 | 3.5 | Medium — solution landscape |
| `use_case` | 2.4 | N/A | N/A | Lower — focused lookup |

**Key pattern:** Technical evaluation and discovery prompts produce 3–5x more sub-queries than use-case prompts. A gap in a high-fanout prompt type suppresses more citations than the same gap in a low-fanout type.

---

## Page-Type → Fan-out Mapping

When Scan evaluates a page, the page type determines what sub-queries models would chain from that page's topic:

| Page Type | GPT-5.4 Avg (Max) | Claude Avg | Gemini Avg | Sub-queries Triggered |
|---|---|---|---|---|
| Blog post | 4.5 (9) | 3.0 | 6.0 | Temporal verification, technical depth, competing content |
| Homepage | 2.5 (4) | 2.0 | 6.0 | Identity queries, competitor comparisons |
| Pricing page | 2.0 (3) | 1.5 | 4.0 | Per-competitor pricing lookups |
| Product page | 2.5 (3) | 2.0 | 3.0 | Feature decomposition, per-feature searches |
| Docs page | 3.0 (4) | N/A | N/A | Implementation step verification |

**Key patterns:**
- **Blog posts** trigger the deepest fan-out across all models — models verify freshness, check competing content, and validate technical claims
- **Pricing pages** trigger focused per-competitor lookups (each competitor's pricing searched separately)
- **Homepage queries** trigger identity + comparison sub-queries ("what does X do" + "X vs Y")
- **Product pages** trigger feature decomposition (each capability searched individually)

---

## The Two-Phase Search Pattern (GPT-5.4)

GPT-5.4 consistently follows a two-phase research strategy critical to understand for Scan:

### Phase 1: Broad Landscape Scan

The model issues 1–3 broad queries to map the solution space. These queries are keyword-dense with brand names, features, and year markers:
```
"best corporate cards startups automated expense tracking 2026 official Ramp Brex Airbase BILL Spend docs pricing features"
```

### Phase 2: Targeted Deep Dives

The model then issues `site:domain.com` queries to verify claims on specific company websites:
```
site:ramp.com pricing corporate card expense management Ramp pricing 2026
site:bill.com Divvy pricing expense management corporate card official 2026
```

This is where the gap becomes explicit — if the model searches `site:theauditedsitehere.com pricing` and finds nothing, it pulls pricing data from wherever else it can find it.

**Scan must simulate both phases** to produce accurate coverage scoring.

---

## Citation-Producing vs. Silent Sub-Queries

Not all fan-out sub-queries produce visible citations. Scan must distinguish between the two when scoring coverage.

### Citation-producing sub-queries (weight: 1.5x)

These sub-queries, when answered, result in the site being cited in the model's response:

| Scenario | Details |
|---|---|
| Time-sensitive queries with year markers | All models search and cite for temporal queries |
| Comparison queries ("A vs B") | Entities' official sites get cited |
| Brand-specific queries | Brand website + review sites cited |
| "Best X for Y" recommendations | Listicle and review sites cited |
| Pricing and features lookups | Direct source pages cited |

### Silent sub-queries (weight: 0.5x)

These sub-queries inform the model's synthesis but may not produce a visible citation:

| Scenario | Details |
|---|---|
| Generic "how to" without temporal markers | Models may skip search or synthesize without citing |
| Broad or ambiguous queries | Models answer from parametric knowledge |
| `site:` deep dives (GPT-5.4) | Informs the answer but often synthesized rather than cited verbatim |
| "Official docs" queries (GPT-5.4) | Model pulls facts from docs but synthesizes them into its own phrasing |

### `site:` operator queries (weight: 2x)

When GPT-5.4 searches `site:theauditedsitehere.com [topic]` and finds nothing, this is the most critical gap type. The model explicitly looked for content on the audited site and came up empty. These count 2x in coverage scoring.

**Critical finding:** GPT-5.4's pattern of adding "official docs" to queries means it pulls from documentation but often synthesizes rather than citing verbatim. Pages optimized for clear, extractable facts are more likely to survive this synthesis and still get cited.

---

## Coverage Scoring — 10-Point Rubric

### Simulation Procedure

For each audited domain:

1. **Identify the site's core topics** from page content, headings, and metadata
2. **Generate simulated sub-queries** per topic using the per-model rules above (use GPT-5.4 as the primary baseline; use Gemini as a secondary check for comparison topics)
3. **Check site coverage** — for each sub-query, determine whether the site has a page that answers it
4. **Apply citation weights** — citation-producing sub-queries count 1.5x, silent sub-queries count 0.5x, `site:` queries count 2x
5. **Calculate weighted coverage** — `(weighted answered / weighted total) × 10`

### Scoring Tiers

| Score | Coverage | Meaning |
|---|---|---|
| 9–10 | 90%+ | Site answers nearly every sub-query models would chain |
| 7–8 | 70–80% | Most sub-queries covered, some gaps in adjacent topics |
| 5–6 | 50–60% | Core topic covered but half of related sub-queries unanswered |
| 3–4 | 30–40% | Significant content gaps — models cannot verify claims from this site |
| 1–2 | 10–20% | Minimal coverage — most sub-queries land on competitor sites |
| 0 | 0% | No relevant content for any simulated sub-query |

### "No Search" Threshold

When a prompt is generic/timeless AND the model has high confidence in the solution space, it skips web search entirely and answers from parametric knowledge. Adding temporal markers ("2026") or specific brand names triggers search. Pages without temporal signals in their content may not even enter the fan-out evaluation.

---

## Issue ID Pattern

Issue IDs for fan-out coverage problems follow the pattern: `fanout-{specific-problem}`

Examples:
- `fanout-no-comparison-content` — No content addressing competitor comparison queries
- `fanout-no-pricing-content` — No structured pricing content for pricing sub-queries
- `fanout-unanswered-subquery` — Specific sub-query has no matching page
- `fanout-wrong-page-type` — Sub-query answered on wrong page type (e.g., pricing info buried in a blog post instead of a dedicated pricing page)
- `fanout-no-alternative-content` — No "alternative to [competitor]" content (Gemini exposure)
- `fanout-missing-entity-coverage` — Comparison page mentions entity but no dedicated entity content exists
- `fanout-no-site-match` — GPT-5.4 `site:` query returns no relevant page
- `fanout-stale-temporal` — Content lacks temporal markers, reducing search trigger probability
- `fanout-thin-topic-coverage` — Topic is covered superficially; deeper sub-queries go unanswered
- `fanout-no-docs-content` — No documentation or how-to content for implementation sub-queries

For full severity logic and trigger conditions per issue type, read `morphiq-rank/references/issue-catalog.md`.

---

## Audit Heuristics

Use these quick tests during the fan-out evaluation:

### Sub-query coverage test
For the site's top 5 topics, generate the expected fan-out sub-queries. Can the site answer at least 70% of them?

### `site:` simulation test
Search `site:domain.com [core topic]` for each key product. Does a relevant page appear?

### Competitor parity test
For the top 3 competitors, does the site have content that would surface in comparison queries? Gemini always searches "[Brand] alternatives" — check whether the site has alternative-to content.

### Page-type alignment test
Are answers on the right page type? Pricing info should be on a pricing page (not a blog post), feature details on a product page (not the homepage).

### Temporal freshness test
Do key pages include year markers and recent dates? Pages without temporal signals may not enter GPT-5.4's fan-out at all.

### Comparison decomposition test
For topics involving the audited brand vs. competitors, does the site have dedicated content for each entity? All models decompose comparisons per-entity — missing entity coverage means missing from the comparison response.
