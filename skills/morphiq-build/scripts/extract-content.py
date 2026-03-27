#!/usr/bin/env python3
"""extract-content.py — Process fetched HTML into structured content extractions.

Usage: echo '{"pages": [...]}' | python3 extract-content.py
Input: JSON with pages array (each having url, html fields)
Output: JSON with structured content extractions

Note: Actual web fetching is done by Claude's web tools. This script
processes the fetched HTML into the structured format the pipeline needs.
"""

import json
import re
import sys
from html.parser import HTMLParser


class TextExtractor(HTMLParser):
    """Extract text content from HTML, stripping tags."""

    def __init__(self):
        super().__init__()
        self.text_parts = []
        self.in_script = False
        self.in_style = False

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript"):
            self.in_script = True

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript"):
            self.in_script = False

    def handle_data(self, data):
        if not self.in_script and not self.in_style:
            text = data.strip()
            if text:
                self.text_parts.append(text)

    def get_text(self) -> str:
        return " ".join(self.text_parts)


def extract_title(html: str) -> str:
    """Extract page title."""
    match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    return match.group(1).strip() if match else ""


def extract_headings(html: str) -> list:
    """Extract heading hierarchy."""
    headings = []
    for match in re.finditer(r"<(h[1-6])[^>]*>(.*?)</\1>", html, re.IGNORECASE | re.DOTALL):
        level = int(match.group(1)[1])
        text = re.sub(r"<[^>]+>", "", match.group(2)).strip()
        if text:
            headings.append({"level": level, "text": text})
    return headings


def extract_links(html: str) -> list:
    """Extract outbound links."""
    links = set()
    for match in re.finditer(r'<a[^>]+href=["\']?(https?://[^"\'>\s]+)', html, re.IGNORECASE):
        links.add(match.group(1))
    return sorted(links)


def extract_publish_date(html: str) -> str:
    """Try to extract publish date from meta tags or schema."""
    patterns = [
        r'property=["\']article:published_time["\'][^>]*content=["\']([^"\']+)',
        r'name=["\']date["\'][^>]*content=["\']([^"\']+)',
        r'"datePublished"\s*:\s*"([^"]+)"',
        r'datetime=["\'](\d{4}-\d{2}-\d{2})',
    ]
    for pattern in patterns:
        match = re.search(pattern, html, re.IGNORECASE)
        if match:
            return match.group(1)
    return ""


def html_to_markdown(html: str) -> str:
    """Simple HTML to markdown conversion for content body."""
    text = html

    # Remove script/style
    text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)

    # Convert headings
    for i in range(1, 7):
        text = re.sub(rf"<h{i}[^>]*>(.*?)</h{i}>", rf"{'#' * i} \1\n\n", text, flags=re.DOTALL | re.IGNORECASE)

    # Convert paragraphs
    text = re.sub(r"<p[^>]*>(.*?)</p>", r"\1\n\n", text, flags=re.DOTALL | re.IGNORECASE)

    # Convert lists
    text = re.sub(r"<li[^>]*>(.*?)</li>", r"- \1\n", text, flags=re.DOTALL | re.IGNORECASE)

    # Convert bold/strong
    text = re.sub(r"<(strong|b)[^>]*>(.*?)</\1>", r"**\2**", text, flags=re.DOTALL | re.IGNORECASE)

    # Convert links
    text = re.sub(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', r"[\2](\1)", text, flags=re.DOTALL | re.IGNORECASE)

    # Strip remaining tags
    text = re.sub(r"<[^>]+>", "", text)

    # Clean up whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()

    return text


def process_page(page: dict) -> dict:
    """Process a single page into a structured extraction."""
    url = page.get("url", "")
    html = page.get("html", "")

    if not html:
        return {
            "url": url,
            "extraction_status": "failed",
            "error": "No HTML content provided",
        }

    # Extract text for word count
    extractor = TextExtractor()
    try:
        extractor.feed(html)
    except Exception:
        pass
    plain_text = extractor.get_text()

    return {
        "url": url,
        "title": extract_title(html),
        "content_markdown": html_to_markdown(html),
        "word_count": len(plain_text.split()),
        "publish_date": extract_publish_date(html),
        "headings": extract_headings(html),
        "outbound_links": extract_links(html),
        "extraction_status": "success",
    }


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"Invalid JSON input: {e}"}))
        sys.exit(1)

    pages = data.get("pages", [data] if "url" in data else [])

    extractions = [process_page(page) for page in pages]
    successful = sum(1 for e in extractions if e["extraction_status"] == "success")

    result = {
        "extractions": extractions,
        "successful": successful,
        "failed": len(extractions) - successful,
    }

    print(json.dumps(result, indent=2))

    if successful == 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
