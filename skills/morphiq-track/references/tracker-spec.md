# MORPHIQ-TRACKER.md Specification

The tracker is the persistent `.md` file that lives in the user's project root. It is the single source of state for the entire Morphiq pipeline. Every skill reads it, every skill writes to it. The agent updates it on every run.

This document defines the complete file format, all KPI definitions, calculation formulas, and the exact update behavior per skill and run type.

---

## File Location

```
{project-root}/MORPHIQ-TRACKER.md
```

Created by morphiq-track on its first run. If the file does not exist when any skill runs, the skill should note that no tracker state is available and instruct the user to run morphiq-track first (unless running morphiq-scan or morphiq-rank, which can operate without it).

---

## Complete File Structure

The tracker has 14 sections. Each section is described below with its format, KPI definitions, and update rules.

```markdown
# Morphiq Tracker — {domain}

## Score Summary
## Score Breakdown by Category
## Open Issues
## Resolved Issues
## Share of Voice
## SoV Trend
## Citation Analytics
## Tracked Prompts
## Competitors
## Per-Page Performance
## Content Performance
## Query Fanout Coverage
## Content Creation Queue
## Run History
```

---

## Section 1: Score Summary

```markdown
## Score Summary

**Current Score: 62/100**
Last scan: 2025-03-25 | Last track: 2025-03-25 | Runs: 8
```

### KPIs

| KPI | Definition | Calculation |
| --- | --- | --- |
| Current Score | Aggregate AI visibility score | Sum of all 5 category scores (from latest scan) |
| Last scan | Date of most recent morphiq-scan run | ISO date from latest scan run history entry |
| Last track | Date of most recent morphiq-track run | ISO date from latest track run history entry |
| Runs | Total number of pipeline runs recorded | Count of rows in Run History |

### Update Rules

| Skill | Action |
| --- | --- |
| morphiq-scan | Overwrites Current Score, updates Last scan date, increments Runs |
| morphiq-track | Updates Last track date, increments Runs |
| morphiq-rank | No change |
| morphiq-build | No change |

---

## Section 2: Score Breakdown by Category

```markdown
## Score Breakdown by Category

| Category | Score | Max | % | Previous | Delta |
|----------|-------|-----|---|----------|-------|
| Agentic Readiness | 26 | 45 | 57.8% | 22 | +4 |
| Content Quality | 14 | 20 | 70.0% | 12 | +2 |
| Chunking & Retrieval | 10 | 15 | 66.7% | 10 | 0 |
| Query Fanout | 6 | 10 | 60.0% | 4 | +2 |
| Policy Files | 6 | 10 | 60.0% | 4 | +2 |
| **Total** | **62** | **100** | **62.0%** | **52** | **+10** |
```

### KPIs

| KPI | Definition | Calculation |
| --- | --- | --- |
| Category Score | Points earned in this category | From scan report `scores.{category}` |
| Max | Maximum possible points | From scan report `scores_max.{category}` |
| % | Category completion percentage | `(Score / Max) * 100` |
| Previous | Score from the prior scan | From previous scan's `scores.{category}` |
| Delta | Change since last scan | `Current Score - Previous Score` |

### Update Rules

| Skill | Action |
| --- | --- |
| morphiq-scan | Overwrites all scores. Moves current values to Previous column. Recalculates Delta. |
| morphiq-track | No change (scores come from scans only) |
| morphiq-rank | No change |
| morphiq-build | No change (score only changes on next scan) |

---

## Section 3: Open Issues

```markdown
## Open Issues (12)

| Priority | Issue | Category | Severity | Tier | Status | Affected URLs |
|----------|-------|----------|----------|------|--------|---------------|
| 1 | policy-blocks-gptbot | policy_files | high | 1 | open | /robots.txt |
| 2 | policy-no-llms-txt | policy_files | high | 1 | in-progress | — |
| 3 | agentic-missing-product-schema | agentic_readiness | high | 2 | open | /product |
| 4 | content-thin-faq | content_quality | medium | 3 | open | /product |
```

### KPIs

| KPI | Definition | Calculation |
| --- | --- | --- |
| Open Issues Count | Total unresolved issues | Count of rows where Status is not `resolved` |
| Issues by Severity | Distribution across severity levels | Count per `critical`, `high`, `medium`, `low` |
| Issues by Tier | Distribution across tiers | Count per tier 1-4 |

