# Morphiq Skills Pipeline

## Overview

The four Morphiq skills form a sequential pipeline. Each skill produces structured JSON output that the next skill consumes as input. This document defines the user-facing skill flow, the workflows each skill supports, and the exact data contracts between them.

```
morphiq-scan → morphiq-rank → morphiq-build → morphiq-track
                  ↑                                    │
                  └────────────────────────────────────┘
```

---

## Skill Flow

Users download the Morphiq skills from skills.sh and invoke them in Claude Code.

### Initial Audit

The user triggers the full audit-to-issue pipeline in a single instruction:

> "Use Morphiq Scan to audit the entire website, then use Morphiq Rank to create the issues."

This runs two skills sequentially:

1. **morphiq-scan** audits the domain across all evaluation categories, scores it on a 100-point rubric, and outputs a Scan Report.
2. **morphiq-rank** consumes the Scan Report, creates prioritized issues with accurate references, and outputs a Prioritized Roadmap.

The user reviews the issues. When ready to fix:

> "Use Morphiq Build to fix the issues."

3. **morphiq-build** consumes the Prioritized Roadmap and produces build artifacts — the actual content, schema, and policy files that resolve each issue.

### Ongoing Workflows

After the initial audit and build cycle, **morphiq-track** drives three ongoing workflows:

> "Use Morphiq Track to run a tracking cycle."

4. **morphiq-track** generates `MORPHIQ-TRACKER.md` — the persistent state file that records scores, issues, SoV deltas, prompts, competitors, and content creation queues. This file is updated every run and serves as input for all downstream workflows.

From the tracker, users invoke specific workflows:

> "Use Morphiq Build to optimize existing content." (Content Optimization)
> "Use Morphiq Build to create new content." (Content Creation)

---

## 1. morphiq-scan

### Workflow

morphiq-scan performs a full AI visibility audit of one domain. It evaluates every page (including blogs) across five categories:

**1. Content Quality (20 points)**
Evaluates E-E-A-T signals, clear titles, TL;DR summaries, statistics/citations, and examples. Applies to all pages including blog posts. Scored per reference: `content-quality.md`.

**2. Agentic Readiness / Content Structure (45 points)**
Evaluates JSON-LD schema, semantic HTML, heading hierarchy, metadata, canonical URLs, Open Graph tags, and structured data. Checks whether AI agents can extract facts from the page. Applies to all pages including blog posts.

**3. Chunking & Retrieval (15 points)**
Evaluates ease of chunking and retrieval by LLMs: heading hierarchy as semantic boundaries, section scope, paragraph self-containment, answer-first structure, retrieval vocabulary, and FAQ presence. Applies to all pages including blog posts. Scored per reference: `chunking-retrieval.md`.

**4. Policy Files (10 points)**
Scans for `robots.txt` and `llms.txt` at the domain root. Checks whether AI crawlers (GPTBot, Google-Extended, etc.) are allowed or blocked. Checks whether `llms.txt` exists and follows the spec.

**5. Query Fanout (10 points) — Diagnostic**
Simulates the chain-of-thought queries an LLM would generate about the company, its products, and its content. Checks whether the site has pages that answer each sub-query. Identifies coverage gaps — queries the site cannot answer. Also suggests content creations based on what models would likely ask given the existing content and prompts.

**Scoring**
After evaluating all categories, morphiq-scan applies the 100-point scoring rubric (`scoring-rubric.md`) to produce the overall score and per-category breakdowns. The Scan Report with all scores and issues is then passed as input to morphiq-rank.

### Contract: Scan Report

morphiq-scan produces a **scan report** — a full AI visibility audit of one domain. morphiq-rank consumes this report to prioritize issues.

```json
{
  "schema_version": "1.0",
  "generated_at": "2025-03-25T14:30:00Z",
  "domain": "example.com",
  "pages_scanned": 12,
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
      "title": "Example Product — Best Widget for Teams",
      "score": 58,
      "issues": [
        {
          "id": "agentic-missing-product-schema",
          "category": "agentic_readiness",
          "severity": "high",
          "summary": "No Product schema detected",
          "detail": "This product page has no JSON-LD Product markup. LLMs cannot extract structured product attributes.",
          "affected_element": null,
          "remediation_hint": "Add Product schema with name, description, offers, and aggregateRating"
        },
        {
          "id": "content-thin-faq",
          "category": "content_quality",
          "severity": "medium",
          "summary": "No FAQ section found",
          "detail": "Product page has no FAQ content. AI agents frequently look for Q&A pairs when answering comparison queries.",
          "affected_element": null,
          "remediation_hint": "Add 5-8 FAQs covering common purchase/comparison questions"
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
          "detail": "GPTBot is disallowed. Content will not be indexed by ChatGPT.",
          "remediation_hint": "Remove GPTBot disallow rule or add targeted allow rules"
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
          "detail": "No llms.txt file at /llms.txt. AI agents that support this standard have no structured entry point.",
          "remediation_hint": "Create llms.txt with site summary, key pages, and structured navigation"
        }
      ]
    }
  },
  "query_fanout": {
    "simulated_queries": [
      "What does Example Company do?",
      "Example Company pricing",
      "Example Company vs competitors",
      "Is Example Company good for enterprise?",
      "Example Company reviews"
    ],
    "coverage_score": 6,
    "gaps": [
      "No pricing page or structured pricing content found",
      "No comparison content addressing competitor queries"
    ],
    "suggested_content": [
      {
        "query": "Example Company vs competitors",
        "suggestion": "Create a comparison page addressing top competitor queries",
        "rationale": "LLMs chain comparison queries when users ask about alternatives — no content exists to be cited"
      },
      {
        "query": "Example Company pricing",
        "suggestion": "Add structured pricing page with plan details",
        "rationale": "Pricing queries are high-intent — models currently have no source to cite for this"
      }
    ]
  }
}
```

