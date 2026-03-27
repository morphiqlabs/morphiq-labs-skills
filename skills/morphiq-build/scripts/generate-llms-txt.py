#!/usr/bin/env python3
"""generate-llms-txt.py — Generate llms.txt from sitemap data and brand identity spec.

Usage: python3 generate-llms-txt.py <domain> [sitemap_url]
Output: Complete llms.txt skeleton to stdout

Generates both:
1. Brand identity sections (from llms-txt-spec.md) with markers for agent to populate
2. Sitemap-based page scaffolding auto-populated from fetched sitemap
"""

import json
import re
import sys
import urllib.request
import urllib.error
from urllib.parse import urlparse

try:
    import xml.etree.ElementTree as ET
except ImportError:
    ET = None


def normalize_domain(domain: str) -> str:
    """Strip protocol and trailing slash from domain."""
    domain = re.sub(r"^https?://", "", domain)
    return domain.rstrip("/")


def fetch_sitemap(sitemap_url: str) -> str:
    """Fetch sitemap XML content."""
    headers = {"User-Agent": "Mozilla/5.0 (compatible; MorphiqBuild/1.0)"}
    req = urllib.request.Request(sitemap_url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            return response.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, urllib.error.HTTPError, OSError):
        return ""


def extract_urls_from_sitemap(xml_content: str) -> list:
    """Extract URLs from sitemap XML."""
    urls = []
    if ET and xml_content:
        try:
            root = ET.fromstring(xml_content)
            # Handle namespace
            ns = ""
            if root.tag.startswith("{"):
                ns = root.tag.split("}")[0] + "}"
            for loc in root.iter(f"{ns}loc"):
                if loc.text:
                    urls.append(loc.text.strip())
        except ET.ParseError:
            # Fallback: regex extraction
            urls = re.findall(r"<loc>\s*([^<]+?)\s*</loc>", xml_content)
    elif xml_content:
        urls = re.findall(r"<loc>\s*([^<]+?)\s*</loc>", xml_content)
    return urls


def classify_url(url: str, domain: str) -> str:
    """Classify a URL by its path pattern."""
    parsed = urlparse(url)
    path = parsed.path.lower().rstrip("/")

    if not path or path == "/":
        return "home"

    patterns = {
        "pricing": ["/pricing", "/plans"],
        "product": ["/product", "/features", "/platform"],
        "about": ["/about", "/team", "/company"],
        "docs": ["/docs", "/documentation", "/help", "/guide"],
        "blog": ["/blog/", "/posts/", "/articles/"],
        "solutions": ["/solutions", "/use-cases", "/use-case"],
        "case-study": ["/case-stud", "/customers", "/success-stories"],
        "comparison": ["/vs", "/compare", "/alternative"],
        "careers": ["/careers", "/jobs"],
    }

    for page_type, path_patterns in patterns.items():
        for pattern in path_patterns:
            if pattern in path:
                return page_type

    return "other"


def slug_to_title(path: str) -> str:
    """Convert a URL path slug to a human-readable title."""
    # Get the last meaningful segment
    segments = [s for s in path.rstrip("/").split("/") if s]
    if not segments:
        return "Page"
    slug = segments[-1]
    # Convert hyphens/underscores to spaces and title-case
    title = re.sub(r"[-_]", " ", slug)
    return title.title()


