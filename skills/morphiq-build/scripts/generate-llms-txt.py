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

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from typing import Dict, List, Optional, Tuple
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


# ── Evidence Patterns ──────────────────────────────────────────────────────

DATE_PATTERN = re.compile(
    r"\b(?:"
    r"\d{4}[-/]\d{1,2}[-/]\d{1,2}"
    r"|(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}"
    r"|(?:Founded|Established|Since)\s+(?:in\s+)?\d{4}"
    r")\b",
    re.IGNORECASE,
)

PRICE_PATTERN = re.compile(
    r"\$\d[\d,]*(?:\.\d{2})?(?:/(?:mo|month|yr|year|user|seat))?"
    r"|free\s+(?:plan|tier|to start)",
    re.IGNORECASE,
)

FACT_PATTERN = re.compile(
    r"\b\d[\d,]*\+?\s*(?:customers|users|companies|businesses|employees|countries|integrations|clients)"
    r"|\b\d[\d,]*%\s+\w+",
    re.IGNORECASE,
)


# ── Context Collection Orchestrator ────────────────────────────────────────


def build_evidence(scraped_pages, allowed_urls):
    # type: (List[Dict], List[str]) -> Dict
    """Build grounding evidence from scraped content.

    Returns dict with: allowed_urls (capped at MAX_SITEMAP_URLS),
    date_literals, price_literals, headings (capped at 50),
    facts (capped at 20), key_terms (capped at 30).
    """
    date_literals = []   # type: List[str]
    price_literals = []  # type: List[str]
    facts = []           # type: List[str]
    all_headings = []    # type: List[str]

    seen_dates = set()   # type: set
    seen_prices = set()  # type: set
    seen_facts = set()   # type: set

    for page in scraped_pages:
        text = page.get("text", "")
        headings = page.get("headings", [])

        for m in DATE_PATTERN.finditer(text):
            val = m.group()
            if val not in seen_dates:
                seen_dates.add(val)
                date_literals.append(val)

        for m in PRICE_PATTERN.finditer(text):
            val = m.group()
            if val not in seen_prices:
                seen_prices.add(val)
                price_literals.append(val)

        for m in FACT_PATTERN.finditer(text):
            val = m.group()
            if val not in seen_facts:
                seen_facts.add(val)
                facts.append(val)

        all_headings.extend(headings)

    # Deduplicate headings preserving order
    seen_h = set()  # type: set
    unique_headings = []  # type: List[str]
    for h in all_headings:
        if h not in seen_h:
            seen_h.add(h)
            unique_headings.append(h)

    # Key terms: headings with 2-5 words
    key_terms = []  # type: List[str]
    seen_terms = set()  # type: set
    for h in unique_headings:
        words = h.split()
        if 2 <= len(words) <= 5 and h not in seen_terms:
            seen_terms.add(h)
            key_terms.append(h)

    return {
        "allowed_urls": allowed_urls[:MAX_SITEMAP_URLS],
        "date_literals": date_literals,
        "price_literals": price_literals,
        "headings": unique_headings[:50],
        "facts": facts[:20],
        "key_terms": key_terms[:30],
    }


# ── Prompt Construction ───────────────────────────────────────────────────────


