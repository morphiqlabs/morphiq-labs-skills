# Issue Catalog

Use this reference when morphiq-rank creates issues from a scan report. This document defines all issue type families, their trigger conditions, severity logic, and the standard issue format.

## Issue Format

Every issue follows this standard structure:

| Field | Description |
|---|---|
| `id` | Unique identifier in `{category}-{specific-problem}` format |
| `category` | One of: `agentic_readiness`, `content_quality`, `chunking_retrieval`, `query_fanout`, `policy_files`, `ai_visibility` |
| `severity` | `critical`, `high`, `medium`, `low` |
| `summary` | One-line human-readable description |
| `detail` | Full explanation of the issue and its AI visibility impact |
| `affected_urls` | URLs where the issue appears |
| `remediation_hint` | Actionable fix instruction |

## Severity Definitions

| Severity | Definition | AI Visibility Impact |
|---|---|---|
| `critical` | Blocks AI access entirely | Models cannot reach or parse the site at all |
| `high` | Directly suppresses citations | Models can access the site but are unlikely to cite it |
| `medium` | Weakens citation quality or coverage | Models may cite but with lower confidence or frequency |
| `low` | Optimization opportunity | Site functions but leaves visibility on the table |

---

## Issue Type Families

### `agentic-*` — Agentic Readiness Issues

Issues with machine-readable structure that prevent AI agents from extracting facts.

| Issue ID | Severity | Trigger | Remediation |
|---|---|---|---|
| `agentic-missing-product-schema` | high | Product page has no JSON-LD Product markup | Add Product schema with name, description, offers, aggregateRating |
| `agentic-missing-article-schema` | high | Blog/article page has no Article or BlogPosting schema | Add Article/BlogPosting schema with headline, author, datePublished |
| `agentic-missing-faq-schema` | medium | Page has FAQ content but no FAQPage schema | Add FAQPage schema wrapping existing Q&A content |
| `agentic-missing-howto-schema` | medium | Step-by-step content has no HowTo schema | Add HowTo schema with step names and descriptions |
| `agentic-missing-breadcrumb` | medium | No BreadcrumbList schema for navigation | Add BreadcrumbList schema reflecting site hierarchy |
| `agentic-no-canonical` | high | Missing canonical URL | Add canonical link element pointing to the preferred URL |
| `agentic-broken-heading-hierarchy` | high | Heading levels skipped or multiple H1s | Fix heading hierarchy to be sequential without skips |
| `agentic-weak-meta-description` | medium | Meta description missing, too short (<100 chars), or too long (>160 chars) | Write a 150–160 character meta description reflecting the page's core query |
| `agentic-missing-og-tags` | low | No Open Graph tags | Add og:title, og:description, og:image, og:url |
| `agentic-no-semantic-html` | medium | Page uses div soup instead of semantic elements | Convert to semantic HTML (nav, main, article, section, aside) |
| `agentic-duplicate-schema` | low | Multiple conflicting schema types on same page | Consolidate to one authoritative schema per type |

---

### `content-*` — Content Quality Issues

Issues with content depth, authority, and citation-readiness.

