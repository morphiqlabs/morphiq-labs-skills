# Content Lab Pipeline — 5-Step Workflow

This is the core content creation and optimization pipeline for morphiq-build. It takes tracked prompts and captured sources (from morphiq-track) or a user prompt, and produces final optimized content that AI systems will cite.

## Pipeline Overview

```
Input: tracked prompts + captured sources (from morphiq-track)
   OR: user prompt + optional source URLs

   ┌──────────────────────────────────┐
   │  Step 1: Ingest Sources          │
   │  Validate URLs, deduplicate      │
   ├──────────────────────────────────┤
   │  Step 2: Extract Content         │
   │  Crawl → extract → structured    │
   ├──────────────────────────────────┤
   │  Step 3: Analyze Gaps            │
   │  Content/data/format/depth gaps  │
   │  Generate research queries       │
   ├──────────────────────────────────┤
   │  Step 4: Research to Fill Gaps   │
   │  Live web search for stats,      │
   │  quotes, sources                 │
   ├──────────────────────────────────┤
   │  Step 5: Generate / Rewrite      │
   │  Final optimized content         │
   │  Content Quality + Structure     │
   │  applied as production standard  │
   └──────────────────────────────────┘

Output: final rewritten content + metadata
   → feeds into schema injection, metadata rewrite, FAQ creation
   → output contract matches PIPELINE.md Build Output format
```

## Input Sources

morphiq-build accepts input from two paths:

**Path A — From morphiq-track (primary flow):**

- Tracked prompts that the user wants to create content for
- Citation sources captured from AI provider responses during tracking runs
- The user says: "based on the prompts we have and sources, run the content lab"

**Path B — From user prompt (direct entry):**

- User provides a topic/question and optionally up to 5 source URLs
- Optionally provides ICP (Ideal Customer Profile) and brand context

Both paths converge at Step 1.

## Step 1 — Ingest Sources

**Script:** `scripts/ingest-sources.py`

**What it does:**

- Validates all input URLs (http/https only)
- Filters known blocked or unreliable domains
- Deduplicates URLs
- Caps at 10 URLs maximum
- Accepts raw text or PDF content as alternative inputs

**Input:** list of URLs, raw text, or PDF paths **Output:** validated source list with metadata

```json
{
  "sources": [
    {
      "url": "https://example.com/article",
      "type": "url",
      "status": "valid"
    }
  ],
  "rejected": [
    {
      "url": "ftp://invalid.com",
      "reason": "Invalid protocol — only http/https accepted"
    }
  ],
  "total_valid": 5,
  "total_rejected": 1
}
```

**Failure condition:** If zero valid sources remain, the pipeline halts with an error.

## Step 2 — Extract Content

**Script:** `scripts/extract-content.py`

**What it does:**

- Crawls each validated URL using the agent's built-in web search/fetch capabilities
- Converts HTML to clean markdown
- Extracts: title, main content body, outbound links, publication date
- Structures extracted content for gap analysis

**Input:** validated source list from Step 1 **Output:** structured content extractions

```json
{
  "extractions": [
    {
      "url": "https://example.com/article",
      "title": "How to Optimize for AI Search",
      "content_markdown": "# How to Optimize...\n\n...",
      "word_count": 1420,
      "publish_date": "2025-02-15",
      "outbound_links": ["https://gartner.com/report"],
      "extraction_status": "success"
    }
  ],
  "successful": 4,
  "failed": 1
}
```

**Failure condition:** At least 1 successful extraction required to proceed.

## Step 3 — Analyze Gaps

**Script:** `scripts/analyze-gaps.py`

**What it does:**

- Analyzes extracted content against the query space (tracked prompts)
- Identifies five types of gaps:

| Gap Type | What's Missing |
| --- | --- |
| **Content gaps** | Unanswered questions, missing perspectives, topics not covered |
| **Data gaps** | Missing statistics, comparisons, quantitative evidence |
| **Format gaps** | No tables, step-by-steps, FAQs, comparison formats |
| **Depth gaps** | Surface-level explanations, no expert insight |
| **Fanout coverage gaps** | Sub-queries AI models would chain about this topic that the site cannot answer |

- Detects comparative intent — checks if prompt contains "vs", "best", "compare", etc.
- If comparative intent detected → flags "brand positioning gap"
- Evaluates fanout coverage — checks whether the content addresses the sub-queries models would chain from this topic (see Fanout-Aware Gap Analysis below)
- Generates up to 5 targeted search queries to fill identified gaps

**Input:** extracted content from Step 2 + tracked prompts + optional ICP **Output:** gap analysis report with research queries