### Status Values

| Status | Meaning |
| --- | --- |
| `open` | Issue detected, not yet addressed |
| `in-progress` | morphiq-build is working on this issue |
| `resolved` | Fix applied — moves to Resolved Issues on next update |
| `wont-fix` | User decided not to address this issue |
| `regressed` | Was resolved, but re-scan detected the issue again |

### Update Rules

| Skill | Action |
| --- | --- |
| morphiq-scan | Refreshes entire issue list from scan results. New issues added as `open`. Previously resolved issues that reappear marked `regressed`. Issues no longer detected are removed. |
| morphiq-rank | Reorders priorities, may reassign tiers based on new impact data |
| morphiq-build | Changes status to `in-progress` when starting work, `resolved` when artifact produced |
| morphiq-track | May add new issues from `flagged_actions` (e.g., `citation_loss` → new issue) |

---

## Section 4: Resolved Issues

```markdown
## Resolved Issues (3)

| Issue | Category | Severity | Resolved Date | Artifact | Verified |
|-------|----------|----------|---------------|----------|----------|
| agentic-no-canonical | agentic_readiness | high | 2025-03-20 | build-005 | yes (scan 2025-03-25) |
| policy-blocks-claude | policy_files | medium | 2025-03-18 | build-003 | pending |
| content-missing-tldr | content_quality | low | 2025-03-18 | build-007 | yes (scan 2025-03-25) |
```

### KPIs

| KPI | Definition | Calculation |
| --- | --- | --- |
| Resolved Count | Total issues fixed | Count of rows |
| Verified Count | Resolved issues confirmed by re-scan | Count where Verified is not `pending` |
| Resolution Rate | Issues resolved over total ever detected | `Resolved / (Open + Resolved)` |

### Update Rules

| Skill | Action |
| --- | --- |
| morphiq-scan | Sets Verified to `yes (scan {date})` if the issue no longer appears. If issue reappears, moves it back to Open Issues as `regressed` and removes from Resolved. |
| morphiq-build | Adds row when artifact resolves an issue. Verified starts as `pending`. |
| morphiq-rank | No change |
| morphiq-track | No change |

---

## Section 5: Share of Voice

```markdown
## Share of Voice: 34.2% (+5.6) | Weighted: 28.1% (+4.8) | Influence: 52.0% (+6.0)

| Provider | SoV | Previous | Delta |
|----------|-----|----------|-------|
| OpenAI | 40.0% | 32.0% | +8.0 |
| Gemini | 30.0% | 26.0% | +4.0 |
| Perplexity | 38.0% | 30.0% | +8.0 |
| Anthropic | 28.8% | 26.4% | +2.4 |
| **Aggregate** | **34.2%** | **28.6%** | **+5.6** |

### SoV by Type
| Metric | Value | Previous | Delta |
|--------|-------|----------|-------|
| Mention SoV (standard) | 34.2% | 28.6% | +5.6 |
| Fanout-Weighted SoV | 28.1% | 23.3% | +4.8 |
| Influence SoV | 52.0% | 46.0% | +6.0 |
| Conversion Gap | 17.8pp | 17.4pp | +0.4 |
```

### KPIs

| KPI | Definition | Calculation |
| --- | --- | --- |
| Share of Voice (SoV) | Percentage of AI responses that mention the company | `(company mentions / total mentions across all responses) * 100` |
| Per-Provider SoV | SoV broken down by AI provider | Same formula, scoped to one provider's responses |
| Aggregate SoV | Average across all providers | `mean(provider SoVs)` |
| SoV Delta | Change since last tracking run | `Current SoV - Previous SoV` |
| Fanout-Weighted SoV | SoV weighted by fan-out depth per prompt type | `Σ(prompt_type_SoV × fanout_weight) / Σ(fanout_weights)` — see `prompt-taxonomy.md` for weights |
| Influence SoV | Whether brand appeared in model sub-queries during research | `(prompts where brand in sub-queries / total prompts) × 100` — see `share-of-voice.md` |
| Conversion Gap | Difference between Influence and Citation SoV | `Influence SoV - Citation SoV` — high gap = brand researched but not cited |

### Update Rules