### Field Definitions

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `schema_version` | string | yes | Always `"1.0"` for this version |
| `generated_at` | ISO 8601 | yes | When the scan ran |
| `domain` | string | yes | Root domain scanned |
| `pages_scanned` | integer | yes | Total pages analyzed |
| `overall_score` | integer (0-100) | yes | Aggregate score per scoring rubric |
| `scores` | object | yes | Category breakdown — keys match `scores_max` |
| `scores_max` | object | yes | Maximum possible points per category |
| `pages[]` | array | yes | Per-page audit results |
| `pages[].url` | string | yes | Full URL |
| `pages[].page_type` | string | yes | Detected type: `homepage`, `product`, `pricing`, `blog`, `about`, `contact`, `docs`, `landing`, `comparison`, `case-study`, `careers`, `legal`, `other` |
| `pages[].score` | integer (0-100) | yes | Page-level score |
| `pages[].issues[]` | array | yes | Issues found on this page |
| `pages[].issues[].id` | string | yes | Unique issue identifier (kebab-case) |
| `pages[].issues[].category` | string | yes | Must match a key in `scores` |
| `pages[].issues[].severity` | enum | yes | `critical`, `high`, `medium`, `low` |
| `pages[].issues[].summary` | string | yes | One-line human-readable summary |
| `pages[].issues[].detail` | string | yes | Full explanation |
| `pages[].issues[].affected_element` | string/null | no | CSS selector or element reference if applicable |
| `pages[].issues[].remediation_hint` | string | yes | What to do about it |
| `pages[].schema_detected` | string\[\] | yes | Schema types found on page |
| `pages[].schema_missing` | string\[\] | yes | Schema types expected but absent for this page type |
| `pages[].meta` | object | yes | Page metadata extracted |
| `policy_files` | object | yes | robots.txt and llms.txt audit |
| `query_fanout` | object | yes | Simulated AI query coverage analysis |
| `query_fanout.simulated_queries` | string\[\] | yes | The sub-questions an LLM would generate |
| `query_fanout.coverage_score` | integer (0-10) | yes | How well the site answers these |
| `query_fanout.gaps` | string\[\] | yes | Queries the site cannot answer |
| `query_fanout.suggested_content` | array | yes | Content creation suggestions derived from unanswered queries |
| `query_fanout.suggested_content[].query` | string | yes | The unanswered query |
| `query_fanout.suggested_content[].suggestion` | string | yes | What content to create |
| `query_fanout.suggested_content[].rationale` | string | yes | Why models would ask this and why it matters |

### Issue ID Convention

Issue IDs follow the pattern: `{category}-{specific-problem}`

Examples:

- `agentic-missing-product-schema` — Product schema not found
- `agentic-no-canonical` — Missing canonical tag
- `agentic-no-breadcrumb` — No BreadcrumbList for navigation
- `agentic-broken-heading-hierarchy` — Invalid heading structure
- `content-thin-faq` — No or insufficient FAQ content
- `policy-blocks-gptbot` — robots.txt blocks GPTBot
- `chunking-long-paragraphs` — Paragraphs exceed retrieval-friendly length
- `fanout-no-comparison-content` — No content for competitor comparison queries
- `fanout-no-pricing-content` — No structured pricing content for pricing queries

---

## 2. morphiq-rank

### Workflow

morphiq-rank consumes the Scan Report and creates the issues that the user needs to fix. It does not just list them — it applies issue creation criteria with accurate references:

1. **Reads the Scan Report** — all issues, scores, and query fanout gaps
2. **Calculates impact scores** — weights each issue by how much it affects AI visibility (not just severity, but which pages and categories it affects)
3. **Estimates effort** — low/medium/high based on the type of fix
4. **Organizes into progressive discovery tiers** — Foundation → Structure → Content → Optimization
5. **Sets dependency ordering** — some issues must be resolved before others make sense (e.g., fix schema before adding FAQ that references schema)
6. **Outputs the Prioritized Roadmap** with every issue as an actionable item the user can work through

Each action in the roadmap includes: the original issue ID, the affected URLs, the remediation instruction, and what it depends on. This is the user's fix list.

### Contract: Prioritized Roadmap

morphiq-rank consumes the scan report and produces a **prioritized roadmap** — issues organized into progressive discovery tiers, ranked by impact and effort.

```json
{
  "schema_version": "1.0",
  "generated_at": "2025-03-25T14:35:00Z",
  "domain": "example.com",
  "source_scan_score": 62,
  "total_issues": 24,
  "tiers": [
    {
      "tier": 1,
      "name": "Foundation — Crawlability & Policy",
      "description": "Ensure AI crawlers can access and understand the site at all",
      "estimated_impact": "high",
      "actions": [
        {
          "priority": 1,
          "issue_id": "policy-blocks-gptbot",
          "category": "policy_files",
          "severity": "high",
          "impact_score": 95,
          "effort": "low",
          "summary": "robots.txt blocks GPTBot",
          "remediation": "Remove GPTBot disallow rule from robots.txt",
          "affected_urls": ["https://example.com/robots.txt"],
          "page_type": null,
          "depends_on": []
        },
        {
          "priority": 2,
          "issue_id": "policy-no-llms-txt",
          "category": "policy_files",
          "severity": "high",
          "impact_score": 90,
          "effort": "medium",
          "summary": "No llms.txt file found",
          "remediation": "Create llms.txt with site summary, key pages, and structured navigation aids",
          "affected_urls": [],
          "page_type": null,
          "depends_on": []
        }
      ]
    },
    {
      "tier": 2,
      "name": "Structure — Schema & Metadata",
      "description": "Add machine-readable structure so AI can extract facts",
      "estimated_impact": "high",
      "actions": [
        {
          "priority": 3,
          "issue_id": "agentic-missing-product-schema",
          "category": "agentic_readiness",
          "severity": "high",
          "impact_score": 85,
          "effort": "medium",
          "summary": "No Product schema on product page",
          "remediation": "Add JSON-LD Product schema with name, description, offers, aggregateRating",
          "affected_urls": ["https://example.com/product"],
          "page_type": "product",
          "depends_on": []
        }
      ]
    },
    {
      "tier": 3,
      "name": "Content — Depth & Coverage",
      "description": "Fill content gaps that prevent AI from citing the site",
      "estimated_impact": "medium",
      "actions": [
        {
          "priority": 4,
          "issue_id": "content-thin-faq",
          "category": "content_quality",
          "severity": "medium",
          "impact_score": 70,
          "effort": "medium",
          "summary": "No FAQ section on product page",
          "remediation": "Add 5-8 FAQs covering common purchase and comparison questions",
          "affected_urls": ["https://example.com/product"],
          "page_type": "product",
          "depends_on": ["agentic-missing-product-schema"]
        }
      ]
    },
    {
      "tier": 4,
      "name": "Optimization — Retrieval & Citation Quality",
      "description": "Fine-tune content for LLM chunking and citation patterns",
      "estimated_impact": "low",
      "actions": []
    }
  ]
}
```

### Field Definitions

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `schema_version` | string | yes | Always `"1.0"` |
| `generated_at` | ISO 8601 | yes | When the ranking ran |
| `domain` | string | yes | Carried from scan report |
| `source_scan_score` | integer | yes | The overall_score from the scan |
| `total_issues` | integer | yes | Count of all issues across all tiers |
| `tiers[]` | array | yes | Ordered list of progressive discovery tiers |
| `tiers[].tier` | integer | yes | Tier number (1 = highest priority) |
| `tiers[].name` | string | yes | Human-readable tier name |
| `tiers[].description` | string | yes | What this tier accomplishes |
| `tiers[].estimated_impact` | enum | yes | `high`, `medium`, `low` |
| `tiers[].actions[]` | array | yes | Ordered actions within the tier |
| `actions[].priority` | integer | yes | Global priority rank (1 = do first) |
| `actions[].issue_id` | string | yes | Matches `issues[].id` from scan report |
| `actions[].category` | string | yes | Issue category |
| `actions[].severity` | enum | yes | `critical`, `high`, `medium`, `low` |
| `actions[].impact_score` | integer (0-100) | yes | Weighted AI visibility impact |
| `actions[].effort` | enum | yes | `low`, `medium`, `high` |
| `actions[].summary` | string | yes | One-line issue description |
| `actions[].remediation` | string | yes | What to do |
| `actions[].affected_urls` | string\[\] | yes | URLs where this issue appears |
| `actions[].page_type` | string/null | no | Page type if page-specific |
| `actions[].depends_on` | string\[\] | yes | Issue IDs that should be resolved first |