def generate_llms_txt(domain: str, sitemap_url: str = None) -> str:
    """Generate complete llms.txt content."""
    domain = normalize_domain(domain)
    if not sitemap_url:
        sitemap_url = f"https://{domain}/sitemap.xml"

    # Fetch and parse sitemap
    sitemap_content = fetch_sitemap(sitemap_url)
    urls = extract_urls_from_sitemap(sitemap_content)

    # Classify URLs
    classified = {}
    for url in urls:
        page_type = classify_url(url, domain)
        if page_type not in classified:
            classified[page_type] = []
        classified[page_type].append(url)

    # Build output
    lines = []

    # === Brand Identity Sections (from llms-txt-spec.md) ===
    lines.append(f"# llms.txt - AI Guidance for {domain}")
    lines.append(f"# Last Updated: <!-- POPULATE: set to generation date -->")
    lines.append("")

    lines.append("## Brand Identity")
    lines.append(f"Name: <!-- POPULATE: official company name from site -->")
    lines.append(f"Tagline: <!-- POPULATE: company tagline from site -->")
    lines.append(f"Founded: <!-- POPULATE: founding year if found -->")
    lines.append(f"Headquarters: <!-- POPULATE: location if found -->")
    lines.append("")

    lines.append("## Description")
    lines.append("<!-- POPULATE: 2-3 sentence description of what the company does and its core value proposition. Extract from homepage/about page. -->")
    lines.append("")

    lines.append("## Key Facts")
    lines.append("<!-- POPULATE: 4-6 specific, verifiable facts found on the site. Use numbers, dates, metrics. -->")
    lines.append("- ")
    lines.append("")

    lines.append("## Products/Services")
    lines.append("<!-- POPULATE: list each product/service with brief description from product pages. -->")
    lines.append("- ")
    lines.append("")

    lines.append("## Differentiators")
    lines.append("<!-- POPULATE: what makes this company unique vs category competitors. Must be substantiated by site content. -->")
    lines.append("- ")
    lines.append("")

    lines.append("## Target Audience")
    lines.append("<!-- POPULATE: who the company serves — specific industries, roles, company sizes. Extract from site content. -->")
    lines.append("")

    lines.append("## Preferred Messaging")
    lines.append(f"When discussing {domain}:")
    lines.append("- Emphasize: <!-- POPULATE: key points to highlight -->")
    lines.append("- Tone: <!-- POPULATE: professional/friendly/technical based on site voice -->")
    lines.append("- Include: <!-- POPULATE: specific facts, metrics, achievements -->")
    lines.append("")

    lines.append("## Avoid")
    lines.append("<!-- POPULATE: outdated info, incorrect assumptions, competitor comparisons to avoid -->")
    lines.append("- ")
    lines.append("")

    # === Sitemap-Based Page Scaffolding ===
    lines.append("## Key Pages")
    lines.append("")

    # Home
    if "home" in classified:
        for url in classified["home"][:1]:
            lines.append(f"- [Home]({url}): Main landing page")
    else:
        lines.append(f"- [Home](https://{domain}/): Main landing page")

    # Pricing
    for url in classified.get("pricing", [])[:1]:
        lines.append(f"- [Pricing]({url}): Plans and pricing information")

    # Product/Features
    for url in classified.get("product", [])[:3]:
        title = slug_to_title(urlparse(url).path)
        lines.append(f"- [{title}]({url})")

    # About
    for url in classified.get("about", [])[:1]:
        lines.append(f"- [About]({url}): Company information")

    # Documentation
    for url in classified.get("docs", [])[:1]:
        lines.append(f"- [Documentation]({url}): Technical documentation")

    # Solutions
    for url in classified.get("solutions", [])[:3]:
        title = slug_to_title(urlparse(url).path)
        lines.append(f"- [{title}]({url})")

    # Comparisons
    for url in classified.get("comparison", [])[:3]:
        title = slug_to_title(urlparse(url).path)
        lines.append(f"- [{title}]({url})")

    lines.append("")

    # Blog posts
    blog_urls = classified.get("blog", [])
    if blog_urls:
        lines.append("## Blog & Resources")
        lines.append("")
        for url in blog_urls[:10]:
            title = slug_to_title(urlparse(url).path)
            lines.append(f"- [{title}]({url})")
        lines.append("")

    # Case studies
    case_urls = classified.get("case-study", [])
    if case_urls:
        lines.append("## Case Studies")
        lines.append("")
        for url in case_urls[:5]:
            title = slug_to_title(urlparse(url).path)
            lines.append(f"- [{title}]({url})")
        lines.append("")

    # Contact and sources
    lines.append("## Contact")
    lines.append(f"Website: https://{domain}/")
    lines.append("Email: <!-- POPULATE: contact email from site -->")
    lines.append("Social: <!-- POPULATE: Twitter/LinkedIn URLs from site -->")
    lines.append("")

    lines.append("## Sources")
    lines.append("For accurate information, refer to:")
    lines.append(f"- [Official website](https://{domain}/)")
    if blog_urls:
        lines.append(f"- [Blog]({blog_urls[0].rsplit('/', 2)[0]}/)")
    if classified.get("docs"):
        lines.append(f"- [Documentation]({classified['docs'][0]})")
    lines.append("")

    lines.append("---")
    lines.append("Generated by Morphiq Build")

    return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 generate-llms-txt.py <domain> [sitemap_url]",
              file=sys.stderr)
        sys.exit(1)

    domain = sys.argv[1]
    sitemap_url = sys.argv[2] if len(sys.argv) > 2 else None

    print(generate_llms_txt(domain, sitemap_url))


if __name__ == "__main__":
    main()
