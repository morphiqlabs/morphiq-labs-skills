#!/usr/bin/env python3
"""generate-llms-txt.py — Generate an optimised llms.txt for any domain.

Pipeline (7 steps):
  1. URL Discovery    — robots.txt, sitemap, homepage anchor crawl
  2. Page Scoring     — rank pages by type/signal relevance
  3. Deep Scrape      — fetch top-N pages, extract visible text
  4. LLM Synthesis    — summarise scraped content into llms.txt sections
  5. Assembly         — stitch sections into spec-compliant llms.txt
  6. Validation       — size budget, link-check, schema conformance
  7. Output           — write to stdout or file

This module currently implements Step 1 (URL Discovery).

Usage: python3 generate-llms-txt.py <domain>
"""

import re
import sys
import urllib.error
import urllib.request
from html.parser import HTMLParser
from typing import List, Optional, Tuple
from urllib.parse import urljoin, urlparse

try:
    import xml.etree.ElementTree as ET
except ImportError:
    ET = None

# ── Constants ────────────────────────────────────────────────────────────────

MAX_CONTEXT_CHARS = 24000
DEEP_SCRAPE_LIMIT = 4
DEEP_CHAR_LIMIT = 3000
SHALLOW_CHAR_LIMIT = 900
SIZE_BUDGET_KB = 100
MAX_SITEMAP_URLS = 80
LLM_MAX_TOKENS = 4096

DOCS_PATH_PATTERNS = [
    "/docs",
    "/documentation",
    "/help",
    "/guide",
    "/api",
    "/reference",
    "/developer",
]

USER_AGENT = "Mozilla/5.0 (compatible; MorphiqBuild/1.0)"

# ── URL Discovery helpers ────────────────────────────────────────────────────


def normalize_domain(domain: str) -> str:
    """Strip protocol and trailing slash from domain."""
    domain = re.sub(r"^https?://", "", domain)
    return domain.rstrip("/")


class AnchorExtractor(HTMLParser):
    """Extract href values from <a> tags."""

    def __init__(self):
        super().__init__()
        self.hrefs = []  # type: List[str]

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            for name, value in attrs:
                if name == "href" and value:
                    self.hrefs.append(value)


def extract_anchor_urls(html: str, base_url: str) -> List[str]:
    """Extract all absolute HTTP(S) URLs from <a> tags in *html*.

    - Resolves relative URLs against *base_url*.
    - Skips mailto:, tel:, and fragment-only links.
    - Returns a deduplicated list preserving first-seen order.
    """
    if not html:
        return []

    parser = AnchorExtractor()
    parser.feed(html)

    seen = set()   # type: set
    urls = []      # type: List[str]

    for href in parser.hrefs:
        href = href.strip()
        if not href:
            continue
        # Skip non-http schemes and bare fragments
        lower = href.lower()
        if lower.startswith("mailto:") or lower.startswith("tel:"):
            continue
        if href.startswith("#"):
            continue

        absolute = urljoin(base_url, href)
        # Only keep http/https URLs
        if not absolute.lower().startswith(("http://", "https://")):
            continue
        if absolute not in seen:
            seen.add(absolute)
            urls.append(absolute)

    return urls


def parse_robots_sitemaps(robots_txt: str) -> List[str]:
    """Extract Sitemap: directive URLs from robots.txt content."""
    if not robots_txt:
        return []
    sitemaps = []  # type: List[str]
    for line in robots_txt.splitlines():
        line = line.strip()
        if line.lower().startswith("sitemap:"):
            url = line.split(":", 1)[1].strip()
            if url:
                sitemaps.append(url)
    return sitemaps