| Skill | Action |
| --- | --- |
| morphiq-track | Overwrites all SoV values. Moves current to Previous. Recalculates Delta. |
| morphiq-scan | No change |
| morphiq-rank | No change |
| morphiq-build | No change |

---

## Section 6: SoV Trend

```markdown
## SoV Trend

| Date | Aggregate | OpenAI | Gemini | Perplexity | Anthropic | Prompts |
|------|-----------|--------|--------|------------|-----------|---------|
| 2025-03-25 | 34.2% | 40.0% | 30.0% | 38.0% | 28.8% | 25 |
| 2025-03-18 | 28.6% | 32.0% | 26.0% | 30.0% | 26.4% | 25 |
| 2025-03-11 | 24.0% | 28.0% | 22.0% | 26.0% | 20.0% | 20 |
```

### Purpose

This is the historical record. Unlike Section 5 (which only shows current vs. previous), this table preserves every tracking run's SoV values so the user can see the full trajectory.

### Update Rules

| Skill | Action |
| --- | --- |
| morphiq-track | Prepends a new row with current run's values |
| All other skills | No change |

---

## Section 7: Citation Analytics

```markdown
## Citation Analytics

**Total Citations: 14** | Gained: +3 | Lost: 0 | Stable: 11

### Citations Gained (This Run)
| URL | Provider | Prompt | Prompt Type | First Seen |
|-----|----------|--------|-------------|------------|
| /product | openai | best widgets for teams | category | 2025-03-25 |
| /blog/guide | perplexity | how to choose a widget | use_case | 2025-03-25 |
| /product | gemini | widget comparison | comparison | 2025-03-25 |

### Citations Lost (This Run)
| URL | Provider | Prompt | Prompt Type | Last Seen |
|-----|----------|--------|-------------|-----------|
(none)

### All Active Citations
| URL | Provider | Prompt | Prompt Type | First Seen | Consecutive Runs |
|-----|----------|--------|-------------|------------|------------------|
| / | perplexity | what is Example Company | brand | 2025-03-11 | 3 |
| /product | openai | best widgets for teams | category | 2025-03-25 | 1 |
| ... | | | | | |

### Citation History
| Date | Total | Gained | Lost | Net |
|------|-------|--------|------|-----|
| 2025-03-25 | 14 | +3 | 0 | +3 |
| 2025-03-18 | 11 | +4 | -1 | +3 |
| 2025-03-11 | 8 | +8 | 0 | +8 |
```

### KPIs

| KPI | Definition | Calculation |
| --- | --- | --- |
| Total Citations | Number of unique (URL, provider, prompt) triples where the site is cited | Count of All Active Citations rows |
| Citations Gained | New citations this run vs. previous | Count of new (URL, provider, prompt) triples |
| Citations Lost | Citations from previous run no longer appearing | Count of disappeared triples |
| Net Citations | Net change | `Gained - Lost` |
| Consecutive Runs | How many consecutive runs a citation has been stable | Incremented each run if citation persists, reset to 1 if it reappears after loss |
| Citation Stability | Percentage of citations maintained | `Stable / (Stable + Lost) * 100` |

### Update Rules

| Skill | Action |
| --- | --- |
| morphiq-track | Rebuilds Gained/Lost from delta report. Updates All Active Citations (add gained, remove lost, increment Consecutive Runs for stable). Prepends Citation History row. |
| All other skills | No change |

---

## Section 8: Tracked Prompts

```markdown
## Tracked Prompts

| Prompt | Type | Mentioned | Cited | Best Provider | First Run | Runs Tracked |
|--------|------|-----------|-------|---------------|-----------|--------------|
| what is Example Company | brand | yes | yes | perplexity | 2025-03-11 | 3 |
| best widgets for teams | category | yes | yes | openai | 2025-03-18 | 2 |
| Example Company vs Competitor A | comparison | yes | no | — | 2025-03-18 | 2 |
| widget implementation guide | use_case | no | no | — | 2025-03-25 | 1 |
```

### KPIs

| KPI | Definition | Calculation |
| --- | --- | --- |
| Total Prompts | Number of prompts being tracked | Count of rows |
| Mentioned Rate | % of prompts where company is mentioned | `(Mentioned=yes count / Total) * 100` |
| Cited Rate | % of prompts where company URL is cited | `(Cited=yes count / Total) * 100` |
| Mention-to-Citation Gap | Prompts where mentioned but not cited | Count where Mentioned=yes and Cited=no |

