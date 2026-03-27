#!/usr/bin/env python3
"""inject-schema.py — Generate JSON-LD schema markup for a page.

Usage: echo '{"url": "...", "page_type": "...", "title": "...", ...}' | python3 inject-schema.py
Output: JSON with generated schema blocks and skip reasons

Follows the "no placeholders" principle: if data cannot be extracted,
the schema type is skipped with a logged reason.
"""

import json
import sys
from urllib.parse import urlparse

# Page type → expected schemas
PAGE_TYPE_SCHEMAS = {
    "home": ["Organization", "WebSite"],
    "blog": ["BlogPosting", "BreadcrumbList"],
    "product": ["SoftwareApplication", "BreadcrumbList"],  # SaaS default
    "pricing": ["SoftwareApplication", "BreadcrumbList"],
    "features": ["SoftwareApplication", "BreadcrumbList"],
    "documentation": ["Article", "BreadcrumbList"],
    "about": ["Organization", "AboutPage", "BreadcrumbList"],
    "solutions": ["Service", "BreadcrumbList"],
    "integrations": ["ItemList", "BreadcrumbList"],
    "customers": ["Organization", "BreadcrumbList"],
    "resources": ["CollectionPage", "BreadcrumbList"],
    "use-cases": ["Article", "BreadcrumbList"],
}

# Types that are always skipped
ALWAYS_SKIPPED = {
    "VideoObject": "Cannot extract thumbnailUrl, uploadDate, duration reliably",
    "Review": "Cannot extract author, itemReviewed, reviewRating reliably",
    "OfferCatalog": "Cannot extract real pricing tiers from HTML",
    "Person": "Cannot extract author data reliably",
}


def generate_breadcrumb(url: str) -> dict:
    """Generate BreadcrumbList from URL path."""
    parsed = urlparse(url)
    segments = [s for s in parsed.path.strip("/").split("/") if s]

    if not segments:
        return None

    items = [{"@type": "ListItem", "position": 1, "name": "Home", "item": f"{parsed.scheme}://{parsed.netloc}/"}]

    for i, segment in enumerate(segments):
        name = segment.replace("-", " ").replace("_", " ").title()
        path = "/".join(segments[:i+1])
        items.append({
            "@type": "ListItem",
            "position": i + 2,
            "name": name,
            "item": f"{parsed.scheme}://{parsed.netloc}/{path}",
        })

    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": items,
    }


def generate_organization(data: dict) -> dict:
    """Generate Organization schema."""
    name = data.get("title", "")
    url = data.get("url", "")
    if not name:
        return None
    return {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": name.split(" - ")[0].split(" | ")[0].strip(),
        "url": url,
    }


def generate_website(data: dict) -> dict:
    """Generate WebSite schema."""
    name = data.get("title", "")
    url = data.get("url", "")
    if not name:
        return None
    return {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": name.split(" - ")[0].split(" | ")[0].strip(),
        "url": f"{urlparse(url).scheme}://{urlparse(url).netloc}",
    }


def generate_article(data: dict, schema_type: str = "Article") -> dict:
    """Generate Article or BlogPosting schema."""
    headline = data.get("h1", data.get("title", ""))
    if not headline:
        return None
    schema = {
        "@context": "https://schema.org",
        "@type": schema_type,
        "headline": headline,
    }
    if data.get("publish_date"):
        schema["datePublished"] = data["publish_date"]
    if data.get("meta_description"):
        schema["description"] = data["meta_description"]
    if data.get("author_name"):
        schema["author"] = {"@type": "Person", "name": data["author_name"]}
    return schema


def generate_software_application(data: dict) -> dict:
    """Generate SoftwareApplication schema."""
    name = data.get("h1", data.get("title", ""))
    if not name:
        return None
    return {
        "@context": "https://schema.org",
        "@type": "SoftwareApplication",
        "name": name.split(" - ")[0].split(" | ")[0].strip(),
        "applicationCategory": "BusinessApplication",
        "operatingSystem": "Web",
    }


def generate_faq_page(data: dict) -> dict:
    """Generate FAQPage schema from detected FAQs."""
    faqs = data.get("faqs", [])
    if not faqs:
        return None
    main_entity = []
    for faq in faqs:
        q = faq.get("question", "")
        a = faq.get("answer", "")
        if q and a:
            main_entity.append({
                "@type": "Question",
                "name": q,
                "acceptedAnswer": {"@type": "Answer", "text": a},
            })
    if not main_entity:
        return None
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": main_entity,
    }


def generate_howto(data: dict) -> dict:
    """Generate HowTo schema from headings."""
    headings = data.get("headings", [])
    sub_headings = [h for h in headings if h.get("level", 0) in (2, 3)]
    if len(sub_headings) < 2:
        return None
    name = data.get("h1", data.get("title", ""))
    if not name:
        return None
    return {
        "@context": "https://schema.org",
        "@type": "HowTo",
        "name": name,
        "step": [
            {"@type": "HowToStep", "name": h["text"]}
            for h in sub_headings
        ],
    }


# Schema type → generator function
GENERATORS = {
    "Organization": generate_organization,
    "WebSite": generate_website,
    "Article": lambda d: generate_article(d, "Article"),
    "BlogPosting": lambda d: generate_article(d, "BlogPosting"),
    "SoftwareApplication": generate_software_application,
    "Service": generate_software_application,  # Similar structure
    "FAQPage": generate_faq_page,
    "HowTo": generate_howto,
    "AboutPage": generate_organization,  # Shares structure
    "CollectionPage": generate_organization,
    "ItemList": generate_organization,
}


def inject_schemas(data: dict) -> dict:
    """Generate all applicable schemas for a page."""
    url = data.get("url", "")
    page_type = data.get("page_type", "other")
    is_saas = data.get("is_saas", False)

    expected = list(PAGE_TYPE_SCHEMAS.get(page_type, ["BreadcrumbList"]))

    # Swap Product for SoftwareApplication if not SaaS
    if not is_saas and "SoftwareApplication" in expected:
        expected = ["Product" if s == "SoftwareApplication" else s for s in expected]

    # Add FAQPage if FAQ content detected
    if data.get("faqs") and "FAQPage" not in expected:
        expected.append("FAQPage")

    generated = []
    skipped = []

    for schema_type in expected:
        # Check always-skipped types
        if schema_type in ALWAYS_SKIPPED:
            skipped.append({"type": schema_type, "reason": ALWAYS_SKIPPED[schema_type]})
            continue

        # Handle BreadcrumbList specially
        if schema_type == "BreadcrumbList":
            bc = generate_breadcrumb(url)
            if bc:
                generated.append({"type": "BreadcrumbList", "json_ld": bc})
            continue

        # Use generator
        generator = GENERATORS.get(schema_type)
        if generator:
            result = generator(data)
            if result:
                generated.append({"type": schema_type, "json_ld": result})
            else:
                skipped.append({"type": schema_type, "reason": "Insufficient data to populate required fields"})
        else:
            skipped.append({"type": schema_type, "reason": f"No generator for type {schema_type}"})

    return {
        "url": url,
        "page_type": page_type,
        "schemas_generated": generated,
        "schemas_skipped": skipped,
        "total_generated": len(generated),
        "total_skipped": len(skipped),
    }


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"Invalid JSON: {e}"}))
        sys.exit(1)

    result = inject_schemas(data)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
