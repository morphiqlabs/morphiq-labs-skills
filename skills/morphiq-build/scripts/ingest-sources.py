#!/usr/bin/env python3
"""ingest-sources.py — Validate, filter, and deduplicate source URLs.

Usage: python3 ingest-sources.py --urls "url1,url2,url3" [--max 10]
   or: echo '{"urls": [...]}' | python3 ingest-sources.py
Output: JSON with validated sources and rejected entries
"""

import json
import sys
import argparse
from urllib.parse import urlparse

BLOCKED_DOMAINS = {
    "example.com", "localhost", "127.0.0.1",
    "bit.ly", "tinyurl.com", "t.co",  # URL shorteners
}

ALLOWED_PROTOCOLS = {"http", "https"}
MAX_SOURCES = 10


def validate_url(url: str) -> dict:
    """Validate a single URL."""
    url = url.strip()
    if not url:
        return {"url": url, "valid": False, "reason": "Empty URL"}

    try:
        parsed = urlparse(url)
    except Exception:
        return {"url": url, "valid": False, "reason": "Malformed URL"}

    if parsed.scheme not in ALLOWED_PROTOCOLS:
        return {"url": url, "valid": False, "reason": f"Invalid protocol — only http/https accepted (got {parsed.scheme or 'none'})"}

    if not parsed.netloc:
        return {"url": url, "valid": False, "reason": "No domain found"}

    domain = parsed.netloc.lower().split(":")[0]  # Strip port
    if domain in BLOCKED_DOMAINS:
        return {"url": url, "valid": False, "reason": f"Blocked domain: {domain}"}

    return {"url": url, "valid": True, "domain": domain, "type": "url", "status": "valid"}


def deduplicate(sources: list) -> list:
    """Remove duplicate URLs (normalize before comparing)."""
    seen = set()
    unique = []
    for source in sources:
        normalized = source["url"].rstrip("/").lower()
        if normalized not in seen:
            seen.add(normalized)
            unique.append(source)
    return unique


def ingest(urls: list, max_sources: int = MAX_SOURCES) -> dict:
    """Full ingestion pipeline: validate, filter, deduplicate, cap."""
    validated = [validate_url(url) for url in urls]

    valid = [s for s in validated if s.get("valid")]
    rejected = [{"url": s["url"], "reason": s["reason"]} for s in validated if not s.get("valid")]

    # Deduplicate
    unique = deduplicate(valid)
    dup_count = len(valid) - len(unique)

    # Cap at max
    capped = unique[:max_sources]
    over_cap = len(unique) - len(capped)

    sources = [{"url": s["url"], "type": s["type"], "status": s["status"]} for s in capped]

    return {
        "sources": sources,
        "rejected": rejected,
        "total_input": len(urls),
        "total_valid": len(sources),
        "total_rejected": len(rejected),
        "duplicates_removed": dup_count,
        "over_cap_removed": over_cap,
    }


def main():
    parser = argparse.ArgumentParser(description="Validate and filter source URLs")
    parser.add_argument("--urls", default="", help="Comma-separated URLs")
    parser.add_argument("--max", type=int, default=MAX_SOURCES, help="Max sources")
    args = parser.parse_args()

    if args.urls:
        urls = [u.strip() for u in args.urls.split(",") if u.strip()]
    else:
        try:
            data = json.load(sys.stdin)
            urls = data.get("urls", data) if isinstance(data, dict) else data
        except json.JSONDecodeError:
            urls = [line.strip() for line in sys.stdin if line.strip()]

    result = ingest(urls, args.max)
    print(json.dumps(result, indent=2))

    if result["total_valid"] == 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