### Prompt Types

| Type | Definition | Example |
| --- | --- | --- |
| `brand` | Direct company name query | "what is Example Company" |
| `category` | Category/market query | "best widgets for teams" |
| `comparison` | Head-to-head comparison | "Example Company vs Competitor A" |
| `feature` | Specific feature/capability query | "widget automation features" |
| `use_case` | How-to or use case query | "how to implement a widget for remote teams" |

### Update Rules

| Skill | Action |
| --- | --- |
| morphiq-track | Updates Mentioned/Cited/Best Provider based on latest run. Increments Runs Tracked. Adds new prompts from `create-prompts.py`. |
| All other skills | No change |

---

## Section 9: Competitors

```markdown
## Competitors

| Company | Mentions | SoV | Previous SoV | Delta | Top Prompt Type |
|---------|----------|-----|-------------|-------|-----------------|
| Competitor A | 52 | 43.3% | 41.7% | +1.6 | category |
| Competitor B | 38 | 31.7% | 33.0% | -1.3 | comparison |
| Our Company | 41 | 34.2% | 28.6% | +5.6 | brand |

### Competitor SoV Trend
| Date | Our Company | Competitor A | Competitor B |
|------|-------------|-------------|-------------|
| 2025-03-25 | 34.2% | 43.3% | 31.7% |
| 2025-03-18 | 28.6% | 41.7% | 33.0% |
| 2025-03-11 | 24.0% | 40.0% | 34.5% |
```

### KPIs

| KPI | Definition | Calculation |
| --- | --- | --- |
| Competitor SoV | Competitor's share of all mentions | `(competitor mentions / total mentions) * 100` |
| SoV Gap | Difference between competitor and our SoV | `Competitor SoV - Our SoV` |
| Trend Direction | Whether competitor is gaining or losing | Sign of Delta over last 3 runs |
| Top Prompt Type | Which prompt type the competitor dominates | Prompt type with highest mention count for that competitor |

### Update Rules

| Skill | Action |
| --- | --- |
| morphiq-track | Updates all competitor data from delta report. Moves current to Previous. Prepends Competitor SoV Trend row. |
| All other skills | No change |

---

## Section 10: Per-Page Performance

```markdown
## Per-Page Performance

| URL | Page Type | Score | Previous | Delta | Citations | Issues Open | Issues Resolved |
|-----|-----------|-------|----------|-------|-----------|-------------|-----------------|
| / | homepage | 72 | 65 | +7 | 3 | 2 | 1 |
| /product | product | 58 | 52 | +6 | 4 | 3 | 2 |
| /blog/guide | blog | 81 | 81 | 0 | 2 | 0 | 0 |
| /pricing | pricing | 45 | — | new | 0 | 5 | 0 |
| /about | about | 68 | 68 | 0 | 1 | 1 | 0 |
```

### KPIs

| KPI | Definition | Calculation |
| --- | --- | --- |
| Page Score | Per-page AI visibility score | From scan report `pages[].score` |
| Page Delta | Score change since last scan | `Current - Previous` |
| Page Citations | Active citations pointing to this URL | Count from Citation Analytics where URL matches |
| Page Issues Open | Unresolved issues on this page | Count from Open Issues where Affected URLs includes this page |
| Page Issues Resolved | Resolved issues on this page | Count from Resolved Issues for this page |

### Update Rules

| Skill | Action |
| --- | --- |
| morphiq-scan | Refreshes all page scores. Adds new pages. Moves current to Previous. Calculates Delta. |
| morphiq-track | Updates Citations column from latest citation data |
| morphiq-build | Updates Issues Resolved count when artifacts are produced for this page |
| morphiq-rank | No change |

---

## Section 11: Content Performance

```markdown
## Content Performance

| Artifact | Type | Target URL | Issue Fixed | Built Date | Schema Status | Cited | Cited By | First Cited |
|----------|------|------------|-------------|------------|---------------|-------|----------|-------------|
| build-003 | policy_file | /llms.txt | policy-no-llms-txt | 2025-03-20 | — | — | — | — |
| build-005 | schema | /product | agentic-missing-product-schema | 2025-03-20 | implemented | yes | openai | 2025-03-25 |
| build-007 | content | /blog/new-guide | brief-001 | 2025-03-22 | — | yes | perplexity | 2025-03-25 |
| build-008 | content | /blog/pricing-comparison | brief-002 | 2025-03-24 | — | no | — | — |
```

