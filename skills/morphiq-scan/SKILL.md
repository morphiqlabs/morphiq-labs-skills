---
name: morphiq-scan
description: >-
  Performs a full AI visibility audit of a website across 5 categories (agentic readiness, content quality,
  chunking & retrieval, query fanout, policy files) and scores the domain on a 100-point rubric. Use when
  the user asks to "audit a website for AI visibility", "scan a domain", "check AI readiness", "evaluate
  content quality", "run a Morphiq Scan", "check if a site is optimized for LLMs", or mentions scanning
  a website for LLM citation readiness.
license: Apache-2.0
metadata:
  version: "0.7.1"
  author: morphiq-labs
---

This skill runs one step only. Do not chain to morphiq-rank, morphiq-build, or morphiq-track.

Extract the target domain from the user message. Begin Step 1 immediately — fetch `{domain}/robots.txt` now.

## Output structure (read before starting)

Write `MORPHIQ-SCAN.json` with exactly these top-level keys — no others:

```
schema_version, generated_at, domain, pages_scanned, overall_score,
scores, scores_max, pages, policy_files, query_fanout
```

- `scores` uses keys: `agentic_readiness`, `content_quality`, `chunking_retrieval`, `query_fanout`, `policy_files`
- Each page in `pages[]` has: `url`, `page_type`, `title`, `score`, `issues[]`, `schema_detected[]`, `schema_missing[]`, `meta{}`
- Each issue object has: `id`, `category`, `severity`, `summary`, `detail`, `affected_element`, `remediation_hint`
- Issue IDs must come from the closed set in `references/output-contract.md` — format is `{category}-{problem}` (e.g. `policy-no-llms-txt`, `agentic-missing-product-schema`, `content-thin-page`). Do not invent IDs like `AR-001`, `PF-001`, or `missing_jsonld_schema`.

Read `references/output-contract.md` now for the full JSON schema, all valid issue IDs, and writing rules.

Write the file using your file-write tool, not shell heredoc or `cat`.

## Step 1: Discover pages

Fetch `{domain}/robots.txt` and `{domain}/sitemap.xml`. Select up to 10 marketing-relevant pages prioritized: home > pricing > features > product > solutions > about > blog > other > documentation. Exclude non-marketing pages (contact, login, signup, legal, demo, careers, changelog).

Read `references/page-type-rules.md` before classifying pages. It contains SaaS detection rules and page-type schemas.

## Step 2: Audit policy files (10 pts)

Fetch `{domain}/llms.txt`, `{domain}/llms-full.txt`, and evaluate `robots.txt` for AI crawler access.

Read `references/policy-files.md` before scoring this category.

## Step 3: Fetch and score each page

For each page, fetch the HTML and evaluate three categories:

- **Agentic readiness (45 pts)** — Read `references/agentic-readiness.md` before scoring. Covers schema, metadata, FAQ, content signals.
- **Content quality (20 pts)** — Read `references/content-quality.md` before scoring. Covers title clarity, TL;DR, E-E-A-T, citations, examples.
- **Chunking & retrieval (15 pts)** — Read `references/chunking-retrieval.md` before scoring. Covers headings, scope, self-containment, answer-first, vocabulary.

## Step 4: Simulate query fanout (10 pts)

Identify topics the domain covers, simulate sub-queries LLMs would chain, check which sub-queries the site can answer.

Read `references/query-fanout.md` before scoring this category.

## Step 5: Compute scores

Read `references/scoring-rubric.md` before computing. Categories 1–3 average across pages then scale. Categories 4–5 are domain-level. No score may exceed its maximum (45 / 20 / 15 / 10 / 10).

## Step 6: Write MORPHIQ-SCAN.json

Use your file-write tool to write `MORPHIQ-SCAN.json` to the workspace root. The JSON must match the structure described in "Output structure" above. Do not add extra top-level keys (`critical_issues`, `recommendations`, `quick_wins`, `seo_readiness`, etc.) — they break the downstream pipeline.

Validate every issue `id` against the closed set in `references/output-contract.md` before writing.

A site scoring ~60/100 typically has 15–25 issues. Fewer than 10 usually means something was missed.

## Step 7: Normalize (optional)

Run `python scripts/normalize-scan.py MORPHIQ-SCAN.json` if the script is available. Otherwise skip.

## Step 8: Display summary

Show: overall score, per-category scores, top issues by severity, pages analyzed.

End with:

> **Scan complete.** MORPHIQ-SCAN.json written to workspace root.
> To continue: type **"Run Morphiq Rank"** to prioritize the issues.
