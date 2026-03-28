# Scoring Rubric — AI Visibility Assessment

Use this reference when calculating scores during a morphiq-scan audit. This document defines both the per-page Technical Score (machine-readability) and the pipeline AI Visibility Score (5-category aggregate), the relationship between them, and how to compute each.

## Two Scoring Systems

Morphiq runs two parallel scoring engines that measure fundamentally different things:

| System | What It Measures | Range | Core Question |
|---|---|---|---|
| Technical Score | Website machine-readability | 0–100 pts | "Can AI systems parse and understand this site?" |
| GEO Score (AI Visibility) | Brand mention rate across AI providers | 0–100% | "Does AI actually mention this brand?" |

Neither directly influences the other — a technically perfect site can still have zero AI visibility, and a highly-mentioned brand can have terrible structured data. Together they form the complete AEO picture.

The Technical Score is computed during **morphiq-scan**. The GEO Score is computed during **morphiq-track** (see `query-targets.md` for GEO methodology).

---

## I. Per-Page Technical Score (0–100)

Each page is scored across four dimensions. This is the detailed per-page methodology.

| Dimension | Max Points | Weight | Core Question |
|---|---|---|---|
| Schema | 40 | 40% | "Can AI extract structured facts?" |
| Metadata | 30 | 30% | "Can crawlers find and summarize this?" |
| FAQ | 20 | 20% | "Can AI answer questions from this page?" |
| Content | 10 | 10% | "Is there enough signal to reason over?" |

### Schema (40 points)

JSON-LD is the primary way AI systems extract structured facts from pages. Schema gets 40% because it is the direct interface between the page and AI agents.

| Check | Points | What to Test |
|---|---|---|
| J1 — Present | 10 | At least one `<script type="application/ld+json">` block exists |
| J2a — Valid Structure | 4 | Every block has `@context` AND `@type` |
| J2b — Required Properties | 4 | All Google-required properties present for each type |
| J3 — Relevant Type | 11 | Schema type is one of 17 AEO-relevant types |
| J4 — Coverage | 11 | ALL recommended schemas for this page type are present |

**17 AEO-Relevant Schema Types:**
Organization, WebSite, Product, Service, Article, BlogPosting, FAQPage, BreadcrumbList, HowTo, SoftwareApplication, CollectionPage, WebApplication, OfferCatalog, VideoObject, ItemList, Review, Person, AboutPage

**Subtype recognition:** NewsArticle → Article, MobileApplication → SoftwareApplication, LocalBusiness → Organization

**J4 — Coverage** requires knowing the page type. Match against the recommended schema list per type (see `page-type-rules.md`). Score 11 only if ALL recommended schemas are present.

### Metadata (30 points)

| Check | Points | What to Test |
|---|---|---|
| M1 — Title | 8 | `<title>` tag present and non-empty |
| M2 — Description | 8 | `<meta name="description">` present |
| M3 — Canonical | 6 | `<link rel="canonical">` with `href` |
| M4 — Open Graph | 4 | At least `og:title` OR `og:description` |
| M5 — Twitter Cards | 4 | At least `twitter:card` OR `twitter:title` |

### FAQ (20 points) — Linear Scale

| FAQ Count | Points |
|---|---|
| 0 | 0 |
| 1 | 5 |
| 2 | 10 |
| 3 | 15 |
| 4+ | 20 (capped) |

Only applies to marketing-relevant pages (home, pricing, features, product, solutions, blog, use-cases, customers). Non-marketing pages receive 0/0 — not penalized, not counted.

FAQ detection methods (priority order):
1. JSON-LD `FAQPage` schema with `mainEntity`
2. HTML `<details>`/`<summary>` in FAQ containers
3. Accordion patterns (button + collapsed div)
4. Pattern matching (Q: ... A: ... format)

### Content (10 points)

| Check | Points | What to Test |
|---|---|---|
| C1 — Word Count | 5 | Total page text ≥ 300 words |
| C2 — Paragraphs | 5 | At least 3 `<p>` tags |

### Per-Page Score Thresholds

| Score | Rating |
|---|---|
| ≥ 85 | Excellent |
| ≥ 70 | Good |
| ≥ 50 | Needs Improvement |
| < 50 | Poor |

### Multi-Page Averaging

- Scrape up to 10 pages per analysis
- Score each marketing page individually (0–100)
- Site Technical Score = average of all marketing page scores
- Non-marketing pages (contact, login, signup, legal) excluded from average

For detailed check procedures, read `agentic-readiness.md`. For page type classification and expected schemas, read `page-type-rules.md`.

---

## II. Pipeline AI Visibility Score (0–100)

The pipeline uses a 5-category model for the aggregate scan score. This is the output that morphiq-rank consumes.

