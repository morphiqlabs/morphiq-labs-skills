---
name: Morphiq Rank
description: This skill should be used when the user asks to "create issues from a scan", "prioritize what to fix", "rank the issues", "run Morphiq Rank", or mentions creating a prioritized roadmap from scan results. Consumes a Morphiq Scan Report, applies issue creation criteria with impact/effort weighting, and organizes issues into 4 progressive discovery tiers.
version: 0.1.0
---

## Pipeline Position
Step 2 of 4 — consumes morphiq-scan output.
Input: Scan Report (JSON).
Output: Prioritized Roadmap (JSON) → consumed by morphiq-build.

<!-- TODO: Workflow instructions, issue creation criteria, tier assignment logic, reference file pointers -->
