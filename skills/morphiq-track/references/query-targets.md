# Query Targets — Provider Distribution & Citation Tracking

Use this reference when morphiq-track determines which AI systems to query, how to distribute prompts, and how to categorize extracted citations.

## Which Providers to Query

### Active Providers

| Provider | Model | When to Include |
|---|---|---|
| OpenAI | gpt-4o | Always — highest fanout, most visibility signal |
| Gemini | gemini-3-flash-preview | Always — systematic enumerator, alternative exploration |
| Perplexity | sonar-pro | Always — opaque but high citation density |
| Anthropic | claude-sonnet-4-5 | Always — efficient, but serialized due to token quota |

### Provider Selection Rules

- **Initial analysis (onboarding):** Query all 4 providers
- **Ongoing tracking:** Query all 4 providers per run
- **Budget-constrained runs:** Prioritize OpenAI + Gemini (highest combined fanout signal), add Perplexity, then Anthropic

For per-provider configuration, model details, and the response analysis pipeline, refer to `provider-strategies.md`.

---

## Prompt Distribution

### Distribution Strategy

Prompts are split evenly across providers. Each provider receives a subset:

```
per_provider_count = ceil(total_prompts / active_provider_count)
```

### Initial Analysis (Onboarding)

50 prompts total, distributed across 5 GEO categories:

| Category | Share | Count | Brand Name? | What It Tests |
|---|---|---|---|---|
| Organic | 45% | ~23 | No | Unprompted discovery — does AI recommend without being asked? |
| Competitor | 11% | ~6 | Mixed | Competitive positioning — "alternatives to X" |
| How-to Guides | 14% | ~7 | No | Solution discovery — tool-seeking problem queries |
| Brand-Specific | 13% | ~7 | Yes | Direct brand knowledge — does AI know who you are? |
| FAQ | 17% | ~9 | No | Educational/learning context — "how/what/why" queries |

### Quality Rules Per GEO Category

| Category | Rules |
|---|---|
| **Organic** | <120 chars, concise (<20 words), 10–35% start with "Best", must express buying/evaluation intent |
| **Competitor** | 70% discovery ("alternatives to X"), 30% direct comparison ("[Brand] vs X") — NEVER "Competitor A vs Competitor B" without brand |
| **How-to** | Must include tool-seeking phrase ("what tools help with this?", "what platforms do people recommend?") |
| **FAQ** | Must start with question word (How, What, Why, Can, Is, Does, Which) |
| **Brand-Specific** | Must contain brand name |

### Ongoing Recommendations

20 additional prompts per recommendation cycle via market research pipeline:

1. Extract brand context from profile
2. Generate seed queries per category
3. Expand via search suggestion APIs
4. Relevance validation via LLM
5. Search volume lookup
6. Deduplication (70%+ word overlap = duplicate)
7. Competitor round-robin diversity enforcement
8. 7-day cooldown between runs

### GEO Categories → Pipeline Prompt Types

The 5 GEO categories map to the 9 pipeline prompt types used in MORPHIQ-TRACKER.md:

| GEO Category | Pipeline Prompt Types |
|---|---|
| Organic | `category`, `discovery`, `recommendation` |
| Competitor | `comparison` |
| How-to | `use_case`, `problem_seeking` |
| Brand-Specific | `brand` |
| FAQ | `use_case`, `problem_seeking` |

For the full prompt type taxonomy, fanout depth profiles, and generation rules, refer to `prompt-taxonomy.md`.

---

## GEO Score Calculation

The GEO Score (AI Visibility, 0–100%) is calculated from provider mention rates:

```
provider_score = (prompts_where_brand_mentioned / total_prompts_for_provider) × 100
GEO_score = mean(all_provider_scores)
```

This is a separate scoring system from the Technical Score. For the relationship between the two, refer to `scoring-rubric.md`.

### GEO Score Thresholds

| Score | Rating | Color |
|---|---|---|
| ≥ 60 | Excellent | Green |
| ≥ 40 | Good | Blue |
| ≥ 20 | Fair | Yellow |
| ≥ 10 | Poor | Orange |
| < 10 | Very Poor | Red |

### Intent-Weighted GEO Score

Beyond the simple average, a weighted score values different discovery intents:

```
Weighted GEO = (Organic × 0.45) + (Competitor × 0.22) + (How-to × 0.22) + (Brand × 0.11)
```

- **Organic at 45%:** Unprompted discovery — highest value signal
- **Competitor at 22%:** Head-to-head competitive positioning
- **How-to at 22%:** Solution recommendation context
- **Brand-Specific at 11%:** Sanity check — expected to be high for any real brand

FAQ category excluded from weighted score (uses standard average only).

---

## Citation Extraction

### What Citations Are

Citations are URLs that appear in AI responses as sources. They are extracted from provider-specific response formats but NOT used for the GEO score itself — they serve as evidence and insight.

### Citation Frequency

```
citation_frequency = (responses_containing_citation / total_responses) × 100
```

Tracked per citation source and per category.

---

## Citation Categories (11 Types)

| Category | Pattern Examples |
|---|---|
| Wiki | Wikipedia, WikiHow, `/wiki/` paths |
| Forum | StackOverflow, Reddit, Quora, Discourse |
| Video | YouTube, Vimeo, TikTok |
| Social | Twitter/X, LinkedIn, Facebook, Mastodon, Bluesky |
| Review | Trustpilot, G2, ProductHunt, AlternativeTo |
| Academic | .edu, ArXiv, PubMed, IEEE, Nature |
| Documentation | `/docs`, `/api/`, ReadTheDocs, GitBook |
| News | TechCrunch, TheVerge, Reuters, Forbes, WSJ |
| Listicle | G2, Capterra, `/best-`, `-alternatives`, `-vs-` |
| Blog | Medium, Substack, Dev.to, `/blog` paths |
| Product | `/product`, `/pricing`, `/features`, root domains |

### Category Detection

Match citation URLs against category patterns in priority order:
1. Domain-based matching (e.g., `reddit.com` → Forum)
2. Path-based matching (e.g., `/blog` → Blog, `/docs` → Documentation)
3. TLD-based matching (e.g., `.edu` → Academic)

A single URL matches the first category it qualifies for.

### Citation Analysis Value

| Insight | What It Means |
|---|---|
| High Wiki citations | Brand has Wikipedia presence — strong authority signal |
| High Forum citations | User-generated content drives visibility — community strategy |
| High Review citations | Review sites shape AI recommendations — review management matters |
| High Documentation citations | Technical docs are discoverable — developer audience |
| Low Product citations | Brand's own pages rarely cited — content optimization needed |
| High Listicle citations | Third-party comparison sites dominate — may need owned comparison content |
