# Tier Progression — Progressive Discovery Model

Use this reference when morphiq-rank assigns issues to tiers and sets dependency ordering. This document defines the four progressive discovery tiers, the logic for assigning issues to tiers, and the dependency rules that determine execution order.

## Core Principle

Issues are organized into four tiers that mirror the **order of operations** for AI visibility. Each tier builds on the previous — fixing Structure issues is pointless if Foundation issues prevent AI crawlers from accessing the site. Fixing Content gaps is pointless if the content will not be machine-readable. Optimization only matters when the base content exists.

---

## Tier Definitions

### Tier 1: Foundation — Crawlability & Policy

**Purpose:** Ensure AI crawlers can access the site at all.

**Primary categories:** `policy-*`

**Issues that belong here:**
- robots.txt blocking AI crawlers (`policy-blocks-gptbot`, `policy-blocks-google-extended`, `policy-blocks-anthropic`, `policy-blocks-perplexity`)
- No robots.txt file (`policy-no-robots-txt`)
- Invalid robots.txt syntax (`policy-invalid-robots-syntax`)
- No llms.txt file (`policy-no-llms-txt`)
- Weak llms.txt content (`policy-weak-llms-txt`)

**Exit criteria:** All major AI crawlers (GPTBot, Google-Extended, Anthropic-AI, PerplexityBot) are allowed access. llms.txt exists and provides a machine-readable site overview.

**Why Tier 1:** If crawlers are blocked, nothing downstream matters. No amount of content quality, schema, or fan-out coverage produces citations if the model cannot access the site.

---

### Tier 2: Structure — Schema & Metadata

**Purpose:** Add machine-readable structure so AI can extract facts from pages.

**Primary categories:** `agentic-*`

**Issues that belong here:**
- Missing JSON-LD schema (`agentic-missing-product-schema`, `agentic-missing-article-schema`, `agentic-missing-faq-schema`, `agentic-missing-howto-schema`, `agentic-missing-breadcrumb`)
- Missing or broken heading hierarchy (`agentic-broken-heading-hierarchy`)
- Missing canonical URLs (`agentic-no-canonical`)
- Missing or weak meta descriptions (`agentic-weak-meta-description`)
- Missing Open Graph tags (`agentic-missing-og-tags`)
- No semantic HTML (`agentic-no-semantic-html`)
- Duplicate/conflicting schema (`agentic-duplicate-schema`)

**Exit criteria:** Every page has the correct JSON-LD schema for its type, proper heading hierarchy, canonical URL, and metadata. AI agents can extract structured facts from any page.

**Dependency on Tier 1:** Schema and metadata are only useful if crawlers can access the pages. Resolve all `policy-*` issues before investing in structure.

---

### Tier 3: Content — Depth & Coverage

**Purpose:** Fill content gaps that prevent AI from citing the site.

**Primary categories:** `content-*`, `fanout-*`, `visibility-*`

**Issues that belong here:**

AI visibility issues (brand-level, from morphiq-track):
- Low mention rate (`visibility-low-mention-rate`)
- Weak citations (`visibility-weak-citations`)
- Poor position in ranked lists (`visibility-poor-position`)
- Negative sentiment (`visibility-negative-sentiment`)

Content quality issues:
- Missing TL;DR (`content-no-tldr`)
- Missing author attribution (`content-no-author`)
- Unsourced statistics (`content-unsourced-stats`)
- Wrong citation format (`content-wrong-citation-format`)
- Missing expert quotes (`content-no-expert-quotes`)
- Stale content dates (`content-stale-date`)
- Thin FAQ content (`content-thin-faq`)
- Fabricated examples (`content-fabricated-examples`)
- No examples (`content-no-examples`)
- Generic advice (`content-generic-advice`)

Query fanout gaps:
- No comparison content (`fanout-no-comparison-content`)
- No pricing content (`fanout-no-pricing-content`)
- No alternative-to content (`fanout-no-alternative-content`)
- Missing entity coverage (`fanout-missing-entity-coverage`)
- Wrong page type for answer (`fanout-wrong-page-type`)
- No `site:` match (`fanout-no-site-match`)
- Stale temporal markers (`fanout-stale-temporal`)
- Unanswered sub-queries (`fanout-unanswered-subquery`)
- Thin topic coverage (`fanout-thin-topic-coverage`)
- No documentation content (`fanout-no-docs-content`)

