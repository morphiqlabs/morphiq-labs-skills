---
name: morphiq-rank
description: This skill should be used when the user asks to "create issues from a scan", "prioritize what to fix", "rank the issues", "build a roadmap from scan results", "run Morphiq Rank", or mentions creating a prioritized roadmap from scan results. Consumes a Morphiq Scan Report, applies issue creation criteria with impact/effort weighting, and organizes issues into 4 progressive discovery tiers.
metadata:
  version: "0.1.1"
  author: morphiq-labs
---

## EXECUTION INSTRUCTIONS

You are now executing Morphiq Rank. This is a WORKFLOW — you must read the Scan Report, create issues, compute priority scores, and produce a Prioritized Roadmap. Do NOT just describe what the skill does. EXECUTE the steps.

**Input:** Read `MORPHIQ-SCAN.json` from the workspace root (produced by morphiq-scan). If the scan just ran in this session, use the scan results from context.
**Output:** You MUST write a Prioritized Roadmap JSON file to `MORPHIQ-RANK.json` in the workspace root AND display a human-readable summary.

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

Write the Prioritized Roadmap as JSON to `MORPHIQ-RANK.json` in the workspace root. The JSON MUST follow the schema in `PIPELINE.md` §2.

**Required in the JSON:**
- `source_scan_score` — the overall score from the scan
- `total_issues` — count of all issues
- `tiers[]` — each tier with its issues sorted by `priority_score` (descending)
- Each issue MUST include: `id` (from catalog), `severity`, `priority_score` (numeric), `summary`, `detail`, `affected_urls`, `remediation_hint`, `dependencies`

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
