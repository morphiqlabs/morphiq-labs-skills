#!/usr/bin/env python3
"""research-live.py — Structure and format live research findings.

Usage: echo '{"queries": [...], "findings": [...]}' | python3 research-live.py
Output: JSON with structured research findings for content generation

Note: Actual web searches are performed by Claude's web search tools.
This script structures the search queries, formats findings, and validates
sources for the content generation step.
"""

import json
import sys
from urllib.parse import urlparse

FINDING_TYPES = ["statistic", "expert_quote", "authoritative_source", "industry_insight"]

# Preferred source domains for authority
AUTHORITY_DOMAINS = {
    "high": [
        "gartner.com", "mckinsey.com", "forrester.com", "hbr.org",
        "nature.com", "ieee.org", "acm.org", "arxiv.org",
    ],
    "medium": [
        "techcrunch.com", "theverge.com", "reuters.com", "bloomberg.com",
        "forbes.com", "wsj.com", "nytimes.com", "wired.com",
    ],
    "low": [
        "medium.com", "dev.to", "substack.com", "reddit.com",
    ],
}


def assess_source_authority(url: str) -> str:
    """Assess the authority level of a source URL."""
    try:
        domain = urlparse(url).netloc.lower().replace("www.", "")
    except Exception:
        return "unknown"

    for level, domains in AUTHORITY_DOMAINS.items():
        if any(d in domain for d in domains):
            return level

    # .edu and .gov are high authority
    if domain.endswith(".edu") or domain.endswith(".gov"):
        return "high"

    return "medium"


def format_statistic(content: str, source_name: str, source_url: str) -> dict:
    """Format a statistic finding."""
    return {
        "type": "statistic",
        "content": content,
        "source_name": source_name,
        "source_url": source_url,
        "authority": assess_source_authority(source_url),
        "citation_format": f"According to [{source_name}]({source_url}), {content.lower()}" if not content[0].isdigit() else f"[{source_name}]({source_url}) reports that {content.lower()}",
    }


def format_expert_quote(content: str, speaker: str, credential: str, source_url: str) -> dict:
    """Format an expert quote finding."""
    return {
        "type": "expert_quote",
        "content": content,
        "speaker": speaker,
        "credential": credential,
        "source_url": source_url,
        "authority": assess_source_authority(source_url),
        "citation_format": f'"{content}" — {speaker}, {credential}',
    }


def format_source(name: str, url: str, finding_type: str) -> dict:
    """Format a source reference."""
    return {
        "name": name,
        "url": url,
        "type": finding_type,
        "authority": assess_source_authority(url),
    }


def structure_findings(queries: list, raw_findings: list) -> dict:
    """Structure raw findings into the pipeline format."""
    findings = []
    stats_count = 0
    quotes_count = 0
    sources = []

    for finding in raw_findings:
        ftype = finding.get("type", "authoritative_source")

        if ftype == "statistic":
            formatted = format_statistic(
                content=finding.get("content", ""),
                source_name=finding.get("source_name", ""),
                source_url=finding.get("source_url", ""),
            )
            stats_count += 1
        elif ftype == "expert_quote":
            formatted = format_expert_quote(
                content=finding.get("content", ""),
                speaker=finding.get("speaker", ""),
                credential=finding.get("credential", ""),
                source_url=finding.get("source_url", ""),
            )
            quotes_count += 1
        else:
            formatted = {
                "type": ftype,
                "content": finding.get("content", ""),
                "source_name": finding.get("source_name", ""),
                "source_url": finding.get("source_url", ""),
                "authority": assess_source_authority(finding.get("source_url", "")),
            }

        findings.append(formatted)

        # Track sources
        source_url = finding.get("source_url", "")
        if source_url:
            sources.append(format_source(
                name=finding.get("source_name", ""),
                url=source_url,
                finding_type=ftype,
            ))

    # Deduplicate sources
    seen_urls = set()
    unique_sources = []
    for s in sources:
        if s["url"] not in seen_urls:
            seen_urls.add(s["url"])
            unique_sources.append(s)

    return {
        "queries_executed": len(queries),
        "findings": findings,
        "total_findings": len(findings),
        "stats_found": stats_count,
        "quotes_found": quotes_count,
        "sources_found": len(unique_sources),
        "sources": unique_sources,
    }


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"Invalid JSON input: {e}"}))
        sys.exit(1)

    queries = data.get("queries", data.get("search_queries", []))
    findings = data.get("findings", [])

    result = structure_findings(queries, findings)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