### Tier Definitions

| Tier | Name | Focus |
| --- | --- | --- |
| 1 | Foundation — Crawlability & Policy | robots.txt, llms.txt, basic accessibility |
| 2 | Structure — Schema & Metadata | JSON-LD, meta tags, OG, canonicals |
| 3 | Content — Depth & Coverage | FAQ, content gaps, query coverage |
| 4 | Optimization — Retrieval & Citation Quality | Chunking, heading hierarchy, E-E-A-T |

---

## 3. morphiq-build

### Workflow

morphiq-build fixes the issues generated by morphiq-rank. It consumes the Prioritized Roadmap and produces build artifacts — the actual content, schema, and policy files that resolve each issue.

morphiq-build has two entry points that converge to the same output format:

- **From prompt** (Content Creation workflow): User describes what to create, or content creation briefs from the tracker are used → content lab pipeline generates it
- **From existing content** (Content Optimization workflow): Existing content is ingested → analyzed for gaps → enriched → rewritten as final optimized output

Both entry points run through the 5-step content lab pipeline (`content-lab-pipeline.md`):

1. **Ingest Sources** — URL validation, deduplication, fetch content
2. **Extract Content** — HTML to markdown conversion, structure preservation
3. **Analyze Gaps** — Identify content, data, format, and depth gaps (`gap-taxonomy.md`)
4. **Research to Fill Gaps** — Live web search for statistics, citations, expert quotes (`enrichment-sources.md`)
5. **Generate/Rewrite** — Apply content quality standards, metadata optimization, schema injection

Post-pipeline: FAQs (`faq-guidelines.md`), metadata (`metadata-patterns.md`), JSON-LD schema (`schema-templates.md`), `llms.txt` generation (`llms-txt-spec.md`).

### Contract: Build Output

```json
{
  "schema_version": "1.0",
  "generated_at": "2025-03-25T15:00:00Z",
  "domain": "example.com",
  "source_roadmap_score": 62,
  "entry_point": "existing_content",
  "artifacts": [
    {
      "artifact_id": "build-001",
      "type": "content",
      "action_ref": {
        "issue_id": "content-thin-faq",
        "priority": 4,
        "tier": 3
      },
      "target_url": "https://example.com/product",
      "page_type": "product",
      "title": "Product FAQ Section",
      "content": {
        "format": "html",
        "body": "<section class=\"faq\"><h2>Frequently Asked Questions</h2>..."
      },
      "placement": {
        "instruction": "Add after the product features section and before the CTA",
        "selector": "section.product-features"
      }
    },
    {
      "artifact_id": "build-002",
      "type": "schema",
      "action_ref": {
        "issue_id": "agentic-missing-product-schema",
        "priority": 3,
        "tier": 2
      },
      "target_url": "https://example.com/product",
      "page_type": "product",
      "title": "Product JSON-LD Schema",
      "content": {
        "format": "json-ld",
        "body": "{\"@context\":\"https://schema.org\",\"@type\":\"Product\",...}"
      },
      "placement": {
        "instruction": "Add to <head> as <script type=\"application/ld+json\">",
        "selector": "head"
      }
    },
    {
      "artifact_id": "build-003",
      "type": "policy_file",
      "action_ref": {
        "issue_id": "policy-no-llms-txt",
        "priority": 2,
        "tier": 1
      },
      "target_url": "https://example.com/llms.txt",
      "page_type": null,
      "title": "llms.txt",
      "content": {
        "format": "text",
        "body": "# example.com\n\n> Example Company builds widgets for teams...\n\n## Key Pages\n..."
      },
      "placement": {
        "instruction": "Create file at site root: /llms.txt",
        "selector": null
      }
    },
    {
      "artifact_id": "build-004",
      "type": "metadata",
      "action_ref": {
        "issue_id": "agentic-weak-meta-description",
        "priority": 6,
        "tier": 2
      },
      "target_url": "https://example.com/product",
      "page_type": "product",
      "title": "Optimized Meta Description",
      "content": {
        "format": "meta",
        "body": {
          "description": "Example Widget helps teams collaborate 3x faster. Compare features, pricing, and integrations.",
          "og_description": "Example Widget helps teams collaborate 3x faster.",
          "title": "Example Widget — Team Collaboration Tool | Example Company"
        }
      },
      "placement": {
        "instruction": "Replace existing meta description and OG tags in <head>",
        "selector": "head"
      }
    }
  ],
  "summary": {
    "total_artifacts": 4,
    "by_type": {
      "content": 1,
      "schema": 1,
      "policy_file": 1,
      "metadata": 1
    },
    "issues_addressed": ["content-thin-faq", "agentic-missing-product-schema", "policy-no-llms-txt", "agentic-weak-meta-description"],
    "tiers_covered": [1, 2, 3]
  }
}
```

