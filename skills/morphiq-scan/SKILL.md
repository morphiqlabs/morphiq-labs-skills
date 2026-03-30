---
name: morphiq-scan
description: Audit a website for AI visibility. Scan a domain, check AI readiness, evaluate LLM citation quality. Scores across 5 categories on a 100-point rubric and produces a detailed scan report JSON.
argument-hint: <url>
allowed-tools: WebFetch, Read, Write, Grep, Glob, Bash
metadata:
  version: "0.3.0"
  author: morphiq-labs
---

## EXECUTION INSTRUCTIONS

You are now executing Morphiq Scan. This is a WORKFLOW — you must perform each step below by fetching real URLs, analyzing real content, and computing real scores. Do NOT just describe what the skill does. Do NOT print help text. EXECUTE the steps.

**Input:** The user provides a domain URL. Extract it from their message.
**Output:** You MUST write a Scan Report JSON file to **`MORPHIQ-SCAN.json`** (exactly this filename, with hyphens not underscores) in the workspace root AND display a human-readable summary.

### HARD RULES — VALIDATE BEFORE WRITING OUTPUT

1. **Output filename:** `MORPHIQ-SCAN.json` — NOT `MORPHIQ_SCAN_REPORT.json`, NOT `morphiq-scan.json`, NOT any other variation.
2. **Issue IDs are a closed set.** You MUST only use IDs from the catalog in Step 8. If an ID is not in that table, it is INVALID. Do NOT generate descriptive IDs like `policy-llms-txt-missing` or `agentic-readiness-thin-schema`. The correct IDs are `policy-no-llms-txt` and `agentic-missing-product-schema`. Before writing the JSON, validate every issue ID against the table.
3. **Field names are exact.** Use `scores` not `category_scores`. Use `scores_max` not `max_scores`. Use `schema_detected` not `schemas_found`. See the JSON template in Step 9.

## Pipeline Position

Step 1 of 4 — entry point.
- **Input:** A domain URL from the user.
- **Output:** Scan Report JSON file (`MORPHIQ-SCAN.json`) → consumed by morphiq-rank.
- **Data contract:** See `PIPELINE.md` §1 for the Scan Report schema.

## Purpose

Morphiq Scan audits a website's readiness for AI visibility. It answers two questions: "Can AI systems parse and understand this site?" (Technical Score) and "Where are the gaps preventing AI citations?" (issue identification). The output feeds morphiq-rank for prioritization.

## Workflow

### Step 1: Discover Pages

DO THIS NOW — fetch these URLs using your web/fetch tool:

1. Fetch `{domain}/robots.txt` — extract sitemap URLs
2. Fetch `{domain}/sitemap.xml` if not found in robots.txt
3. Classify discovered pages by type using URL pattern matching
4. Select up to 10 marketing-relevant pages, prioritized:
   home → pricing → features → product → solutions → about → blog → other → documentation
5. Exclude non-marketing pages from scoring (contact, login, signup, legal, demo, careers, changelog)

For page type classification and URL patterns, read `references/page-type-rules.md`.

### Step 2: Audit Policy Files (Category 5 — Domain Level)

1. **robots.txt** — Validate existence, format, AI crawler access (GPTBot, Google-Extended, Anthropic-AI, PerplexityBot)
2. **llms.txt** — Validate existence and quality (≥500 chars = good, <500 = thin)
3. **llms-full.txt** — Check existence
4. **sitemap.xml** — Validate XML structure

Score on 10-point scale. Generate issues for findings.

For detection rules and scoring, read `references/policy-files.md`.

### Step 3: Score Each Page — Per-Page Technical Score (0–100)

For each selected page, compute across four dimensions:

| Dimension | Points | Sub-checks |
|---|---|---|
| Schema | 40 | J1 (present), J2a (valid structure), J2b (required properties), J3 (relevant type), J4 (coverage) |
| Metadata | 30 | M1 (title), M2 (description), M3 (canonical), M4 (OG), M5 (Twitter) |
| FAQ | 20 | Linear scale: 0 FAQs=0, 1=5, 2=10, 3=15, 4+=20 |
| Content | 10 | C1 (word count ≥300), C2 (≥3 paragraphs) |

For sub-check methodology, read `references/agentic-readiness.md`.

### Step 4: Score Content Quality (Category 2 — Per Page, 20 pts)

