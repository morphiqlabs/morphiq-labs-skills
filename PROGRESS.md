# Morphiq Skills — Build Progress

Last updated: 2025-07-16

## Legend
- [x] Done
- [ ] Not started

---

## Root

| File | Status |
|------|--------|
| PIPELINE.md | [x] Done — 5-category scoring, all 4 data contracts |
| README.md | [x] Done — install, usage, skill descriptions |
| AGENTS.md | [x] Done — cross-agent discoverability |
| LICENSE | [x] Done — Apache-2.0 |
| PROGRESS.md | [x] This file |

---

## morphiq-scan — Audit

### SKILL.md
| File | Status |
|------|--------|
| SKILL.md | [x] Full workflow instructions, 9 steps, frontmatter with license |

### references/

| File | Status | Notes |
|------|--------|-------|
| agentic-readiness.md | [x] | ~141 lines — full site readiness: schema types, structure, machine-readability |
| scoring-rubric.md | [x] | ~240 lines — 100-point scoring methodology |
| page-type-rules.md | [x] | ~130 lines — page type detection + expected elements per type |
| chunking-retrieval.md | [x] | ~340 lines — research-grounded (Anthropic, Google, HuggingFace, SEL citations) |
| query-fanout.md | [x] | ~290 lines — chain-of-thought sub-question framework |
| content-quality.md | [x] | ~115 lines — 5 quality pillars, E-E-A-T, citation format rules |
| policy-files.md | [x] | ~100 lines — robots.txt + llms.txt detection + audit rules |

### scripts/

| File | Status |
|------|--------|
| extract-meta.py | [x] |
| score-page.py | [x] |
| normalize-scan.py | [x] |

### evals/
| Status |
|--------|
| [ ] Not started |

---

## morphiq-rank — Prioritize

### SKILL.md
| File | Status |
|------|--------|
| SKILL.md | [x] Full workflow instructions, 7 steps + reconciliation, frontmatter with license |

### references/

| File | Status | Notes |
|------|--------|-------|
| issue-catalog.md | [x] | ~290 lines — all issue types + severity |
| tier-progression.md | [x] | ~245 lines — progressive discovery tiers |

### evals/
| Status |
|--------|
| [ ] Not started (has .gitkeep) |

---

## morphiq-build — Implement

### SKILL.md
| File | Status |
|------|--------|
| SKILL.md | [x] Full workflow instructions, 7 steps (6-step content lab), frontmatter with license |

### references/

| File | Status | Notes |
|------|--------|-------|
| content-lab-pipeline.md | [x] | ~350 lines — 5-step workflow adapted for skills context |
| schema-templates.md | [x] | ~230 lines — JSON-LD templates per page type |
| metadata-patterns.md | [x] | ~150 lines — title, description, OG, TL;DR, author byline, brand positioning |
| faq-guidelines.md | [x] | ~120 lines — FAQ structure, question selection, brand positioning, anti-patterns |
| llms-txt-spec.md | [x] | ~195 lines — full llms.txt format, generation process, robots.txt companion |
| enrichment-sources.md | [x] | ~175 lines — name-drop + link citations, expert quotes, source authority tiers |
| gap-taxonomy.md | [x] | ~150 lines — 5 gap types with detection signals, severity guides, search queries |

### scripts/

| File | Status |
|------|--------|
| ingest-sources.py | [x] |
| extract-content.py | [x] |
| analyze-gaps.py | [x] |
| research-live.py | [x] |
| create-from-prompt.py | [x] |
| inject-schema.py | [x] |
| generate-llms-txt.py | [x] |
| enrich-content.py | [x] |
| restructure-content.py | [x] |
| quality-rewrite.py | [x] |
| validate-coverage.py | [x] |
| test_generate_llms_txt.py | [x] |

### evals/
| Status |
|--------|
| [ ] Not started |

---

## morphiq-track — Monitor

### SKILL.md
| File | Status |
|------|--------|
| SKILL.md | [x] Full workflow instructions, multi-step with 3 content workflows, frontmatter with license |

### references/

| File | Status | Notes |
|------|--------|-------|
| tracker-spec.md | [x] | ~460 lines — full MORPHIQ-TRACKER.md spec, 14 sections, KPI definitions |
| prompt-taxonomy.md | [x] | ~300 lines — brand, category, comparison, feature prompt types |
| query-targets.md | [x] | ~210 lines — which AI systems to query + when to use each |
| provider-strategies.md | [x] | ~260 lines — OpenAI, Gemini, Perplexity, Anthropic — API keys + data shapes |
| delta-scoring.md | [x] | ~145 lines — citations gained/lost, mention shift measurement |
| share-of-voice.md | [x] | ~250 lines — (Mentions/Total) × 100 + competitive tracking over time |
| state-layer.md | [x] | ~370 lines — JSON state management, migration, manifest spec |

### scripts/

| File | Status |
|------|--------|
| create-prompts.py | [x] |
| run-queries.py | [x] |
| diff-results.py | [x] |
| analyze-fanout.py | [x] |
| generate-report.py | [x] |

### evals/
| Status |
|--------|
| [ ] Not started |

---

## Summary

| Category | Done | Not Started | Total |
|----------|------|-------------|-------|
| Root files | 5 | 0 | 5 |
| SKILL.md files | 4 | 0 | 4 |
| Reference files | 23 | 0 | 23 |
| Scripts | 20 | 0 | 20 |
| Evals | 0 | 4 | 4 |
| **Total** | **52** | **4** | **56** |

## Remaining Work

4 eval suites need creation:
1. `morphiq-scan/evals/` — scan trigger + output validation
2. `morphiq-rank/evals/` — rank trigger + tier assignment validation
3. `morphiq-build/evals/` — build trigger + artifact generation validation
4. `morphiq-track/evals/` — track trigger + provider query validation
