---
name: morphiq-scan
description: This skill should be used when the user asks to "audit a website for AI visibility", "scan a domain", "check AI readiness", "evaluate content quality", "run a Morphiq Scan", "check if a site is optimized for LLMs", or mentions scanning a website for LLM citation readiness. Performs a full AI visibility audit across 5 categories (agentic readiness, content quality, chunking & retrieval, query fanout, policy files) and scores the domain on a 100-point rubric.
metadata:
  version: "0.6.1"
  author: morphiq-labs
---

## EXECUTION INSTRUCTIONS

You are now executing Morphiq Scan. This is a WORKFLOW — you must perform each step below by fetching real URLs, analyzing real content, and computing real scores. Do NOT just describe what the skill does. Do NOT print help text. EXECUTE the steps.

**Input:** The user provides a domain URL. Extract it from their message or from `$ARGUMENTS`.
**Output:** You MUST write a Scan Report JSON file to **`MORPHIQ-SCAN.json`** in the workspace root AND display a human-readable summary.

### DO THIS NOW — Step 1 starts immediately

Fetch `$ARGUMENTS/robots.txt` using your web fetch tool. Do not write a response. Make the tool call.

**Target domain:** $ARGUMENTS

### Output File Contract

Write `MORPHIQ-SCAN.json` to the **workspace root**. The JSON MUST use these **exact top-level keys** — the downstream pipeline depends on them:

```
schema_version, generated_at, domain, pages_scanned, overall_score,
scores, scores_max, pages, policy_files, query_fanout
```

- `scores` is an object with keys: `agentic_readiness`, `content_quality`, `chunking_retrieval`, `query_fanout`, `policy_files`
- `scores_max` is: `{ "agentic_readiness": 45, "content_quality": 20, "chunking_retrieval": 15, "query_fanout": 10, "policy_files": 10 }`
- `pages` is an array of page objects, each with: `url`, `page_type`, `title`, `score`, `issues[]`, `schema_detected[]`, `schema_missing[]`, `meta{}`
- Each issue has: `id`, `category`, `severity`, `summary`, `detail`, `affected_element`, `remediation_hint`
- `policy_files` has `robots_txt{}` and `llms_txt{}` sub-objects
- `query_fanout` has `simulated_queries[]`, `fanout_depth{}`, `coverage_score`, `gaps[]`, `suggested_content[]`

See the full JSON example in PIPELINE.md section 1.

### Issue IDs — Closed Set

Use ONLY these IDs. Do NOT invent IDs like `J001`, `SCHEMA-001`, or `content-thin-secondary-pages`.

| Category | Valid IDs |
|---|---|
| `policy_files` | `policy-no-llms-txt`, `policy-weak-llms-txt`, `policy-blocks-gptbot`, `policy-blocks-google-extended`, `policy-blocks-anthropic`, `policy-blocks-perplexity`, `policy-no-robots-txt`, `policy-invalid-robots-syntax` |
| `agentic_readiness` | `agentic-missing-product-schema`, `agentic-missing-organization-schema`, `agentic-missing-article-schema`, `agentic-missing-faq-schema`, `agentic-missing-howto-schema`, `agentic-missing-breadcrumb`, `agentic-no-canonical`, `agentic-broken-heading-hierarchy`, `agentic-weak-meta-description`, `agentic-missing-og-tags`, `agentic-no-semantic-html`, `agentic-duplicate-schema` |
| `content_quality` | `content-thin-page`, `content-low-word-count`, `content-no-tldr`, `content-no-author`, `content-unsourced-stats`, `content-wrong-citation-format`, `content-no-expert-quotes`, `content-stale-date`, `content-thin-faq`, `content-no-examples`, `content-generic-advice` |
| `chunking_retrieval` | `chunking-broken-heading-hierarchy`, `chunking-generic-headings`, `chunking-overscoped-section`, `chunking-buried-answer`, `chunking-long-paragraphs`, `chunking-no-faq-coverage`, `chunking-no-top-summary`, `chunking-missing-query-terms` |
| `query_fanout` | `fanout-no-comparison-content`, `fanout-no-pricing-content`, `fanout-no-alternative-content`, `fanout-missing-entity-coverage`, `fanout-wrong-page-type`, `fanout-no-site-match`, `fanout-unanswered-subquery`, `fanout-thin-topic-coverage`, `fanout-no-docs-content` |