Evaluate citation-readiness: title clarity (3), TL;DR placement (4), E-E-A-T signals (6), statistics & citations (5), real examples (2).

For criteria, read `references/content-quality.md`.

### Step 5: Score Chunking & Retrieval (Category 3 — Per Page, 15 pts)

Evaluate LLM retrieval optimization: heading hierarchy (3), section scope (3), paragraph self-containment (2.25), answer-first openings (2.25), vocabulary/lists/FAQ/summary (4.5).

For criteria, read `references/chunking-retrieval.md`.

### Step 6: Simulate Query Fanout (Category 4 — Domain Level, 10 pts)

1. Identify core topics from page content
2. Generate simulated sub-queries using per-model rules (GPT-5.4 two-phase, Claude bundled, Gemini systematic)
3. Check site coverage per sub-query
4. Apply citation weights (citation-producing 1.5x, silent 0.5x, `site:` 2x)
5. Score: `(weighted answered / weighted total) × 10`

For simulation rules and coverage scoring, read `references/query-fanout.md`.

### Step 7: Compute Aggregate Score (0–100)

```
overall = agentic_readiness(45) + content_quality(20) + chunking_retrieval(15) + query_fanout(10) + policy_files(10)
```

Categories 1–3 averaged across pages then scaled. Categories 4–5 are domain-level.

For the full rubric, read `references/scoring-rubric.md`.

### Step 8: Generate Issues

For every finding, create an issue. Use EXACT issue IDs from the catalog below. Do NOT invent IDs — every issue ID you emit must appear in this table.

**Issue ID Quick Reference** (use exactly these IDs):

| Category | Valid Issue IDs |
|---|---|
| `policy_files` | `policy-no-llms-txt`, `policy-weak-llms-txt`, `policy-blocks-gptbot`, `policy-blocks-google-extended`, `policy-blocks-anthropic`, `policy-blocks-perplexity`, `policy-no-robots-txt`, `policy-invalid-robots-syntax` |
| `agentic_readiness` | `agentic-missing-product-schema`, `agentic-missing-article-schema`, `agentic-missing-faq-schema`, `agentic-missing-howto-schema`, `agentic-missing-breadcrumb`, `agentic-no-canonical`, `agentic-broken-heading-hierarchy`, `agentic-weak-meta-description`, `agentic-missing-og-tags`, `agentic-no-semantic-html`, `agentic-duplicate-schema` |
| `content_quality` | `content-thin-page`, `content-low-word-count`, `content-no-tldr`, `content-no-author`, `content-unsourced-stats`, `content-wrong-citation-format`, `content-no-expert-quotes`, `content-stale-date`, `content-thin-faq`, `content-no-examples`, `content-generic-advice` |
| `chunking_retrieval` | `chunking-broken-heading-hierarchy`, `chunking-generic-headings`, `chunking-overscoped-section`, `chunking-buried-answer`, `chunking-long-paragraphs`, `chunking-no-faq-coverage`, `chunking-no-top-summary`, `chunking-missing-query-terms` |
| `query_fanout` | `fanout-no-comparison-content`, `fanout-no-pricing-content`, `fanout-no-alternative-content`, `fanout-missing-entity-coverage`, `fanout-wrong-page-type`, `fanout-no-site-match`, `fanout-unanswered-subquery`, `fanout-thin-topic-coverage`, `fanout-no-docs-content` |

Each issue MUST have: `id`, `category`, `severity`, `summary`, `detail`, `affected_element` (or null), `remediation_hint`.

**Thoroughness check:** A site scoring 60/100 typically has 15–25 issues. If you found fewer than 10, you missed checks. Go back and re-evaluate each page against ALL issue types in the catalog.

### Step 9: Produce Scan Report

Write the Scan Report as JSON to `MORPHIQ-SCAN.json` in the workspace root. The JSON MUST use the **exact field names and structure** shown below. Do NOT rename, flatten, or restructure fields.

