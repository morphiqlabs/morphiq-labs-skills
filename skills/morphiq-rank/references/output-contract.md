# Rank Output Contract

This defines the exact JSON structure for `MORPHIQ-RANK.json`. The downstream pipeline (morphiq-build) depends on these exact keys and shapes.

## Output Filename

`MORPHIQ-RANK.json` — not `MORPHIQ_ROADMAP.json`, not `morphiq-rank.json`, not any other variation.

## Top-Level Structure

```json
{
  "schema_version": "1.0",
  "generated_at": "ISO-8601 timestamp",
  "domain": "example.com",
  "source_scan_score": 62,
  "total_issues": 24,
  "tiers": [ ... ]
}
```

## tiers[]

Each tier object:

```json
{
  "tier": 1,
  "name": "Foundation — Crawlability & Policy",
  "description": "Ensure AI crawlers can access and understand the site",
  "estimated_impact": "high",
  "actions": [ ... ]
}
```

The four tiers are:
1. Foundation — Crawlability & Policy
2. Structure — Schema & Metadata
3. Content — Depth & Coverage
4. Optimization — Retrieval & Citation Quality

## actions[]

Each action object:

```json
{
  "priority": 1,
  "issue_id": "policy-no-llms-txt",
  "category": "policy_files",
  "severity": "high",
  "impact_score": 90,
  "effort": "medium",
  "summary": "No llms.txt file found",
  "remediation": "Create llms.txt with site summary and key pages",
  "affected_urls": [],
  "page_type": null,
  "depends_on": []
}
```

For `fanout-*` issues, add `fanout_context`:

```json
{
  "priority": 5,
  "issue_id": "fanout-no-pricing-content",
  "category": "query_fanout",
  "severity": "high",
  "impact_score": 80,
  "effort": "high",
  "summary": "No pricing content for pricing sub-queries",
  "remediation": "Create dedicated pricing page",
  "affected_urls": [],
  "page_type": "pricing",
  "depends_on": [],
  "fanout_context": {
    "triggering_sub_queries": [
      {
        "query": "site:example.com pricing official",
        "model_origin": "openai",
        "prompt_type": "category",
        "citation_weight": "site_targeted",
        "parent_prompt": "best widgets for teams 2026"
      }
    ],
    "competitor_sources": []
  }
}
```

## Critical Field Names

These exact names are required — do not use alternatives:

| Correct | Wrong |
|---|---|
| `issue_id` | `id` |
| `impact_score` | `priority_score` |
| `remediation` | `remediation_hint` |
| `depends_on` | `dependencies` |
| `model_origin` | `model` |

Actions are sorted by `priority` (ascending = highest priority first) within each tier.

## Issue ID Validation

Every `issue_id` must come from `references/issue-catalog.md`. Do not invent descriptive IDs.

Wrong: `policy-llms-txt-missing`, `agentic-readiness-thin-schema`, `content-quality-thin-body-copy`
Correct: `policy-no-llms-txt`, `agentic-missing-product-schema`, `content-thin-page`

## Input Normalization

The scan JSON may use non-standard key names. Map these aliases before processing:

| Expected Key | Possible Aliases |
|---|---|
| `scores` | `category_scores`, `scoring_breakdown`, `overall_score_breakdown`, `score_breakdown` |
| `overall_score` | `total_score`, `score`, `aggregate_score`, nested inside `domain_summary.overall_score` |
| `pages` | `pages_analyzed`, `pages_audited`, `page_results`, `per_page_technical_scores` |
| `policy_files` | `policies`, `policy` |
| `query_fanout` | `fanout`, `query_coverage` |

For scores: if `scores` is missing, reconstruct from `category_scores` (extract `.score` from each sub-object).

For pages: if page issues are strings instead of issue objects (e.g. `["missing_jsonld_schema"]`), map each string to the closest valid issue ID from `references/issue-catalog.md` and construct proper issue objects.

For issue IDs: the scan may use invented IDs like `AR-001`, `PF-001`, `CQ-001`, or descriptive strings like `missing_jsonld_schema`. Map these to valid catalog IDs:
- `AR-001` / `missing_jsonld_schema` → multiple `agentic-missing-*-schema` IDs based on page type
- `PF-001` / `missing_llms_txt` → `policy-no-llms-txt`
- `AR-002` / `generic_title` → `agentic-weak-meta-description`
- `CQ-001` / `thin_content` → `content-thin-page`
- `AR-003` / `no_explicit_canonical` → `agentic-no-canonical`
- `AR-004` / `missing_faq_schema` → `agentic-missing-faq-schema`
- `CR-001` / `missing_breadcrumblist_schema` → `agentic-missing-breadcrumb`
- `CQ-002` / `missing_author_attribution` → `content-no-author`

For remediation: `remediation_hint` may appear as `remediation`, `fix`, or `recommendation`. Normalize to `remediation` in the output.
