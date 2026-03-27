# Page Type Rules — Detection & Expected Elements

Use this reference during morphiq-scan to classify pages by type and determine expected schema, metadata, and structural elements per page type.

## Page Type Classification (19 Types)

Detection uses URL pattern matching on the normalized pathname (locale prefixes stripped):

| Page Type | URL Patterns |
|---|---|
| home | `/` or empty path |
| blog | `/blog`, `/posts`, `/articles` |
| pricing | `/pricing` |
| features | `/features`, `/tools`, `/calculator` |
| product | `/product`, `/products`, `/payment` |
| solutions | `/solution` |
| about | `/about`, `/team`, `/company`, `/partner` |
| documentation | `/docs`, `/documentation`, `/help`, `/guide` |
| use-cases | `/use-case`, `/use-cases` |
| customers | `/customer`, `/case-stud`, `/success-stor` |
| resources | `/resource`, `/whitepaper`, `/ebook` |
| integrations | `/integration` |
| changelog | `/changelog`, `/release-notes` |
| careers | `/career`, `/jobs` |
| legal | `/legal`, `/privacy`, `/terms`, `/cookie` |
| contact | `/contact` |
| demo | `/demo` |
| login | `/login` |
| signup | `/signup` |
| other | Catch-all for unmatched patterns |

---

## Marketing vs. Non-Marketing Pages

Only marketing-relevant pages contribute to the site Technical Score average:

**Marketing pages** (scored): home, pricing, features, product, solutions, blog, use-cases, customers, resources, integrations, about

**Non-marketing pages** (excluded from average): contact, login, signup, legal, demo, careers, changelog

This distinction also affects FAQ scoring — non-marketing pages receive 0/0 for FAQ (not penalized, not counted).

---

## Recommended Schemas Per Page Type

| Page Type | Expected Schemas | Notes |
|---|---|---|
| home | Organization, WebSite | No BreadcrumbList on home |
| blog | BlogPosting, Person (post) / CollectionPage (index) | Differentiates post vs listing |
| product | SoftwareApplication (SaaS) or Product | SaaS signal detection |
| pricing | Product/SoftwareApplication + OfferCatalog | Multiple pricing tiers |
| features | SoftwareApplication (if SaaS) | Only if SaaS signals detected |
| documentation | Article | Single type, not HowTo |
| about | Organization, Person, AboutPage | Company + team profiles |
| solutions | SoftwareApplication (SaaS) or Service | Context-dependent |
| integrations | ItemList | List of integration items |
| customers | Organization | Case studies / testimonials |
| resources | CollectionPage | Resource library |

### Deterministic Rules (Applied to All Pages)

These rules apply regardless of page type:

| Schema Type | Rule |
|---|---|
| BreadcrumbList | Added to ALL non-home pages |
| FAQPage | Added if FAQ content detected but schema missing |
| VideoObject | Added if video is primary content |
| Review | Added if testimonial content detected |

---

## SaaS Detection

A site is classified as SaaS when 2+ of 3 content sources match SaaS indicator terms:

**Content sources:**
1. Title + meta description
2. Headings (H1–H3)
3. Paragraph text (first 500 words)

**SaaS indicator terms:** platform, saas, cloud, api, sdk, deploy, infrastructure, gpu, serverless, dashboard, cli, developer, subscription, hosted, multi-tenant

When SaaS is detected:
- Product pages use `SoftwareApplication` instead of `Product`
- Pricing pages include `SoftwareApplication` + `OfferCatalog`
- Features pages include `SoftwareApplication`
- Solutions pages use `SoftwareApplication` or `Service`

---

## 17 AEO-Relevant Schema Types

Organization, WebSite, Product, Service, Article, BlogPosting, FAQPage, BreadcrumbList, HowTo, SoftwareApplication, CollectionPage, WebApplication, OfferCatalog, VideoObject, ItemList, Review, Person, AboutPage

### Subtype Recognition

Child types map to their parent AEO-relevant type:

| Subtype | Maps To |
|---|---|
| NewsArticle | Article |
| TechArticle | Article |
| MobileApplication | SoftwareApplication |
| LocalBusiness | Organization |

---

## Multi-Page Site Analysis

- Scrape up to 10 pages per analysis
- Score each page individually (0–100 Technical Score)
- Site score = average of all marketing page scores
- Non-marketing pages excluded from average
- Page selection priority: home → pricing → features → product → solutions → about → blog → other → documentation

---

## Page Type → Fan-out Mapping

For the relationship between page types and the sub-queries AI models generate about them, refer to `query-fanout.md`.
