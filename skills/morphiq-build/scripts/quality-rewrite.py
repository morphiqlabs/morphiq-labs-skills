#!/usr/bin/env python3
"""quality-rewrite.py — Analyze content against Morphiq quality standards.

Usage: echo '{"content": "...", "topic": "..."}' | python3 quality-rewrite.py
Output: JSON quality assessment with pass/fail per standard and rewrite instructions

This script performs the quality CHECK. The actual rewriting is done by Claude
using these results as instructions for what needs to change.
"""

import json
import re
import sys

QUALITY_STANDARDS = {
    "word_count": {
        "min": 1200, "max": 1600,
        "description": "Content length between 1,200–1,600 words",
    },
    "h1_title": {
        "description": "Clear H1 title reflecting the topic",
    },
    "tldr": {
        "description": "TL;DR or direct-answer summary at top",
    },
    "h2_sections": {
        "min": 5, "max": 7,
        "description": "5–7 H2 sections with direct-answer openings",
    },
    "statistics": {
        "min": 3,
        "description": "Minimum 3 statistics with name-drop + link citations",
    },
    "expert_quote": {
        "min": 1,
        "description": "Minimum 1 expert quote with in-text attribution",
    },
    "faq_section": {
        "min_questions": 3, "max_questions": 5,
        "description": "FAQ with 3–5 Q&As",
    },
    "citation_format": {
        "description": "All citations use name-drop + link format",
    },
    "no_fabrication": {
        "description": "No fabricated case studies or examples",
    },
    "sources_section": {
        "description": "Sources section with all references",
    },
}


def check_word_count(content: str) -> dict:
    """Check word count requirement."""
    count = len(content.split())
    standard = QUALITY_STANDARDS["word_count"]
    passed = standard["min"] <= count <= standard["max"]
    return {
        "standard": "word_count",
        "passed": passed,
        "current": count,
        "required": f"{standard['min']}–{standard['max']}",
        "action": None if passed else (
            f"Expand content by ~{standard['min'] - count} words" if count < standard["min"]
            else f"Trim content by ~{count - standard['max']} words"
        ),
    }


def check_h1(content: str) -> dict:
    """Check H1 title."""
    h1s = re.findall(r'^#\s+(.+)$', content, re.MULTILINE)
    passed = len(h1s) == 1 and len(h1s[0]) > 10
    return {
        "standard": "h1_title",
        "passed": passed,
        "current": h1s[0] if h1s else None,
        "action": None if passed else "Add a clear, specific H1 title",
    }


def check_tldr(content: str) -> dict:
    """Check TL;DR presence."""
    has_tldr = "tl;dr" in content[:1000].lower()
    has_blockquote = bool(re.search(r'^>\s+', content[:1000], re.MULTILINE))
    passed = has_tldr or has_blockquote
    return {
        "standard": "tldr",
        "passed": passed,
        "action": None if passed else "Add TL;DR or blockquote summary after H1",
    }


def check_h2_sections(content: str) -> dict:
    """Check H2 section count."""
    h2s = re.findall(r'^##\s+(.+)$', content, re.MULTILINE)
    standard = QUALITY_STANDARDS["h2_sections"]
    passed = standard["min"] <= len(h2s) <= standard["max"]
    return {
        "standard": "h2_sections",
        "passed": passed,
        "current": len(h2s),
        "required": f"{standard['min']}–{standard['max']}",
        "sections": h2s,
        "action": None if passed else f"Adjust to {standard['min']}–{standard['max']} H2 sections",
    }


def check_statistics(content: str) -> dict:
    """Check statistics with citations."""
    # Find statistics near citations
    stat_pattern = r'\d+(?:\.\d+)?(?:%|\$|x\b)'
    citation_pattern = r'\[.*?\]\(https?://.*?\)'

    stats = list(re.finditer(stat_pattern, content))
    cited_stats = 0
    for stat in stats:
        start = max(0, stat.start() - 200)
        end = min(len(content), stat.end() + 200)
        context = content[start:end]
        if re.search(citation_pattern, context):
            cited_stats += 1

    standard = QUALITY_STANDARDS["statistics"]
    passed = cited_stats >= standard["min"]
    return {
        "standard": "statistics",
        "passed": passed,
        "current": cited_stats,
        "required": standard["min"],
        "action": None if passed else f"Add {standard['min'] - cited_stats} more cited statistics",
    }


def check_expert_quote(content: str) -> dict:
    """Check expert quote with attribution."""
    quote_pattern = r'"[^"]{20,}"[^"]*?(?:—|--|said|according to)\s*[A-Z][a-z]+'
    quotes = re.findall(quote_pattern, content)
    passed = len(quotes) >= 1
    return {
        "standard": "expert_quote",
        "passed": passed,
        "current": len(quotes),
        "required": 1,
        "action": None if passed else "Add at least 1 expert quote with speaker name and credentials",
    }


def check_faq(content: str) -> dict:
    """Check FAQ section."""
    faq_match = re.search(r'#{2,3}\s+(?:FAQ|Frequently Asked)', content, re.IGNORECASE)
    if not faq_match:
        return {
            "standard": "faq_section",
            "passed": False,
            "current": 0,
            "action": "Add FAQ section with 3–5 Q&As",
        }

    faq_content = content[faq_match.start():]
    questions = re.findall(r'#{3,4}\s+(.+\?)', faq_content)
    standard = QUALITY_STANDARDS["faq_section"]
    passed = standard["min_questions"] <= len(questions) <= standard["max_questions"]
    return {
        "standard": "faq_section",
        "passed": passed,
        "current": len(questions),
        "required": f"{standard['min_questions']}–{standard['max_questions']}",
        "action": None if passed else f"Adjust FAQ to {standard['min_questions']}–{standard['max_questions']} questions",
    }


def check_citation_format(content: str) -> dict:
    """Check citation format (name-drop + link, not parenthetical)."""
    # Bad patterns
    bad_citations = re.findall(r'\([A-Z][a-z]+,?\s*\d{4}\)', content)
    passed = len(bad_citations) == 0
    return {
        "standard": "citation_format",
        "passed": passed,
        "issues": bad_citations[:5],
        "action": None if passed else f"Convert {len(bad_citations)} parenthetical citations to name-drop + link format",
    }


def check_sources_section(content: str) -> dict:
    """Check for sources section."""
    has_sources = bool(re.search(r'#{2,3}\s+(?:Sources|References)', content, re.IGNORECASE))
    return {
        "standard": "sources_section",
        "passed": has_sources,
        "action": None if has_sources else "Add Sources section listing all referenced URLs",
    }


def assess_quality(content: str, topic: str = "") -> dict:
    """Run all quality checks."""
    checks = [
        check_word_count(content),
        check_h1(content),
        check_tldr(content),
        check_h2_sections(content),
        check_statistics(content),
        check_expert_quote(content),
        check_faq(content),
        check_citation_format(content),
        check_sources_section(content),
    ]

    passed = sum(1 for c in checks if c["passed"])
    total = len(checks)
    failed_checks = [c for c in checks if not c["passed"]]

    return {
        "topic": topic,
        "overall_pass": passed == total,
        "score": f"{passed}/{total}",
        "passed_count": passed,
        "failed_count": total - passed,
        "checks": checks,
        "rewrite_instructions": [c["action"] for c in failed_checks if c.get("action")],
    }


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"Invalid JSON: {e}"}))
        sys.exit(1)

    content = data.get("content", "")
    topic = data.get("topic", "")

    result = assess_quality(content, topic)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
