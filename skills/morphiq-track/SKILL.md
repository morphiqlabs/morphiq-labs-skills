---
name: morphiq-track
description: >-
  Queries multiple LLM providers with generated prompts, computes GEO and Share of Voice scores, produces
  delta reports, and maintains MORPHIQ-TRACKER.md as the persistent state file. Use when the user asks to
  "run a tracking cycle", "measure AI visibility", "check share of voice", "run Morphiq Track",
  "run Morphiq Analyze", "track citations", "check GEO score", "generate prompts", "run content
  creation workflow", or mentions monitoring LLM mentions or measuring brand visibility.
license: Apache-2.0
metadata:
  version: "0.7.1"
  author: morphiq-labs
---

This skill runs one step only. Do not chain to any other skill.

Do not describe what you will do. Execute each step, show the result, then move to the next step. If a step fails, stop and report the error.

## Step 0: Validate API keys (do this first)

Run this command now to check which provider keys are set:

```
echo "OPENAI=$(if [ -n "$OPENAI_API_KEY" ]; then echo SET; else echo MISSING; fi) ANTHROPIC=$(if [ -n "$ANTHROPIC_API_KEY" ]; then echo SET; else echo MISSING; fi) PERPLEXITY=$(if [ -n "$PERPLEXITY_API_KEY" ]; then echo SET; else echo MISSING; fi) GEMINI=$(if [ -n "$GEMINI_API_KEY" ]; then echo SET; else echo MISSING; fi)"
```

Print which keys are present and which are missing. If ALL four are missing, stop here and tell the user:
> Set at least one API key: `export OPENAI_API_KEY=sk-...` (or ANTHROPIC_API_KEY, PERPLEXITY_API_KEY, GEMINI_API_KEY).

If at least one key is set, continue. Skip providers with missing keys.

Do not simulate, estimate, or fabricate provider responses. Tracking data must reflect real LLM behavior.

## Step 1: Load inputs

Read `MORPHIQ-BUILD.json` from the workspace root now. If missing, stop and tell the user to run Morphiq Build first.

Check if `morphiq-track/manifest.json` exists:
- **Missing (first run):** Continue to Step 2.
- **Present (subsequent run):** Load `morphiq-track/prompts.json`, skip to Step 3. If cooldown elapsed, generate 20 new prompts via `scripts/create-prompts.py --state-dir morphiq-track/ --refresh`.

Read `references/state-layer.md` before creating or updating any state files.

## Step 2: Generate prompts (first run only)

Generate 50 prompts across 5 GEO categories (Organic 45%, Competitor 11%, How-to 14%, Brand-Specific 13%, FAQ 17%).

Read `references/prompt-taxonomy.md` before generating — it defines taxonomy, fanout profiles, quality rules, and temporal markers.

Run `scripts/create-prompts.py --state-dir morphiq-track/ --brand {brand} --category {category} --competitors {competitors}`. If unavailable, generate prompts manually following the taxonomy.

You should now have a `morphiq-track/prompts.json` file with 50 prompts. If not, stop.

## Step 3: Query AI providers

Read `references/provider-strategies.md` before querying — it defines provider-specific response parsing, citation extraction, and sub-query extraction for each provider (OpenAI, Perplexity, Anthropic, Gemini).

Read `references/query-targets.md` before distributing prompts — it defines selection rules and distribution strategy.

Run `scripts/run-queries.py --state-dir morphiq-track/ --mode execute`. If unavailable, call provider APIs directly. Do not create wrapper scripts.

For every query: store full response text, extract sub-queries from tool calls, deduplicate citations (strip UTM params), retry once on transient failure.

You should now have response data for each prompt. If zero queries succeeded, stop and report the errors.

## Step 4: Analyze responses

5-step pipeline: extract raw response/citations/sub-queries → structured analysis → brand mention validation (exact → TLD → LLM judge) → competitor filtering → entity normalization.

Use the `config` block from `morphiq-track/prompts.json` for brand, domain, and competitors — never hardcode values.

## Step 5: Compute GEO score

Read `references/query-targets.md` for GEO methodology. Weighted GEO = (Organic × 0.45) + (Competitor × 0.22) + (How-to × 0.22) + (Brand × 0.11). Thresholds: ≥60 Excellent, ≥40 Good, ≥20 Fair, ≥10 Poor, <10 Very Poor.

## Step 6: Compute Share of Voice

Read `references/share-of-voice.md` before computing — it defines Mention SoV, Fanout-Weighted SoV, Influence SoV, and Conversion Gap formulas.

## Step 7: Compute deltas

Run `scripts/diff-results.py --state-dir morphiq-track/`. If unavailable, compare the two most recent result files manually. Flag changes >5 points.

Read `references/delta-scoring.md` before computing deltas.

## Step 8: Update state layer and tracker

Read `references/state-layer.md` before updating state files. Rebuild `citations.json`, update `prompts.json` tracking fields, update `manifest.json`.

Read `references/tracker-spec.md` before updating MORPHIQ-TRACKER.md — it defines all 14 sections of the user-facing dashboard.

Write files using your file-write tool, not shell heredoc or `cat`.

## Step 9: Produce delta report

Write `MORPHIQ-DELTA-REPORT.json` to workspace root using your file-write tool. Include: scores, deltas, citations, SoV breakdown.

## Three ongoing workflows

These workflows feed back into the pipeline on subsequent runs:

- **Workflow A (Content Optimization):** Identify pages with declining SoV or lost citations → feed to morphiq-build (existing content path) → re-track.
- **Workflow B (Content Creation):** Collect prompts where brand is absent, identify competitor citation sources → feed to morphiq-build (new content path).
- **Workflow C (Query Fanout Expansion):** Run `scripts/analyze-fanout.py --state-dir morphiq-track/` to extract sub-queries, compare against site inventory, generate content briefs. Update MORPHIQ-TRACKER.md §12–§13.

End with:

> **Tracking complete.** MORPHIQ-TRACKER.md and MORPHIQ-DELTA-REPORT.json updated.
> To re-optimize: type **"Run Morphiq Rank"** to reprioritize based on new data.
