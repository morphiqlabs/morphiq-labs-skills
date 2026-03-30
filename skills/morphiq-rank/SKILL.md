---
name: morphiq-rank
description: Create issues from a scan report, prioritize what to fix, rank by impact. Consumes MORPHIQ-SCAN.json and produces a tiered roadmap with weighted priority scores.
allowed-tools: Read, Write, Grep, Glob
metadata:
  version: "0.3.0"
  author: morphiq-labs
---

## EXECUTION INSTRUCTIONS

You are now executing Morphiq Rank. This is a WORKFLOW — you must read the Scan Report, create issues, compute priority scores, and produce a Prioritized Roadmap. Do NOT just describe what the skill does. EXECUTE the steps.

**Input:** Read **`MORPHIQ-SCAN.json`** from the workspace root (produced by morphiq-scan). If that file doesn't exist, also try `MORPHIQ_SCAN_REPORT.json` (legacy name). If the scan just ran in this session, use the scan results from context.
**Output:** You MUST write a Prioritized Roadmap JSON file to **`MORPHIQ-RANK.json`** (exactly this filename, with hyphens not underscores) in the workspace root AND display a human-readable summary.

### HARD RULES — VALIDATE BEFORE WRITING OUTPUT

1. **Output filename:** `MORPHIQ-RANK.json` — NOT `MORPHIQ_ROADMAP.json`, NOT `morphiq-rank.json`, NOT any other variation.
2. **Issue IDs are a closed set.** You MUST only use IDs from `references/issue-catalog.md`. Do NOT invent descriptive IDs. Wrong: `policy-llms-txt-missing`, `agentic-readiness-thin-schema`, `content-quality-thin-body-copy`. Correct: `policy-no-llms-txt`, `agentic-missing-product-schema`, `content-thin-page`. Before writing the JSON, validate every `issue_id` against the catalog.
3. **Field names are exact.** Use `issue_id` not `id`. Use `impact_score` not `priority_score`. Use `remediation` not `remediation_hint`. See the JSON template in Step 7.

## Pipeline Position

Step 2 of 4 — consumes morphiq-scan output.
- **Input:** Scan Report (JSON) from morphiq-scan — either `MORPHIQ-SCAN.json` or in-context results.
- **Output:** Prioritized Roadmap JSON file (`MORPHIQ-RANK.json`) → consumed by morphiq-build.
- **Data contract:** See `PIPELINE.md` §2 for the Prioritized Roadmap schema.

## Purpose

Morphiq Rank transforms raw scan findings into an actionable, prioritized roadmap. It determines severity, assigns progressive discovery tiers, calculates priority scores, and controls how many issues are revealed. The output tells morphiq-build what to fix and in what order.

## Workflow

### Step 1: Ingest Scan Report

Parse the Scan Report JSON. Extract per-page scores, domain-level scores, all identified issues, and the overall pipeline score (0–100).

### Step 2: Create Issues

For each finding, create a formal issue. You MUST use the EXACT issue IDs defined in `references/issue-catalog.md`. Do NOT invent abbreviations like "PF-001" or "AR-002".

Examples of correct IDs: `policy-no-llms-txt`, `agentic-missing-product-schema`, `content-no-tldr`, `chunking-buried-answer`, `fanout-no-comparison-content`.

| Field | Description |
|---|---|
| `id` | EXACT ID from issue-catalog.md in `{category}-{specific-problem}` format |
| `category` | `agentic_readiness`, `content_quality`, `chunking_retrieval`, `query_fanout`, `policy_files`, `ai_visibility` |
| `severity` | From issue catalog + escalation rules |
| `summary` | One-line description |
| `detail` | Full explanation with AI visibility impact |
| `affected_urls` | URLs where the issue appears |
| `remediation_hint` | Actionable fix instruction |

For fanout issues, severity depends on parent prompt type fan-out depth. `site:` and citation-producing sub-queries escalate one level.

For `fanout-*` issues, populate `fanout_context` from the scan report's `query_fanout.simulated_queries[]` and `query_fanout.suggested_content[]`. Each simulated query mapping to this issue becomes a `triggering_sub_queries` entry:
- `query` ← from `simulated_queries[].query`
- `model_origin` ← from `simulated_queries[].model` (rename `model` → `model_origin`)
- `prompt_type` ← from `simulated_queries[].prompt_type`
- `citation_weight` ← from `simulated_queries[].citation_weight`
- `parent_prompt` ← for simulated queries, set to `"(simulated)"`; for `suggested_content[]` entries, use the `suggestion` field

