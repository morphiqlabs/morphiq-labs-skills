---
name: morphiq-build
description: >-
  Consumes MORPHIQ-RANK.json and produces build artifacts (content, schema, metadata, policy files) through
  a 6-step content lab pipeline. Use when the user asks to "fix the issues", "optimize existing content",
  "create new content for AI visibility", "run Morphiq Build", "generate schema markup", "create an
  llms.txt file", "run the content lab", or mentions building content fixes, generating schema, rewriting
  content for AI citations, or creating policy files.
license: Apache-2.0
metadata:
  version: "0.7.1"
  author: morphiq-labs
---

This skill runs one step only. Do not chain to morphiq-track.

Read `MORPHIQ-RANK.json` from the workspace root now. If the file does not exist, stop and tell the user to run Morphiq Rank first.

## Entry points

- **Path A — From roadmap:** Process issues from `MORPHIQ-RANK.json` by tier and priority. Route each to the appropriate fix workflow (see routing table below).
- **Path B — From user prompt:** Accept topic, optional source URLs (up to 5), optional ICP/brand context. Route to the content lab pipeline.
- **Path C — From existing content:** Accept content URL or raw text. Route to quality rewrite (Step 5).

## Issue type → fix routing

| Issue category | Fix approach |
|---|---|
| `agentic-*` schema | Schema injection — read `references/schema-templates.md` before generating JSON-LD |
| `agentic-*` metadata | Metadata optimization — read `references/metadata-patterns.md` before generating tags |
| `content-*` quality | Quality rewrite via Step 5 |
| `chunking-buried-answer` | Quality rewrite via Step 5 (answer-first restructure) |
| `chunking-*` structure | Content restructuring (fix headings, split paragraphs) |
| `policy-*` files | Policy file generation — read `references/llms-txt-spec.md` before creating llms.txt |
| `fanout-*` coverage | Full 6-step pipeline. Pass `fanout_context.triggering_sub_queries` to Step 3 and `competitor_sources` to Step 4. Run Step 6 before post-pipeline. |
| `visibility-*` | Enrich existing content via pipeline |

## Content lab pipeline (6 steps)

### Step 1: Ingest sources

Validate URLs, filter blocked domains, deduplicate, cap at 10. Halt if zero valid sources.

### Step 2: Extract content

Fetch each URL → clean markdown. Extract title, content, outbound links, publish date. Halt if zero successful extractions.

### Step 3: Analyze gaps

Read `references/gap-taxonomy.md` before analyzing. Identify 5 gap types: content, data, format, depth, fanout coverage. Detect comparative intent. Generate up to 5 search queries.

### Step 4: Research to fill gaps

Run up to 5 live web searches. Read `references/enrichment-sources.md` before collecting sources — it defines citation format, source preferences, and quality thresholds.

### Step 5: Generate or rewrite

Read `references/content-lab-pipeline.md` before writing — it defines the full Morphiq content standard (E-E-A-T signals, heading hierarchy, word targets, FAQ rules).

### Step 6: Validate fanout coverage (fanout issues only)

For `fanout-*` issues with `fanout_context`: validate generated content addresses all triggering sub-queries. Run `scripts/validate-coverage.py` if available, otherwise manually verify each sub-query is addressed. Revise once if coverage < 80%.

## Post-pipeline processing

After generating content, apply these as needed:

| Process | Reference |
|---|---|
| Schema injection (JSON-LD) | `references/schema-templates.md` |
| Metadata (meta description, OG tags) | `references/metadata-patterns.md` |
| llms.txt generation | `references/llms-txt-spec.md` |
| FAQ generation | `references/faq-guidelines.md` |
| Enrichment (missing stats/citations) | `references/enrichment-sources.md` |

Read the relevant reference file before producing each artifact.

## Write MORPHIQ-BUILD.json

Write to workspace root using your file-write tool, not shell heredoc or `cat`.

Required fields: `schema_version`, `generated_at`, `domain`, `source_roadmap_score`, `entry_point` ("prompt" or "existing_content"), `artifacts[]`, `summary`.
Each artifact has: `artifact_id` (build-001, build-002...), `type`, `action_ref` (issue_id, priority, tier), `target_url`, `title`, `content` (format + body), `placement` (instruction + selector).
Schema artifacts include `status`: "designed" (existing_content) or "embedded" (prompt).
`summary` has: `total_artifacts`, `by_type`, `issues_addressed[]`, `tiers_covered[]`.

End with:

> **Build complete.** MORPHIQ-BUILD.json written to workspace root.
> To continue: type **"Run Morphiq Analyze"** to measure AI visibility with real provider API calls (API keys required).
