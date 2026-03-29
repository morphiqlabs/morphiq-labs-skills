---
name: morphiq-scan
description: This skill should be used when the user asks to "audit a website for AI visibility", "scan a domain", "check AI readiness", "evaluate content quality", "run a Morphiq Scan", "check if a site is optimized for LLMs", or mentions scanning a website for LLM citation readiness. Performs a full AI visibility audit across 5 categories (agentic readiness, content quality, chunking & retrieval, query fanout, policy files) and scores the domain on a 100-point rubric.
metadata:
  version: "0.1.1"
  author: morphiq-labs
---

## EXECUTION INSTRUCTIONS

You are now executing Morphiq Scan. This is a WORKFLOW — you must perform each step below by fetching real URLs, analyzing real content, and computing real scores. Do NOT just describe what the skill does. Do NOT print help text. EXECUTE the steps.

**Input:** The user provides a domain URL. Extract it from their message.
**Output:** You MUST write a Scan Report JSON file to `MORPHIQ-SCAN.json` in the workspace root AND display a human-readable summary.

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

For every finding, create an issue. Use EXACT issue IDs from the catalog — examples:
- `policy-no-llms-txt` (not "PF-001")
- `agentic-missing-product-schema` (not "AR-001")
- `content-no-tldr` (not "CQ-001")
- `chunking-buried-answer` (not "CR-001")
- `fanout-no-comparison-content` (not "QF-001")

Each issue MUST have: `id`, `category`, `severity`, `summary`, `detail`, `affected_urls`, `remediation_hint`.

**Thoroughness check:** A site scoring 60/100 typically has 15–25 issues. If you found fewer than 10, you missed checks. Go back and re-evaluate each page against ALL issue types in the catalog.

### Step 9: Produce Scan Report

Write the Scan Report as JSON to `MORPHIQ-SCAN.json` in the workspace root. The JSON MUST follow the schema in `PIPELINE.md` §1.

**Required fields you MUST include:**
- `overall_score` — the aggregate 0–100 score
- `scores` — per-category breakdown: `{ agentic_readiness: X, content_quality: X, chunking_retrieval: X, query_fanout: X, policy_files: X }`
- `pages[]` — per-page results with `url`, `page_type`, `score`, `issues[]`, `schema_detected`, `schema_missing`, `meta`
- `policy_files` — robots.txt and llms.txt audit results
- `query_fanout` — simulated queries with `model`, `citation_weight`, coverage score, gaps, and suggested content

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