| Issue ID | Severity | Effort | Trigger | Remediation |
|---|---|---|---|---|
| `content-thin-page` | high | high | Page has fewer than 150 words of body content | Expand content to minimum 300 words with substantive information |
| `content-low-word-count` | medium | medium | Page has 150–300 words — insufficient depth | Expand content to 500+ words with supporting detail and examples |
| `content-no-tldr` | medium | low | No summary or direct answer at top of page | Add TL;DR or direct-answer block within first 2–3 sentences |
| `content-no-author` | medium | low | No author attribution or credentials | Add visible author byline with name, role, and credentials |
| `content-unsourced-stats` | high | medium | Statistics stated without source attribution | Add name-drop + link format for every statistic |
| `content-wrong-citation-format` | medium | medium | Citations use trailing parenthetical instead of name-drop format | Rewrite citations: "According to [Source](url), ..." |
| `content-no-expert-quotes` | medium | medium | No expert quotes with in-text attribution | Add at least 1 expert quote with speaker name + credential in sentence |
| `content-stale-date` | medium | low | Content date older than 18 months on fast-moving topics | Update content and publication/last-updated date |
| `content-thin-faq` | medium | medium | No or insufficient FAQ content on informational pages | Add 3–5 FAQs covering realistic user questions |
| `content-fabricated-examples` | high | high | Case studies appear fictional or unverifiable | Replace with real, sourced case studies with metrics |
| `content-no-examples` | low | medium | No case studies or concrete examples | Add at least 1 real example with problem, approach, outcome |
| `content-generic-advice` | medium | high | Content is surface-level with no specific implementation detail | Add depth: methodology, steps, metrics, named examples |

---

### `chunking-*` — Chunking & Retrieval Issues

Issues with content structure that impair LLM retrieval, grounding, and citation.

| Issue ID | Severity | Effort | Trigger | Remediation |
|---|---|---|---|---|
| `chunking-broken-heading-hierarchy` | high | low | Heading levels skipped or multiple H1s | Fix heading levels to be sequential |
| `chunking-generic-headings` | medium | medium | Headings are vague ("Overview", "Details", "More Info") | Rewrite headings as specific statements or likely queries |
| `chunking-overscoped-section` | medium | medium | Section covers multiple unrelated ideas | Split into focused sections, one major idea per heading |
| `chunking-weak-local-context` | medium | medium | Paragraphs rely on context from elsewhere on the page | Add explicit subjects, entities, and timeframes locally |
| `chunking-buried-answer` | high | medium | Answer buried after multiple preamble paragraphs | Move direct answer to first paragraph under the heading |
| `chunking-missing-query-terms` | medium | medium | Page lacks literal terminology users would search | Add exact-match terms, product names, and category language |
| `chunking-long-paragraphs` | medium | medium | Paragraphs exceed retrieval-friendly length (>100 words) | Split into focused paragraphs of 50–75 words |
| `chunking-poor-paragraph-structure` | medium | medium | Paragraphs mix multiple ideas without clear boundaries | Restructure so each paragraph expresses one main idea |
| `chunking-prose-instead-of-list` | low | low | Sequential steps described in paragraph form | Convert to numbered list |
| `chunking-unparseable-table` | medium | medium | Comparison data in prose or image-based tables | Convert to parseable HTML tables with clear headers |
| `chunking-no-faq-coverage` | low | medium | Informational page has no FAQ section | Add FAQ with 3–5 Q&As covering adjacent intent |
| `chunking-no-top-summary` | medium | low | Long-form page has no top-of-page summary | Add TL;DR or summary block near the top |
| `chunking-ambiguous-paragraphs` | medium | medium | Pronoun-heavy paragraphs with unclear referents | Make subjects explicit and reduce pronoun chains |
| `chunking-split-supporting-evidence` | low | medium | Evidence for a claim is in a different section | Move supporting data near the claim it supports |

---

### `policy-*` — Policy File Issues

Issues with AI crawler access and machine-readable navigation aids.

| Issue ID | Severity | Effort | Trigger | Remediation |
|---|---|---|---|---|
| `policy-blocks-gptbot` | high | low | robots.txt blocks GPTBot | Remove GPTBot disallow rule |
| `policy-blocks-google-extended` | high | low | robots.txt blocks Google-Extended | Remove Google-Extended disallow rule |
| `policy-blocks-anthropic` | high | low | robots.txt blocks Anthropic-AI or ClaudeBot | Remove Anthropic/Claude disallow rule |
| `policy-blocks-perplexity` | medium | low | robots.txt blocks PerplexityBot | Remove PerplexityBot disallow rule |
| `policy-no-robots-txt` | medium | low | No robots.txt file at domain root | Create robots.txt allowing major AI crawlers |
| `policy-invalid-robots-syntax` | low | low | robots.txt has syntax errors | Fix syntax per robots.txt specification |
| `policy-no-llms-txt` | high | medium | No llms.txt file at /llms.txt | Create llms.txt following the spec |
| `policy-weak-llms-txt` | medium | medium | llms.txt exists but lacks key sections or is poorly structured | Improve llms.txt with site summary, key pages, navigation aids |