**Exit criteria:** Key content pages meet E-E-A-T standards. The site answers at least 70% of simulated fan-out sub-queries. Comparison, pricing, and features content exists for all core products.

**Dependency on Tier 2:** New content must be machine-readable. If a content page lacks schema, heading structure, and metadata, models cannot extract it effectively — even if the content itself is high quality. Resolve `agentic-*` issues on affected pages before or alongside content creation.

**Ordering within Tier 3:**
1. Fix existing content quality issues first (`content-*`) — these affect pages that already exist
2. Create new content for high-severity fanout gaps (`fanout-no-comparison-content`, `fanout-no-pricing-content`, `fanout-no-site-match`) — these require new pages
3. Create new content for medium-severity fanout gaps (`fanout-no-alternative-content`, `fanout-missing-entity-coverage`) — these expand coverage
4. Address low-severity fanout gaps (`fanout-stale-temporal`, `fanout-thin-topic-coverage`) — these are refinements

---

### Tier 4: Optimization — Retrieval & Citation Quality

**Purpose:** Fine-tune content for LLM chunking, retrieval, and citation patterns.

**Primary categories:** `chunking-*`

**Issues that belong here:**
- Broken heading hierarchy (`chunking-broken-heading-hierarchy`)
- Generic headings (`chunking-generic-headings`)
- Overscoped sections (`chunking-overscoped-section`)
- Weak local context (`chunking-weak-local-context`)
- Buried answers (`chunking-buried-answer`)
- Missing retrieval vocabulary (`chunking-missing-query-terms`)
- Prose instead of structured lists/tables (`chunking-prose-instead-of-list`, `chunking-unparseable-table`)
- No FAQ coverage (`chunking-no-faq-coverage`)
- No top-of-page summary (`chunking-no-top-summary`)
- Ambiguous paragraphs (`chunking-ambiguous-paragraphs`)
- Split supporting evidence (`chunking-split-supporting-evidence`)

**Exit criteria:** Content survives chunking, retrieval, and reranking. Key claims are self-contained in paragraphs. Answers appear early in sections. Retrieval vocabulary covers both semantic and exact-match queries.

**Dependency on Tier 3:** Optimization requires content to exist. Improving the chunking quality of a page that does not exist is impossible. Resolve content gaps first, then optimize the resulting content.

---

## Dependency Ordering Logic

### Cross-Tier Dependencies

Issues have implicit dependencies based on their tier:

```
Tier 1 (Foundation) → Tier 2 (Structure) → Tier 3 (Content) → Tier 4 (Optimization)
```

An issue in a higher tier should only be marked as actionable when its dependency tier's issues on the same affected URLs are resolved.

### Within-Tier Dependencies

Some issues within the same tier have explicit dependencies:

| Issue | Depends On | Rationale |
|---|---|---|
| `agentic-missing-faq-schema` | FAQ content exists on the page | Cannot add FAQPage schema without FAQ content |
| `fanout-missing-entity-coverage` | `fanout-no-comparison-content` | Entity pages only needed if comparison content exists to link them |
| `chunking-no-faq-coverage` | `content-thin-faq` | FAQ optimization depends on FAQ existing |
| `agentic-weak-meta-description` | Content is finalized | Do not write meta descriptions for content that will change |

### Priority Scoring

Within each tier, issues are ranked by a composite priority score:

```
priority_score = (severity_weight × 0.4) + (page_impact × 0.3) + (citation_potential × 0.2) + (effort_inverse × 0.1)
```

Where:
- **severity_weight**: critical=100, high=75, medium=50, low=25
- **page_impact**: percentage of scanned pages affected by this issue (0–100)
- **citation_potential**: estimated impact on AI citation probability (0–100), derived from issue category and context:

| Issue Category | citation_potential | Rationale |
|---|---|---|
| `policy-*` | 90 | Blocking all citations entirely |
| `agentic-*` on pages with existing citations | 80 | Directly affects already-cited pages |
| `agentic-*` on pages without citations | 60 | Enables future citations |
| `content-*` on high-traffic pages | 70 | Improves quality of high-visibility content |
| `content-*` on other pages | 50 | General content improvement |
| `fanout-*` for citation-producing sub-queries | 75 | Fills gaps in high-value query chains |
| `fanout-*` for silent sub-queries | 35 | Informational only, lower citation impact |
| `chunking-*` | 40 | Optimization — improves retrieval, not access |
| `visibility-*` | 65 | Brand-level visibility interventions |
| Default | 50 | When category context is ambiguous |
- **effort_inverse**: low_effort=100, medium_effort=50, high_effort=25