---

## Step 1: Discover Pages

Fetch these URLs using your web/fetch tool:

1. Fetch `{domain}/robots.txt` — extract sitemap URLs
2. Fetch `{domain}/sitemap.xml` if not found in robots.txt
3. Select up to 10 marketing-relevant pages, prioritized:
   home > pricing > features > product > solutions > about > blog > other > documentation
4. Exclude non-marketing pages (contact, login, signup, legal, demo, careers, changelog)

**READ NOW:** `references/page-type-rules.md`

## Step 2: SaaS Detection

Detect SaaS by matching 2+ of 3 content sources against indicator terms (platform, saas, cloud, api, etc.). Changes expected schemas. See `references/page-type-rules.md`.

## Step 3: Audit Policy Files (10 pts)

1. Fetch `{domain}/llms.txt` and `{domain}/llms-full.txt`
2. **robots.txt** — Validate AI crawler access (GPTBot, Google-Extended, Anthropic-AI, PerplexityBot)
3. **llms.txt** — Validate existence and quality (>=500 chars = good, <500 = thin)

**READ NOW:** `references/policy-files.md`

## Step 4: Fetch and Score Each Page

For each page, fetch the HTML and evaluate:

**Agentic Readiness (45 pts):** Schema (40pts: J1-J4), Metadata (30pts: M1-M5), FAQ (20pts), Content (10pts). See `references/agentic-readiness.md`.

**Content Quality (20 pts):** title clarity (3), TL;DR (4), E-E-A-T (6), citations (5), examples (2). See `references/content-quality.md`.

**Chunking and Retrieval (15 pts):** headings (3), scope (3), self-containment (2.25), answer-first (2.25), vocabulary (4.5). See `references/chunking-retrieval.md`.

For each page, record: `url`, `page_type`, `title`, `score`, `issues[]`, `schema_detected[]`, `schema_missing[]`, `meta{}` (title_length, description_length, og_image, canonical, h1_count, heading_hierarchy_valid, word_count).

## Step 5: Simulate Query Fanout (10 pts)

Identify topics, simulate sub-queries, check coverage. See `references/query-fanout.md`.

Record: `simulated_queries[]` (each with query, model, prompt_type, citation_weight, page_type_source), `fanout_depth{}`, `coverage_score`, `gaps[]`, `suggested_content[]`.

## Step 6: Compute Scores

```
overall_score = agentic_readiness (max 45) + content_quality (max 20) + chunking_retrieval (max 15) + query_fanout (max 10) + policy_files (max 10)
```

Categories 1-3: average across pages then scale. Categories 4-5: domain-level. See `references/scoring-rubric.md`.

**Scores must NOT exceed their maximums.** If agentic_readiness > 45 or any score > its max, you miscalculated.

## Step 7: Write MORPHIQ-SCAN.json

Use your **file write tool** (e.g., Write / create_file) to write `MORPHIQ-SCAN.json` directly to the **workspace root**.

**CRITICAL — do NOT:**
- Run `cat > file.json << 'EOF'` or any bash/shell heredoc
- Run a Python script to generate the file
- Write to `/tmp/` or any other path
- Add extra top-level keys beyond the Output File Contract above (`critical_findings`, `summary_and_recommendations`, etc. are NOT part of the contract and will break downstream pipeline)

The file must be written with a direct Write tool call to the workspace root path (e.g., `MORPHIQ-SCAN.json` or the absolute workspace path).

A site scoring ~60/100 typically has 15-25 issues. If you find fewer than 10, re-check.

## Step 8: Normalize (Safety Net)

After writing the JSON, run the normalizer to ensure pipeline compatibility:

```
python "${CLAUDE_SKILL_DIR}/scripts/normalize-scan.py" MORPHIQ-SCAN.json
```

If the normalizer is not available, skip this step.

## Step 9: Display Summary

Show a human-readable summary: overall score, per-category scores, top issues by severity, pages analyzed.