---

### `fanout-*` — Query Fanout Coverage Issues

Issues where the site cannot answer sub-queries that AI models would chain about the company, its products, or its content. These are **topical coverage gaps** — structurally different from content quality or chunking issues because the fix is typically to create new content, not improve existing content.

#### Trigger Conditions

A fanout issue is triggered when:
1. **Sub-query unanswered** — No page on the site matches the simulated sub-query
2. **Sub-query answered on wrong page type** — The answer exists but on an inappropriate page (e.g., pricing info only in a blog post, not on a dedicated pricing page)
3. **Entity missing dedicated coverage** — A comparison page mentions an entity but no page provides dedicated coverage for it

#### Severity Logic

Severity is determined by the **fan-out depth of the parent prompt type** combined with the **citation weight** of the sub-query:

| Parent Prompt Type | Avg Fan-outs | Base Severity | Rationale |
|---|---|---|---|
| `technical_eval` | 11.0 | high | Most visibility surface area — each gap is a missed citation opportunity |
| `discovery` | 7.5 | high | Landscape-building queries shape which brands the model includes |
| `recommendation` | 5.8 | medium | Drives purchase intent responses |
| `comparison` | 5.4 | medium | Always decomposes per-entity — missing entity = missing from comparison |
| `problem_seeking` | 2.8 | medium | Solution landscape, but lower fan-out |
| `use_case` | 2.4 | low | Narrow focus, fewer sub-queries at stake |

**Severity escalation rules:**
- If the sub-query is a `site:` operator query (GPT-5.4 behavior): escalate one level — the model explicitly searched the audited site and found nothing
- If the sub-query is citation-producing (pricing, features, comparison): escalate one level
- If the sub-query is silent/informational only: no escalation

#### Issue Types

| Issue ID | Severity | Effort | Trigger | Remediation |
|---|---|---|---|---|
| `fanout-no-comparison-content` | high | high | No content addressing competitor comparison queries | Create comparison page or section with per-entity analysis |
| `fanout-no-pricing-content` | high | high | No structured pricing content for pricing sub-queries | Create dedicated pricing page with plan details, feature breakdown |
| `fanout-no-alternative-content` | medium | high | No "alternative to [competitor]" content (Gemini exposure) | Create alternative-to pages for top competitors |
| `fanout-missing-entity-coverage` | medium | high | Comparison mentions entity but no dedicated page exists | Create dedicated content for each entity in comparisons |
| `fanout-wrong-page-type` | medium | medium | Answer exists but on wrong page type | Move or duplicate key information to the appropriate page type |
| `fanout-no-site-match` | high | high | GPT-5.4 `site:` simulation returns no relevant page | Create or optimize page for the specific `site:` query topic |
| `fanout-stale-temporal` | medium | low | Content lacks year markers, reducing search trigger probability | Add temporal markers (year, "latest", "updated") to key content |
| `fanout-unanswered-subquery` | varies | high | Specific simulated sub-query has no matching page | Create content targeting the unanswered sub-query |
| `fanout-thin-topic-coverage` | medium | high | Topic covered superficially — deeper sub-queries go unanswered | Expand content depth or create supporting pages for sub-topics |
| `fanout-no-docs-content` | medium | high | No documentation or how-to content for implementation sub-queries | Create docs or guide content for implementation queries |

---

## `visibility-*` — AI Visibility Issues

