# Policy Files — robots.txt + llms.txt Audit

Use this reference during morphiq-scan to detect, validate, and audit policy files that control AI crawler access and provide machine-readable site navigation.

## Files to Check

| File | Location | What to Check | Validation |
|---|---|---|---|
| robots.txt | `/robots.txt` | Exists, valid plain text (not HTML 404), user-agent blocks, allow/disallow rules, sitemap references | `isValidRobotsTxt()` |
| llms.txt | `/llms.txt` | Exists, valid plain text | `isValidLlmsTxt()` |
| llms-full.txt | `/llms-full.txt` | Exists, valid plain text | Same validation |
| sitemap.xml | `/sitemap.xml` | Exists, starts with `<?xml` or `<urlset>` or `<sitemapindex>` | XML structure check |

---

## robots.txt Audit

### Detection

Fetch `{domain}/robots.txt`. Validate:
1. HTTP 200 response
2. Content-type is `text/plain` (not HTML — many 404 pages return HTML)
3. Contains at least one `User-agent:` directive

### AI Crawler User-Agents

Check allow/disallow rules for these critical user-agents:

| User-Agent | Provider | Blocking Impact |
|---|---|---|
| GPTBot | OpenAI | Blocks ChatGPT from accessing site content |
| Google-Extended | Google | Blocks Gemini and AI Overviews |
| Anthropic-AI / ClaudeBot | Anthropic | Blocks Claude from accessing site content |
| PerplexityBot | Perplexity | Blocks Perplexity from accessing site content |

### Validation Rules

- A `Disallow: /` rule under a matching user-agent blocks the entire site
- A `Disallow:` with no path means nothing is disallowed (allow all)
- More specific paths override broader ones
- `Allow:` rules take precedence over `Disallow:` when equally specific

### Sitemap Discovery

Extract sitemap URLs from robots.txt `Sitemap:` directives. These determine which pages get analyzed during the scan.

---

## llms.txt Audit

### Detection

Fetch `{domain}/llms.txt`. Validate:
1. HTTP 200 response
2. Content-type is `text/plain`
3. Non-empty content

### Quality Assessment

| Quality Level | Criteria |
|---|---|
| **Good** (≥500 characters) | Site summary, key page links, structured navigation, clear descriptions |
| **Thin** (<500 characters) | Exists but lacks useful structure or content |
| **Missing** | File does not exist or returns non-200 |

### llms-full.txt

Same detection and validation as llms.txt. This extended file provides more comprehensive site content for LLM consumption.

---

## Issue Generation

Policy file findings generate issues with the following severity:

| Finding | Issue ID | Severity | Rationale |
|---|---|---|---|
| Missing llms.txt | `policy-no-llms-txt` | high | Primary AI navigation aid — without it, models navigate blind |
| Thin llms.txt (<500 chars) | `policy-weak-llms-txt` | medium | Exists but does not provide useful structure |
| No robots.txt | `policy-no-robots-txt` | medium | Missing, but most crawlers default to allow |
| Invalid robots.txt syntax | `policy-invalid-robots-syntax` | low | May cause unpredictable crawler behavior |
| Blocks GPTBot | `policy-blocks-gptbot` | high | Blocks the highest-fanout AI model |
| Blocks Google-Extended | `policy-blocks-google-extended` | high | Blocks Gemini and AI Overviews |
| Blocks Anthropic-AI | `policy-blocks-anthropic` | high | Blocks Claude |
| Blocks PerplexityBot | `policy-blocks-perplexity` | medium | Blocks Perplexity (lower fanout visibility) |

---

## Scoring Impact

Policy files are scored at the **domain level**, not per-page:

- robots.txt: 1 point per major AI crawler allowed (GPTBot, Google-Extended, Anthropic-AI, PerplexityBot), +1 for clean syntax = max 5 points
- llms.txt: 3 points for existence, +2 for quality (spec compliance, useful content) = max 5 points
- Total: 10 points (matching Category 5 in `scoring-rubric.md`)

---

## llms.txt Spec Reference

For the full llms.txt specification and generation rules, refer to `../morphiq-build/references/llms-txt-spec.md`.
