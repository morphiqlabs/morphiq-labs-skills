# Provider Strategies — Multi-Provider Query Architecture

Use this reference when morphiq-track configures and executes queries against AI providers. This document defines the per-provider model, search tool, geo targeting, concurrency strategy, and the response analysis pipeline.

## Provider Configuration

| Provider | Model | Search Tool | Geo Targeting | Concurrency |
|---|---|---|---|---|
| OpenAI | gpt-4o | `web_search` (search_context_size: high) | `user_location` param | Full concurrency |
| Perplexity | sonar-pro | Native search | `web_search_options` + language filter | 2 concurrent |
| Anthropic | claude-sonnet-4-5 | `web_search_20250305` | `user_location` param | Serialized (token quota) |
| Gemini | gemini-3-flash-preview → 2.5-flash → 2.5-flash-lite | `googleSearch` tool | BrightData residential proxy (no native geo) | 3 concurrent |

---

## Provider-Specific Notes

### OpenAI (GPT-4o / GPT-5.4 behavior)

- Highest fanout model (avg 4.92 sub-queries per prompt)
- Responses API exposes all `web_search` tool calls — full sub-query visibility
- `search_context_size: high` ensures comprehensive search behavior
- Uses `site:` operator queries in ~46% of searches
- Two-phase search pattern: broad landscape scan → targeted `site:domain.com` deep dives
- 85% of queries append "official" to `site:` searches
- 92% trigger web search with temporal markers

### Perplexity (Sonar Pro)

- Opaque search architecture — no visible sub-queries
- Native search integration (no tool calling)
- Avg 7.5 citations per response
- Rate limited to 2 concurrent requests
- `web_search_options` allows specifying search recency and domain filters

### Anthropic (Claude)

- Most efficient searcher — avg 1.7 sub-queries per prompt
- Max 3 searches per response, ~10 citations per search
- No `site:` operator usage
- Bundles comparisons into single queries
- Serialized due to token quota limits — run one at a time
- Tool use results expose search queries when web search tools are active

### Gemini (Flash models)

- Systematic enumerator — avg 6.5 sub-queries per prompt
- Up to 14 sub-queries on comparison prompts
- Per-entity × per-angle matrix decomposition
- Searches "[Brand] alternatives" pattern
- No native geo targeting — use BrightData residential proxy for location-specific results
- Model fallback chain: gemini-3-flash-preview → 2.5-flash → 2.5-flash-lite
- Grounding metadata may expose search queries in some API configurations

---

## Prompt Distribution

Prompts are split evenly across providers. Each provider tests a subset, not all prompts:

```
per_provider_count = ceil(total_prompts / active_provider_count)
```

For prompt category distribution and generation rules, refer to `prompt-taxonomy.md`.
For which providers to query and when, refer to `query-targets.md`.

---

## Response Analysis Pipeline

Each AI response goes through a 5-step analysis pipeline:

### Step 1: Raw Response Extraction

Extract from each provider's API response:
- Response text (the AI's answer)
- Citations and source URLs (provider-specific format)
- Sub-queries / tool calls (when available)

### Step 2: GPT-5.2 JSON Analysis

Pass each response through GPT-5.2 for structured extraction:

```json
{
  "brand_mentioned": true,
  "brand_position": 2,
  "competitors_mentioned": ["Competitor A", "Competitor B"],
  "sentiment": "Positive",
  "confidence": "high"
}
```

Fields:
- `brand_mentioned` — whether the tracked brand appears in the response
- `brand_position` — position in any ranked list (1 = first mentioned)
- `competitors_mentioned` — other brands that appear
- `sentiment` — Positive, Neutral, Negative, or Mixed
- `confidence` — analysis confidence level

### Step 3: Brand Mention Validation

Multi-layer validation to handle ambiguous brand names:

1. **Exact match** — direct string match of brand name in response text
2. **TLD-stripped variants** — match domain without TLD (e.g., "example" for "example.com")
3. **LLM judge** — for ambiguous names (e.g., "Scale" could be ScaleAI or the word "scale"), use an LLM call to disambiguate in context

Default to "not mentioned" when ambiguous — false negatives are safer than false positives.

### Step 4: Competitor Filtering

Clean the competitor list:
- Remove generic terms ("AI", "machine learning", "analytics")
- Remove category descriptors ("leading platform", "enterprise solution")
- Remove the brand itself if it appears in competitor list
- Keep only actual company/product names

### Step 5: Entity Normalization

Single LLM call to deduplicate competitor aliases across all providers:

```
Input:  ["OpenAI", "Open AI", "ChatGPT", "GPT-4", "Anthropic", "Claude"]
Output: {"OpenAI": ["OpenAI", "Open AI", "ChatGPT", "GPT-4"], "Anthropic": ["Anthropic", "Claude"]}
```

This ensures consistent competitor tracking across providers where different models may use different names for the same entity.

---

## Error Handling

| Scenario | Behavior |
|---|---|
| Provider API timeout | Retry once, then mark prompt as failed for that provider |
| Rate limit hit | Back off with exponential delay, respect provider limits |
| Model returns empty response | Log as failed, do not count toward SoV |
| Citation URL is unreachable | Still record the citation (URL validity is not SoV's concern) |
| Brand validation ambiguous | Default to "not mentioned" — false negatives safer than false positives |

---

## Citation Extraction

Citations extracted from AI responses are categorized into 11 types. For the full citation category definitions and frequency calculation, refer to `query-targets.md`.
