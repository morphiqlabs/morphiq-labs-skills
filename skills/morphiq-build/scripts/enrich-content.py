#!/usr/bin/env python3
"""enrich-content.py — Post-pipeline content enrichment.

Usage: echo '{"content": "...", "metadata": {...}}' | python3 enrich-content.py
Output: JSON with enrichment analysis and actionable items

Analyzes content that has been through the pipeline and identifies
remaining enrichment opportunities (missing stats, citations, etc.).
Claude uses this analysis to perform additional web searches and
produce the final enriched version.
"""

import json
import re
import sys


def count_statistics(content: str) -> list:
    """Find statistics with citations in the content."""
    stats = []
    # Pattern: number + context (percentages, dollar amounts, counts)
    stat_patterns = [
        r'(\d+(?:\.\d+)?%)',
        r'(\$\d+(?:\.\d+)?(?:\s*(?:billion|million|thousand|B|M|K))?)',
        r'(\d+(?:\.\d+)?x)',
    ]
    for pattern in stat_patterns:
        for match in re.finditer(pattern, content):
            # Check if it has a citation nearby (within 200 chars)
            start = max(0, match.start() - 100)
            end = min(len(content), match.end() + 100)
            context = content[start:end]
            has_citation = bool(re.search(r'\[.*?\]\(https?://.*?\)', context))
            stats.append({
                "value": match.group(1),
                "has_citation": has_citation,
                "position": match.start(),
            })
    return stats


def count_expert_quotes(content: str) -> list:
    """Find expert quotes with attribution."""
    quotes = []
    # Pattern: quoted text with attribution
    quote_patterns = [
        r'"([^"]{20,})"[^"]*?(?:—|--|said|according to)\s*([^,\n]+)',
        r'"([^"]{20,})"',
    ]
    for pattern in quote_patterns:
        for match in re.finditer(pattern, content, re.IGNORECASE):
            quotes.append({
                "text": match.group(1)[:100] + "..." if len(match.group(1)) > 100 else match.group(1),
                "has_attribution": len(match.groups()) > 1,
                "position": match.start(),
            })
    return quotes


def check_citation_format(content: str) -> list:
    """Check citation formatting (name-drop + link vs trailing parenthetical)."""
    issues = []

    # Good format: "According to [Source](url)" or "[Source](url) reports"
    good_citations = re.findall(r'(?:According to|per|from)\s*\[.*?\]\(https?://.*?\)', content, re.IGNORECASE)

    # Bad format: "(Source, 2025)" or "(source.com)"
    bad_citations = re.findall(r'\([A-Z][a-z]+(?:\s+\d{4})?\)', content)
    bad_citations += re.findall(r'\([a-z]+\.[a-z]+\)', content)

    for bad in bad_citations:
        issues.append({
            "type": "wrong_citation_format",
            "text": bad,
            "fix": "Convert to name-drop + link format: According to [Source](url)",
        })

    return issues


def check_heading_structure(content: str) -> dict:
    """Check heading hierarchy."""
    headings = re.findall(r'^(#{1,6})\s+(.+)$', content, re.MULTILINE)

    issues = []
    h1_count = sum(1 for h in headings if len(h[0]) == 1)
    h2_count = sum(1 for h in headings if len(h[0]) == 2)

    if h1_count == 0:
        issues.append("Missing H1 title")
    elif h1_count > 1:
        issues.append(f"Multiple H1 tags ({h1_count})")

    if h2_count < 5:
        issues.append(f"Only {h2_count} H2 sections (need 5–7)")

    # Check for FAQ section
    has_faq = any("faq" in h[1].lower() or "frequently" in h[1].lower() for h in headings)
    if not has_faq:
        issues.append("Missing FAQ section")

    # Check for TL;DR
    has_tldr = "tl;dr" in content.lower() or "> " in content[:500]
    if not has_tldr:
        issues.append("Missing TL;DR or summary block")

    return {
        "h1_count": h1_count,
        "h2_count": h2_count,
        "total_headings": len(headings),
        "has_faq": has_faq,
        "has_tldr": has_tldr,
        "issues": issues,
    }


def analyze_content(content: str, metadata: dict = None) -> dict:
    """Analyze content and identify enrichment opportunities."""
    metadata = metadata or {}
    word_count = len(content.split())

    statistics = count_statistics(content)
    expert_quotes = count_expert_quotes(content)
    citation_issues = check_citation_format(content)
    heading_structure = check_heading_structure(content)

    # Identify enrichment needs
    enrichment_needed = []

    uncited_stats = [s for s in statistics if not s["has_citation"]]
    if uncited_stats:
        enrichment_needed.append({
            "type": "uncited_statistics",
            "count": len(uncited_stats),
            "action": "Search for authoritative sources for uncited statistics",
        })

    cited_stats = [s for s in statistics if s["has_citation"]]
    if len(cited_stats) < 3:
        enrichment_needed.append({
            "type": "insufficient_statistics",
            "current": len(cited_stats),
            "required": 3,
            "action": "Search for additional statistics with authoritative sources",
        })

    unattributed_quotes = [q for q in expert_quotes if not q["has_attribution"]]
    if unattributed_quotes:
        enrichment_needed.append({
            "type": "unattributed_quotes",
            "count": len(unattributed_quotes),
            "action": "Add speaker name and credentials to quotes",
        })

    if len(expert_quotes) < 1:
        enrichment_needed.append({
            "type": "no_expert_quotes",
            "action": "Search for expert quotes on this topic",
        })

    if citation_issues:
        enrichment_needed.append({
            "type": "citation_format_issues",
            "count": len(citation_issues),
            "action": "Convert to name-drop + link format",
        })

    if word_count < 1200:
        enrichment_needed.append({
            "type": "below_word_count",
            "current": word_count,
            "required": 1200,
            "action": "Expand content to reach 1,200–1,600 word target",
        })

    for issue in heading_structure["issues"]:
        enrichment_needed.append({
            "type": "structure_issue",
            "detail": issue,
            "action": f"Fix: {issue}",
        })

    return {
        "word_count": word_count,
        "statistics": {
            "total": len(statistics),
            "cited": len(cited_stats),
            "uncited": len(uncited_stats),
        },
        "expert_quotes": {
            "total": len(expert_quotes),
            "attributed": len(expert_quotes) - len(unattributed_quotes),
        },
        "citation_format_issues": citation_issues,
        "heading_structure": heading_structure,
        "enrichment_needed": enrichment_needed,
        "enrichment_count": len(enrichment_needed),
        "meets_standard": len(enrichment_needed) == 0,
    }


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"Invalid JSON: {e}"}))
        sys.exit(1)

    content = data.get("content", "")
    metadata = data.get("metadata", {})

    result = analyze_content(content, metadata)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