### KPIs

| KPI | Definition | Calculation |
| --- | --- | --- |
| Total Artifacts Built | Content/schema/policy files created by morphiq-build | Count of rows |
| Artifacts Cited | Built artifacts that are now being cited by AI providers | Count where Cited=yes |
| Citation Rate | % of built content that achieved citations | `(Artifacts Cited / Total Artifacts Built) * 100` |
| Time to First Citation | Days from build to first citation | `First Cited date - Built Date` |
| Schema Implementation Rate | % of schema artifacts that reached implemented or embedded status | `(implemented + embedded) / total schema artifacts * 100` |

### Purpose

This section answers: "Is the content we're creating actually working?" It tracks whether artifacts produced by morphiq-build are achieving their goal — being cited by AI providers. This closes the feedback loop: Scan found the gap → Rank prioritized it → Build created the fix → Track confirms it worked.

### Update Rules

| Skill | Action |
| --- | --- |
| morphiq-build | Adds row for each new artifact. For schema artifacts, sets Schema Status to `embedded` (new content) or `designed` (existing content). |
| morphiq-track | Updates Cited/Cited By/First Cited columns by cross-referencing citation data with artifact target URLs |
| morphiq-scan | For schema artifacts with `status: "designed"`, verifies schema presence on target page and transitions Schema Status to `implemented`. |
| morphiq-rank | No change |

---

## Section 12: Query Fanout Coverage

```markdown
## Query Fanout Coverage

**Coverage Score: 6/10** (Previous: 4/10, Delta: +2)

### Unanswered Queries
| Query | Source Content | Model Origin | Prompt Type | Brief Status | Content Created |
|-------|---------------|-------------|-------------|-------------|-----------------|
| widget pricing comparison 2025 | /blog/best-widgets | GPT-5.4 (site:) | discovery | completed | /blog/pricing-comparison |
| widget implementation timeline | /blog/best-widgets | GPT-5.4 | use_case | pending | — |
| CRM vs widget integration | /product | Gemini | comparison | pending | — |
| widget alternatives 2026 | /product | Gemini | comparison | pending | — |

### Answered Queries (covered by existing content)
| Query | Answered By | Model Origin | Cited | Influence Only |
|-------|------------|-------------|-------|----------------|
| what is Example Company | / | all | yes | — |
| Example Company features | /product | GPT-5.4 (site:) | yes | — |
| how to use widgets | /blog/guide | Claude | no | yes (GPT-5.4) |
```

### KPIs

| KPI | Definition | Calculation |
| --- | --- | --- |
| Coverage Score | How many simulated queries the site can answer | From scan report `query_fanout.coverage_score` |
| Coverage Delta | Change in coverage since last scan | `Current - Previous` |
| Unanswered Count | Queries with no site content | Count of Unanswered Queries rows |
| Brief Completion Rate | % of unanswered queries with content created | `(completed briefs / total briefs) * 100` |
| Fanout Citation Rate | % of answered queries where the site is actually cited | `(Cited=yes / total answered) * 100` |
| Influence-Only Rate | % of answered queries where the site appears in sub-queries but not final citations | `(Influence Only != — / total answered) * 100` |

### Column Definitions

| Column | Description |
| --- | --- |
| Model Origin | Which model generated this sub-query during simulation. `GPT-5.4 (site:)` indicates a `site:` operator query. `all` means all models would generate this sub-query. |
| Prompt Type | The parent prompt type that triggered this sub-query (determines severity weighting — see `prompt-taxonomy.md`) |
| Influence Only | When the site appeared in a model's sub-queries but NOT in the final cited response. Indicates conversion potential — the model researched the site but did not cite it. |

### Purpose

This section tracks the progression from "models would ask this" → "we created content for it" → "models now cite us for it." It connects the diagnostic fanout (Scan) with the generative fanout (Track Workflow C) and measures whether filling query gaps actually results in citations. The Model Origin and Influence Only columns connect this section to the SoV section's invisible SoV tracking — revealing where the site is being researched by models but failing to convert that research into citations.

### Update Rules

