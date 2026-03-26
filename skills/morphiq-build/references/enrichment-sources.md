# Enrichment Sources — Citation & Research Rules

Use this reference during Step 4 (Research) and Step 5 (Generate/Rewrite) to
ensure all statistics, quotes, and claims follow the Morphiq citation standard.
These rules directly impact AI citability — improperly cited content gets skipped
by AI models.

## Citation Format: Name-Drop + Link

Every statistic and claim must use **name-drop + link** format: the source is named
IN the sentence with a markdown/hyperlink.

### Correct Format

```markdown
According to [Gartner](https://gartner.com/report), 80% of enterprises will adopt AI by 2026.
```

```markdown
Research from [McKinsey](https://mckinsey.com/insights) shows a 35% productivity gain.
```

### Wrong Formats — Do Not Use

```markdown
80% of enterprises will adopt AI by 2026 ([Gartner](https://gartner.com/report)).
```
Trailing parenthetical — AI models miss the source association.

```markdown
80% of enterprises will adopt AI by 2026.
```
No source at all — unsourceable claim.

```markdown
80% of enterprises will adopt AI by 2026. [1]
```
Footnote-style — AI models don't resolve footnotes during retrieval.

### Why This Matters

AI models parse sentences as atomic units. When the source name appears IN the sentence,
the model associates the claim with the source. Trailing parentheticals and footnotes
are structurally separate — the model often cites the claim without the source, or
skips the claim entirely because it can't verify it.

Statistics addition increases AI visibility by +41% (Princeton GEO research).
Quotation addition increases AI visibility by +28%.

## Minimum Thresholds

| Element | Minimum Required | Notes |
|---------|-----------------|-------|
| Statistics with source attribution | 3 per article | Integrated in paragraphs, not standalone sections |
| Expert quotes with in-text attribution | 1 per article | Speaker name + credential in sentence body |
| Authoritative external sources | 3 per article | Named + linked in text |

## Expert Quote Format: In-Text Attribution

Expert quotes use **in-text attribution**: speaker name + credential in the sentence body.

### Correct Format

```markdown
As Dr. Jane Smith, Chief AI Officer at Acme Corp, explains: "AI adoption requires a data-first strategy."
```

### Wrong Format — Do Not Use

```markdown
> "AI adoption requires a data-first strategy."
> — Dr. Jane Smith, Chief AI Officer at Acme Corp
```
Blockquote style — AI models treat blockquotes as decorative content and often skip them
during retrieval.

### Why This Matters

AI models give higher confidence to quotes that are inline with the prose. Blockquote-
formatted quotes are visually distinct to humans but structurally ambiguous to LLMs.
The model can't reliably attribute the quote to the speaker when they're in separate
structural elements.

## Source Authority Preference

When multiple sources cover the same data point, prefer in this order:

### Tier 1 — Highest Authority
- Gartner, McKinsey, Forrester, Deloitte, BCG, Bain
- Harvard Business Review, MIT Sloan Management Review
- Peer-reviewed academic journals
- Government/standards body publications (NIST, ISO, W3C)

### Tier 2 — High Authority
- Major tech research (IDC, Statista, CB Insights)
- Reputable news outlets (Reuters, Bloomberg, WSJ, NYT)
- Industry-specific publications (TechCrunch, Wired, The Information)

### Tier 3 — Acceptable
- Niche-specific authoritative sources
- Company research reports (if the company is credible in the space)
- Conference proceedings and presentations

### Tier 4 — Use Only When Nothing Else Available
- Blog posts from recognized experts
- Community surveys and polls
- Self-reported company data

**Never use:**
- Wikipedia as a primary source (acceptable for background context)
- Social media posts
- Anonymous or unverifiable sources
- Content farms or SEO-optimized aggregators

## Research Strategy for Gap Filling

When running live web searches in Step 4, follow this strategy:

### For Data Gaps
- Search for: `"{topic} statistics {year}"`, `"{topic} market size"`, `"{topic} adoption rate"`
- Target Tier 1-2 sources
- Capture: exact number + unit + source name + URL + publication date

### For Depth Gaps
- Search for: `"{topic} expert opinion"`, `"{topic} interview {year}"`, `"{person} {topic}"`
- Target expert interviews, conference talks, published opinions
- Capture: quote text + speaker name + credential + source URL

### For Content Gaps
- Search for: the specific question that's unanswered
- Target comprehensive articles, guides, or research that address the gap
- Capture: key findings + source attribution

### For Brand Positioning Gaps
- Search for: `"{brand} vs {competitor}"`, `"{brand} review {year}"`, `"{brand} case study"`
- Target independent reviews, analyst reports, customer testimonials
- Capture: differentiators + metrics + source attribution

## Integration Rules

When integrating research findings into content:

1. **Statistics**: Place within the paragraph where the claim is made, not in a separate statistics section
2. **Expert quotes**: Weave into the narrative flow, not as standalone blockquotes
3. **Sources**: Link at point of first mention, not in a bibliography at the bottom
4. **Data visualizations**: When used, always describe the data in text beneath the visual
5. **Freshness**: Prefer data from the current or previous year; flag data older than 2 years
