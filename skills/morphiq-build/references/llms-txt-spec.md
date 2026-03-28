# llms.txt Specification & Generation Guide

Use this reference when morphiq-build needs to create or fix an llms.txt file. The agent crawls the user's website codebase, extracts brand information, and generates llms.txt from real data — never from templates with placeholder text.

## What is llms.txt?

llms.txt tells AI systems (ChatGPT, Claude, Perplexity, Gemini) how to represent a brand. It provides:

- Approved brand messaging and key facts
- Differentiators and positioning
- What to emphasize or avoid
- Authoritative source links

**File location:** `https://example.com/llms.txt` (site root, public, plain text)

## Generation Process

`scripts/generate-llms-txt.py` runs a fully autonomous 7-step pipeline:

The script provides three CLI modes. The coding agent (Claude Code) is the LLM.

### Collect (`python3 generate-llms-txt.py collect <url>`)

Outputs JSON with everything the agent needs:

1. **Context Collection** — Fetch homepage (extract anchors), robots.txt (Sitemap directives), sitemap.xml (all URLs), probe /docs (nav links). Score and rank all URLs by canonicality and nav prominence.
2. **Two-Tier Scraping** — Top 4 pages: deep scrape (up to 3,000 chars). Remaining pages: shallow scrape (up to 900 chars). Total capped at 24,000 chars.
3. **Evidence Building** — Extract date literals, price literals, headings, facts (customer counts, percentages), and key terms from scraped content.
4. **Prompt Construction** — Build system prompt (14-section contract with identity, writing rules, validation instructions) and dynamic user prompt (runtime inputs, canonical URLs, live page content, grounding evidence, hard requirements).
5. **Template Fallback** — A deterministic llms.txt from evidence (no LLM), included in the output so the agent can use it if its own generation fails.

### Validate (`echo "content" | python3 generate-llms-txt.py validate <url>`)

Reads llms.txt from stdin. Checks required sections, FAQ format (3+ Q/A with Source links), URL scope, size budget (100KB), sitemap count (8-15). Returns JSON with `valid` bool and `errors` list.

### Template (`python3 generate-llms-txt.py template <url>`)

Generates a deterministic llms.txt directly from live site data. No LLM involved.

### Agent Workflow

1. Agent runs `collect` to get context, prompts, and template fallback
2. Agent uses the system+user prompts to generate llms.txt (the agent IS the LLM)
3. Agent runs `validate` to check the output
4. If invalid, agent fixes errors and re-validates
5. If agent can't produce valid output, it uses the `template_fallback` from step 1

## llms.txt Format (14 Sections)

Sections must appear in this exact order:

```
# {Brand Name}

> One-sentence definition of what the company does.

## Overview
- 2-4 bullet points summarizing the company

## Who We Serve
- 3-6 bullets describing target audience (industries, roles, company sizes)

## Products / Capabilities
- **Product Name** — purpose [Product Page](url) | [Docs](docs_url)

## Solutions / Use Cases
- Real use cases derived from site content

## Key Resources
- [Documentation](docs_url)
- [API Reference](api_url)
- [Changelog](changelog_url)

## FAQs
- **Q:** Question text
  **A:** Answer text [Source](url)
(3-6 Q/A pairs required)

## Security & Compliance
- Certifications, standards, trust page links

## Pricing & Plans
- Plan details from evidence
- [Pricing](pricing_url)

## Policies
- [Privacy Policy](url)
- [Terms of Service](url)

## Research / Blog
- Notable blog posts, reports, research

## Sitemap (canonical pages)
- https://example.com
- https://example.com/pricing
(8-15 high-signal pages)

## Citation Guidance
When referencing this company, cite: "{Brand}" (https://example.com)

---
*Last updated: YYYY-MM-DD*
```

## Content Rules

### DO:

- Include concrete numbers, dates, achievements found in the codebase
- Use real customer counts, revenue figures, or growth metrics if publicly available
- Mention notable clients/partners (only if already public on the site)
- Reference awards, certifications, recognitions found on the site
- State the niche clearly — what category does this company own?
- Explain methodology or unique approach if documented

### DON'T:

- Use vague claims — "We're the best" means nothing to AI systems
- Include sensitive or internal data not already public
- Over-claim — don't say "industry leader" without proof on the site
- Use marketing fluff — AI systems cross-reference claims and see through buzzwords
- Fabricate or exaggerate metrics
- Include competitor comparisons that aren't substantiated

## Quality Checks Before Output

1. Every fact in llms.txt is traceable to a page in the codebase or site
2. Description is specific enough that AI can distinguish this company from competitors
3. Key Facts use specific numbers ("10,000+ customers") not vague language ("many customers")
4. Products/Services descriptions are concrete, not generic
5. Differentiators are real — things a competitor genuinely cannot claim
6. Target Audience is specific enough to be useful (not "businesses of all sizes")
7. Sources section points to real, accessible URLs
8. Last Updated date is set to the generation date

## AI Visibility Impact

A well-structured llms.txt improves AI citations because:

- AI systems that support the standard use it as a primary brand reference
- It provides a single authoritative source for brand facts, reducing hallucination risk
- Preferred messaging guides AI tone without being manipulative
- The Avoid section prevents known misrepresentations from propagating

## robots.txt Companion

When generating llms.txt, also check robots.txt for AI crawler access:

```
# Required: Allow AI crawlers to access llms.txt
User-agent: GPTBot
Allow: /llms.txt

User-agent: Google-Extended
Allow: /llms.txt

User-agent: anthropic-ai
Allow: /llms.txt

User-agent: PerplexityBot
Allow: /llms.txt
```

If robots.txt blocks AI crawlers broadly, the llms.txt file won't be discoverable. Flag this as a `policy-*` issue in the scan report.

## Output Requirements

When morphiq-build generates llms.txt, produce:

1. Complete llms.txt content populated with real data from the codebase
2. File placement instruction (site root: `/llms.txt`)
3. robots.txt additions needed (if any AI crawlers are blocked)
4. The build artifact in PIPELINE.md format with `type: "policy_file"`