| Skill | Action |
| --- | --- |
| morphiq-scan | Refreshes Coverage Score. Updates Unanswered/Answered lists based on new scan. |
| morphiq-track (Workflow C) | Adds new unanswered queries from per-content fanout analysis. Creates briefs. |
| morphiq-build | Updates Brief Status to `completed`, fills Content Created column |
| morphiq-track (measurement) | Updates Cited column by cross-referencing citations with answered query URLs |
| morphiq-rank | No change |

---

## Section 13: Content Creation Queue

```markdown
## Content Creation Queue

| Brief | Source | Derived Query | Rationale | Status | Created | Completed |
|-------|--------|---------------|-----------|--------|---------|-----------|
| brief-001 | /blog/best-widgets | widget pricing comparison 2025 | Sub-query from "best widgets" — high-intent, no content exists | completed | 2025-03-20 | 2025-03-22 |
| brief-002 | /blog/best-widgets | widget implementation timeline | Sub-query from "best widgets" — how-to intent, no content | in-progress | 2025-03-20 | — |
| brief-003 | /product | CRM vs widget integration | Comparison query from product page fanout | pending | 2025-03-25 | — |
```

### Status Values

| Status | Meaning |
| --- | --- |
| `pending` | Brief created, not yet picked up by morphiq-build |
| `in-progress` | morphiq-build is creating content for this brief |
| `completed` | Content created and published |
| `skipped` | User decided not to create this content |

### Update Rules

| Skill | Action |
| --- | --- |
| morphiq-track (Workflow C) | Adds new briefs from per-content query fanout |
| morphiq-track (Workflow B) | Sets status to `in-progress` when create-prompts.py picks up the brief |
| morphiq-build | Sets status to `completed`, fills Completed date |
| morphiq-scan | May add new briefs from site-level `query_fanout.suggested_content` |
| morphiq-rank | No change |

---

## Section 14: Run History

```markdown
## Run History

| Date | Type | Skill | Score | SoV | Issues Resolved | Citations Net | Notes |
|------|------|-------|-------|-----|-----------------|---------------|-------|
| 2025-03-25 | track | morphiq-track | 62 | 34.2% | 0 | +3 | 3 citations gained, 0 lost |
| 2025-03-24 | build | morphiq-build | 62 | — | 2 | — | Created pricing comparison blog |
| 2025-03-22 | build | morphiq-build | 62 | — | 1 | — | Created new guide from brief-001 |
| 2025-03-20 | build | morphiq-build | 62 | — | 3 | — | Tier 1 complete (policy files) |
| 2025-03-18 | track | morphiq-track | 58 | 28.6% | 0 | +3 | Baseline run |
| 2025-03-15 | rank | morphiq-rank | 58 | — | 0 | — | 24 issues prioritized |
| 2025-03-15 | scan | morphiq-scan | 58 | — | — | — | Initial audit, 12 pages scanned |
```

### Run Types

| Type | Skill | What it records |
| --- | --- | --- |
| `scan` | morphiq-scan | Score at time of scan |
| `rank` | morphiq-rank | Number of issues prioritized |
| `build` | morphiq-build | Issues resolved, artifacts created |
| `track` | morphiq-track | SoV, citation net change |
| `optimize` | morphiq-build (Workflow A) | Issues resolved via content enrichment |
| `create` | morphiq-build (Workflow B) | New content created from briefs |

### Update Rules

Every skill prepends a new row to Run History when it completes a run. The row captures the state snapshot at that moment.

---

## Update Behavior Summary

### On morphiq-scan run:
1. Overwrite Score Summary (new score, new date)
2. Overwrite Score Breakdown (new category scores, move current → previous, calc delta)
3. Refresh Open Issues (new issues from scan, detect regressions)
4. Update Resolved Issues (verify resolved issues, detect regressions)
5. Refresh Per-Page Performance (new page scores, move current → previous)
6. Refresh Query Fanout Coverage (new coverage score, update answered/unanswered)
7. Append Run History row

### On morphiq-rank run:
1. Reorder Open Issues (new priorities, tier assignments)
2. Append Run History row

### On morphiq-build run:
1. Update Open Issues (status → `in-progress` or `resolved`)
2. Move newly resolved issues to Resolved Issues
3. Add rows to Content Performance
4. Update Content Creation Queue (status → `completed`)
5. Update Query Fanout Coverage (brief status → `completed`)
6. Update Per-Page Performance (issues resolved count)
7. Append Run History row

