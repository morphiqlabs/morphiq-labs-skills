# Schema Templates — JSON-LD Generation

Use this reference during morphiq-build when generating JSON-LD schema markup for content artifacts. This document defines the template generation rules per schema type, required data sources, and skip conditions.

## Core Principle: No Placeholders

If data cannot be extracted from the actual page content, that schema type is skipped with a reason logged. Templates are populated from real DOM data only — never generate schema with placeholder or fabricated values.

---

## Template Generation Per Schema Type

| Schema Type | Required Data | Source | Skipped If |
|---|---|---|---|
| Organization | name, url | Title tag, canonical URL | No title |
| WebSite | name, url | Title tag, canonical URL | No title |
| Product | name, description | H1, meta description | No H1 |
| Service | name, description | Title/H1 + meta description | No title/H1/meta |
| Article | headline, datePublished | H1, publish date | No H1 |
| BlogPosting | headline, datePublished, author | H1, date, author element | No H1 |
| HowTo | name, step[] | H1 (name), H2/H3s (steps) | < 2 sub-headings |
| BreadcrumbList | itemListElement[] | URL path segments | Always generated (never skipped) |
| FAQPage | mainEntity[] | Extracted FAQ Q&A pairs | No FAQ content detected |
| SoftwareApplication | name, applicationCategory, offers | Title/H1, content analysis | No title/H1 |
| CollectionPage | name, description | Title, meta description | No title |
| ItemList | itemListElement[] | List items on page | No structured list |
| AboutPage | name, description | Title, meta/H1 | No title |

### Always-Skipped Types

These types require data that cannot be reliably extracted from page content alone:

| Schema Type | Reason for Skip |
|---|---|
| VideoObject | Cannot extract `thumbnailUrl`, `uploadDate`, `duration` reliably |
| Review | Cannot extract `author`, `itemReviewed`, `reviewRating` reliably |
| OfferCatalog | Cannot extract real pricing tiers from HTML structure |
| Person | Cannot extract author data (affiliation, image, credentials) reliably |

When a type is skipped, log the reason in the build output metadata for transparency.

---

## Template Structures

### Organization

```json
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "[extracted from title]",
  "url": "[canonical URL]",
  "logo": "[extracted from og:image or site logo if detectable]"
}
```

### WebSite

```json
{
  "@context": "https://schema.org",
  "@type": "WebSite",
  "name": "[extracted from title]",
  "url": "[canonical URL]"
}
```

### Product / SoftwareApplication

```json
{
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  "name": "[extracted from H1]",
  "applicationCategory": "[detected from content]",
  "operatingSystem": "Web",
  "offers": {
    "@type": "Offer",
    "price": "[if detectable]",
    "priceCurrency": "USD"
  }
}
```

Use `SoftwareApplication` when SaaS is detected (see morphiq-scan skill's `references/page-type-rules.md`), `Product` otherwise.

### Article / BlogPosting

```json
{
  "@context": "https://schema.org",
  "@type": "BlogPosting",
  "headline": "[extracted from H1]",
  "datePublished": "[extracted from publish date]",
  "dateModified": "[extracted from last modified date]",
  "author": {
    "@type": "Person",
    "name": "[extracted from author element]"
  },
  "description": "[extracted from meta description]"
}
```

### HowTo

```json
{
  "@context": "https://schema.org",
  "@type": "HowTo",
  "name": "[extracted from H1]",
  "step": [
    {
      "@type": "HowToStep",
      "name": "[extracted from H2/H3]",
      "text": "[extracted from following paragraph]"
    }
  ]
}
```

Requires at least 2 sub-headings to generate the step array.

### BreadcrumbList

```json
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    {
      "@type": "ListItem",
      "position": 1,
      "name": "Home",
      "item": "[root URL]"
    },
    {
      "@type": "ListItem",
      "position": 2,
      "name": "[segment name]",
      "item": "[segment URL]"
    }
  ]
}
```

Built from URL path segments. Always generated for non-home pages.

### FAQPage

```json
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "[extracted question text]",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "[extracted answer text]"
      }
    }
  ]
}
```

Only generated when FAQ content is detected (see FAQ detection methods in morphiq-scan skill's `references/agentic-readiness.md`).

---

## Page Type → Schema Assignment

For the mapping of page types to expected schemas, SaaS detection logic, and deterministic rules, refer to morphiq-scan skill's `references/page-type-rules.md`.

---

## Build Output Integration

Each schema injection produces a build artifact:

```json
{
  "type": "schema",
  "page_url": "[target page URL]",
  "schema_type": "[Organization, Product, etc.]",
  "json_ld": "[complete JSON-LD block]",
  "placement": "Inject into <head> as <script type=\"application/ld+json\">"
}
```

Skipped schemas are recorded in metadata:

```json
{
  "skipped_schemas": [
    {
      "type": "VideoObject",
      "reason": "Cannot extract thumbnailUrl and uploadDate"
    }
  ]
}
```