```json
{
  "schema_version": "1.0",
  "generated_at": "ISO-8601 timestamp",
  "domain": "example.com",
  "pages_scanned": 10,
  "overall_score": 62,
  "scores": {
    "agentic_readiness": 26,
    "content_quality": 14,
    "chunking_retrieval": 10,
    "query_fanout": 6,
    "policy_files": 6
  },
  "scores_max": {
    "agentic_readiness": 45,
    "content_quality": 20,
    "chunking_retrieval": 15,
    "query_fanout": 10,
    "policy_files": 10
  },
  "pages": [
    {
      "url": "https://example.com/product",
      "page_type": "product",
      "title": "Page Title",
      "score": 58,
      "issues": [
        {
          "id": "agentic-missing-product-schema",
          "category": "agentic_readiness",
          "severity": "high",
          "summary": "No Product schema detected",
          "detail": "Full explanation of AI visibility impact",
          "affected_element": null,
          "remediation_hint": "Actionable fix instruction"
        }
      ],
      "schema_detected": ["Organization"],
      "schema_missing": ["Product", "FAQPage", "BreadcrumbList"],
      "meta": {
        "title_length": 42,
        "description_length": 148,
        "og_image": true,
        "canonical": "https://example.com/product",
        "h1_count": 1,
        "heading_hierarchy_valid": true,
        "word_count": 620
      }
    }
  ],
  "policy_files": {
    "robots_txt": {
      "exists": true,
      "allows_ai_crawlers": false,
      "blocked_agents": ["GPTBot", "Google-Extended"],
      "issues": [
        {
          "id": "policy-blocks-gptbot",
          "category": "policy_files",
          "severity": "high",
          "summary": "robots.txt blocks GPTBot",
          "detail": "Explanation",
          "remediation_hint": "Fix instruction"
        }
      ]
    },
    "llms_txt": {
      "exists": false,
      "valid": false,
      "issues": [
        {
          "id": "policy-no-llms-txt",
          "category": "policy_files",
          "severity": "high",
          "summary": "No llms.txt file found",
          "detail": "Explanation",
          "remediation_hint": "Fix instruction"
        }
      ]
    }
  },
  "query_fanout": {
    "simulated_queries": [
      {
        "query": "What does Example Company do?",
        "model": "all",
        "prompt_type": "brand",
        "citation_weight": "silent",
        "page_type_source": "homepage"
      }
    ],
    "fanout_depth": {
      "total_subqueries": 12,
      "by_model": { "gpt-5.4": 5, "claude": 2, "gemini": 5 },
      "by_prompt_type": { "brand": 2, "category": 4, "comparison": 6 }
    },
    "coverage_score": 6,
    "gaps": [
      "No pricing page or structured pricing content found"
    ],
    "suggested_content": [
      {
        "query": "Example Company vs competitors",
        "model_origin": "all",
        "prompt_type": "comparison",
        "suggestion": "Create a comparison page",
        "rationale": "Why models would ask this and why it matters"
      }
    ]
  }
}
```

**Critical field rules:**
- Use `scores` and `scores_max` (NOT `category_scores` or `max_scores`)
- Each page in `pages[]` MUST have `schema_detected`, `schema_missing`, and `meta` objects
- `policy_files` has nested `robots_txt` and `llms_txt` objects, each with their own `issues[]`
- `query_fanout.simulated_queries[]` each need `model`, `prompt_type`, `citation_weight`, `page_type_source`
- `query_fanout.fanout_depth` is a required nested object with `total_subqueries`, `by_model`, `by_prompt_type`
- `citation_weight` values: `"citation_producing"` (1.5x), `"silent"` (0.5x), `"site_targeted"` (2x)
- Issue IDs MUST come from the catalog — see Step 8

After writing the JSON file, display a human-readable summary showing: overall score, per-category scores, top issues by severity, and page-by-page highlights.

## SaaS Detection

Before scoring, detect SaaS by matching 2+ of 3 content sources against indicator terms (platform, saas, cloud, api, etc.). Changes expected schemas for product/pricing/features/solutions pages.

For detection logic, read `references/page-type-rules.md`.

## Reference Files

| File | Purpose |
|---|---|
| `references/scoring-rubric.md` | Full 100-point rubric — Technical Score + 5-category pipeline model |
| `references/agentic-readiness.md` | Per-page Technical Score sub-checks (J1–J4, M1–M5, C1–C2, FAQ) |
| `references/page-type-rules.md` | 19 page types, URL patterns, expected schemas, SaaS detection |
| `references/content-quality.md` | 5 content quality pillars for citation-readiness |
| `references/chunking-retrieval.md` | 10 evaluation areas for LLM retrieval optimization |
| `references/query-fanout.md` | Per-model fan-out simulation rules, citation weights, coverage scoring |
| `references/policy-files.md` | robots.txt + llms.txt detection, validation, and scoring |
