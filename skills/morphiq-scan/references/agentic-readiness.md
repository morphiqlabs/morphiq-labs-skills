# Agentic Readiness — Machine-Readable Structure Assessment

Use this reference during morphiq-scan when evaluating whether AI agents can extract structured facts from a website. This document synthesizes the per-page Technical Score methodology with page type expectations to answer: "Can AI systems parse and understand this site?"

## Core Concept

Agentic readiness measures whether a website is machine-readable — whether AI models, agents, and answer engines can extract structured facts, identify entities, and ground citations from the page content. Without agentic readiness, content quality, fan-out coverage, and retrieval optimization are irrelevant: the model cannot parse what it cannot read.

---

## Per-Page Technical Score (0–100)

Each page receives a Technical Score across four dimensions:

| Dimension | Max Points | Weight | Core Question |
|---|---|---|---|
| Schema | 40 | 40% | "Can AI extract structured facts?" |
| Metadata | 30 | 30% | "Can crawlers find and summarize this?" |
| FAQ | 20 | 20% | "Can AI answer questions from this page?" |
| Content | 10 | 10% | "Is there enough signal to reason over?" |

---

### Schema Dimension (40 points)

JSON-LD is the primary way AI systems extract structured facts from pages. This dimension carries the highest weight.

| Check | Points | What to Test |
|---|---|---|
| J1 — Present | 10 | At least one `<script type="application/ld+json">` block exists |
| J2a — Valid Structure | 4 | Every block has `@context` AND `@type` |
| J2b — Required Properties | 4 | All Google-required properties present for each type |
| J3 — Relevant Type | 11 | Schema type is one of the 17 AEO-relevant types |
| J4 — Coverage | 11 | ALL recommended schemas for this page type are present |

**17 AEO-Relevant Schema Types:**
Organization, WebSite, Product, Service, Article, BlogPosting, FAQPage, BreadcrumbList, HowTo, SoftwareApplication, CollectionPage, WebApplication, OfferCatalog, VideoObject, ItemList, Review, Person, AboutPage

**Subtype recognition:** NewsArticle → Article, MobileApplication → SoftwareApplication, LocalBusiness → Organization

**J4 — Coverage evaluation** requires knowing the page type. Match the page type (from `page-type-rules.md`) against the recommended schema list for that type. Score 11 points only if ALL recommended schemas are present.

---

### Metadata Dimension (30 points)

| Check | Points | What to Test |
|---|---|---|
| M1 — Title | 8 | `<title>` tag present and non-empty |
| M2 — Description | 8 | `<meta name="description">` present |
| M3 — Canonical | 6 | `<link rel="canonical">` with `href` |
| M4 — Open Graph | 4 | At least `og:title` OR `og:description` |
| M5 — Twitter Cards | 4 | At least `twitter:card` OR `twitter:title` |

---

### FAQ Dimension (20 points) — Linear Scale

| FAQ Count | Points |
|---|---|
| 0 FAQs | 0 |
| 1 FAQ | 5 |
| 2 FAQs | 10 |
| 3 FAQs | 15 |
| 4+ FAQs | 20 (capped) |

**Scope:** Only applies to marketing-relevant pages (home, pricing, features, product, solutions, blog, use-cases, customers). Non-marketing pages (contact, login, legal) receive 0/0 — not penalized, not counted.

**FAQ Detection Methods** (priority order):
1. JSON-LD `FAQPage` schema with `mainEntity`
2. HTML `<details>`/`<summary>` elements in FAQ containers
3. Accordion patterns (button + collapsed div)
4. Pattern matching (Q: ... A: ... format)

---

### Content Dimension (10 points)

| Check | Points | What to Test |
|---|---|---|
| C1 — Word Count | 5 | Total page text ≥ 300 words |
| C2 — Paragraphs | 5 | At least 3 `<p>` tags |

---

## Score Thresholds

| Score | Rating |
|---|---|
| ≥ 85 | Excellent |
| ≥ 70 | Good |
| ≥ 50 | Needs Improvement |
| < 50 | Poor |

---

## Multi-Page Scoring

- Scrape up to 10 pages per analysis
- Score each marketing page individually (0–100)
- Site Technical Score = average of all marketing page scores
- Non-marketing pages excluded from average (contact, login, signup, legal)
- Page selection priority: home → pricing → features → product → solutions → about → blog → other → documentation

---

## Page Type → Expected Elements

For each page type, there are expected schema types, metadata patterns, and structural elements. These expectations drive the J4 (Coverage) check. For the complete page type classification rules, URL pattern matching, and expected schemas per type, refer to `page-type-rules.md`.

### Key Relationships

- **Schema coverage (J4)** depends on page type detection — a product page without `Product` or `SoftwareApplication` schema fails J4
- **FAQ scoring** depends on page classification — non-marketing pages are excluded
- **SaaS detection** changes expected schemas — `SoftwareApplication` replaces `Product` when SaaS signals are detected

---

## SaaS Detection

A site is classified as SaaS when 2+ of 3 content sources match SaaS indicator terms:

**Content sources:** title + meta description, headings (H1–H3), paragraph text (first 500 words)

**Indicator terms:** platform, saas, cloud, api, sdk, deploy, infrastructure, gpu, serverless, dashboard, cli, developer, subscription, hosted, multi-tenant

When detected, SaaS classification changes the expected schema for product, pricing, features, and solutions pages.

---

## Connection to Pipeline Categories

The per-page Technical Score (0–100) maps to the pipeline's scoring categories:

| Technical Dimension | Feeds Into | Pipeline Points |
|---|---|---|
| Schema (40pts) + Metadata (30pts) | Category 1: Agentic Readiness | 45 pts |
| FAQ (20pts) + structural checks | Category 3: Chunking & Retrieval | 15 pts |
| Content (10pts) + quality checks | Category 2: Content Quality | 20 pts |

The pipeline's 5-category model (100 pts) is a weighted summary. The per-page Technical Score provides the detailed sub-check methodology that feeds into it. For the full 5-category model, refer to `scoring-rubric.md`.
