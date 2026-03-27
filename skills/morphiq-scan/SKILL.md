---
name: Morphiq Scan
description: This skill should be used when the user asks to "audit a website for AI visibility", "scan a domain", "check AI readiness", "evaluate content quality", "run a Morphiq Scan", or mentions scanning a website for LLM citation readiness. Performs a full AI visibility audit across 5 categories (agentic readiness, content quality, chunking & retrieval, query fanout, policy files) and scores the domain on a 100-point rubric.
version: 0.1.0
---

## Pipeline Position
Step 1 of 4 — entry point.
Input: a domain URL from the user.
Output: Scan Report (JSON) → consumed by morphiq-rank.

<!-- TODO: Workflow instructions, evaluation steps, scoring process, reference file pointers -->