def extract_urls_from_sitemap(xml_content: str) -> List[str]:
    """Parse sitemap XML using ElementTree, regex fallback on parse errors."""
    if not xml_content:
        return []

    urls = []  # type: List[str]

    if ET:
        try:
            root = ET.fromstring(xml_content)
            # Detect namespace
            ns = ""
            if root.tag.startswith("{"):
                ns = root.tag.split("}")[0] + "}"
            for loc in root.iter(f"{ns}loc"):
                if loc.text:
                    urls.append(loc.text.strip())
            return urls
        except ET.ParseError:
            pass  # fall through to regex

    # Regex fallback (also used when ET is None)
    urls = re.findall(r"<loc>\s*([^<]+?)\s*</loc>", xml_content)
    return urls


def find_docs_base(urls: List[str], domain: str) -> Optional[str]:
    """Return the docs-base URL from *urls* by matching DOCS_PATH_PATTERNS.

    Prefers shorter paths (closer to root) when multiple matches exist.
    Returns None if nothing matches.
    """
    matches = []  # type: List[str]
    for url in urls:
        parsed = urlparse(url)
        path = parsed.path.lower()
        for pattern in DOCS_PATH_PATTERNS:
            if pattern in path:
                matches.append(url)
                break

    if not matches:
        return None

    # Prefer shortest path (closest to docs root)
    matches.sort(key=lambda u: len(urlparse(u).path))
    return matches[0]


def fetch_url(url: str, timeout: int = 15) -> Tuple[int, str]:
    """Fetch *url* with urllib. Return (status_code, body_text).

    Returns (0, "") on any network or HTTP error.
    """
    headers = {"User-Agent": USER_AGENT}
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return (resp.status, body)
    except (urllib.error.URLError, urllib.error.HTTPError, OSError, ValueError):
        return (0, "")


# ── URL Classification & Scoring ────────────────────────────────────────────

CLASSIFICATION_PATTERNS = {
    "pricing": ["/pricing", "/plans"],
    "product": ["/product", "/features", "/platform"],
    "about": ["/about", "/team", "/company"],
    "docs": ["/docs", "/documentation", "/help", "/guide", "/api", "/reference"],
    "blog": ["/blog", "/posts", "/articles"],
    "solutions": ["/solutions", "/use-cases", "/use-case"],
    "case-study": ["/case-stud", "/customers", "/success-stories"],
    "comparison": ["/vs", "/compare", "/alternative"],
    "careers": ["/careers", "/jobs"],
    "security": ["/security", "/trust", "/compliance"],
    "legal": ["/privacy", "/terms", "/legal", "/cookie"],
    "changelog": ["/changelog", "/updates", "/release-notes", "/whats-new"],
}

CANONICALITY_SCORES = {
    "home": 100,
    "pricing": 90,
    "product": 85,
    "docs": 80,
    "about": 70,
    "solutions": 65,
    "security": 60,
    "legal": 55,
    "changelog": 50,
    "case-study": 45,
    "comparison": 40,
    "blog": 30,
    "careers": 20,
    "other": 10,
}


def classify_url(url: str, domain: str) -> str:
    """Classify a URL by its path pattern.

    Returns one of: home, pricing, product, about, docs, blog, solutions,
    case-study, comparison, careers, security, legal, changelog, other.
    """
    parsed = urlparse(url)
    path = parsed.path.lower().rstrip("/")

    # Home page: empty path or just "/"
    if not path:
        return "home"

    for category, patterns in CLASSIFICATION_PATTERNS.items():
        for pattern in patterns:
            if pattern in path:
                return category

    return "other"


def score_url(url: str, domain: str, nav_urls=None) -> int:
    """Score a URL for ranking. Higher = more important.

    - Base score from CANONICALITY_SCORES.
    - +20 if url is in nav_urls.
    - -5 per path segment beyond depth 2.
    - +10 if path has <= 1 segments (canonical bonus).
    """
    category = classify_url(url, domain)
    score = CANONICALITY_SCORES.get(category, 10)

    parsed = urlparse(url)
    path = parsed.path.strip("/")
    segments = [s for s in path.split("/") if s] if path else []
    num_segments = len(segments)

    # Canonical bonus: short paths
    if num_segments <= 1:
        score += 10

    # Depth penalty: segments beyond 2
    if num_segments > 2:
        score -= 5 * (num_segments - 2)

    # Nav URL boost
    if nav_urls and url in nav_urls:
        score += 20

    return score