### Field Definitions

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `schema_version` | string | yes | Always `"1.0"` |
| `generated_at` | ISO 8601 | yes | When the build ran |
| `domain` | string | yes | Carried from roadmap |
| `source_roadmap_score` | integer | yes | The scan score from the roadmap |
| `entry_point` | enum | yes | `prompt` or `existing_content` |
| `artifacts[]` | array | yes | All generated artifacts |
| `artifacts[].artifact_id` | string | yes | Unique ID for this artifact (`build-NNN`) |
| `artifacts[].type` | enum | yes | `content`, `schema`, `policy_file`, `metadata`, `robots_txt_rule` |
| `artifacts[].action_ref` | object | yes | Links back to the roadmap action |
| `artifacts[].action_ref.issue_id` | string | yes | The issue this artifact addresses |
| `artifacts[].action_ref.priority` | integer | yes | Priority from roadmap |
| `artifacts[].action_ref.tier` | integer | yes | Tier from roadmap |
| `artifacts[].target_url` | string | yes | URL this artifact targets |
| `artifacts[].page_type` | string/null | no | Page type if applicable |
| `artifacts[].title` | string | yes | Human-readable artifact name |
| `artifacts[].content.format` | enum | yes | `html`, `json-ld`, `text`, `meta`, `markdown` |
| `artifacts[].content.body` | string/object | yes | The actual content (string for html/json-ld/text/markdown, object for meta) |
| `artifacts[].placement` | object | yes | Where and how to insert the artifact |
| `artifacts[].placement.instruction` | string | yes | Human/agent-readable placement instruction |
| `artifacts[].placement.selector` | string/null | no | CSS selector if applicable |
| `summary` | object | yes | Rollup of what was built |

---

## 4. morphiq-track

### Workflow

morphiq-track is the measurement and flywheel skill. It generates and maintains `MORPHIQ-TRACKER.md` — the persistent state file that every subsequent run reads and updates. The tracker stores scores, open issues, SoV deltas, prompt results, competitor data, and content creation queues.

morphiq-track drives three distinct workflows:

### Workflow A: Content Optimization

**Trigger:** User has existing website content (pages, blog posts) that needs AI visibility enrichment.

**What it does:**
1. Reads `MORPHIQ-TRACKER.md` for current state — open issues, scores, previous deltas
2. Takes existing content and runs it through the 5-step content lab pipeline (via morphiq-build, entry point: `existing_content`)
3. Does NOT re-process the original input sources — only enriches the content itself (adds citations, restructures for chunking, improves E-E-A-T signals, injects schema)
4. Updates `MORPHIQ-TRACKER.md` with resolved issues, new scores

**Flow:**
```
MORPHIQ-TRACKER.md (current state)
  → identify pages with open issues
  → morphiq-build (entry: existing_content)
  → 5-step content lab pipeline (enrich only, not re-ingest)
  → artifacts produced
  → MORPHIQ-TRACKER.md updated (issues marked resolved)
```

### Workflow B: Content Creation

**Trigger:** User wants to create new content to fill gaps identified by scan or tracking.

**What it does:**
1. Reads `MORPHIQ-TRACKER.md` for current blog posts, tracked prompts, and content creation queue
2. Runs `create-prompts.py` — generates prompts derived from existing content, tracked queries, and query fanout gaps
3. Runs `run-queries.py` — executes prompts against LLM providers (OpenAI, Gemini, Perplexity, Anthropic) to gather input
4. Stores results in `MORPHIQ-TRACKER.md` — prompt results, model outputs, competitor mentions, citation data
5. Takes the gathered input (existing sources + prompt results) and runs it through the 5-step content lab pipeline (via morphiq-build, entry point: `prompt`)
6. Updates `MORPHIQ-TRACKER.md` with new content entries, updated SoV, new baselines

**Flow:**
```
MORPHIQ-TRACKER.md (current state + existing blog posts)
  → create-prompts.py (generate prompts from content + gaps)
  → run-queries.py (execute against LLM providers)
  → store results in MORPHIQ-TRACKER.md (prompts, competitors, deltas)
  → morphiq-build (entry: prompt, with gathered sources)
  → 5-step content lab pipeline (full creation)
  → artifacts produced
  → MORPHIQ-TRACKER.md updated (new content tracked, SoV baselines set)
```

### Workflow C: Query Fanout Content Generation

**Trigger:** User wants to expand content coverage by creating sub-content derived from existing content's query chains.

**What it does:**
For each existing piece of content (blog post, product page), morphiq-track:

