---
name: Morphiq Rank
description: This skill should be used when the user asks to "create issues from a scan", "prioritize what to fix", "rank the issues", "build a roadmap from scan results", "run Morphiq Rank", or mentions creating a prioritized roadmap from scan results. Consumes a Morphiq Scan Report, applies issue creation criteria with impact/effort weighting, and organizes issues into 4 progressive discovery tiers.
version: 0.1.0
---

## Pipeline Position

Step 2 of 4 — consumes morphiq-scan output.
- **Input:** Scan Report (JSON) from morphiq-scan.
- **Output:** Prioritized Roadmap (JSON) → consumed by morphiq-build.
- **Data contract:** See `PIPELINE.md` §2 for the Prioritized Roadmap schema.

## Purpose

Morphiq Rank transforms raw scan findings into an actionable, prioritized roadmap. It determines severity, assigns progressive discovery tiers, calculates priority scores, and controls how many issues are revealed. The output tells morphiq-build what to fix and in what order.

## Workflow

### Step 1: Ingest Scan Report

Parse the Scan Report JSON. Extract per-page scores, domain-level scores, all identified issues, and the overall pipeline score (0–100).

### Step 2: Create Issues

For each finding, create a formal issue:

| Field | Description |
|---|---|
| `id` | Pattern: `{category}-{specific-problem}` |
| `category` | `agentic_readiness`, `content_quality`, `chunking_retrieval`, `query_fanout`, `policy_files`, `ai_visibility` |
| `severity` | From issue catalog + escalation rules |
| `summary` | One-line description |
| `detail` | Full explanation with AI visibility impact |
| `affected_urls` | URLs where the issue appears |
| `remediation_hint` | Actionable fix instruction |

For fanout issues, severity depends on parent prompt type fan-out depth. `site:` and citation-producing sub-queries escalate one level.

**Deduplication:** Technical issues hash by `brandId + checkCode + pageUrl`. AI visibility issues hash by `brandId + category + title`.

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

**Score-based:** <30 → fundamental only, ≥30 → +intermediate, ≥60 → +advanced, ≥80 → all tiers.

**Page-based:** First run = homepage only. Each subsequent run unlocks one more page (home → pricing → features → product → solutions → about → blog → other → docs).

**Backlog cap:** Max 10 issues in `identified` state.

### Step 6: Set Dependencies

Cross-tier: `T1 → T2 → T3 → T4`. Higher-tier issues on same URLs only become actionable when lower-tier issues are resolved. Within-tier explicit dependencies also apply.

### Step 7: Produce Prioritized Roadmap

Assemble JSON (`PIPELINE.md` §2): issues by tier, sorted by priority, with severity, remediation hints, affected URLs, dependencies, and reveal state metadata.

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