def build_system_prompt():
    # type: () -> str
    """Build the system prompt that instructs the LLM to generate llms.txt.

    Returns a deterministic string containing the full contract:
    identity block, inputs description, data-source rules, selection ranking,
    writing style, 14-section order, validation pass, and output format.
    """
    return """\
<identity>
You are an autonomous backend agent for generating llms.txt files.
Your tone is neutral, factual, and deterministic.
You produce structured, spec-compliant llms.txt content from scraped website data.
You never invent information. Every claim must be traceable to the provided content.
</identity>

## Inputs

You receive the following runtime inputs:
- root_url — the canonical root URL of the target website
- docs_base — the documentation root URL (may be null)
- brand_name — the company or product name
- tagline — the brand tagline or one-line description
- locales — list of locale codes (default: ["en"])
- size_budgets — maximum output size in KB
- run_date — ISO-8601 date of this generation run

## Data Sources

ONLY use the provided scraped content. Do NOT hallucinate URLs, features, pricing,
or any claims not present in the source material. Every statement must be traceable
to a specific scraped page or evidence item.

## Selection Ranking

When choosing which pages and facts to include, apply this priority order:
1. Canonicality — root, /pricing, /product, /docs rank highest
2. Nav prominence — pages linked from the main navigation
3. Product/docs coverage — feature pages and documentation
4. Policies — privacy, terms, security pages
5. Pricing/about/blog — lower priority supplementary content

## Writing Style

- Neutral and factual — no marketing fluff, no superlatives
- Compact — prefer bullet points over paragraphs
- Specific numbers — use exact figures from source material
- Absolute HTTPS URLs only — never use relative paths or http://

## Section Order

Generate exactly these 14 sections in this order:

a. **H1** — `# {brand_name}` followed by a blockquote definition of the company/product
b. **Overview** — 2-4 bullets summarising what the product/company does
c. **Who We Serve** — 3-6 bullets identifying the target audience
d. **Products / Capabilities** — name, one-line purpose, and link for each product
e. **Solutions / Use Cases** — key use cases or solution areas
f. **Key Resources** — docs, API reference, SDKs, changelog, and other developer resources
g. **FAQs** — 3-6 Q/A pairs using **Q:**/**A:** format, each ending with [Source](url)
h. **Security & Compliance** — certifications, compliance standards, trust page links
i. **Pricing & Plans** — plan names, prices, and feature highlights
j. **Policies** — links to privacy policy, terms of service, cookie policy, etc.
k. **Research / Reports / Blog** — notable posts, reports, or whitepapers
l. **Sitemap** — 8-15 high-signal pages as a markdown link list
m. **Citation Guidance** — instructions for LLMs on how to cite this source
n. **Last Updated** — ISO-8601 date of this generation run

## Validation Pass

Before finalising output, run a validation pass:
- Verify every URL is absolute HTTPS
- Verify no claims lack a source in the provided evidence
- Verify the section count is exactly 14
- Verify FAQs use **Q:**/**A:** format with [Source](url) citations
- Verify Sitemap contains 8-15 entries
- Verify output fits within the size budget

## Output Format

Return exactly one fenced code block labelled ```llms.txt containing the
complete llms.txt content. Do not include any text outside the fenced block.
"""


def build_user_prompt(context, brand_info):
    # type: (Dict, Dict) -> str
    """Build the user prompt from collected context and brand info.

    Arguments:
        context: dict from collect_llms_context with keys root_url, domain,
                 docs_base, ranked_urls, scraped_pages, evidence.
        brand_info: dict with keys name, tagline, and optionally description,
                    products, audience, industry.

    Returns a string containing runtime inputs, canonical source URLs,
    brand information, live page content, grounding evidence, and
    hard requirements.
    """
    run_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    root_url = context.get("root_url", "")
    docs_base = context.get("docs_base") or "N/A"
    brand_name = brand_info.get("name", "")
    tagline = brand_info.get("tagline", "")

    # ── Runtime inputs block ──────────────────────────────────────────
    parts = []
    parts.append("Generate llms.txt for this website. Follow the system prompt contract exactly.")
    parts.append("")
    parts.append("<runtime_inputs>")
    parts.append(f"root_url: {root_url}")
    parts.append(f"docs_base: {docs_base}")
    parts.append(f"brand_name: {brand_name}")
    parts.append(f"tagline: {tagline}")
    parts.append("locales: [\"en\"]")
    parts.append(f"size_budgets: {SIZE_BUDGET_KB} KB")
    parts.append(f"run_date: {run_date}")
    parts.append("</runtime_inputs>")

    # ── Canonical source URLs ─────────────────────────────────────────
    evidence = context.get("evidence", {})
    allowed_urls = evidence.get("allowed_urls", [])

    parts.append("")
    parts.append("<canonical_source_urls>")
    for url in allowed_urls:
        parts.append(f"- {url}")
    parts.append("</canonical_source_urls>")

    # ── Brand section ─────────────────────────────────────────────────
    parts.append("")
    parts.append("## Brand Information")
    parts.append(f"- Company: {brand_name}")
    parts.append(f"- Website: {root_url}")
    parts.append(f"- Tagline: {tagline}")
    if brand_info.get("description"):
        parts.append(f"- Description: {brand_info['description']}")
    if brand_info.get("products"):
        parts.append(f"- Products: {brand_info['products']}")
    if brand_info.get("audience"):
        parts.append(f"- Audience: {brand_info['audience']}")
    if brand_info.get("industry"):
        parts.append(f"- Industry: {brand_info['industry']}")

    # ── Live page content ─────────────────────────────────────────────
    parts.append("")
    parts.append("## Live Page Content")
    scraped_pages = context.get("scraped_pages", [])
    for page in scraped_pages:
        url = page.get("url", "")
        tier = page.get("tier", "shallow")
        headings = page.get("headings", [])
        text = page.get("text", "")

        char_limit = DEEP_CHAR_LIMIT if tier == "deep" else SHALLOW_CHAR_LIMIT
        truncated_text = text[:char_limit]

        parts.append("")
        parts.append(f"### {url}")
        parts.append(f"Tier: {tier}")
        if headings:
            parts.append(f"Headings: {', '.join(headings)}")
        parts.append(f"Content: {truncated_text}")

    # ── Grounding evidence ────────────────────────────────────────────
    parts.append("")
    parts.append("## Grounding Evidence")
    parts.append(json.dumps(evidence, indent=2))

    # ── Hard requirements ─────────────────────────────────────────────
    parts.append("")
    parts.append("## Hard Requirements")
    parts.append("- Output MUST be exactly one fenced code block labelled ```llms.txt")
    parts.append("- All links MUST be absolute HTTPS URLs")
    parts.append("- All content MUST be scoped to the provided domain — do not reference external sites")
    parts.append("- FAQs MUST use **Q:**/**A:** format with [Source](url) citations")
    parts.append("- Sitemap section MUST contain 8-15 high-signal page links")
    parts.append(f"- Total output MUST fit within {SIZE_BUDGET_KB} KB")

    return "\n".join(parts)