1. Identifies the prompt or topic that the content addresses
2. Simulates the query fanout — the sub-queries a model would chain when a user asks that prompt (e.g., if the blog is about "best CRM tools," models would chain: "CRM pricing comparison," "CRM for small business," "CRM implementation timeline," etc.)
3. Checks whether the site already has content answering each sub-query
4. For unanswered sub-queries, creates content creation briefs
5. Each brief enters the content creation queue in `MORPHIQ-TRACKER.md`
6. When the user triggers content creation, these briefs flow through Workflow B (create-prompts → run-queries → content lab pipeline)

**Flow:**
```
Existing content (blogs, pages)
  → for each piece: derive sub-queries models would chain
  → check site coverage for each sub-query
  → unanswered sub-queries → content creation briefs
  → briefs added to MORPHIQ-TRACKER.md content creation queue
  → user triggers Workflow B → briefs become new content
  → MORPHIQ-TRACKER.md updated
```

**Key distinction from Scan's query fanout:** Scan performs diagnostic fanout at the site level ("can the site answer what models would ask about this company?"). Track performs generative fanout at the per-content level ("for this specific blog post, what follow-up queries would models chain, and should we create content for them?"). Scan identifies the gap. Track fills it.

### Contract: Delta Report

morphiq-track produces a **delta report** — a comparison between the current measurement run and the previous one, showing what changed in AI visibility.

This report loops back to morphiq-rank as supplementary input for re-prioritization.

```json
{
  "schema_version": "1.0",
  "generated_at": "2025-03-25T16:00:00Z",
  "domain": "example.com",
  "run_id": "track-2025-03-25",
  "previous_run_id": "track-2025-03-18",
  "is_baseline": false,
  "providers_queried": ["openai", "gemini", "perplexity", "anthropic"],
  "prompt_count": 25,
  "share_of_voice": {
    "current": 34.2,
    "previous": 28.6,
    "delta": 5.6,
    "breakdown": {
      "openai": { "current": 40.0, "previous": 32.0, "delta": 8.0 },
      "gemini": { "current": 30.0, "previous": 26.0, "delta": 4.0 },
      "perplexity": { "current": 38.0, "previous": 30.0, "delta": 8.0 },
      "anthropic": { "current": 28.8, "previous": 26.4, "delta": 2.4 }
    }
  },
  "citations": {
    "gained": [
      {
        "url": "https://example.com/product",
        "provider": "openai",
        "prompt": "best widgets for teams",
        "prompt_type": "category",
        "first_seen": "2025-03-25"
      }
    ],
    "lost": [],
    "stable": [
      {
        "url": "https://example.com/",
        "provider": "perplexity",
        "prompt": "what is Example Company",
        "prompt_type": "brand"
      }
    ]
  },
  "mentions": {
    "current_total": 41,
    "previous_total": 34,
    "delta": 7,
    "by_prompt_type": {
      "brand": { "current": 12, "previous": 10, "delta": 2 },
      "category": { "current": 8, "previous": 5, "delta": 3 },
      "comparison": { "current": 6, "previous": 6, "delta": 0 },
      "feature": { "current": 9, "previous": 8, "delta": 1 },
      "use_case": { "current": 6, "previous": 5, "delta": 1 }
    }
  },
  "competitor_mentions": [
    {
      "company": "Competitor A",
      "current_mentions": 52,
      "previous_mentions": 50,
      "delta": 2,
      "share_of_voice": 43.3
    }
  ],
  "flagged_actions": [
    {
      "type": "citation_opportunity",
      "summary": "Product page now cited by OpenAI for category queries — consider expanding comparison content to capture comparison queries too",
      "related_prompt_type": "comparison",
      "suggested_issue_id": "content-no-comparison"
    }
  ],
  "content_creation_queue": [
    {
      "brief_id": "brief-001",
      "source_content": "https://example.com/blog/best-widgets",
      "derived_query": "widget pricing comparison 2025",
      "rationale": "Sub-query chained from 'best widgets for teams' — no site content answers this",
      "status": "pending",
      "created_at": "2025-03-25"
    }
  ],
  "raw_results": {
    "storage": "morphiq-track/results/track-2025-03-25.json",
    "format": "Per-provider raw responses stored separately for audit"
  }
}
```

