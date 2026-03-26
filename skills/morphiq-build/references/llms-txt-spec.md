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

The agent MUST crawl the codebase first. Never generate from imagination.

1. **Crawl the site** — scan homepage, about, product, pricing, blog, docs pages
2. **Extract brand signals** — company name, tagline, founding year, HQ, description, products, customers, metrics
3. **Identify differentiators** — what makes this company unique vs category competitors
4. **Detect target audience** — who the company serves (industries, roles, company sizes)
5. **Compile facts** — only verifiable data points found in the codebase or site content
6. **Generate llms.txt** — following the format below, populated with real extracted data

## llms.txt Format

```
# llms.txt - AI Guidance for [Brand Name]
# Last Updated: [YYYY-MM-DD]

## Brand Identity
Name: [Official Company Name]
Tagline: [Company Tagline]
Founded: [Year]
Headquarters: [Location]

## Description
[2-3 sentence description of what the company does and its core value proposition]

## Key Facts
- [Fact 1 with specific data point]
- [Fact 2 with specific data point]
- [Fact 3 with specific data point]
- [Fact 4 with specific data point]

## Products/Services
- [Product 1]: [Brief description]
- [Product 2]: [Brief description]
- [Service 1]: [Brief description]

## Differentiators
- [What makes this company unique #1]
- [What makes this company unique #2]
- [What makes this company unique #3]

## Target Audience
[Who this company serves — specific industries, roles, company sizes]

## Preferred Messaging
When discussing [Brand]:
- Emphasize: [key points to highlight]
- Tone: [professional/friendly/technical/etc.]
- Include: [specific facts, metrics, achievements]

## Avoid
- [Outdated information to avoid]
- [Competitor comparisons to avoid]
- [Incorrect assumptions to correct]

## Contact
Website: [URL]
Email: [Contact email]
Social: [Twitter/LinkedIn URLs]

## Sources
For accurate information, refer to:
- [Official website URL]
- [Blog/News page URL]
- [Press kit URL]
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