Issues detected during morphiq-track that indicate problems with brand presence in AI responses. These are brand-level issues, not per-page.

| Issue ID | Category | Severity | Effort | Trigger | Remediation |
|---|---|---|---|---|---|
| `visibility-low-mention-rate` | `ai_visibility` | high | high | Brand mentioned in <40% of prompts across providers | Improve content authority, add structured data, create comparison/alternative content |
| `visibility-weak-citations` | `ai_visibility` | medium | high | Brand mentioned but cited (URL linked) in <30% of mentions | Strengthen citation signals — name-drop format, source authority, statistics |
| `visibility-poor-position` | `ai_visibility` | medium | high | Average brand position >3 in ranked lists | Improve content depth, add comparison tables, strengthen E-E-A-T signals |
| `visibility-negative-sentiment` | `ai_visibility` | high | high | AI portrays brand negatively | Address source content, respond to negative reviews, create counter-narrative content |

### Tier Assignment

Visibility issues are **Tier 3** (Content — Depth & Coverage) because they require content-level interventions. However, they depend on Tier 1 (crawlability) and Tier 2 (structure) being resolved — AI systems must be able to access and parse the site before visibility interventions take effect.

---

## Issue Deduplication

### Technical Issues (per-page)

```
hash = SHA256(brandId + "technical_structure" + checkCode + normalizedPageUrl)
```

The same check on different pages creates different issues.

### AI Visibility Issues (brand-level)

```
hash = SHA256(brandId + category + title)
```

Brand-level issues are not per-page — one issue per brand per type.

---

## Technical Score Check Code Mapping

The per-page Technical Score sub-checks (from `scoring-rubric.md`) map to issue types:

| Check Code | Technical Score Points | Issue Generated |
|---|---|---|
| J1 — No JSON-LD | 10 pts lost | `agentic-missing-product-schema`, `agentic-missing-article-schema`, etc. |
| J2a — Invalid structure | 4 pts lost | Issue with remediation to fix `@context`/`@type` |
| J2b — Missing properties | 4 pts lost | Issue to add Google-required properties |
| J3 — Non-AEO types | 11 pts lost | Issue to switch to AEO-relevant schema types |
| J4 — Incomplete coverage | 11 pts lost | Issue to add missing recommended schemas for page type |
| M1 — Missing title | 8 pts lost | `agentic-missing-title` |
| M2 — Missing description | 8 pts lost | `agentic-weak-meta-description` |
| M3 — Missing canonical | 6 pts lost | `agentic-no-canonical` |
| M4 — Missing OG | 4 pts lost | `agentic-missing-og-tags` |
| M5 — Missing Twitter | 4 pts lost | `agentic-missing-twitter-cards` |
| C1 — Thin content (<150w) | 5 pts lost | `content-thin-page` |
| C1 — Low content (150–300w) | 5 pts lost | `content-low-word-count` |
| C2 — Poor paragraph structure | 5 pts lost | `chunking-poor-paragraph-structure` |
| FAQ — Missing on relevant page | Up to 20 pts lost | `content-thin-faq` or `agentic-missing-faq-schema` |

---

## Tier Assignment Summary

Each issue category has a natural tier affinity. Morphiq-rank uses these defaults, adjusted by impact and dependencies:

| Tier | Name | Primary Categories |
|---|---|---|
| 1 | Foundation — Crawlability & Policy | `policy-*` |
| 2 | Structure — Schema & Metadata | `agentic-*` |
| 3 | Content — Depth & Coverage | `content-*`, `fanout-*`, `visibility-*` |
| 4 | Optimization — Retrieval & Citation Quality | `chunking-*` |

**Fanout issues are Tier 3** because they are content gaps. However, a fanout issue depends on Foundation and Structure being resolved first: new content must be crawlable (Tier 1) and machine-readable (Tier 2) to be effective.

For detailed tier assignment logic and dependency ordering, read `tier-progression.md`.