### Field Definitions

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `schema_version` | string | yes | Always `"1.0"` |
| `generated_at` | ISO 8601 | yes | When the tracking run completed |
| `domain` | string | yes | Domain being tracked |
| `run_id` | string | yes | Unique run identifier |
| `previous_run_id` | string/null | yes | Previous run for delta comparison (null if baseline) |
| `is_baseline` | boolean | yes | True if this is the first run (no delta) |
| `providers_queried` | string\[\] | yes | Which AI providers were queried |
| `prompt_count` | integer | yes | Total prompts fired |
| `share_of_voice` | object | yes | SoV calculation: (company mentions / total mentions) x 100 |
| `share_of_voice.current` | float | yes | Current run SoV percentage |
| `share_of_voice.previous` | float/null | yes | Previous run SoV (null if baseline) |
| `share_of_voice.delta` | float/null | yes | Change in SoV |
| `share_of_voice.breakdown` | object | yes | Per-provider SoV |
| `citations` | object | yes | URL-level citation tracking |
| `citations.gained[]` | array | yes | New citations since last run |
| `citations.lost[]` | array | yes | Citations that disappeared |
| `citations.stable[]` | array | yes | Citations maintained |
| `mentions` | object | yes | Mention count tracking |
| `mentions.by_prompt_type` | object | yes | Breakdown by prompt category |
| `competitor_mentions[]` | array | no | Competitor tracking if configured |
| `flagged_actions[]` | array | yes | Suggested next actions based on deltas |
| `flagged_actions[].type` | enum | yes | `citation_opportunity`, `citation_loss`, `sov_drop`, `competitor_gain` |
| `flagged_actions[].suggested_issue_id` | string | no | Issue ID format for feeding back to morphiq-rank |
| `content_creation_queue[]` | array | yes | Content briefs from query fanout (Workflow C) |
| `content_creation_queue[].brief_id` | string | yes | Unique brief identifier |
| `content_creation_queue[].source_content` | string | yes | URL of the content that generated this brief |
| `content_creation_queue[].derived_query` | string | yes | The sub-query to create content for |
| `content_creation_queue[].rationale` | string | yes | Why this sub-query matters |
| `content_creation_queue[].status` | enum | yes | `pending`, `in_progress`, `completed` |
| `content_creation_queue[].created_at` | string | yes | ISO date when brief was created |
| `raw_results` | object | yes | Pointer to raw provider response data |

### Baseline Run Behavior

On the first run (`is_baseline: true`):

- `previous_run_id` is `null`
- All `delta` fields are `null`
- `citations.gained` contains all found citations
- `citations.lost` and `citations.stable` are empty
- The report establishes the measurement baseline

### Loop Back to morphiq-rank

When morphiq-track output is fed back to morphiq-rank:

1. `flagged_actions` with `suggested_issue_id` are treated as new issues
2. Citation losses trigger severity escalation of related existing issues
3. SoV drops trigger re-prioritization of the affected prompt type categories
4. The rank skill merges these with any existing scan report issues
5. `content_creation_queue` briefs with `status: pending` are surfaced as content gap issues

---

## 5. MORPHIQ-TRACKER.md

### Purpose

`MORPHIQ-TRACKER.md` is the persistent state file that lives in the user's project root. Every skill reads it, every skill writes to it. It is the shared state that makes the pipeline loop work without requiring a database or external service.

It is generated by morphiq-track on first run and updated on every subsequent run of any skill.

### Full Specification

The complete tracker specification — all 14 sections, KPI definitions, calculation formulas, and per-skill update rules — is defined in:

> `morphiq-track/references/tracker-spec.md`

### Sections Overview

| # | Section | What it tracks | Primary owner |
| --- | --- | --- | --- |
| 1 | Score Summary | Aggregate score + run counts | morphiq-scan |
| 2 | Score Breakdown by Category | Per-category scores with deltas | morphiq-scan |
| 3 | Open Issues | All unresolved issues with status | morphiq-scan, morphiq-build |
| 4 | Resolved Issues | Fixed issues with verification status | morphiq-build, morphiq-scan |
| 5 | Share of Voice | Current SoV per provider | morphiq-track |
| 6 | SoV Trend | Historical SoV across all runs | morphiq-track |
| 7 | Citation Analytics | Gained/lost/stable citations + history | morphiq-track |
| 8 | Tracked Prompts | All prompts with mention/citation status | morphiq-track |
| 9 | Competitors | Competitor mentions, SoV, trends | morphiq-track |
| 10 | Per-Page Performance | Per-URL scores, citations, issues | morphiq-scan, morphiq-track |
| 11 | Content Performance | Whether built artifacts get cited | morphiq-build, morphiq-track |
| 12 | Query Fanout Coverage | Coverage score progression + brief tracking | morphiq-scan, morphiq-track |
| 13 | Content Creation Queue | Briefs from query fanout with status | morphiq-track, morphiq-build |
| 14 | Run History | Every pipeline run with snapshot data | all skills |

### What Each Skill Does to the Tracker

| Skill | Reads | Writes |
| --- | --- | --- |
| morphiq-scan | Previous scores, previous issues | Refreshes scores (sections 1-2), refreshes issue list (3-4), refreshes per-page performance (10), refreshes query fanout coverage (12), appends run history (14) |
| morphiq-rank | Issue list, scores | Reorders issue priorities (3), appends run history (14) |
| morphiq-build | Open issues, content creation queue | Marks issues resolved (3→4), adds content performance entries (11), updates content creation queue (13), appends run history (14) |
| morphiq-track | Everything | Updates SoV (5-6), citation analytics (7), tracked prompts (8), competitors (9), per-page citations (10), content citation status (11), query fanout coverage (12), content creation queue (13), appends run history (14) |

