# Morphiq Skills

AI visibility audit, prioritization, content optimization, and monitoring — as installable agent skills.

Morphiq Skills encodes [Mudra Labs'](https://trymudra.com) AI visibility methodology into reusable skills for any compatible coding agent (Claude Code, Cursor, Copilot, Codex, etc.). Built on the [Agent Skills](https://agentskills.io) open standard.

## Install

```bash
npx skills add morphiqlabs/morphiq-labs-skills
```

## Skills

### morphiq-scan — Audit
Crawls a target domain and produces a full AI visibility audit.

- Technical structure + agentic readiness analysis
- Schema markup coverage evaluation
- Content quality + E-E-A-T assessment
- LLM chunking and retrieval quality scoring
- Query fan-out analysis (simulated AI sub-questions)
- Policy file detection (robots.txt, llms.txt)
- 100-point scoring against the Morphiq rubric

**Output:** Structured scan report (JSON) → feeds into morphiq-rank

### morphiq-rank — Prioritize
Takes the scan output and produces a prioritized action roadmap.

- Weights every issue by AI visibility impact
- Organizes into 4 progressive discovery tiers
- Ranks by effort vs ROI
- Flags policy file and schema issues as high-priority
- Tracks dependencies between issues

**Output:** Tiered roadmap (JSON) → feeds into morphiq-build

### morphiq-build — Implement
Creates and optimizes content for AI visibility. Two entry points:

**From existing content** — runs the 5-step Content Lab pipeline:
1. Ingest sources (URLs, PDFs, raw text)
2. Extract and structure content
3. Analyze gaps vs query space
4. Live web research to fill gaps
5. Generate final optimized content

**From user prompt** — generates AEO-structured content directly.

Also handles: schema injection, llms.txt creation, metadata optimization, FAQ generation.

**Output:** Build artifacts (JSON) → feeds into morphiq-track

### morphiq-track — Monitor
Recurring measurement of AI visibility across providers.

- Generates prompt sets (brand, category, comparison, feature, use case)
- Queries OpenAI, Gemini, Perplexity, and Anthropic APIs
- Captures structured responses per provider
- Computes Share of Voice: (Company Mentions / Total Mentions) x 100
- Diffs results against previous runs
- Generates delta report with flagged actions

**Output:** Delta report (JSON) → loops back to morphiq-rank

## Pipeline

The four skills form a sequential pipeline:

```
morphiq-scan → morphiq-rank → morphiq-build → morphiq-track
                  ↑                                    │
                  └────────────────────────────────────┘
```

Each skill produces structured JSON that the next skill consumes. Data contracts are defined in [PIPELINE.md](PIPELINE.md).

## Scoring Categories

| Category | Max Points | Covers |
|----------|-----------|--------|
| Agentic Readiness | 45 | Technical structure, schema markup, machine-readability |
| Content Quality | 20 | Depth, E-E-A-T, citations, examples |
| Chunking & Retrieval | 15 | Heading hierarchy, paragraph quality, retrieval resilience |
| Query Fan-Out | 10 | Sub-question coverage, reasoning retrieval support |
| Policy Files | 10 | robots.txt, llms.txt configuration |

## API Keys (morphiq-track)

morphiq-track queries AI providers directly. Set these environment variables:

```
OPENAI_API_KEY        # web_search tool with forced tool_choice
ANTHROPIC_API_KEY     # tool use pattern
PERPLEXITY_API_KEY    # native search behavior
GEMINI_API_KEY        # grounding with URL resolution
```

## Project Structure

```
morphiq-labs-skills/
├── README.md
├── PIPELINE.md          # Data contracts between skills
├── PROGRESS.md          # Build tracker
├── LICENSE
└── skills/
    ├── morphiq-scan/    # Audit
    ├── morphiq-rank/    # Prioritize
    ├── morphiq-build/   # Implement
    └── morphiq-track/   # Monitor
```

Each skill contains:
- `SKILL.md` — Workflow instructions + frontmatter (the skill itself)
- `references/` — Deep methodology loaded conditionally
- `scripts/` — Deterministic utilities the agent calls
- `evals/` — User-facing self-tests

## License

Apache-2.0

## Links

- [Morphiq](https://trymudra.com) — AI visibility platform
- [Agent Skills Standard](https://agentskills.io) — Skill specification
- [skills.sh](https://skills.sh) — Agent skills marketplace
