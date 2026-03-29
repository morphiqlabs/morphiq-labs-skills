# JSON State Layer Specification

The state layer is the machine-readable complement to `MORPHIQ-TRACKER.md`. It stores full prompt metadata, versioned raw results, and structured citation data that scripts need to consume across runs. The tracker remains the user-facing dashboard — the state layer is the data backbone that feeds it.

---

## Directory Structure

```
{project-root}/
  MORPHIQ-TRACKER.md              # Unchanged — human-readable dashboard
  morphiq-track/
    manifest.json                  # Run index + file pointers
    prompts.json                   # Full prompt state (persisted across runs)
    citations.json                 # Structured citation state
    results/
      track-{YYYY-MM-DD}.json     # Per-run raw results (versioned)
      track-{YYYY-MM-DD}-NNN.json # Same-day disambiguator
```

All paths are relative to the project root. The `morphiq-track/` directory is created by the agent on the first tracking run.

---

## File Schemas

### 1. manifest.json — Run Index

The entry point. Any script that needs to find state files reads this first.

```json
{
  "schema_version": "1.0",
  "domain": "example.com",
  "brand": "Example Company",
  "created_at": "2026-03-25T14:00:00Z",
  "updated_at": "2026-03-27T10:30:00Z",
  "files": {
    "prompts": "morphiq-track/prompts.json",
    "citations": "morphiq-track/citations.json",
    "tracker": "MORPHIQ-TRACKER.md"
  },
  "runs": [
    {
      "run_id": "track-2026-03-27",
      "type": "track",
      "date": "2026-03-27",
      "is_baseline": false,
      "results_path": "morphiq-track/results/track-2026-03-27.json",
      "prompt_count": 50,
      "providers_queried": ["openai", "perplexity", "anthropic", "gemini"]
    },
    {
      "run_id": "track-2026-03-25",
      "type": "track",
      "date": "2026-03-25",
      "is_baseline": true,
      "results_path": "morphiq-track/results/track-2026-03-25.json",
      "prompt_count": 50,
      "providers_queried": ["openai", "perplexity", "anthropic", "gemini"]
    }
  ]
}
```

#### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `schema_version` | string | yes | Always `"1.0"` |
| `domain` | string | yes | Root domain being tracked |
| `brand` | string | yes | Brand name |
| `created_at` | ISO 8601 | yes | When the state layer was initialized |
| `updated_at` | ISO 8601 | yes | Last modification timestamp |
| `files` | object | yes | Relative paths to state files |
| `runs` | array | yes | Ordered newest-first. Scripts take `runs[0]` for current, `runs[1]` for previous. |
| `runs[].run_id` | string | yes | Format: `track-{YYYY-MM-DD}`. Same-day runs append `-NNN`. |
| `runs[].type` | string | yes | Always `"track"` for tracking runs |
| `runs[].date` | string | yes | ISO date of the run |
| `runs[].is_baseline` | boolean | yes | True if first run (no delta comparison possible) |
| `runs[].results_path` | string | yes | Relative path to the versioned results file |
| `runs[].prompt_count` | integer | yes | Number of prompts executed |
| `runs[].providers_queried` | string[] | yes | Providers used in this run |

---

### 2. prompts.json — Full Prompt State

Persists the complete output of `create-prompts.py` plus tracking state accumulated over runs. This is what `run-queries.py` reads directly — no regeneration from markdown.

```json
{
  "schema_version": "1.0",
  "generated_at": "2026-03-25T14:00:00Z",
  "updated_at": "2026-03-27T10:30:00Z",
  "config": {
    "brand": "Example Company",
    "domain": "example.com",
    "competitors": ["Competitor A", "Competitor B"],
    "category": "SaaS"
  },
  "prompts": [
    {
      "id": "prompt-001",
      "text": "Best SaaS tools for team collaboration 2026",
      "geo_category": "organic",
      "pipeline_type": "category",
      "contains_brand": false,
      "contains_temporal": true,
      "created_at": "2026-03-25",
      "tracking": {
        "mentioned": true,
        "cited": true,
        "best_provider": "openai",
        "first_run": "2026-03-25",
        "runs_tracked": 3,
        "last_run": "2026-03-27"
      }
    }
  ],
  "validation": {
    "total_prompts": 50,
    "valid": true,
    "issues": [],
    "distribution": {
      "organic": 23,
      "competitor": 6,
      "howto": 7,
      "brand_specific": 7,
      "faq": 7
    }
  },
  "recommendations": {
    "last_generated": "2026-03-27",
    "cooldown_days": 7,
    "pending": []
  }
}
```

#### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `schema_version` | string | yes | Always `"1.0"` |
| `generated_at` | ISO 8601 | yes | When prompts were first generated |
| `updated_at` | ISO 8601 | yes | Last tracking update |
| `config` | object | yes | The config block `run-queries.py` consumes |
| `config.brand` | string | yes | Brand name |
| `config.domain` | string | yes | Root domain |
| `config.competitors` | string[] | yes | Tracked competitors |
| `config.category` | string | yes | Product category |
| `prompts[]` | array | yes | Full prompt set |
| `prompts[].id` | string | yes | Unique prompt ID (`prompt-NNN`) |
| `prompts[].text` | string | yes | The prompt text |
| `prompts[].geo_category` | string | yes | GEO category (organic, competitor, howto, brand_specific, faq) |
| `prompts[].pipeline_type` | string | yes | Pipeline type (brand, category, comparison, feature, use_case, technical_eval, discovery, recommendation, problem_seeking) |
| `prompts[].contains_brand` | boolean | yes | Whether prompt text contains brand name |
| `prompts[].contains_temporal` | boolean | yes | Whether prompt has year/temporal markers |
| `prompts[].created_at` | string | yes | ISO date when prompt was created |
| `prompts[].tracking` | object | no | Null until first run completes. Populated by agent after each run. |
| `prompts[].tracking.mentioned` | boolean | yes | Brand mentioned in any provider response |
| `prompts[].tracking.cited` | boolean | yes | Domain URL cited in any provider response |
| `prompts[].tracking.best_provider` | string/null | yes | Provider with strongest brand signal, null if no mention |
| `prompts[].tracking.first_run` | string | yes | ISO date of first tracking run |
| `prompts[].tracking.runs_tracked` | integer | yes | Number of runs this prompt has been tracked |
| `prompts[].tracking.last_run` | string | yes | ISO date of most recent run |
| `validation` | object | yes | Quality validation from `create-prompts.py` |
| `recommendations` | object | yes | Recommendation generation state |
| `recommendations.last_generated` | string/null | yes | ISO date of last recommendation batch, null if never |
| `recommendations.cooldown_days` | integer | yes | Days between recommendation batches (default: 7) |
| `recommendations.pending` | array | yes | Recommended prompts not yet added to main set |

---

### 3. results/track-{YYYY-MM-DD}.json — Per-Run Raw Results

Each tracking run produces a new file. Never overwritten. This is the versioned output of `run-queries.py`.

```json
{
  "schema_version": "1.0",
  "run_id": "track-2026-03-27",
  "generated_at": "2026-03-27T10:30:00Z",
  "config": {
    "brand": "Example Company",
    "domain": "example.com",
    "competitors": ["Competitor A", "Competitor B"]
  },
  "results": [
    {
      "prompt_id": "prompt-001",
      "prompt_text": "Best SaaS tools for team collaboration 2026",
      "geo_category": "organic",
      "pipeline_type": "category",
      "provider": "openai",
      "response_text": "Here are the best SaaS tools for team collaboration in 2026...",
      "citations": [
        {
          "url": "https://example.com/product",
          "title": "Example Company Product",
          "citation_weight": 2,
          "resolved_domain": "example.com"
        }
      ],
      "sub_queries": [
        "best SaaS collaboration tools 2026",
        "site:example.com product features"
      ],
      "analysis": {
        "brand_mentioned": true,
        "mention_type": "named_mention",
        "brand_position": 2,
        "sentiment": "Positive",
        "competitors_mentioned": ["Competitor A"],
        "domain_cited": true
      },
      "error": null
    }
  ],
  "total": 50,
  "summary": {
    "mentioned": 41,
    "cited": 14,
    "errors": 2,
    "by_provider": {
      "openai": { "total": 18, "errors": 0, "mentioned": 12, "sub_queries": 89 },
      "perplexity": { "total": 18, "errors": 1, "mentioned": 10, "sub_queries": 0 },
      "anthropic": { "total": 17, "errors": 1, "mentioned": 9, "sub_queries": 31 },
      "gemini": { "total": 17, "errors": 0, "mentioned": 10, "sub_queries": 112 }
    }
  }
}
```

#### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `schema_version` | string | yes | Always `"1.0"` |
| `run_id` | string | yes | Matches `manifest.json` run entry |
| `generated_at` | ISO 8601 | yes | When the queries completed |
| `config` | object | yes | Config snapshot from `prompts.json` |
| `results[]` | array | yes | One entry per prompt-provider pair |
| `results[].prompt_id` | string | yes | References `prompts.json` prompt ID |
| `results[].prompt_text` | string | yes | The prompt text (denormalized for readability) |
| `results[].geo_category` | string | yes | GEO category |
| `results[].pipeline_type` | string | yes | Pipeline type |
| `results[].provider` | string | yes | Which provider answered (`openai`, `perplexity`, `anthropic`, `gemini`) |
| `results[].response_text` | string | yes | **Full response text — never truncated.** morphiq-build reads this for content creation. |
| `results[].citations[]` | array | yes | Deduplicated citations from the response |
| `results[].citations[].url` | string | yes | Citation URL (UTM params stripped) |
| `results[].citations[].title` | string | no | Page title if available |
| `results[].citations[].citation_weight` | integer | yes | Times this URL appeared in the response |
| `results[].citations[].resolved_domain` | string | no | Domain name (for Gemini proxy URL resolution) |
| `results[].sub_queries[]` | string[] | yes | Search queries the model issued. Feeds Workflow C and Influence SoV. |
| `results[].analysis` | object | yes | Structured analysis of the response |
| `results[].analysis.brand_mentioned` | boolean | yes | Whether brand appears in response |
| `results[].analysis.mention_type` | string/null | yes | `recommendation`, `named_mention`, `passing_reference`, or null |
| `results[].analysis.brand_position` | integer/null | no | Position in ranked list, null if not listed |
| `results[].analysis.sentiment` | string | yes | `Positive`, `Negative`, `Neutral` |
| `results[].analysis.competitors_mentioned` | string[] | yes | Competitor names found in response |
| `results[].analysis.domain_cited` | boolean | yes | Whether any citation URL matches the tracked domain |
| `results[].error` | string/null | yes | Error message if query failed, null on success |
| `total` | integer | yes | Total prompts executed |
| `summary` | object | yes | Aggregated run statistics |

---

### 4. citations.json — Structured Citation State

Accumulates citation data across runs. Machine-readable counterpart of MORPHIQ-TRACKER.md Section 7.

```json
{
  "schema_version": "1.0",
  "updated_at": "2026-03-27T10:30:00Z",
  "domain": "example.com",
  "total_active": 14,
  "active_citations": [
    {
      "url": "https://example.com/product",
      "provider": "openai",
      "prompt_id": "prompt-001",
      "prompt_text": "Best SaaS tools for team collaboration 2026",
      "prompt_type": "category",
      "citation_weight": 2,
      "authority_tier": "self",
      "first_seen": "2026-03-25",
      "last_seen": "2026-03-27",
      "consecutive_runs": 3,
      "status": "stable"
    }
  ],
  "history": [
    {
      "run_id": "track-2026-03-27",
      "date": "2026-03-27",
      "total": 14,
      "gained": 3,
      "lost": 0,
      "net": 3,
      "gained_citations": [
        {
          "url": "https://example.com/blog/guide",
          "provider": "perplexity",
          "prompt_id": "prompt-015",
          "prompt_type": "use_case"
        }
      ],
      "lost_citations": []
    }
  ]
}
```

#### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `schema_version` | string | yes | Always `"1.0"` |
| `updated_at` | ISO 8601 | yes | Last update timestamp |
| `domain` | string | yes | Tracked domain |
| `total_active` | integer | yes | Count of `active_citations` |
| `active_citations[]` | array | yes | All currently active citations |
| `active_citations[].url` | string | yes | Cited URL |
| `active_citations[].provider` | string | yes | Which provider cited this URL |
| `active_citations[].prompt_id` | string | yes | Which prompt triggered the citation |
| `active_citations[].prompt_text` | string | yes | Denormalized prompt text |
| `active_citations[].prompt_type` | string | yes | Pipeline prompt type |
| `active_citations[].citation_weight` | integer | yes | Times URL appeared in that response |
| `active_citations[].authority_tier` | string | yes | `"self"` (own domain), `"high"`, `"medium"`, `"low"` per `enrichment-sources.md` |
| `active_citations[].first_seen` | string | yes | ISO date of first appearance |
| `active_citations[].last_seen` | string | yes | ISO date of most recent appearance |
| `active_citations[].consecutive_runs` | integer | yes | Consecutive runs this citation has appeared. Reset to 1 if it reappears after loss. |
| `active_citations[].status` | string | yes | `"new"` (first seen this run), `"stable"` (consecutive runs), `"at_risk"` (was lost then regained) |
| `history[]` | array | yes | Per-run citation delta history |
| `history[].run_id` | string | yes | Matches manifest run entry |
| `history[].date` | string | yes | ISO date |
| `history[].total` | integer | yes | Total active citations at run time |
| `history[].gained` | integer | yes | New citations this run |
| `history[].lost` | integer | yes | Lost citations this run |
| `history[].net` | integer | yes | `gained - lost` |
| `history[].gained_citations` | array | yes | Specific citations gained |
| `history[].lost_citations` | array | yes | Specific citations lost |