| Category | Max Points | Weight | Reference File |
|---|---|---|---|
| Agentic Readiness | 45 | 45% | `agentic-readiness.md` |
| Content Quality | 20 | 20% | `content-quality.md` |
| Chunking & Retrieval | 15 | 15% | `chunking-retrieval.md` |
| Query Fanout | 10 | 10% | `query-fanout.md` |
| Policy Files | 10 | 10% | `policy-files.md` |
| **Total** | **100** | **100%** | |

### Relationship Between Technical Score and Pipeline Categories

The per-page Technical Score and the pipeline AI Visibility Score are **independent scoring systems** that evaluate overlapping concerns from different angles:

| Technical Score Dimension | Correlated Pipeline Category | Relationship |
|---|---|---|
| Schema (40pts) + Metadata (30pts) | Category 1: Agentic Readiness (45 pts) | Both evaluate machine-readability. High Technical Schema → high Category 1. |
| FAQ (20pts) | Category 3: Chunking & Retrieval (0.75 pts for FAQ) | Technical Score measures FAQ presence/count. Category 3 measures FAQ retrieval quality. A page can have 4 FAQs (full Technical points) but poorly phrased ones (low Category 3). |
| Content (10pts) | Category 2: Content Quality (20 pts) | Technical Score checks word count and paragraph count. Category 2 evaluates E-E-A-T, citations, and depth — a much richer assessment. |

Neither score derives from the other. They are computed independently per page and averaged across scanned pages. A high Technical Score generally correlates with high Pipeline Category scores, but the mapping is not formulaic.

Categories 4 (Query Fanout) and 5 (Policy Files) are domain-level and do not derive from the per-page Technical Score.

---

### Category 1: Agentic Readiness (45 points)

Evaluates whether AI agents can extract structured facts from the page. This is the highest-weighted category because without machine-readable structure, no amount of content quality or fan-out coverage matters — the model cannot parse the page.

#### Scoring Components

| Component | Points | What to Check |
|---|---|---|
| JSON-LD Schema | 15 | Correct schema types for page type, valid markup, key properties populated |
| Semantic HTML | 10 | Proper heading hierarchy, semantic elements (nav, main, article, section), no div soup |
| Metadata | 10 | Title tag, meta description, canonical URL, Open Graph tags — all present and well-formed |
| Structured Data Completeness | 5 | Schema properties beyond minimum (aggregateRating, offers, FAQ, breadcrumb) |
| Page-Type Alignment | 5 | Detected page type matches expected schema and structure patterns |

#### Scoring Method

Evaluate each component per page. The page score is the sum of earned points across all components. The category score is the average across all scanned pages, scaled to the 45-point maximum:

```
category_score = avg_page_percentage × 45
```

#### Fail Conditions (automatic 0 for component)
- No JSON-LD on a page that requires it (product, FAQ, article, how-to)
- Multiple H1 tags or broken heading hierarchy
- Missing canonical URL on any page
- No meta description

For detailed per-page Technical Score sub-checks (J1–J4, M1–M5, C1–C2), read `agentic-readiness.md`.

---

### Category 2: Content Quality (20 points)

Evaluates whether content is citable by AI systems — whether an LLM would confidently reference, quote, or recommend it.

#### Scoring Components

| Component | Points | What to Check |
|---|---|---|
| Clear Relevant Title | 3 | Title specificity, keyword alignment, query match |
| TL;DR / Answer Upfront | 4 | Direct answer placement, conciseness, top-of-page summary |
| E-E-A-T Signals | 6 | Author credentials, first-hand experience, authoritative sources, currency, balanced tone |
| Statistics & Citations | 5 | Count, name-drop + link format, source authority, integration |
| Specific Examples | 2 | Real case studies with metrics (if applicable) |

#### Scoring Method

Evaluate each component per page using the content quality pillar weights. The category score is the average across all scanned pages, scaled to 20 points:

```
category_score = avg_page_percentage × 20
```

#### Fail Conditions
- No author attribution on article/blog pages
- Statistics without source attribution
- Citations using trailing parenthetical instead of name-drop format
- Content date older than 18 months on fast-moving topics

For detailed criteria, read `content-quality.md`.

---

### Category 3: Chunking & Retrieval (15 points)

Evaluates how well content structure supports LLM retrieval, grounding, quoting, and citation.

#### Scoring Components

