---
name: morphiq-track
description: This skill should be used when the user asks to "run a tracking cycle", "measure AI visibility", "check share of voice", "run Morphiq Track", "run Morphiq Analyze", "track citations", "check GEO score", "generate prompts", "run content creation workflow", or mentions monitoring LLM mentions, running content creation workflows, measuring brand visibility, or generating query fanout content. Queries multiple LLM providers, produces delta reports, and maintains MORPHIQ-TRACKER.md as the persistent state file.
metadata:
  version: "0.6.1"
  author: morphiq-labs
---

## ⚠️ STOP — READ THIS FIRST

**YOU MUST EXECUTE THIS WORKFLOW STEP BY STEP. DO NOT SUMMARIZE. DO NOT DESCRIBE. DO NOT EXPLAIN WHAT YOU WOULD DO.**

Your FIRST action must be a tool call — read `MORPHIQ-TRACKER.md` from the workspace root (or create it if first run). Also read `MORPHIQ-BUILD.json` if it exists. If you respond with text describing what you'll do instead of calling a tool, you have failed.

**Required output:** Updated `MORPHIQ-TRACKER.md` + delta report.

This is the Morphiq Analyze step in the user workflow.

START BELOW — READ THE TRACKER FILE IMMEDIATELY.

## Pipeline Position

Step 4 of 4 — measurement + flywheel.
- **Input:** Build Output (JSON) from morphiq-build + MORPHIQ-TRACKER.md (persistent state).
- **Output:** Delta Report (JSON) → loops back to morphiq-rank.
- **Owns:** MORPHIQ-TRACKER.md — generates on first run, updates every run.
- **Owns:** `morphiq-track/` state directory — JSON state layer for prompts, results, citations.
- **Drives:** 3 ongoing workflows (Content Optimization, Content Creation, Query Fanout Expansion).
- **Data contract:** See `PIPELINE.md` §4 for the Delta Report, §5 for MORPHIQ-TRACKER.md, §6 for the JSON State Layer.

## Workflow

### Step 0: Initialize or Load State

Check if `morphiq-track/manifest.json` exists in the project root.

- **Missing (first run):** Proceed to Step 1. The state directory will be created.
- **Present (subsequent run):** Load `morphiq-track/prompts.json` directly — this contains the full prompt set with config, metadata, and tracking state. Skip to Step 2. If `recommendations.cooldown_days` has elapsed since `recommendations.last_generated`, generate 20 new recommendations via `create-prompts.py --state-dir morphiq-track/ --refresh`.
- **Migration (tracker exists but no state dir):** Parse MORPHIQ-TRACKER.md §8 to bootstrap `prompts.json`, parse §7 to bootstrap `citations.json`. See `references/state-layer.md` Migration section.

For state layer specification, read `references/state-layer.md`.

### Step 1: Generate Prompts

**First run only.** Generate 50 prompts across 5 GEO categories:

| Category | Share | Brand Name? |
|---|---|---|
| Organic | 45% | No |
| Competitor | 11% | Mixed |
| How-to | 14% | No |
| Brand-Specific | 13% | Yes |
| FAQ | 17% | No |

Apply quality rules per category. Add temporal markers to 70%+ prompts. Include entities in comparison/technical prompts.

Run `scripts/create-prompts.py --state-dir morphiq-track/ --brand {brand} --category {category} --competitors {competitors}`. This writes `morphiq-track/prompts.json` and initializes `morphiq-track/manifest.json`.

For taxonomy, fanout profiles, and generation rules, read `references/prompt-taxonomy.md`.

### Step 1.5: Validate API Keys — HARD GATE

Before querying providers, check for these environment variables:

- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `PERPLEXITY_API_KEY`
- `GEMINI_API_KEY`

**If any key is missing, STOP COMPLETELY and output this message (replacing the bracketed parts):**

> API keys required to run Morphiq Analyze. Missing: [list missing keys].
> Please set these environment variables and re-run:
> - OPENAI_API_KEY — from https://platform.openai.com/api-keys
> - ANTHROPIC_API_KEY — from https://console.anthropic.com/settings/keys
> - PERPLEXITY_API_KEY — from https://www.perplexity.ai/settings/api
> - GEMINI_API_KEY — from https://aistudio.google.com/app/apikey

**Do NOT proceed past this step without real keys. Do NOT simulate, estimate, or fabricate provider responses. Do NOT write placeholder data to any file. The tracking data must reflect real LLM behavior or it is worthless.**

### Step 2: Query AI Providers

Distribute prompts evenly across 4 providers. Execute using `scripts/run-queries.py --state-dir morphiq-track/ --mode execute`. This reads prompts from `morphiq-track/prompts.json`, writes versioned results to `morphiq-track/results/track-{date}.json`, and updates `morphiq-track/manifest.json`.

**DO NOT write a pipeline.js, pipeline.py, or any wrapper script to execute this step. DO NOT create any new script files. Use the existing scripts in `scripts/` directly, or call the provider APIs via your built-in web/fetch tools. If a script fails, debug it — do not rewrite it.**

| Provider | Model | Concurrency |
|---|---|---|
| OpenAI | gpt-4o | Full |
| Perplexity | sonar-pro | 2 concurrent |
| Anthropic | claude-sonnet-4-5-20250514 → claude-sonnet-4-20250514 | Serialized |
| Gemini | gemini-2.5-flash | 3 concurrent |