# ── LLM Call with Multi-Provider Fallback ────────────────────────────────────


def _call_anthropic(system_prompt, user_prompt, max_tokens):
    # type: (str, str, int) -> str
    """Call Anthropic Claude API. Tries claude-sonnet-4-5-20250514 then claude-sonnet-4-20250514."""
    import anthropic

    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))
    models = ["claude-sonnet-4-5-20250514", "claude-sonnet-4-20250514"]
    last_err = None

    for model in models:
        try:
            print(f"[llms-txt] Calling Anthropic model={model}", file=sys.stderr)
            response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
            text = "".join(
                block.text for block in response.content if hasattr(block, "text")
            )
            print(f"[llms-txt] Anthropic OK ({len(text)} chars)", file=sys.stderr)
            return text
        except Exception as exc:
            last_err = exc
            print(f"[llms-txt] Anthropic {model} failed: {exc}", file=sys.stderr)

    raise last_err


def _call_openai(system_prompt, user_prompt, max_tokens):
    # type: (str, str, int) -> str
    """Call OpenAI GPT-4o API."""
    from openai import OpenAI

    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))
    model = "gpt-4o"

    print(f"[llms-txt] Calling OpenAI model={model}", file=sys.stderr)
    response = client.chat.completions.create(
        model=model,
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    text = response.choices[0].message.content
    print(f"[llms-txt] OpenAI OK ({len(text)} chars)", file=sys.stderr)
    return text


def _call_gemini(system_prompt, user_prompt, max_tokens):
    # type: (str, str, int) -> str
    """Call Google Gemini API."""
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY", ""))
    model = "gemini-2.5-flash"
    content = system_prompt + "\n\n" + user_prompt

    print(f"[llms-txt] Calling Gemini model={model}", file=sys.stderr)
    response = client.models.generate_content(
        model=model,
        contents=content,
        config=types.GenerateContentConfig(max_output_tokens=max_tokens),
    )
    text = response.text
    print(f"[llms-txt] Gemini OK ({len(text)} chars)", file=sys.stderr)
    return text


def call_llm(system_prompt, user_prompt, max_tokens=LLM_MAX_TOKENS):
    # type: (str, str, int) -> Optional[str]
    """Call LLM with Anthropic -> OpenAI -> Gemini fallback chain.

    Returns raw text on first success, or None if all providers fail.
    """
    providers = [
        ("anthropic", _call_anthropic),
        ("openai", _call_openai),
        ("gemini", _call_gemini),
    ]

    for name, fn in providers:
        try:
            return fn(system_prompt, user_prompt, max_tokens)
        except Exception as exc:
            print(f"[llms-txt] Provider {name} failed: {exc}", file=sys.stderr)

    return None


# ── Output Validation ──────────────────────────────────────────────────────

REQUIRED_SECTIONS = {
    "overview": r"##\s+Overview",
    "who we serve": r"##\s+Who\s+[Ww]e\s+[Ss]erve",
    "products": r"##\s+Products",
    "solutions": r"##\s+Solutions",
    "key resources": r"##\s+Key\s+Resources",
    "faqs": r"##\s+FAQs?",
    "security": r"##\s+Security",
    "pricing": r"##\s+Pricing",
    "policies": r"##\s+Policies",
}

FAQ_PATTERN = re.compile(
    r"\*\*Q:\*\*.*?\*\*A:\*\*.*?\[Source\]\(https?://[^\)]+\)", re.DOTALL
)
URL_PATTERN = re.compile(r"https?://[^\s\)\]>\"]+")
SITEMAP_SECTION = re.compile(
    r"##\s+Sitemap.*?\n((?:- https?://[^\n]+\n?)+)", re.DOTALL
)


def extract_fenced_block(raw_text):
    # type: (str) -> Optional[str]
    """Extract content from a ```llms.txt fenced code block.

    Returns the stripped content string, or None if not exactly one
    matching block or if the content is empty after stripping.
    """
    matches = re.findall(r"```llms\.txt\n(.*?)```", raw_text, re.DOTALL)
    if len(matches) != 1:
        return None
    content = matches[0].strip()
    if not content:
        return None
    return content


def validate_llms_txt(content, root_url, docs_base):
    # type: (str, str, Optional[str]) -> List[str]
    """Validate llms.txt content against the spec.

    Returns a list of error strings (empty list means valid).
    """
    errors = []  # type: List[str]

    # a. Size check
    size_kb = len(content.encode("utf-8")) / 1024
    if size_kb > SIZE_BUDGET_KB:
        errors.append(
            f"Size {size_kb:.1f} KB exceeds budget of {SIZE_BUDGET_KB} KB"
        )

    # b. Required sections
    for section_name, pattern in REQUIRED_SECTIONS.items():
        if not re.search(pattern, content, re.IGNORECASE):
            errors.append(f"Missing required section: {section_name}")

    # c. FAQ format: need >= 3 Q/A pairs with Source links
    faq_matches = FAQ_PATTERN.findall(content)
    if len(faq_matches) < 3:
        errors.append(
            f"FAQ section has {len(faq_matches)} Q/A pairs, need at least 3"
        )

    # d. URL scope: all URLs must match root_url or docs_base domain
    root_domain = urlparse(root_url).netloc
    allowed_domains = {root_domain}
    if docs_base:
        docs_domain = urlparse(docs_base).netloc
        allowed_domains.add(docs_domain)

    for m in URL_PATTERN.finditer(content):
        url = m.group()
        domain = urlparse(url).netloc
        if domain not in allowed_domains:
            errors.append(
                f"URL out of scope: {url} (domain {domain} not in {allowed_domains})"
            )
            break  # report first offender only

    # e. Sitemap count: 8-15 URLs
    sitemap_match = SITEMAP_SECTION.search(content)
    if sitemap_match:
        sitemap_text = sitemap_match.group(1)
        sitemap_urls = URL_PATTERN.findall(sitemap_text)
        if len(sitemap_urls) < 8 or len(sitemap_urls) > 15:
            errors.append(
                f"Sitemap has {len(sitemap_urls)} URLs, need 8-15"
            )
    else:
        errors.append("Missing Sitemap section with URL list")

    # f. Duplicate URLs: any URL appearing >3 times
    from collections import Counter

    all_urls = URL_PATTERN.findall(content)
    url_counts = Counter(all_urls)
    for url, count in url_counts.items():
        if count > 3:
            errors.append(
                f"Duplicate URL appears {count} times: {url}"
            )
            break  # report first offender only

    return errors


# ── Context Collection Orchestrator ────────────────────────────────────────


def collect_llms_context(root_url):
    # type: (str) -> Dict
    """Main enrichment orchestrator — discover, score, scrape, evidence.

    Returns dict with: root_url, domain, docs_base, all_urls,
    ranked_urls, scraped_pages, evidence, homepage_html.
    """
    parsed_root = urlparse(root_url)
    domain = parsed_root.netloc
    base_scheme = parsed_root.scheme or "https"
    base = f"{base_scheme}://{domain}"

    print(f"[llms-txt] Fetching homepage: {base}", file=sys.stderr)

    # ── 1. Homepage ────────────────────────────────────────────────────
    _, homepage_html = fetch_url(base)
    homepage_nav_urls = extract_anchor_urls(homepage_html, base)

    # ── 2. Robots.txt → sitemaps ───────────────────────────────────────
    print(f"[llms-txt] Fetching robots.txt", file=sys.stderr)
    _, robots_body = fetch_url(f"{base}/robots.txt")
    sitemap_locs = parse_robots_sitemaps(robots_body)

    if not sitemap_locs:
        sitemap_locs = [f"{base}/sitemap.xml"]

    # ── 3. Crawl sitemaps ──────────────────────────────────────────────
    sitemap_urls = []  # type: List[str]
    for smap_url in sitemap_locs:
        print(f"[llms-txt] Fetching sitemap: {smap_url}", file=sys.stderr)
        _, smap_body = fetch_url(smap_url)
        sitemap_urls.extend(extract_urls_from_sitemap(smap_body))

    # ── 4. Merge, scope to domain, deduplicate ────────────────────────
    seen = set()       # type: set
    all_urls = []      # type: List[str]
    for url in sitemap_urls + homepage_nav_urls:
        p = urlparse(url)
        if p.netloc != domain:
            continue
        if url not in seen:
            seen.add(url)
            all_urls.append(url)

    # ── 5. Docs base + docs nav links ─────────────────────────────────
    docs_base = find_docs_base(all_urls, domain)
    if docs_base:
        print(f"[llms-txt] Docs base: {docs_base}", file=sys.stderr)
        _, docs_html = fetch_url(docs_base)
        docs_nav_urls = extract_anchor_urls(docs_html, docs_base)
        for url in docs_nav_urls:
            p = urlparse(url)
            if p.netloc == domain and url not in seen:
                seen.add(url)
                all_urls.append(url)

    # ── 6. Score and rank ──────────────────────────────────────────────
    nav_set = set(homepage_nav_urls)
    ranked_urls = sorted(
        all_urls,
        key=lambda u: score_url(u, domain, nav_urls=nav_set),
        reverse=True,
    )

    print(f"[llms-txt] {len(ranked_urls)} URLs ranked, starting scrape", file=sys.stderr)

    # ── 7. Two-tier scraping ───────────────────────────────────────────
    scraped_pages = []  # type: List[Dict]
    total_chars = 0

    # Homepage always first, deep tier
    homepage_text = extract_page_text(homepage_html, max_chars=DEEP_CHAR_LIMIT)
    homepage_headings = extract_headings(homepage_html)
    scraped_pages.append({
        "url": base,
        "text": homepage_text,
        "headings": homepage_headings,
        "tier": "deep",
    })
    total_chars += len(homepage_text)

    # Filter out homepage from ranked list to avoid double-scraping
    homepage_variants = {base, base + "/"}
    remaining = [u for u in ranked_urls if u not in homepage_variants]

    deep_count = 0
    for url in remaining:
        if total_chars >= MAX_CONTEXT_CHARS:
            break

        if deep_count < DEEP_SCRAPE_LIMIT:
            tier = "deep"
            char_limit = DEEP_CHAR_LIMIT
            deep_count += 1
        else:
            tier = "shallow"
            char_limit = SHALLOW_CHAR_LIMIT

        status, html = fetch_url(url)
        if status == 0 or not html:
            continue

        text = extract_page_text(html, max_chars=char_limit)
        headings = extract_headings(html)

        scraped_pages.append({
            "url": url,
            "text": text,
            "headings": headings,
            "tier": tier,
        })
        total_chars += len(text)

    print(f"[llms-txt] Scraped {len(scraped_pages)} pages ({total_chars} chars)", file=sys.stderr)

    # ── 8. Build evidence ──────────────────────────────────────────────
    evidence = build_evidence(scraped_pages, all_urls)

    return {
        "root_url": root_url,
        "domain": domain,
        "docs_base": docs_base,
        "all_urls": all_urls,
        "ranked_urls": ranked_urls,
        "scraped_pages": scraped_pages,
        "evidence": evidence,
        "homepage_html": homepage_html,
    }


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
