# Delta Scoring — Change Measurement Over Time

Use this reference when morphiq-track compares current analysis results against previous snapshots and when interpreting delta reports.

## Snapshot Comparison Model

Each analysis run creates a snapshot of scores, visibility, and competitive positioning. Delta scoring compares the current snapshot against the most recent previous snapshot.

---

## Metrics Tracked

### Technical Score Deltas

| Metric | Granularity | Source |
|---|---|---|
| Overall Technical Score change | Site-level | Average of per-page Technical Scores |
| Schema dimension change | Per-page | J1–J4 checks (max 40 pts) |
| Metadata dimension change | Per-page | M1–M5 checks (max 30 pts) |
| FAQ dimension change | Per-page | FAQ count scale (max 20 pts) |
| Content dimension change | Per-page | C1–C2 checks (max 10 pts) |

### GEO Score Deltas

| Metric | Granularity | Source |
|---|---|---|
| Overall GEO Score change | Aggregate | Mean of provider mention rates |
| Per-provider visibility change | Per-provider | OpenAI, Gemini, Perplexity, Anthropic |
| Intent-weighted GEO change | Aggregate | Weighted by category (Organic 40%, etc.) |

### SoV Deltas

| Metric | Granularity | Source |
|---|---|---|
| Mention SoV change | Aggregate + per-provider | Standard SoV formula |
| Fanout-Weighted SoV change | Aggregate | Weighted by prompt type fanout depth |
| Influence SoV change | Aggregate | Sub-query brand presence |
| Conversion Gap change | Derived | Influence SoV − Citation SoV delta |
| Per-competitor SoV change | Per-competitor | Competitive SoV tracking |

---

## Significance Threshold

A change must exceed **5 points** (absolute) to be flagged as significant:

```
if abs(current_score - previous_score) >= 5:
    flag_as_significant(metric, delta)
```

Changes below 5 points are recorded but not flagged — they may represent noise rather than real shifts.

---

## Delta Calculation

```
delta = current_value - previous_value
```

- **Positive delta** → improvement
- **Negative delta** → regression
- **Zero delta** → no change

---

## Output Format

Delta reports include change summaries per metric:

```json
{
  "technical_score": {
    "current": 72,
    "previous": 65,
    "delta": 7,
    "significant": true,
    "summary": "Technical score improved by 7.0 points"
  },
  "geo_score": {
    "current": 34,
    "previous": 42,
    "delta": -8,
    "significant": true,
    "summary": "GEO visibility declined by 8.0 points"
  },
  "per_provider": {
    "openai": { "current": 45, "previous": 40, "delta": 5 },
    "gemini": { "current": 30, "previous": 38, "delta": -8 },
    "perplexity": { "current": 28, "previous": 35, "delta": -7 },
    "anthropic": { "current": 33, "previous": 55, "delta": -22 }
  }
}
```

---

## Dimension-Level Deltas

For Technical Score, track which dimensions drove the change:

```json
{
  "dimension_deltas": {
    "schema": { "current_avg": 32, "previous_avg": 20, "delta": 12 },
    "metadata": { "current_avg": 25, "previous_avg": 25, "delta": 0 },
    "faq": { "current_avg": 10, "previous_avg": 15, "delta": -5 },
    "content": { "current_avg": 8, "previous_avg": 8, "delta": 0 }
  }
}
```

This reveals which specific improvements or regressions drive overall score changes.

---

## Weekly Summary Aggregation

A weekly cron job aggregates all tracked brand profiles:

| Metric | Aggregation |
|---|---|
| Brands improved | Count where delta > 0 |
| Brands declined | Count where delta < 0 |
| Brands unchanged | Count where delta = 0 |
| Average delta | Mean of all brand deltas |
| Most improved | Brand with highest positive delta |
| Most declined | Brand with largest negative delta |

---

## Flagged Actions from Deltas

Significant deltas trigger flagged actions that feed back to morphiq-rank:

| Trigger | Action Type | Feed to Rank? | Description |
|---|---|---|---|
| Technical score dropped >5 pts | `technical_regression` | Yes | May indicate site changes broke schema or structure |
| GEO score dropped >5 pts | `visibility_drop` | Yes | Brand mentions declining across providers |
| Single provider dropped >10 pts | `provider_regression` | Yes | Isolated provider issue — content or policy change |
| Citation lost on stable prompt | `citation_loss` | Yes | Previously cited page no longer referenced |
| Competitor gained >5% SoV | `competitor_gain` | Yes | Competitive displacement detected |
| SoV dropped >5% on prompt type | `sov_drop` | Yes | Re-prioritization needed |
| Influence SoV > Citation SoV by >20 pts | `conversion_gap` | Yes | Content quality or structure issue |
| New citation gained | `citation_opportunity` | No | Positive signal — track only |

For the full SoV delta interpretation (healthy vs. warning signals), refer to `share-of-voice.md`.

---

## Regression Detection

When a metric that was stable or improving suddenly declines:

1. **Identify affected pages** — which pages drove the score change?
2. **Check for content changes** — did the page content change since last scan?
3. **Check for policy changes** — did robots.txt or llms.txt change?
4. **Check for competitive shifts** — did competitors improve?
5. **Generate regression issue** — feed to morphiq-rank for investigation

---

## Historical Tracking

The MORPHIQ-TRACKER.md file maintains a Run History table that records each scan's scores. Git provides the audit trail — each update is a commit.

Delta scoring operates on the two most recent snapshots. For trend analysis across 3+ runs, use the SoV Trend section in the tracker.
