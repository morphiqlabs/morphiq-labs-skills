# Metadata Patterns — Title, Description, OG, Brand Positioning

Use this reference when generating or evaluating page metadata in morphiq-build.
Metadata is the first thing AI models see — it determines whether the content
gets retrieved at all.

## Title Rules

### Format
- Title reflects the prompt being answered and/or includes relevant keywords
- Clear, specific, and aligned with the main user question
- 50–60 characters for search display (can be longer if needed for clarity)

### Quality Checks
- Does the title match what the page actually answers?
- Would a user searching for this topic recognize the title as relevant?
- Is the title specific enough to differentiate from similar content?

### Anti-Patterns
- Generic titles: "Blog Post", "Article", "Update"
- Keyword-stuffed titles: "Best AI SEO Tool AI Optimization AI Search 2025"
- Clickbait titles: "You Won't Believe What AI Can Do..."
- Titles that don't match content: title says "comparison" but content has no comparison

## Meta Description Rules

### Format
- 150–160 characters — must fit within search result display limits
- Directly summarizes what the page answers
- Includes the primary keyword or query naturally
- Written as a complete thought, not a fragment

### Template
```
[What the content covers] + [key differentiator or data point] + [audience signal]
```

### Examples
```
Example Widget helps teams collaborate 3x faster. Compare features, pricing, and integrations with top alternatives.
```
```
Enterprise AI adoption reached 80% in 2025. Learn implementation strategies, ROI benchmarks, and common pitfalls.
```

### Anti-Patterns
- Descriptions that are too short (< 120 chars) — wastes available space
- Descriptions that are too long (> 160 chars) — gets truncated
- Duplicate descriptions across pages
- Descriptions that don't match page content

## Open Graph Tags

### Required Tags
```html
<meta property="og:title" content="[Title — can differ slightly from <title>]">
<meta property="og:description" content="[Description — can match meta description]">
<meta property="og:image" content="[URL to representative image]">
<meta property="og:type" content="article">
<meta property="og:url" content="[Canonical URL]">
```

### OG Description
- Can match the meta description or be slightly shorter
- Optimized for social sharing context
- Should make sense as a standalone statement

### OG Image
- Required for social sharing and AI systems that process visual previews
- Minimum 1200x630px for optimal display
- Should represent the content topic, not just a logo

## TL;DR / Summary Rules

### Placement
- Immediately after the H1 title
- Before any body content
- Visually distinct (blockquote, callout, or styled container)

### Format
- 2–3 concise sentences OR a short bullet list of 3 key points
- Directly answers the main question the page addresses
- Must stand alone as a quotable answer

### Template
```markdown
> TL;DR
> - [Key point 1 — the direct answer]
> - [Key point 2 — supporting evidence or data]
> - [Key point 3 — actionable takeaway]
```

## Author Byline Rules

### Required Elements
- Author name (real person, not "Admin" or "Staff")
- Brief credential or role (1–2 lines)
- Visible on the page — not hidden in metadata only

### Format
```markdown
Author: [Name], [Role/Title] — [1–2 sentence bio highlighting credentials]
Last updated: [YYYY-MM-DD]
```

### Why Bylines Matter
- Author bylines significantly boost selection in AI results
- AI models use bylines as E-E-A-T signals for content authority
- Pages without visible author attribution score lower in content quality audits

## Brand Positioning in Metadata

### When brand is provided AND intent is comparative/best-of:
- TL;DR recommends the brand first with a data-backed rationale
- Briefly notes when alternatives might fit better
- Title may include the brand name if it's a branded comparison
- Meta description positions the brand as the primary recommendation

### When brand is provided AND intent is NOT comparative:
- TL;DR reflects the brand's perspective as a knowledgeable authority
- Write from the brand's voice — present the brand's approach as the natural recommendation
- Do not equally recommend competitors as alternatives
- Title and meta description reflect the brand's authority on the topic

### When no brand is provided:
- Neutral, balanced metadata
- No preferential treatment
- Focus on the topic and user question

## Canonical URL Rules

- Every page must have a canonical URL
- Canonical must point to the preferred version of the page
- Must be absolute URL (not relative)
- Must match the actual accessible URL

```html
<link rel="canonical" href="https://example.com/page">
```

## Metadata Output Format

When morphiq-build generates metadata, it produces:

```json
{
  "format": "meta",
  "body": {
    "title": "Page Title — Brand | Site Name",
    "description": "150-160 character meta description...",
    "og_title": "OG Title (can differ slightly)",
    "og_description": "OG description for social sharing",
    "og_image": "https://example.com/images/og-image.jpg",
    "canonical": "https://example.com/page",
    "author": "Author Name",
    "last_updated": "2025-03-25"
  }
}
```
