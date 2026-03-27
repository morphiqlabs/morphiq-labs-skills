# Morphiq Skills — Build Progress

Last updated: 2026-03-26

## Legend
- [x] Done
- [ ] Not started
- [~] Placeholder only (needs real content)
- [!] Blocked — needs Mudra-specific data from trymudra.com extraction

---

## Root

| File | Status |
|------|--------|
| PIPELINE.md | [x] Done — 5-category scoring, all 4 data contracts |
| README.md | [ ] Not started (write last) |
| CHANGELOG.md | [ ] Not started (write last) |
| LICENSE | [ ] Not started (Apache-2.0) |
| PROGRESS.md | [x] This file |

---

## morphiq-scan — Audit

### SKILL.md
| File | Status |
|------|--------|
| SKILL.md | [~] Frontmatter + pipeline position done — needs workflow instructions |

### references/

| File | Status | Notes |
|------|--------|-------|
| agentic-readiness.md | [ ] | Full site readiness: schema types, structure, machine-readability |
| scoring-rubric.md | [!] | 100-point scoring methodology — needs Mudra-specific data |
| page-type-rules.md | [ ] | Page type detection + expected elements per type |
| chunking-retrieval.md | [x] | Research-grounded (Anthropic, Google, HuggingFace, SEL citations) |
| query-fanout.md | [ ] | Chain-of-thought sub-question framework |
| content-quality.md | [x] | 5 quality pillars, E-E-A-T, citation format rules |
| policy-files.md | [ ] | robots.txt + llms.txt detection + audit rules |

### scripts/

| File | Status |
|------|--------|
| extract-meta.sh | [ ] |
| score-page.py | [ ] |

### evals/
| Status |
|--------|
| [ ] Empty — needs README.md, fixtures, sample tests |

---

## morphiq-rank — Prioritize

### SKILL.md
| File | Status |
|------|--------|
| SKILL.md | [~] Frontmatter + pipeline position done — needs workflow instructions |

### references/

| File | Status | Notes |
|------|--------|-------|
| issue-catalog.md | [!] | All issue types + severity — needs Mudra-specific data |
| tier-progression.md | [!] | Progressive discovery tiers — needs Mudra-specific data |

### evals/
| Status |
|--------|
| [ ] Empty — needs README.md, fixtures, sample tests |

---

## morphiq-build — Implement

### SKILL.md
| File | Status |
|------|--------|
| SKILL.md | [~] Frontmatter + pipeline position done — needs workflow instructions |

### references/

| File | Status | Notes |
|------|--------|-------|
| content-lab-pipeline.md | [x] | 5-step workflow adapted for skills context |
| schema-templates.md | [ ] | JSON-LD templates per page type |
| metadata-patterns.md | [x] | Title, description, OG, TL;DR, author byline, brand positioning |
| faq-guidelines.md | [x] | FAQ structure, question selection, brand positioning, anti-patterns |
| llms-txt-spec.md | [x] | Full llms.txt format, generation process, robots.txt companion |
| enrichment-sources.md | [x] | Name-drop + link citations, expert quotes, source authority tiers |
| gap-taxonomy.md | [x] | 5 gap types with detection signals, severity guides, search queries |

### scripts/

| File | Status |
|------|--------|
| ingest-sources.py | [ ] |
| extract-content.py | [ ] |
| analyze-gaps.py | [ ] |
| research-live.py | [ ] |
| create-from-prompt.py | [ ] |
| inject-schema.py | [ ] |
| generate-llms-txt.sh | [ ] |
| enrich-content.py | [ ] |
| restructure-content.py | [ ] |
| quality-rewrite.py | [ ] |

### evals/
| Status |
|--------|
| [ ] Empty — needs README.md, fixtures, sample tests |

---

## morphiq-track — Monitor

### SKILL.md
| File | Status |
|------|--------|
| SKILL.md | [~] Frontmatter + pipeline position done — needs workflow instructions |

### references/

| File | Status | Notes |
|------|--------|-------|
| tracker-spec.md | [x] | Full MORPHIQ-TRACKER.md spec — 14 sections, KPI definitions, update rules per skill |
| prompt-taxonomy.md | [ ] | Brand, category, comparison, feature prompt types |
| query-targets.md | [ ] | Which AI systems to query + when to use each |
| provider-strategies.md | [ ] | OpenAI, Gemini, Perplexity, Anthropic — API keys + data shapes |
| delta-scoring.md | [ ] | Citations gained/lost, mention shift measurement |
| share-of-voice.md | [ ] | (Mentions/Total) × 100 + competitive tracking over time |

### scripts/

| File | Status |
|------|--------|
| create-prompts.py | [ ] |
| run-queries.py | [ ] |
| diff-results.py | [ ] |
| generate-report.py | [ ] |

### evals/
| Status |
|--------|
| [ ] Empty — needs README.md, fixtures, sample tests |

---

## Summary

| Category | Done | Placeholder | Blocked | Not Started | Total |
|----------|------|-------------|---------|-------------|-------|
| Root files | 2 | 0 | 0 | 3 | 5 |
| SKILL.md files | 0 | 4 | 0 | 0 | 4 |
| Reference files | 9 | 0 | 3 | 9 | 21 |
| Scripts | 0 | 0 | 0 | 16 | 16 |
| Evals | 0 | 0 | 0 | 4 | 4 |
| **Total** | **11** | **4** | **3** | **32** | **50** |

## Blockers

3 reference files need Mudra-specific data from trymudra.com extraction:
1. `morphiq-scan/references/scoring-rubric.md` — 100-point scoring methodology
2. `morphiq-rank/references/issue-catalog.md` — All issue types + severity
3. `morphiq-rank/references/tier-progression.md` — Progressive discovery tiers

## Build Order (per spec)

1. ~~PIPELINE.md~~ ✓
2. morphiq-scan ← **next**
3. morphiq-rank
4. morphiq-build
5. morphiq-track
6. README.md + CHANGELOG.md (last)