### On morphiq-track run (measurement):
1. Update Share of Voice (new values, move current → previous)
2. Prepend SoV Trend row
3. Rebuild Citation Analytics (gained/lost/stable, update history)
4. Update Tracked Prompts (mentioned/cited status)
5. Update Competitors (new mentions, SoV, prepend trend row)
6. Update Per-Page Performance (citations column)
7. Update Content Performance (cited status)
8. Update Query Fanout Coverage (cited column for answered queries)
9. Append Run History row

### On morphiq-track Workflow B (content creation):
1. Update Content Creation Queue (briefs → `in-progress`)
2. Update Tracked Prompts (add new prompts from `create-prompts.py`)
3. Store prompt results in Tracked Prompts
4. Hand off to morphiq-build (which does its own updates)
5. Append Run History row (type: `create`)

### On morphiq-track Workflow C (query fanout expansion):
1. Add new briefs to Content Creation Queue
2. Add new unanswered queries to Query Fanout Coverage
3. Append Run History row

---

## Source of Truth: State Layer vs. Tracker

The tracker and the JSON state layer (`morphiq-track/`) are complementary views of the same data. Each section has one canonical source:

| Section | Source of Truth | Sync Direction |
|---------|----------------|----------------|
| §1 Score Summary | MORPHIQ-TRACKER.md (scan-owned) | Not in state layer |
| §2 Score Breakdown | MORPHIQ-TRACKER.md (scan-owned) | Not in state layer |
| §3 Open Issues | MORPHIQ-TRACKER.md (scan/build-owned) | Not in state layer |
| §4 Resolved Issues | MORPHIQ-TRACKER.md (build/scan-owned) | Not in state layer |
| §5 Share of Voice | Derived from `morphiq-track/results/` | **State → Tracker** |
| §6 SoV Trend | `morphiq-track/manifest.json` + results | **State → Tracker** |
| §7 Citation Analytics | `morphiq-track/citations.json` | **State → Tracker** |
| §8 Tracked Prompts | `morphiq-track/prompts.json` | **State → Tracker** |
| §9 Competitors | Derived from `morphiq-track/results/` | **State → Tracker** |
| §10 Per-Page Performance | Mixed (scan scores + track citations) | Both directions |
| §11 Content Performance | MORPHIQ-TRACKER.md (build-owned) | Not in state layer |
| §12 Query Fanout Coverage | MORPHIQ-TRACKER.md (scan/track-owned) | Not in state layer |
| §13 Content Creation Queue | MORPHIQ-TRACKER.md (track/build-owned) | Not in state layer |
| §14 Run History | `morphiq-track/manifest.json` runs array | **State → Tracker** |

**State → Tracker:** After each tracking run, the agent reads computed data from the JSON state layer and writes the corresponding markdown tables into MORPHIQ-TRACKER.md. The state layer is canonical; the tracker markdown is a projection.

**Tracker-only sections:** Data owned by scan, rank, or build stays exclusively in the tracker. The agent reads these directly from markdown when needed.

For the full state layer specification, see `state-layer.md`.

---

## Staleness and Re-scan

The tracker becomes stale when the user modifies the website outside of Morphiq skills. This is expected and handled:

- **Scores** go stale → next morphiq-scan refreshes them
- **Issues** go stale → next morphiq-scan detects resolved issues (removes them) and new issues (adds them), and flags regressions
- **SoV/Citations** go stale → next morphiq-track measurement updates them (from state layer)
- **Content Performance** stays accurate — it only tracks what morphiq-build created

The user does not need to worry about staleness. Running any skill updates the sections that skill owns. The tracker self-corrects over time.

---

## Git as Audit Trail

The tracker is a plain `.md` file committed to git. The state layer files (`morphiq-track/*.json`) are also committed. This means:

- `git log MORPHIQ-TRACKER.md` shows every tracker update with timestamps
- `git log morphiq-track/` shows every state layer change
- `git diff` between commits shows exactly what changed per run
- No database, no external service, no API — the full history is in version control
- The user can revert to any previous state if needed

Every skill run that modifies the tracker or state layer should be followed by a git commit (if the user has opted into auto-commits).