### State Management

- **Each run appends** to run history and updates the sections that skill owns
- **Git provides the full audit trail** — every change to the tracker is a commit, so `git log MORPHIQ-TRACKER.md` shows the complete history
- **The scan is always the source of truth** — if the tracker and reality diverge (user edited the site outside the skill), the next scan refreshes the issue list and scores
- **Stale tracker is fine** — users re-scan when they're ready; the system is on-demand, not a daemon
- **Regressions are detected** — if a resolved issue reappears on re-scan, it moves back to Open Issues with status `regressed`

---

## Data Flow Summary

```
INITIAL AUDIT
==============

  User: "Use Morphiq Scan to audit the website, then use Morphiq Rank to create the issues"

  ┌─────────────┐     Scan Report       ┌──────────────┐
  │ morphiq-scan │  ──────────────────→  │ morphiq-rank │
  │              │     (JSON, ~50KB)     │              │
  │ 5 categories │                       │ 4 tiers      │
  │ 100pt rubric │                       │ impact/effort│
  └─────────────┘                        └──────┬───────┘
                                                │
                                       Prioritized Roadmap
                                         (JSON, ~20KB)
                                                │
                                                ▼
                                          User reviews issues


FIX ISSUES
===========

  User: "Use Morphiq Build to fix the issues"

                                       Prioritized Roadmap
                                                │
                                                ▼
                              ┌───────────────────────────────────┐
                              │          morphiq-build            │
                              │                                   │
                              │  5-step content lab pipeline      │
                              │  → artifacts (content, schema,    │
                              │    policy files, metadata)        │
                              └──────────────┬────────────────────┘
                                             │
                                       Build Output
                                      (JSON, ~100KB)


ONGOING: CONTENT OPTIMIZATION (Workflow A)
===========================================

  User: "Use Morphiq Build to optimize existing content"

  MORPHIQ-TRACKER.md (current state)
        │
        ▼
  Identify pages with open issues
        │
        ▼
  morphiq-build (entry: existing_content)
        │
        ▼
  5-step pipeline (enrich only)
        │
        ▼
  MORPHIQ-TRACKER.md updated (issues resolved)


ONGOING: CONTENT CREATION (Workflow B)
=======================================

  User: "Use Morphiq Build to create new content"

  MORPHIQ-TRACKER.md + existing blog posts
        │
        ▼
  create-prompts.py (generate prompts from content + gaps)
        │
        ▼
  run-queries.py (execute against OpenAI, Gemini, Perplexity, Anthropic)
        │
        ▼
  Store results in MORPHIQ-TRACKER.md (prompts, competitors, deltas)
        │
        ▼
  morphiq-build (entry: prompt, with gathered sources)
        │
        ▼
  5-step content lab pipeline (full creation)
        │
        ▼
  MORPHIQ-TRACKER.md updated (new content tracked, SoV baselines)


ONGOING: QUERY FANOUT EXPANSION (Workflow C)
=============================================

  Existing content (blogs, pages)
        │
        ▼
  For each piece: derive sub-queries models would chain
        │
        ▼
  Check site coverage for each sub-query
        │
        ▼
  Unanswered sub-queries → content creation briefs
        │
        ▼
  Briefs added to MORPHIQ-TRACKER.md content creation queue
        │
        ▼
  User triggers Workflow B → briefs become new content


MEASUREMENT LOOP
=================

  User: "Use Morphiq Track to run a tracking cycle"

  ┌───────────────────────────┐
  │      morphiq-track        │
  │                           │
  │  Queries: OpenAI, Gemini, │
  │  Perplexity, Anthropic    │
  └──────────────┬────────────┘
                 │
            Delta Report
           (JSON, ~30KB)
                 │
                 ├──→ MORPHIQ-TRACKER.md updated
                 │
                 └──→ Back to morphiq-rank
                      (supplementary input for re-prioritization)


RE-AUDIT (after user edits outside the skill)
===============================================

  User makes changes → runs Morphiq Scan again
        │
        ▼
  New scan detects current site state
        │
        ▼
  MORPHIQ-TRACKER.md refreshed (new scores, updated issues)
        │
        ▼
  morphiq-rank re-prioritizes
        │
        ▼
  Cycle continues
```

## Versioning

All contracts use `schema_version: "1.0"`. When breaking changes are introduced:

1. Bump `schema_version`
2. Skills must check `schema_version` and fail with a clear message if incompatible
3. CHANGELOG.md tracks contract changes
