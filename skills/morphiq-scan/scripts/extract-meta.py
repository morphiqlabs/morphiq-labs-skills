#!/usr/bin/env python3
"""extract-meta.py — Extract metadata from a web page for Technical Score computation.

Usage: python3 extract-meta.py <url>
Output: JSON with all fields required by score-page.py

Outputs: url, title, meta_description, canonical, og_title, og_description,
twitter_card, twitter_title, jsonld_count, jsonld_blocks (parsed), schema_types,
expected_schemas, present_schemas, is_marketing_page, faq_count, word_count,
paragraph_count
"""

import json
import re
import sys
import urllib.request
import urllib.error
from html.parser import HTMLParser
from urllib.parse import urlparse


# Page type detection patterns
PAGE_TYPE_PATTERNS = {
    "home": [r"^/$", r"^/index\.html?$"],
    "pricing": [r"/pricing", r"/plans"],
    "product": [r"/product", r"/features", r"/platform"],
    "about": [r"/about", r"/team", r"/company"],
    "blog": [r"/blog/", r"/posts/", r"/articles/"],
    "docs": [r"/docs", r"/documentation", r"/help", r"/guide"],
    "contact": [r"/contact"],
    "careers": [r"/careers", r"/jobs"],
    "legal": [r"/privacy", r"/terms", r"/legal", r"/cookie"],
    "login": [r"/login", r"/signin", r"/sign-in"],
    "signup": [r"/signup", r"/sign-up", r"/register"],
    "demo": [r"/demo", r"/request-demo"],
    "case-study": [r"/case-stud", r"/customers", r"/success-stories"],
    "comparison": [r"/vs", r"/compare", r"/alternative"],
    "solutions": [r"/solutions", r"/use-cases"],
    "changelog": [r"/changelog", r"/releases", r"/whats-new"],
}

# Marketing page types (non-marketing pages exclude FAQ from scoring)
MARKETING_TYPES = {
    "home", "pricing", "product", "about", "blog", "case-study",
    "comparison", "solutions", "landing",
}

# Expected schemas per page type
PAGE_TYPE_SCHEMAS = {
    "home": ["Organization", "WebSite"],
    "pricing": ["SoftwareApplication", "Organization"],
    "product": ["SoftwareApplication", "Organization", "BreadcrumbList"],
    "about": ["Organization", "AboutPage"],
    "blog": ["BlogPosting", "BreadcrumbList"],
    "docs": ["Article", "BreadcrumbList"],
    "case-study": ["Article", "Organization"],
    "comparison": ["Article", "BreadcrumbList"],
    "solutions": ["Article", "BreadcrumbList"],
    "contact": [],
    "careers": [],
    "legal": [],
    "login": [],
    "signup": [],
    "demo": [],
    "changelog": [],
}

# AEO-relevant schema types
AEO_RELEVANT_TYPES = {
    "Organization", "WebSite", "Product", "Service", "Article", "BlogPosting",
    "FAQPage", "BreadcrumbList", "HowTo", "SoftwareApplication", "CollectionPage",
    "WebApplication", "OfferCatalog", "VideoObject", "ItemList", "Review",
    "Person", "AboutPage",
}


class MetaExtractor(HTMLParser):
    """HTML parser that extracts metadata, JSON-LD blocks, and structural info."""

    def __init__(self):
        super().__init__()
        self.title = ""
        self.meta_description = ""
        self.canonical = ""
        self.og_title = ""
        self.og_description = ""
        self.twitter_card = ""
        self.twitter_title = ""
        self.jsonld_blocks = []
        self.faq_count = 0
        self.word_count = 0
        self.paragraph_count = 0
        self.heading_counts = {"h1": 0, "h2": 0, "h3": 0}

        # Internal parsing state
        self._in_title = False
        self._in_jsonld = False
        self._in_body = False
        self._in_p = False
        self._in_details = False
        self._title_text = []
        self._jsonld_text = []
        self._body_text = []
        self._p_depth = 0
        self._faq_schema_found = False
        self._details_count = 0
        self._accordion_count = 0

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        tag_lower = tag.lower()

        if tag_lower == "title":
            self._in_title = True
            self._title_text = []

        elif tag_lower == "meta":
            name = attrs_dict.get("name", "").lower()
            prop = attrs_dict.get("property", "").lower()
            content = attrs_dict.get("content", "")

            if name == "description":
                self.meta_description = content
            elif prop == "og:title":
                self.og_title = content
            elif prop == "og:description":
                self.og_description = content
            elif name == "twitter:card":
                self.twitter_card = content
            elif name == "twitter:title":
                self.twitter_title = content

        elif tag_lower == "link":
            rel = attrs_dict.get("rel", "").lower()
            if rel == "canonical":
                self.canonical = attrs_dict.get("href", "")

        elif tag_lower == "script":
            script_type = attrs_dict.get("type", "").lower()
            if script_type == "application/ld+json":
                self._in_jsonld = True
                self._jsonld_text = []

        elif tag_lower == "body":
            self._in_body = True

        elif tag_lower == "p" and self._in_body:
            self.paragraph_count += 1
            self._in_p = True

        elif tag_lower in ("h1", "h2", "h3") and self._in_body:
            if tag_lower in self.heading_counts:
                self.heading_counts[tag_lower] += 1

        elif tag_lower == "details":
            self._details_count += 1

        # Detect accordion/FAQ patterns from class names
        css_class = attrs_dict.get("class", "").lower()
        if any(kw in css_class for kw in ["accordion", "faq-item", "faq__item", "faq-section"]):
            self._accordion_count += 1

    def handle_endtag(self, tag):
        tag_lower = tag.lower()

        if tag_lower == "title":
            self._in_title = False
            self.title = "".join(self._title_text).strip()

        elif tag_lower == "script" and self._in_jsonld:
            self._in_jsonld = False
            raw = "".join(self._jsonld_text).strip()
            if raw:
                try:
                    parsed = json.loads(raw)
                    self.jsonld_blocks.append(parsed)
                except json.JSONDecodeError:
                    pass

        elif tag_lower == "p":
            self._in_p = False

    def handle_data(self, data):
        if self._in_title:
            self._title_text.append(data)
        elif self._in_jsonld:
            self._jsonld_text.append(data)

        if self._in_body:
            self._body_text.append(data)

    def finalize(self):
        """Compute derived fields after parsing completes."""
        # Word count from body text
        body = " ".join(self._body_text)
        words = re.findall(r"[a-zA-Z]+", body)
        self.word_count = len(words)

        # FAQ count from multiple detection methods
        # Method 1: FAQPage schema
        faq_from_schema = 0
        for block in self.jsonld_blocks:
            faq_from_schema += self._count_faq_in_schema(block)

        # Method 2: details/summary elements
        # Method 3: accordion patterns
        self.faq_count = max(faq_from_schema, self._details_count, self._accordion_count)

    def _count_faq_in_schema(self, obj):
        """Count FAQ questions in a JSON-LD block."""
        if isinstance(obj, dict):
            if obj.get("@type") == "FAQPage":
                self._faq_schema_found = True
                entities = obj.get("mainEntity", [])
                if isinstance(entities, list):
                    return len(entities)
                return 1
            # Check nested @graph
            graph = obj.get("@graph", [])
            if isinstance(graph, list):
                return sum(self._count_faq_in_schema(item) for item in graph)
        elif isinstance(obj, list):
            return sum(self._count_faq_in_schema(item) for item in obj)
        return 0


