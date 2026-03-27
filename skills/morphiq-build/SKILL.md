---
name: morphiq-build
description: This skill should be used when the user asks to "fix the issues", "optimize existing content", "create new content for AI visibility", "run Morphiq Build", "generate schema markup", "create an llms.txt file", "run the content lab", or mentions building content fixes, generating schema, rewriting content for AI citations, or creating policy files. Consumes a Prioritized Roadmap (or user prompt, or existing content) and produces build artifacts through a 5-step content lab pipeline.
metadata:
  version: "0.1.0"
  author: morphiq-labs
---

## Pipeline Position

Step 3 of 4 — consumes morphiq-rank output.
- **Input:** Prioritized Roadmap (JSON) OR user prompt OR existing content.
- **Output:** Build Output (JSON + artifacts) → consumed by morphiq-track.
- **Data contract:** See `PIPELINE.md` §3 for the Build Output schema.

## Purpose

Morphiq Build fixes issues from morphiq-rank. It creates new content, optimizes existing content, generates schema markup, builds policy files, and produces artifacts to improve AI visibility. The core engine is a 5-step content lab pipeline.

## Entry Points

**Path A — From Prioritized Roadmap:** Process issues by tier and priority. Route each to the appropriate fix workflow.

**Path B — From User Prompt:** Accept topic, optional source URLs (up to 5), optional ICP/brand context. Route to content lab pipeline.

**Path C — From Existing Content:** Accept content URL or raw text. Route to quality rewrite workflow.

## Content Lab Pipeline (5 Steps)

### Step 1: Ingest Sources

Validate URLs, filter blocked domains, deduplicate, cap at 10. Accept raw text or PDF alternatives. **Halt if zero valid sources.**

### Step 2: Extract Content

Crawl each URL → clean markdown. Extract title, content, outbound links, publish date. **Halt if zero successful extractions.**

### Step 3: Analyze Gaps

Analyze against query space. Identify 5 gap types:

| Gap Type | What Is Missing |
|---|---|
| Content | Unanswered questions, missing perspectives |
| Data | Missing statistics, quantitative evidence |
| Format | Wrong format for LLM retrieval |
| Depth | Surface-level, no expert insight |
| Fanout coverage | Sub-queries AI would chain but site cannot answer |

Detect comparative intent. Evaluate fanout coverage using content type → sub-query rules. Generate up to 5 search queries.

For gap taxonomy and severity, read `references/gap-taxonomy.md`.

### Step 4: Research to Fill Gaps

Run up to 5 live web searches. Collect authoritative sources, statistics (number + source + URL), expert quotes (speaker + credential), industry insights. If comparative intent, dedicate 1 search to brand data.

For citation rules, read `references/enrichment-sources.md`.

### Step 5: Generate / Rewrite

Produce final content applying Morphiq standard:
- E-E-A-T signals, name-drop citations, expert quotes
- Heading hierarchy, 50–75 word paragraphs, direct-answer blocks
- Brand positioning (comparative or authority mode)
- 1,200–1,600 words, 5–7 H2 sections, FAQ with 3–5 Q&As
- Minimum 3 statistics, 1 expert quote, sources section
- No fabricated case studies

For full pipeline spec, read `references/content-lab-pipeline.md`.

## Post-Pipeline Processing

| Process | What It Does | Reference |
|---|---|---|
| Schema Injection | Classify content type, generate JSON-LD | `references/schema-templates.md` |
| Metadata Optimization | Meta description, slug, OG tags | `references/metadata-patterns.md` |
| llms.txt Scaffolding | Generate llms.txt from sitemap | `references/llms-txt-spec.md` |
| Content Restructuring | Fix headings, split paragraphs | — |
| Internal Linking | Link related pages for `site:` coverage | `references/content-lab-pipeline.md` |
| Enrichment | Additional search for missing stats/citations | `references/enrichment-sources.md` |
| FAQ Generation | Generate FAQ from gap analysis | `references/faq-guidelines.md` |

## Issue Type → Fix Routing

| Issue Category | Fix Approach |
|---|---|
| `agentic-*` schema | Schema Injection — generate JSON-LD |
| `agentic-*` metadata | Metadata Optimization — generate tags |
| `content-*` quality | Quality Rewrite — Step 5 pipeline |
| `chunking-*` structure | Content Restructuring |
| `policy-*` files | Policy file generation |
| `fanout-*` coverage | Full 5-step pipeline for new content |
| `visibility-*` | Enrich existing content via pipeline |

## Build Output

Artifacts with `type`: "content", "schema", "metadata", "policy_file". Each includes placement instructions.

## Reference Files

| File | Purpose |
|---|---|
| `references/content-lab-pipeline.md` | Full 5-step pipeline with I/O formats |
| `references/gap-taxonomy.md` | Gap types, severity, search query rules |
| `references/enrichment-sources.md` | Citation format, source preferences |
| `references/schema-templates.md` | JSON-LD templates, skip conditions |
| `references/metadata-patterns.md` | SEO metadata rules |
| `references/llms-txt-spec.md` | llms.txt spec and generation |
| `references/faq-guidelines.md` | FAQ generation rules |