**Mandatory requirements for every query:**

1. **Full response text.** Store the complete response — never truncate. morphiq-build's content creation workflow requires the full text for analysis.
2. **Sub-query extraction.** For each provider that exposes tool calls, extract the search queries the model issued. These feed Workflow C (Query Fanout Expansion) and invisible SoV.
3. **Citation deduplication.** After collecting citations per response, strip UTM/tracking params from URLs and deduplicate. Track `citation_weight` (number of times each URL was cited).
4. **Retry on transient failure.** Retry once with 2-second delay before marking as error. This handles rate limits.

**Provider-specific requirements:**

- **OpenAI:** Iterate `response.output` for items with `type == "web_search_call"` — extract the `query` field into `sub_queries[]`. This reveals GPT's `site:` operator searches and two-phase research pattern.
- **Perplexity:** Citations are a Perplexity-specific field. Check `response.citations`, then `response.model_extra["citations"]`, then `response.__dict__["citations"]`, then `response.choices[0].message.model_extra["citations"]`. The OpenAI-compatible client puts unknown API fields in `model_extra`.
- **Anthropic:** Tool config must be `{"type": "web_search_20250305", "name": "web_search", "max_uses": 5}`. Try model `claude-sonnet-4-5-20250514` first, fall back to `claude-sonnet-4-20250514`. Response content blocks include `text` (final answer), `web_search_tool_result` (search results with URLs), and `server_tool_use` (the search call). Extract text only from `text` blocks; extract citations from both `text` block inline citations and `web_search_tool_result` block content.
- **Gemini:** Grounding metadata returns `vertexaisearch.cloud.google.com` redirect URLs. Follow the redirect to get the real URL. If redirect fails, use the `grounding_chunk.web.title` as fallback domain: `{url: proxy_url, title: title, resolved_domain: title}`.

For full provider config and response pipeline, read `references/provider-strategies.md`.
For selection rules and distribution, read `references/query-targets.md`.

### Step 3: Analyze Responses

5-step pipeline: extract raw response/citations/sub-queries → structured analysis (using the agent's reasoning capabilities) → brand mention validation (exact → TLD → LLM judge) → competitor filtering → entity normalization.

**Input requirements for analysis:** Each response must include the full response text, deduplicated citations with `citation_weight`, and extracted sub-queries. The analysis uses the `config` block from the prompts file for brand, domain, and competitors — never hardcoded values.

### Step 4: Compute GEO Score

```
GEO = mean(provider_scores)
Weighted GEO = (Organic × 0.45) + (Competitor × 0.22) + (How-to × 0.22) + (Brand × 0.11)
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

Compare against previous snapshot using `scripts/diff-results.py --state-dir morphiq-track/`. The script reads `manifest.json` to auto-resolve the current (`runs[0]`) and previous (`runs[1]`) results paths, and reads `morphiq-track/citations.json` for previous citation state. Flag changes >5 points. Generate flagged actions for regressions, losses, displacement, and conversion gaps.

For delta methodology, read `references/delta-scoring.md`.

### Step 7: Update State Layer and MORPHIQ-TRACKER.md

**State layer updates (JSON — source of truth for track-owned data):**
1. Rebuild `morphiq-track/citations.json` from current results + previous citation state (gained/lost/stable)
2. Update `morphiq-track/prompts.json` tracking fields (mentioned, cited, best_provider, runs_tracked, last_run)
3. Update `morphiq-track/manifest.json` `updated_at`

**Tracker updates (markdown — user-facing dashboard):**
Project state layer data into MORPHIQ-TRACKER.md sections 5-9 and 14 (SoV, SoV Trend, Citations, Prompts, Competitors, Run History). Update remaining sections (1-4, 10-13) per tracker-spec.md rules.

For tracker specification, read `references/tracker-spec.md`.
For state layer specification, read `references/state-layer.md`.

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

1. Run `scripts/analyze-fanout.py --state-dir morphiq-track/` with optional `--scan-report` for page inventory and simulated queries
2. Script extracts sub-queries from latest track results, merges with scan simulated queries (fills Perplexity/Gemini gap)
3. Compares against site page inventory to identify unanswered sub-queries
4. Extracts competitor citation sources for each unanswered sub-query
5. Generates content briefs prioritized by citation weight (`site:` 2x, citation-producing 1.5x, silent 0.5x)
6. Output feeds Delta Report `content_creation_queue` via `--fanout` flag on generate-report.py
7. Update MORPHIQ-TRACKER.md §12 (Query Fanout Coverage) and §13 (Content Creation Queue) with new entries

## Reference Files

| File | Purpose |
|---|---|
| `references/prompt-taxonomy.md` | Prompt types, GEO categories, fanout depth, generation rules |
| `references/share-of-voice.md` | SoV formulas, mention types, invisible SoV, competitive tracking |
| `references/provider-strategies.md` | Provider config, models, response analysis pipeline |
| `references/query-targets.md` | Provider selection, distribution, citation categories, GEO score |
| `references/delta-scoring.md` | Delta calculation, significance thresholds, flagged actions |
| `references/tracker-spec.md` | Full MORPHIQ-TRACKER.md specification (14 sections) |
| `references/state-layer.md` | JSON state layer: directory structure, file schemas, read/write rules, sync rules |