| Component | Points | What to Check |
|---|---|---|
| Heading Hierarchy & Retrieval Anchors | 3.0 | One H1, proper nesting, query-aligned, section-defining |
| Section Scope & Chunk Boundaries | 3.0 | One major idea per section, clean boundaries, nearby context |
| Paragraph Self-Containment | 2.25 | Compact, explicit local context, low ambiguity |
| Answer-First Openings | 2.25 | Direct answer early under major headings |
| Retrieval Vocabulary Coverage | 1.5 | Exact-match terms + semantic phrasing |
| Lists, Tables & Parseable Structure | 1.5 | Structured formatting, parseable tables |
| FAQ / Query Fan-Out Coverage | 0.75 | Long-tail questions, adjacent intent coverage |
| Top-of-Page Summary | 0.75 | Summary or high-signal block appears early |

#### Scoring Method

Evaluate per page using the chunking evaluation weights. Scale to 15 points:

```
category_score = avg_page_percentage × 15
```

For detailed criteria, read `chunking-retrieval.md`.

---

### Category 4: Query Fanout (10 points)

Evaluates whether the site can answer the sub-queries AI models would chain about the company, its products, and its content. This is the only category scored at the **domain level** rather than per-page.

#### Scoring Method

This category uses simulated sub-query coverage rather than per-page evaluation:

1. **Generate simulated sub-queries** for the domain's core topics using the per-model simulation rules in `query-fanout.md`
2. **Check site coverage** — for each sub-query, determine whether the site has a page that answers it
3. **Apply citation weights:**
   - Citation-producing sub-queries: 1.5x weight
   - Silent sub-queries: 0.5x weight
   - `site:` operator queries (GPT-5.4): 2x weight
4. **Calculate score:** `(weighted answered / weighted total) × 10`

#### Scoring Tiers

| Score | Coverage | Meaning |
|---|---|---|
| 9–10 | 90%+ | Site answers nearly every sub-query |
| 7–8 | 70–80% | Most covered, some adjacent gaps |
| 5–6 | 50–60% | Core covered but half of related sub-queries unanswered |
| 3–4 | 30–40% | Significant gaps — models cannot verify claims |
| 1–2 | 10–20% | Most sub-queries land on competitor sites |
| 0 | 0% | No relevant content for any simulated sub-query |

#### Key Inputs
- Fan-out depth varies by prompt type (`technical_eval`: 11.0 avg, `use_case`: 2.4 avg)
- Fan-out varies by page type (blog posts trigger the deepest fan-out)
- GPT-5.4's `site:` queries create explicit, observable gaps

For detailed simulation rules, read `query-fanout.md`.

---

### Category 5: Policy Files (10 points)

Evaluates whether the site allows AI crawler access and provides machine-readable navigation aids.

#### Scoring Components

| Component | Points | What to Check |
|---|---|---|
| robots.txt AI Crawler Access | 4 | GPTBot, Google-Extended, Anthropic-AI, PerplexityBot allowed |
| robots.txt Compliance | 1 | Valid syntax, no conflicting rules |
| llms.txt Existence | 3 | File exists at /llms.txt |
| llms.txt Quality | 2 | Follows spec, includes site summary, key pages, structured navigation |

#### Scoring Method

Binary + quality assessment at the domain level (not per-page):

- robots.txt: 1 point per major AI crawler allowed (GPTBot, Google-Extended, Anthropic-AI, PerplexityBot), +1 for clean syntax
- llms.txt: 3 points for existence, +2 for quality (spec compliance, useful content)

#### Fail Conditions
- robots.txt blocks any major AI crawler: –1 point per blocked crawler
- No robots.txt at all: 0 for robots.txt components
- No llms.txt: 0 for llms.txt components

For detailed criteria, read `policy-files.md`.

---

## Aggregate Score Calculation

```
overall_score = agentic_readiness + content_quality + chunking_retrieval + query_fanout + policy_files
```

Each category score is an integer. The overall score is the sum (0–100).

### Score Interpretation

| Score Range | Rating | Meaning |
|---|---|---|
| 85–100 | Excellent | Well-optimized for AI visibility across all categories |
| 70–84 | Good | Strong foundation with specific areas for improvement |
| 50–69 | Fair | Meaningful gaps that suppress AI citations |
| 30–49 | Poor | Significant structural and content issues |
| 0–29 | Critical | Site is largely invisible to AI systems |

### Per-Page vs. Domain-Level Scoring

- **Categories 1–3** (Agentic Readiness, Content Quality, Chunking & Retrieval) are scored **per-page** and then averaged across all scanned pages
- **Category 4** (Query Fanout) is scored at the **domain level** — it evaluates whether the site as a whole covers the sub-query landscape
- **Category 5** (Policy Files) is scored at the **domain level** — robots.txt and llms.txt are site-wide files

### Delta Tracking

When a previous scan exists, calculate deltas per category:

```
delta = current_score - previous_score
```

Positive deltas indicate improvement; negative deltas indicate regression. Deltas are recorded in the tracker's Score Breakdown section. For the full delta methodology, read `delta-scoring.md` (morphiq-track).