```json
{
  "gaps": [
    {
      "type": "data",
      "description": "No statistics on AI adoption rates in the enterprise segment",
      "severity": "high",
      "search_query": "enterprise AI adoption statistics 2025"
    },
    {
      "type": "content",
      "description": "No comparison between product and top 3 competitors",
      "severity": "high",
      "search_query": "Example Company vs Competitor A vs Competitor B features"
    }
  ],
  "comparative_intent": true,
  "brand_positioning_needed": true,
  "total_gaps": 5,
  "search_queries": [
    "enterprise AI adoption statistics 2025",
    "Example Company vs Competitor A features comparison",
    "AI search optimization ROI case studies",
    "E-E-A-T content ranking factors 2025",
    "Example Company enterprise customers reviews"
  ]
}
```

### Fanout-Aware Gap Analysis

In addition to the standard gap types, Step 3 evaluates whether the content being built or optimized addresses the sub-queries AI models would chain from this topic. The content type determines which sub-queries to target:

**Content type → sub-query generation ruleset:**

| Content Type | Expected Sub-queries | Build Implication |
| --- | --- | --- |
| **Pricing page** | GPT-5.4 chains `site:domain.com` queries for pricing + features per competitor | Ensure per-plan feature breakdown, comparison table with competitors, pricing FAQs |
| **Blog post (category)** | Triggers discovery fan-out (avg 7.5 sub-queries) — landscape, per-entity, alternatives | Generate content that answers 7+ sub-queries, not just the headline topic |
| **Blog post (technical)** | Triggers technical_eval fan-out (avg 11 sub-queries) — per-platform verification | Include per-platform comparisons, benchmarks, implementation details |
| **Comparison page** | Always decomposes per-entity across all models | Ensure every entity in the comparison has dedicated coverage and data |
| **Product page** | Triggers feature decomposition — each capability searched individually | Each feature should be addressable as a standalone retrievable section |
| **Docs/guide page** | Triggers implementation step verification | Each step must be self-contained and answer the specific how-to sub-query |

**`site:` operator implication:** GPT-5.4 heavily uses `site:domain.com` queries to verify claims directly on company websites. Content must be structured so these site-specific queries find authoritative answers. This means:

- Key topics must live on dedicated, appropriately-typed pages (pricing on /pricing, features on /product)
- Internal linking between related pages strengthens `site:` query matches
- Pages should include the exact terminology GPT-5.4 appends to `site:` queries: "pricing", "features", "official", year markers
- If the content being built targets a topic that GPT-5.4 would `site:`-search for, the page URL and title should clearly match that topic

For the full gap taxonomy, read `references/gap-taxonomy.md`.

## Step 4 — Research to Fill Gaps

**Script:** `scripts/research-live.py`

**What it does:**

- Runs up to 5 live web searches based on gap analysis queries
- Uses the agent's built-in web search capabilities
- If comparative intent → dedicates 1 search to brand-specific data
- Collects and structures findings:

| Finding Type | What to Capture |
| --- | --- |
| **Authoritative sources** | Reports, studies, official publications |
| **Statistics** | Number + context + source name + URL |
| **Expert quotes** | Quote text + speaker name + credential + source URL |
| **Industry insights** | Trends, forecasts, analyst opinions |

**Input:** search queries from Step 3 **Output:** research findings structured for content generation

```json
{
  "findings": [
    {
      "query": "enterprise AI adoption statistics 2025",
      "results": [
        {
          "type": "statistic",
          "content": "80% of enterprises will adopt AI by 2026",
          "source_name": "Gartner",
          "source_url": "https://gartner.com/report-2025",
          "confidence": "high"
        },
        {
          "type": "expert_quote",
          "content": "AI adoption requires a data-first strategy before any tooling decisions.",
          "speaker": "Dr. Jane Smith",
          "credential": "Chief AI Officer at Acme Corp",
          "source_url": "https://techreview.com/interview",
          "confidence": "high"
        }
      ]
    }
  ],
  "total_findings": 12,
  "stats_found": 5,
  "quotes_found": 2,
  "sources_found": 8
}
```

For citation format rules and source authority preferences, read `references/enrichment-sources.md`.

## Step 5 — Generate / Rewrite Content

**Scripts:** `scripts/create-from-prompt.py` (new content) or `scripts/quality-rewrite.py` (existing content)

**What it does:**

- Produces final optimized content following the Morphiq content standard
- Applies Content Quality thesis (E-E-A-T, citations, statistics)
- Applies Content Structure thesis (heading hierarchy, paragraphs, FAQ)
- Integrates research findings from Step 4

**Pre-processing:**

1. Partition sources into brand-owned vs external (domain matching)
2. Build citation list from external sources only
3. Build brand knowledge section from brand-owned sources
4. Format statistics and expert quotes with proper attribution

**Content standard applied:**

1. Content Quality rules — E-E-A-T signals, name-drop + link citations, expert quotes with in-text attribution
2. Content Structure rules — heading hierarchy, 50-75 word paragraphs, direct-answer blocks, FAQ
3. Brand positioning — comparative mode (recommend first + alternatives) or authority mode (brand perspective)
4. Gap analysis results addressed — every identified gap has content addressing it

