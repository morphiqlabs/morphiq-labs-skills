# Content Quality Evaluation Criteria

Use this reference when scoring a page's content quality during a morphiq-scan audit.
These criteria determine whether content is **citable by AI systems** — whether an LLM
would confidently reference, quote, or recommend this content in its responses.

## Quality Pillars

Score each page against these five pillars:

### 1. Clear Relevant Title
- Title reflects the question being answered and/or includes relevant keywords
- Title is specific and aligned with the main user query the page should rank for
- **Fail signals**: generic titles ("Blog Post"), keyword-stuffed titles, titles that don't match page content

### 2. Concise Answers Up Front (TL;DR)
- Immediately after the title, the page provides a brief summary or TL;DR that directly answers the core question
- TL;DR is 2–3 concise sentences or a short bullet list of key points
- The direct answer is surfaced at the top — not buried in the body
- **Fail signals**: no summary, answer buried in paragraph 4+, vague opening paragraphs

### 3. E-E-A-T Signals (Experience, Expertise, Authoritativeness, Trustworthiness)

**Author Credentials**
- Author name and brief bio with credentials/experience (certifications, years in field)
- Visible byline — author bylines significantly boost selection in AI results
- **Fail signals**: no author attribution, "Admin" or "Staff" as author, no credentials

**First-Hand Experience**
- Content integrates personal experience and real-world usage
- Look for signals like "In our 5-year study…", "Having implemented this…"
- User-generated content (comments, reviews, case studies) adds experience signals
- **Fail signals**: entirely generic advice, no personal or organizational perspective

**Authoritative Sources**
- Key facts and claims reference reputable external sources (academic, standards bodies, credible news)
- Sources are hyperlinked, not just mentioned
- **Fail signals**: unsourced claims, links to low-authority sites, broken links

**Currency**
- Recent timestamp visible (publication or "Last updated" date)
- Content reflects current state of the topic
- **Fail signals**: no date, dates older than 18 months on fast-moving topics

**Tone**
- Balanced, factual style
- No overly promotional or clickbait language
- **Fail signals**: excessive superlatives, hype language, unsubstantiated claims

### 4. Statistics and Citations

**Citation Format Check**
- Statistics must use **name-drop + link format**: source named IN the sentence with a markdown/hyperlink
- Correct: "According to [Gartner](url), 80% of enterprises will adopt AI by 2026."
- Wrong: "80% of enterprises will adopt AI by 2026 ([Gartner](url))." (trailing parenthetical — AI models miss the source association)
- Wrong: "80% of enterprises will adopt AI by 2026." (no source at all)

**Minimum Thresholds**
- At least 3 statistics with source attribution across body sections
- Statistics integrated naturally within paragraphs — not in standalone "Key Statistics" sections
- At least 1 expert quote with in-text attribution (speaker name + credential in sentence body)
- Correct: "As Dr. Jane Smith, Chief AI Officer at Acme Corp, explains: 'AI adoption requires a data-first strategy.'"
- Wrong: blockquote-style attribution — AI models treat blockquotes as decorative

**Source Authority**
- Prefer recognized industry sources: Gartner, McKinsey, Forrester, HBR, peer-reviewed journals
- Niche-specific sources acceptable when authoritative sources don't cover the topic

### 5. Specific Examples (Mini Case Studies)

- Case studies must be real, sourced, and verifiable
- Structure: Problem → Approach/Action → Outcome (with metrics and timeframe)
- Written as narrative paragraphs, not bullet lists
- **Fail signals**: fabricated examples, fictional company names, no metrics, no source

## Scoring Guide

When evaluating content quality for a page, check each pillar and note issues:

| Pillar | Weight | What to Check |
|--------|--------|---------------|
| Clear Title | 15% | Title specificity, keyword alignment, query match |
| TL;DR | 20% | Answer placement, conciseness, directness |
| E-E-A-T | 30% | Author, experience, sources, currency, tone |
| Statistics/Citations | 25% | Count, format, authority, integration |
| Examples | 10% | Real case studies with metrics (if applicable) |

Issue IDs for content quality problems follow the pattern: `content-{specific-problem}`

Examples:
- `content-no-tldr` — No summary or direct answer at top of page
- `content-no-author` — No author attribution or credentials
- `content-unsourced-stats` — Statistics without source attribution
- `content-wrong-citation-format` — Citations use trailing parenthetical instead of name-drop format
- `content-no-expert-quotes` — No expert quotes with in-text attribution
- `content-stale-date` — Content date older than 18 months
- `content-thin-faq` — No or insufficient FAQ content
- `content-fabricated-examples` — Case studies appear fictional or unverifiable