# ── HTML Content Extraction ─────────────────────────────────────────────────

SKIP_TAGS = frozenset({"script", "style", "noscript", "svg", "head"})


class TextExtractor(HTMLParser):
    """Extract visible text from HTML, skipping script/style/noscript/svg/head."""

    def __init__(self):
        super().__init__()
        self.pieces = []       # type: List[str]
        self._skip_depth = 0   # nesting depth inside skip tags

    def handle_starttag(self, tag, attrs):
        if tag.lower() in SKIP_TAGS:
            self._skip_depth += 1

    def handle_endtag(self, tag):
        if tag.lower() in SKIP_TAGS:
            self._skip_depth = max(0, self._skip_depth - 1)

    def handle_data(self, data):
        if self._skip_depth == 0:
            self.pieces.append(data)

    def get_text(self) -> str:
        raw = " ".join(self.pieces)
        # Collapse whitespace
        return " ".join(raw.split())


def extract_page_text(html: str, max_chars: Optional[int] = None) -> str:
    """Extract visible text from HTML, skipping non-visible elements.

    Returns collapsed whitespace text. Truncates at *max_chars* if set.
    """
    if not html:
        return ""

    extractor = TextExtractor()
    try:
        extractor.feed(html)
    except Exception:
        pass  # graceful on malformed HTML

    text = extractor.get_text()

    if max_chars is not None:
        text = text[:max_chars]

    return text


def extract_headings(html: str) -> List[str]:
    """Extract h1-h3 heading text from HTML via regex.

    Strips inner HTML tags from heading content.
    """
    if not html:
        return []

    # Match <h1>...<h3> tags, including attributes, across lines
    pattern = re.compile(r"<h([1-3])(?:\s[^>]*)?>(.+?)</h\1>", re.DOTALL | re.IGNORECASE)
    headings = []  # type: List[str]

    for match in pattern.finditer(html):
        inner = match.group(2)
        # Strip inner HTML tags
        text = re.sub(r"<[^>]+>", "", inner)
        # Collapse whitespace
        text = " ".join(text.split())
        if text:
            headings.append(text)

    return headings


# ── Main ─────────────────────────────────────────────────────────────────────


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 generate-llms-txt.py <domain>", file=sys.stderr)
        sys.exit(1)

    domain = normalize_domain(sys.argv[1])
    base = f"https://{domain}"

    # 1a. Fetch robots.txt for sitemap directives
    _, robots_body = fetch_url(f"{base}/robots.txt")
    sitemap_urls = parse_robots_sitemaps(robots_body)

    # 1b. Default sitemap fallback
    if not sitemap_urls:
        sitemap_urls = [f"{base}/sitemap.xml"]

    # 1c. Fetch and parse sitemaps
    discovered = []  # type: List[str]
    for smap_url in sitemap_urls:
        _, smap_body = fetch_url(smap_url)
        discovered.extend(extract_urls_from_sitemap(smap_body))

    # 1d. Fetch homepage and extract anchor URLs
    _, homepage_html = fetch_url(base)
    anchor_urls = extract_anchor_urls(homepage_html, base)

    # Merge and deduplicate, cap at MAX_SITEMAP_URLS
    seen = set()     # type: set
    all_urls = []    # type: List[str]
    for url in discovered + anchor_urls:
        if url not in seen:
            seen.add(url)
            all_urls.append(url)
    all_urls = all_urls[:MAX_SITEMAP_URLS]

    # 1e. Find docs base
    docs_base = find_docs_base(all_urls, domain)

    # Output discovery results (later steps will consume this)
    print(f"Domain: {domain}")
    print(f"URLs discovered: {len(all_urls)}")
    if docs_base:
        print(f"Docs base: {docs_base}")
    for url in all_urls:
        print(f"  {url}")


if __name__ == "__main__":
    main()