**Mandatory output requirements:**

- 1,200–1,600 words
- H1 title + TL;DR + author byline + intro
- 5–7 H2 sections, each with a direct-answer opening paragraph
- Comparison table (if comparative intent detected)
- Bottom line / conclusion section immediately before FAQ
- FAQ with 3–5 Q&As as H3/H4
- Minimum 3 statistics with name-drop + link format
- Minimum 1 expert quote with in-text attribution
- Sources section with all references
- No fabricated case studies — real examples only, or omit

**Output format:**

```json
{
  "content": "# Clear Title\n\n> TL;DR\n...",
  "metadata": {
    "title": "Clear Title Reflecting Prompt",
    "meta_description": "150-160 character description...",
    "word_count": 1450,
    "sections": ["Introduction", "Section 1", "..."],
    "author": {
      "name": "Author Name",
      "credentials": "Role / expertise"
    },
    "last_updated": "2025-03-25",
    "sources": [
      {
        "name": "Gartner",
        "url": "https://gartner.com/report",
        "type": "statistic"
      }
    ]
  }
}
```

## Post-Pipeline Processing

After the 5-step pipeline completes, morphiq-build runs additional processing:

**Schema Injection** (`scripts/inject-schema.py`):

- Classifies content type (BlogPosting, TechArticle, HowTo)
- Generates JSON-LD markup
- See `references/schema-templates.md` for templates per content type

Schema injection behavior depends on `entry_point`:

- **`entry_point: "prompt"` (new content):** After generating JSON-LD, embed the `<script type="application/ld+json">` block(s) directly at the end of the content artifact's `content.body`. The content artifact ships complete — the implementer gets one artifact with body + schema already combined. A separate schema artifact is still emitted for auditability, with `status: "embedded"` and `bound_to` referencing the content artifact.
- **`entry_point: "existing_content"` (optimization):** Schema artifacts remain separate. Each schema artifact gets `status: "designed"`. The build is not marked complete until all schema artifacts reach `status: "implemented"` or are explicitly skipped.

**Verification gate (existing content only):** After all artifacts are produced, verify that schema artifacts have been added to the target page HTML. Schema artifacts transition from `"designed"` to `"implemented"` only after verification confirms the `<script type="application/ld+json">` block is present on the page. New content does not need this gate — the schema is already in the body.

**Metadata Optimization** (handled in Step 5 output):

- SEO meta description (150–160 chars)
- SEO-friendly slug
- Open Graph tags
- See `references/metadata-patterns.md` for rules

**llms.txt Scaffolding** (`scripts/generate-llms-txt.py`):

- If building for a full site, generates llms.txt from sitemap
- See `references/llms-txt-spec.md` for the spec

**Content Restructuring** (`scripts/restructure-content.py`):

- Fixes heading hierarchy violations
- Splits oversized paragraphs
- Reorders sections for retrieval optimization

**Internal Linking for `site:` Query Coverage:**

- For each piece of content, identify related pages on the same domain that GPT-5.4 would target with `site:` queries
- Add internal links between the built content and those related pages (pricing ↔ product, comparison ↔ individual entity pages, blog ↔ docs)
- Ensure anchor text uses the terminology models inject into `site:` queries ("pricing", "features", "official", year markers)
- This strengthens the site's ability to answer `site:domain.com [topic]` queries by creating discoverable paths between related content

**Enrichment Pass** (`scripts/enrich-content.py`):

- Takes content that's already been through the pipeline
- Runs additional web search for missing stats/citations
- Produces the final optimized rewritten version
- Output is the finished content — not a brief or suggestions

## Pipeline Data Flow

The full pipeline produces a Build Output matching the PIPELINE.md contract:

- Each piece of content becomes an artifact with `type: "content"`
- Each schema injection becomes an artifact with `type: "schema"`
- Each metadata optimization becomes an artifact with `type: "metadata"`
- Policy file generation becomes an artifact with `type: "policy_file"`

### Schema-to-Content Binding

When `entry_point` is `"prompt"`, schema artifacts are **bound** to their corresponding content artifact:

1. The content artifact's `content.body` includes `<script type="application/ld+json">` block(s) appended after the closing content (after the sources section or final FAQ).
2. The schema artifact is still listed in `artifacts[]` for auditability, with `status: "embedded"` and a `bound_to` field referencing the content artifact's `artifact_id`.
3. The schema artifact's `placement` field is informational only — the schema is already in the content.

When `entry_point` is `"existing_content"`, schema artifacts are **independent**:

1. The content artifact does not contain schema markup.
2. The schema artifact has `status: "designed"` and must be implemented separately.
3. After implementation, verification updates `status` to `"implemented"`.
4. The build is not complete until all schema artifacts are `"implemented"` or explicitly skipped.