def detect_page_type(url: str) -> str:
    """Detect page type from URL patterns."""
    parsed = urlparse(url)
    path = parsed.path.rstrip("/")

    if not path or path == "/":
        return "home"

    path_lower = path.lower()
    for page_type, patterns in PAGE_TYPE_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, path_lower):
                return page_type

    return "other"


def get_schema_types(jsonld_blocks: list) -> list:
    """Extract all @type values from JSON-LD blocks."""
    types = set()

    def extract_types(obj):
        if isinstance(obj, dict):
            t = obj.get("@type")
            if isinstance(t, str):
                types.add(t)
            elif isinstance(t, list):
                types.update(t)
            # Check @graph
            for item in obj.get("@graph", []):
                extract_types(item)
        elif isinstance(obj, list):
            for item in obj:
                extract_types(item)

    for block in jsonld_blocks:
        extract_types(block)

    return sorted(types)


def fetch_url(url: str) -> str:
    """Fetch URL content with proper headers."""
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; MorphiqScan/1.0)",
        "Accept": "text/html,application/xhtml+xml",
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            return response.read().decode(charset, errors="replace")
    except (urllib.error.URLError, urllib.error.HTTPError, OSError) as e:
        raise RuntimeError(f"Failed to fetch URL: {e}")


def extract_metadata(url: str) -> dict:
    """Extract all metadata from a URL for Technical Score computation."""
    html = fetch_url(url)

    parser = MetaExtractor()
    parser.feed(html)
    parser.finalize()

    page_type = detect_page_type(url)
    is_marketing = page_type in MARKETING_TYPES
    schema_types = get_schema_types(parser.jsonld_blocks)
    expected_schemas = PAGE_TYPE_SCHEMAS.get(page_type, [])

    # Determine which expected schemas are present
    present_schemas = [s for s in expected_schemas if s in schema_types]

    # Always add BreadcrumbList and FAQPage to expected if relevant
    if page_type != "home" and "BreadcrumbList" not in expected_schemas:
        expected_schemas = list(expected_schemas)  # copy
    if parser.faq_count > 0 and "FAQPage" not in expected_schemas:
        expected_schemas = list(expected_schemas) + ["FAQPage"]
        if "FAQPage" in schema_types:
            present_schemas = list(present_schemas) + ["FAQPage"]

    return {
        "url": url,
        "title": parser.title,
        "meta_description": parser.meta_description,
        "canonical": parser.canonical,
        "og_title": parser.og_title,
        "og_description": parser.og_description,
        "twitter_card": parser.twitter_card,
        "twitter_title": parser.twitter_title,
        "jsonld_count": len(parser.jsonld_blocks),
        "jsonld_blocks": parser.jsonld_blocks,
        "schema_types": schema_types,
        "expected_schemas": expected_schemas,
        "present_schemas": present_schemas,
        "is_marketing_page": is_marketing,
        "page_type": page_type,
        "faq_count": parser.faq_count,
        "word_count": parser.word_count,
        "paragraph_count": parser.paragraph_count,
        "heading_counts": parser.heading_counts,
    }


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: python3 extract-meta.py <url>"}))
        sys.exit(1)

    url = sys.argv[1]

    try:
        result = extract_metadata(url)
        print(json.dumps(result, indent=2))
    except RuntimeError as e:
        print(json.dumps({"error": str(e), "url": url}))
        sys.exit(1)


if __name__ == "__main__":
    main()
