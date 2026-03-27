---
name: Morphiq Track
description: This skill should be used when the user asks to "run a tracking cycle", "measure AI visibility", "check share of voice", "run Morphiq Track", "track citations", or mentions monitoring LLM mentions, running content creation workflows, or generating query fanout content. Queries multiple LLM providers, produces delta reports, and maintains MORPHIQ-TRACKER.md as the persistent state file for the entire pipeline.
version: 0.1.0
---

## Pipeline Position
Step 4 of 4 — measurement + flywheel.
Input: Build Output (JSON) + MORPHIQ-TRACKER.md (persistent state).
Output: Delta Report (JSON) → loops back to morphiq-rank.
Owns: MORPHIQ-TRACKER.md — generates on first run, updates every run.
Drives: 3 workflows (Content Optimization, Content Creation, Query Fanout Expansion).

<!-- TODO: Workflow instructions, three workflow definitions, measurement loop, reference file pointers -->
