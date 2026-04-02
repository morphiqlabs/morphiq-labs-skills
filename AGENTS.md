# Morphiq Labs — Agent Skills

This repository contains 4 agent skills for AI visibility optimization. Each skill runs independently — invoke one per chat turn and follow the pipeline order below.

## Pipeline

```
morphiq-scan → morphiq-rank → morphiq-build → morphiq-track
```

## Skills

| Skill | Purpose | Input | Output |
|---|---|---|---|
| **morphiq-scan** | Audit a website for AI visibility across 5 categories | Domain URL | `MORPHIQ-SCAN.json` |
| **morphiq-rank** | Prioritize issues into a tiered roadmap | `MORPHIQ-SCAN.json` | `MORPHIQ-RANK.json` |
| **morphiq-build** | Generate content, schema, and policy file fixes | `MORPHIQ-RANK.json` | `MORPHIQ-BUILD.json` |
| **morphiq-track** | Measure AI visibility with real provider queries | API keys + brand info | `MORPHIQ-TRACKER.md` + `MORPHIQ-DELTA-REPORT.json` |

## Usage

Run each skill in a separate chat message:

1. **"Run Morphiq Scan on example.com"**
2. **"Run Morphiq Rank from the scan"**
3. **"Run Morphiq Build to fix the issues"**
4. **"Run Morphiq Track with API keys"**

See [PIPELINE.md](PIPELINE.md) for JSON data contracts between skills.