If the Delta Report's `content_creation_queue` has entries matching this issue, include their `competitor_sources` in `fanout_context.competitor_sources[]`.

**Deduplication:** Technical issues hash by `brandId + checkCode + pageUrl`. AI visibility issues hash by `brandId + category + title`.

**Thoroughness check:** A site scoring ~60/100 typically has 15–25 issues across all 6 categories. If you find fewer than 10, re-read the issue catalog and check every issue type against the scan data. Each page should generate at least 2–3 issues.

For all issue types and severity logic, read `references/issue-catalog.md`.

### Step 3: Assign Tiers

| Tier | Name | Primary Categories |
|---|---|---|
| 1 | Foundation — Crawlability & Policy | `policy-*` |
| 2 | Structure — Schema & Metadata | `agentic-*` |
| 3 | Content — Depth & Coverage | `content-*`, `fanout-*`, `visibility-*` |
| 4 | Optimization — Retrieval Quality | `chunking-*` |

Edge cases: `fanout-wrong-page-type` → Tier 2. Multi-tier issues → lowest applicable tier.

For tier definitions and dependency logic, read `references/tier-progression.md`.

### Step 4: Calculate Priority Scores

```
priority = (severity_weight × 0.4) + (page_impact × 0.3) + (citation_potential × 0.2) + (effort_inverse × 0.1)
```

severity: critical=100, high=75, medium=50, low=25. page_impact: % pages affected. effort_inverse: low=100, medium=50, high=25.

### Step 5: Apply Progressive Reveal

**Score-based reveal** — controls which tiers are shown to the user:
- Score <30 → Show Tier 1 (Foundation) only
- Score ≥30 → Show Tiers 1–2 (Foundation + Structure)
- Score ≥60 → Show Tiers 1–3 (Foundation + Structure + Content)
- Score ≥80 → Show all 4 tiers

Show ALL issues across all scanned pages for the revealed tiers. Do not limit to homepage only.

### Step 6: Set Dependencies

Cross-tier: `T1 → T2 → T3 → T4`. Higher-tier issues on same URLs only become actionable when lower-tier issues are resolved. Within-tier explicit dependencies also apply.

### Step 7: Produce Prioritized Roadmap

Write the Prioritized Roadmap as JSON to `MORPHIQ-RANK.json` in the workspace root. The JSON MUST use the **exact field names and structure** shown below. Do NOT rename, flatten, or restructure fields.

```json
{
  "schema_version": "1.0",
  "generated_at": "ISO-8601 timestamp",
  "domain": "example.com",
  "source_scan_score": 62,
  "total_issues": 24,
  "tiers": [
    {
      "tier": 1,
      "name": "Foundation — Crawlability & Policy",
      "description": "Ensure AI crawlers can access and understand the site",
      "estimated_impact": "high",
      "actions": [
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
          "remediation": "Add JSON-LD Product schema",
          "affected_urls": ["https://example.com/product"],
          "page_type": "product",
          "depends_on": []
        }
      ]
    },
    {
      "tier": 3,
      "name": "Content — Depth & Coverage",
      "description": "Fill content gaps that prevent AI citations",
      "estimated_impact": "medium",
      "actions": [
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

**Critical field rules:**
- Top-level MUST have `source_scan_score`, `total_issues`, `domain`, `tiers[]`
- Each tier has `tier` (number), `name`, `description`, `estimated_impact`, `actions[]`
- Each action uses `issue_id` (NOT `id`), `impact_score` (NOT `priority_score`), `remediation` (NOT `remediation_hint`), `depends_on` (NOT `dependencies`)
- `fanout_context` is ONLY for `fanout-*` issues — includes `triggering_sub_queries[]` with `model_origin`, `citation_weight`, `parent_prompt`
- Actions are sorted by `priority` (ascending = highest priority first) within each tier
- Issue IDs MUST come from `references/issue-catalog.md`

After writing the JSON file, display a human-readable roadmap showing: tier-by-tier breakdown, issue count per tier, top 3 issues per tier with severity and affected URLs, and the recommended execution order.

## Reconciliation (Re-runs)

On subsequent scans with existing issues:
1. Auto-close issues where the check now passes (unless PR-linked)
2. Escalate worsened issues
3. Create new issues for new findings
4. Detect regressions (previously completed issues re-appearing)

For issue lifecycle and auto-close logic, read `references/tier-progression.md`.

## Reference Files

| File | Purpose |
|---|---|
| `references/issue-catalog.md` | All issue types (50+), severity logic, deduplication, check code mapping |
| `references/tier-progression.md` | 4-tier model, dependencies, priority formula, reveal thresholds, lifecycle |