#### Citation Unique Key

A citation is uniquely identified by the triple `(url, provider, prompt_id)`. Two citations with the same URL but different providers or prompts are tracked separately.

---

## Read/Write Rules

### Per Script

| Script | Reads | Writes |
|--------|-------|--------|
| `create-prompts.py --state-dir` | `manifest.json` (check existence), `prompts.json` (if subsequent run) | `prompts.json` (first run: full write; subsequent: append recommendations), `manifest.json` (init on first run) |
| `run-queries.py --state-dir` | `prompts.json` (config + prompt list), `manifest.json` (determine output path) | `results/track-{date}.json` (new file), `manifest.json` (prepend run to `runs` array) |
| `diff-results.py --state-dir` | `manifest.json` (resolve `runs[0]` and `runs[1]` paths), `citations.json` (previous citation state) | stdout (delta JSON) |
| `analyze-fanout.py --state-dir` | `manifest.json` (resolve latest results path), `results/track-{date}.json` (sub-queries + citations), optional scan report (page inventory + simulated queries) | stdout (fanout analysis JSON with content_gaps + content_creation_queue) |
| `generate-report.py --state-dir` | analysis data, deltas, optional fanout analysis | stdout (Delta Report with `raw_results.storage` populated) |
| Agent (morphiq-track) | All state files | `citations.json` (rebuild from delta), `prompts.json` (update tracking fields), `manifest.json` (update `updated_at`), `MORPHIQ-TRACKER.md` |
| Agent (morphiq-build Workflow B) | `manifest.json`, `prompts.json`, `citations.json`, latest `results/track-{date}.json` | None in state layer |

### Write Sequencing — Tracking Cycle

```
1. Agent reads manifest.json
   → Missing: first run. Proceed to step 2.
   → Present: subsequent run. Load prompts.json. Skip to step 3
     (or generate 20 recommendations if cooldown elapsed).

2. Run create-prompts.py --state-dir morphiq-track/
   → Writes prompts.json (full prompt set + config + validation)
   → Writes manifest.json (initial creation, empty runs array)

3. Run run-queries.py --state-dir morphiq-track/ --mode execute
   → Reads config from prompts.json
   → Writes morphiq-track/results/track-{date}.json
   → Prepends entry to manifest.json runs array

4. Run diff-results.py --state-dir morphiq-track/
   → Reads manifest to resolve current (runs[0]) and previous (runs[1]) paths
   → On baseline run (only 1 entry in runs): outputs baseline delta with null deltas
   → Outputs delta JSON to stdout

4.5. Run analyze-fanout.py --state-dir morphiq-track/ [--scan-report scan.json]
     → Reads latest results from manifest
     → Extracts sub-queries, merges with scan simulated queries if available
     → Compares against page inventory, identifies unanswered sub-queries
     → Outputs fanout analysis JSON to stdout (save as fanout-analysis.json)

5. Run generate-report.py --data analysis.json --deltas deltas.json [--fanout fanout-analysis.json]
   → Merges fanout content_gaps into analysis before building content queue
   → Outputs Delta Report JSON to stdout

6. Agent updates state:
   → Rebuilds citations.json from current results + previous citations
   → Updates prompts.json tracking fields (mentioned, cited, best_provider, runs_tracked)
   → Updates MORPHIQ-TRACKER.md (sections 5-9, 14 from state; sections 1-4, 10-13 as applicable)
   → Updates manifest.json updated_at
```

---

## Source of Truth

The state layer and MORPHIQ-TRACKER.md are complementary views of the same data. Each section has one source of truth:

| Tracker Section | Source of Truth | Sync Direction |
|----------------|----------------|----------------|
| §1 Score Summary | MORPHIQ-TRACKER.md (scan-owned) | Not in state layer |
| §2 Score Breakdown | MORPHIQ-TRACKER.md (scan-owned) | Not in state layer |
| §3 Open Issues | MORPHIQ-TRACKER.md (scan/build-owned) | Not in state layer |
| §4 Resolved Issues | MORPHIQ-TRACKER.md (build/scan-owned) | Not in state layer |
| §5 Share of Voice | Derived from results files | **State → Tracker** |
| §6 SoV Trend | `manifest.json` runs + results | **State → Tracker** |
| §7 Citation Analytics | `citations.json` | **State → Tracker** |
| §8 Tracked Prompts | `prompts.json` | **State → Tracker** |
| §9 Competitors | Derived from results files | **State → Tracker** |
| §10 Per-Page Performance | Mixed (scan scores + track citations) | Both directions |
| §11 Content Performance | MORPHIQ-TRACKER.md (build-owned) | Not in state layer |
| §12 Query Fanout Coverage | MORPHIQ-TRACKER.md (scan/track) | Not in state layer |
| §13 Content Creation Queue | MORPHIQ-TRACKER.md (track/build) | Not in state layer |
| §14 Run History | `manifest.json` runs array | **State → Tracker** |

### Sync Rules

**State → Tracker (after every tracking run):**
The agent reads computed SoV, citations, and prompt tracking data from JSON state files and writes the corresponding markdown tables into MORPHIQ-TRACKER.md. This is a one-way projection: the state layer is canonical for track-owned sections; the tracker markdown is regenerated from it.

**Tracker → State (not applicable for track-owned data):**
Sections owned by other skills (scores, issues, content performance, fanout coverage, content queue) remain in the tracker only. The agent reads these directly from MORPHIQ-TRACKER.md markdown when needed. The state layer does not duplicate scan/rank/build data.

---

## morphiq-build Consumption (Workflow B)

morphiq-build accesses the state layer **read-only** for content creation:

```
1. Read manifest.json → get latest results_path
2. Read prompts.json → find prompts where tracking.mentioned=false (content targets)
3. Read citations.json → get authority-tiered citation URLs for research sourcing
4. Read results/track-{latest}.json → extract:
   - response_text for competitor analysis (what do models say?)
   - citations for source identification (what do models cite?)
   - sub_queries for fanout coverage (what do models research?)
5. Pass data to morphiq-build as:
   - Source URLs (from citations with high authority_tier)
   - Topic/prompt text (from unmentioned prompts)
   - Competitive context (from response_text analysis)
6. morphiq-build runs its 5-step content lab pipeline
```

The state layer gives morphiq-build structured, machine-readable access to everything that was previously only available as transient stdout or lossy markdown tables.

---

## Retention

- **Results files:** Keep the last 10 runs in `morphiq-track/results/`. Older files can be pruned. Scripts handle missing files gracefully (the manifest entry remains but `results_path` points to a deleted file).
- **manifest.json:** Retains all run entries (metadata only, lightweight).
- **prompts.json:** Single file. Grows modestly — prompts are capped at ~50-70.
- **citations.json:** Single file. Bounded by the prompt set size.
- **Git history** preserves the full audit trail regardless of file deletion.

---

## Migration

For projects with an existing MORPHIQ-TRACKER.md but no state layer:

1. Agent detects `morphiq-track/manifest.json` does not exist but `MORPHIQ-TRACKER.md` does.
2. Creates `morphiq-track/` directory and initializes `manifest.json` with empty `runs` array.
3. Parses MORPHIQ-TRACKER.md §8 (Tracked Prompts) to bootstrap `prompts.json`. Available fields: text, type, mentioned, cited, best_provider, first_run, runs_tracked. Missing fields (`geo_category`, `pipeline_type`, `contains_temporal`) are re-derived from prompt text using detection rules in `prompt-taxonomy.md`.
4. Parses §7 (Citation Analytics) to bootstrap `citations.json` with active citations.
5. Next `run-queries.py` execution produces the first versioned results file.
6. From this point, the state layer is authoritative and subsequent runs use it directly.

---

## Backward Compatibility

All script changes use an opt-in `--state-dir` flag:

- **Without `--state-dir`:** Scripts behave exactly as before (stdin/stdout, explicit file paths).
- **With `--state-dir morphiq-track/`:** Scripts read/write from the state directory, auto-resolve paths from `manifest.json`, and produce versioned output.

The only additive (non-breaking) change to output schemas is the addition of `run_id`, `generated_at`, and `summary` fields in results files.