High-severity issues affecting many pages with low effort to fix are prioritized first.

---

## Tier Assignment Edge Cases

### Issue spans multiple tiers

Some issues could belong to multiple tiers. Apply the **lowest applicable tier** — fix the foundation first:

- `agentic-broken-heading-hierarchy` affects both Structure (Tier 2) and Retrieval (Tier 4). Assign to **Tier 2** because it blocks schema extraction.
- A page with both `content-no-tldr` and `chunking-buried-answer`: assign the content issue to **Tier 3** and the chunking issue to **Tier 4**.

### Fanout issues that are really structural

If a fanout gap exists because the page type is wrong (`fanout-wrong-page-type` — pricing info only exists in a blog post), this is a **Tier 2 structural concern** despite being a fanout finding. The fix is structural (create the right page type), not content creation. Assign to Tier 2 with a dependency note.

### Quick wins across tiers

If an issue is low-effort and affects many pages regardless of tier, flag it as a "quick win" for early action — but it should still respect tier dependencies on its affected URLs.

---

## Score-Based Reveal Thresholds

Beyond the tier ordering of WHAT to fix, there is a separate WHEN-to-reveal model that prevents overwhelming users with all issues at once. Issues are progressively revealed based on the current Technical Score:

| Score | Tiers Unlocked | Rationale |
|---|---|---|
| < 30 | Fundamental only | Site needs critical basics before anything else |
| ≥ 30 | Fundamental + Intermediate | Basics done — common optimizations become relevant |
| ≥ 60 | Fundamental + Intermediate + Advanced | Strong base — competitive advantage work begins |
| ≥ 80 | All tiers (+ Polish) | High maturity — maximum optimization |

### Mapping Reveal Thresholds to Pipeline Tiers

| Reveal Level | Pipeline Tiers Shown |
|---|---|
| Fundamental | Tier 1 (Foundation) + critical Tier 2 issues |
| Intermediate | Tier 2 (Structure) + common Tier 3 issues |
| Advanced | Tier 3 (Content + Fanout) + citation optimization |
| Polish | Tier 4 (Optimization) + low-severity refinements |

---

## Page-by-Page Progressive Reveal

Issues are revealed incrementally by page, not all at once:

1. **First analysis:** Only homepage issues revealed
2. **Each subsequent run:** One additional page's issues unlocked
3. **Priority order:** home → pricing → features → product → solutions → about → blog → other → documentation

This prevents a first-time user from seeing 50+ issues across 10 pages. Each run surfaces a manageable batch.

---

## Backlog Cap

Maximum **10 technical issues** in `identified` state at any time. If the backlog is full, new issue creation is blocked until existing issues move to `in_progress` or are resolved.

This prevents issue accumulation without action and encourages forward progress.

---

## Issue Lifecycle

Every issue follows this lifecycle:

```
identified → in_progress → completed / merged / failed / dismissed
```

| Status | Meaning |
|---|---|
| `identified` | Issue detected by scan, not yet acted on |
| `in_progress` | User or build pipeline is actively working on it |
| `completed` | Fix applied and verified by re-scan |
| `merged` | Fix deployed (PR merged) — awaiting re-scan verification |
| `failed` | Fix attempted but did not resolve the issue |
| `dismissed` | User explicitly chose not to fix this issue |

### Auto-Close Logic

Issues auto-close when their underlying check passes on re-analysis (`reconcileIssuesWithScores()`):

- Re-run the scan check that originally triggered the issue
- If the check now passes → set status to `completed`
- **Exception:** Issues with an associated PR are never auto-closed — they remain until the PR is merged or closed

### Reconciliation Rules

- If an issue is `identified` and the check passes → auto-close as `completed`
- If an issue is `in_progress` and the check passes → auto-close as `completed`
- If an issue is `dismissed` and the check still fails → leave as `dismissed` (user decision respected)
- If a previously `completed` issue's check fails again → create a new issue (regression detected)
