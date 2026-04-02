---
name: morphiq-rank
description: >-
  Consumes MORPHIQ-SCAN.json and produces a prioritized roadmap of issues organized into 4 progressive
  discovery tiers, ranked by AI visibility impact and effort. Use when the user asks to "create issues
  from a scan", "prioritize what to fix", "rank the issues", "build a roadmap from scan results",
  "run Morphiq Rank", or mentions creating a prioritized roadmap from scan results.
license: Apache-2.0
metadata:
  version: "0.7.1"
  author: morphiq-labs
---

This skill runs one step only. Do not chain to morphiq-build or morphiq-track.

Read `MORPHIQ-SCAN.json` from the workspace root now. If the file does not exist, stop and tell the user to run Morphiq Scan first.

Read `references/output-contract.md` before writing any output — it defines the exact JSON structure, field names, and validation rules for `MORPHIQ-RANK.json`.

## Step 1: Normalize input

The scan JSON may use non-standard key names. Read the input normalization table in `references/output-contract.md` and map any aliases before processing.

## Step 2: Create issues

Read `references/issue-catalog.md` before creating issues — it defines all valid issue IDs, severity logic, and deduplication rules. Every `issue_id` must come from this catalog. Do not invent IDs.

For each scan finding, create a formal issue with: `issue_id`, `category`, `severity`, `summary`, `remediation`, `affected_urls`, `page_type`.

For `fanout-*` issues, populate `fanout_context` from the scan's `query_fanout.simulated_queries[]` and `suggested_content[]`. Map `model` → `model_origin`.

A site scoring ~60/100 typically has 15–25 issues. Fewer than 10 means something was missed — re-check every issue type against the scan data.

## Step 3: Assign tiers

Read `references/tier-progression.md` before assigning tiers — it defines the 4-tier model, dependency logic, and edge cases.

| Tier | Name | Primary categories |
|---|---|---|
| 1 | Foundation — Crawlability & Policy | `policy-*` |
| 2 | Structure — Schema & Metadata | `agentic-*` |
| 3 | Content — Depth & Coverage | `content-*`, `fanout-*`, `visibility-*` |
| 4 | Optimization — Retrieval Quality | `chunking-*` |

## Step 4: Calculate priority scores

```
priority = (severity_weight × 0.4) + (page_impact × 0.3) + (citation_potential × 0.2) + (effort_inverse × 0.1)
```

Severity weights: critical=100, high=75, medium=50, low=25. Effort inverse: low=100, medium=50, high=25.

## Step 5: Apply progressive reveal

Score-based reveal controls which tiers are shown:

- Score <30 → Tier 1 only
- Score ≥30 → Tiers 1–2
- Score ≥60 → Tiers 1–3
- Score ≥80 → All 4 tiers

Show all issues across all scanned pages for the revealed tiers.

## Step 6: Set dependencies

Cross-tier: T1 → T2 → T3 → T4. Higher-tier issues on the same URLs become actionable only after lower-tier issues are resolved.

## Step 7: Write MORPHIQ-RANK.json

Write to workspace root using your file-write tool, not shell heredoc or `cat`.

Required fields: `schema_version`, `generated_at`, `domain`, `source_scan_score`, `total_issues`, `tiers[]`.
Each tier has: `tier` (1-4), `name`, `description`, `estimated_impact`, `actions[]`.
Each action has: `priority`, `issue_id`, `category`, `severity`, `impact_score`, `effort`, `summary`, `remediation`, `affected_urls[]`, `depends_on[]`.
For fanout issues, include `fanout_context` with `triggering_sub_queries[]` and `competitor_sources[]`.

See `references/output-contract.md` for full validation rules.

After writing, display a human-readable roadmap: tier-by-tier breakdown, issue count per tier, top 3 issues per tier with severity and affected URLs.

## Reconciliation (re-runs)

On subsequent scans with existing issues: auto-close resolved issues (unless PR-linked), escalate worsened issues, create new issues for new findings, detect regressions. See `references/tier-progression.md` for lifecycle rules.

End with:

> **Rank complete.** MORPHIQ-RANK.json written to workspace root.
> To continue: type **"Run Morphiq Build"** to generate fixes for the prioritized issues.