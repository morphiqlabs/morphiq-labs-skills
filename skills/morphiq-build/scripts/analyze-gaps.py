#!/usr/bin/env python3
"""analyze-gaps.py — Analyze content against query space and identify gaps.

Usage: echo '{"extractions": [...], "prompts": [...]}' | python3 analyze-gaps.py
Output: JSON gap analysis with typed gaps, severity, and search queries

Note: The actual gap analysis requires LLM reasoning. This script provides
the framework, classification logic, and output formatting. Claude performs
the content analysis using this structure.
"""

import json
import re
import sys

GAP_TYPES = {
    "content": {
        "description": "Unanswered questions, missing perspectives, topics not covered",
        "search_query_prefix": "",
    },
    "data": {
        "description": "Missing statistics, quantitative evidence, numerical comparisons",
        "search_query_prefix": "statistics ",
    },
    "format": {
        "description": "Content in wrong format for LLM retrieval (prose instead of tables, etc.)",
        "search_query_prefix": "",
    },
    "depth": {
        "description": "Surface-level explanations, no expert insight or specifics",
        "search_query_prefix": "expert ",
    },
    "brand_positioning": {
        "description": "No brand-specific data or competitive positioning",
        "search_query_prefix": "",
    },
    "fanout_coverage": {
        "description": "Sub-queries AI would chain but site cannot answer",
        "search_query_prefix": "",
    },
}

SEVERITY_LEVELS = ["high", "medium", "low"]

COMPARATIVE_SIGNALS = ["vs", "versus", "compared to", "best", "compare", "top", "alternative", "which"]


def detect_comparative_intent(prompts: list) -> bool:
    """Check if any tracked prompts indicate comparative intent."""
    for prompt in prompts:
        text = prompt.get("text", "").lower() if isinstance(prompt, dict) else str(prompt).lower()
        if any(signal in text for signal in COMPARATIVE_SIGNALS):
            return True
    return False


def classify_gap(gap_description: str) -> str:
    """Classify a gap description into a gap type."""
    desc_lower = gap_description.lower()

    if any(w in desc_lower for w in ["statistic", "data", "number", "metric", "percentage", "benchmark"]):
        return "data"
    if any(w in desc_lower for w in ["table", "list", "format", "faq", "structured"]):
        return "format"
    if any(w in desc_lower for w in ["surface", "generic", "depth", "expert", "detail"]):
        return "depth"
    if any(w in desc_lower for w in ["brand", "competitor", "positioning", "comparison"]):
        return "brand_positioning"
    if any(w in desc_lower for w in ["sub-query", "fanout", "sub-topic", "fan-out"]):
        return "fanout_coverage"
    return "content"


def assess_severity(gap_type: str, description: str, is_core_topic: bool = True) -> str:
    """Assess gap severity."""
    desc_lower = description.lower()

    # High severity: directly blocks answering a tracked prompt
    if any(w in desc_lower for w in ["no coverage", "completely missing", "blocks", "zero"]):
        return "high"
    if gap_type == "data" and "core claim" in desc_lower:
        return "high"
    if gap_type == "brand_positioning" and is_core_topic:
        return "high"

    # Medium: weakens the answer
    if gap_type in ("depth", "format"):
        return "medium"
    if is_core_topic:
        return "medium"

    return "low"


def generate_search_queries(gaps: list, max_queries: int = 5) -> list:
    """Generate targeted search queries from gaps, prioritized by severity."""
    # Sort by severity priority
    severity_order = {"high": 0, "medium": 1, "low": 2}
    sorted_gaps = sorted(gaps, key=lambda g: severity_order.get(g.get("severity", "low"), 2))

    queries = []
    for gap in sorted_gaps:
        if len(queries) >= max_queries:
            break
        query = gap.get("search_query", "")
        if query and query not in queries:
            queries.append(query)

    return queries


def create_gap_report(extractions: list, prompts: list, icp: dict = None) -> dict:
    """Create a gap analysis report structure.

    This creates the output format. The actual gap identification
    requires Claude's LLM reasoning over the content and prompts.
    """
    comparative = detect_comparative_intent(prompts)

    # Count content stats
    total_words = sum(e.get("word_count", 0) for e in extractions)
    total_sources = len(extractions)

    report = {
        "content_summary": {
            "total_sources": total_sources,
            "total_words": total_words,
            "has_icp": icp is not None,
        },
        "comparative_intent": comparative,
        "brand_positioning_needed": comparative,
        "gaps": [],  # To be populated by Claude's analysis
        "search_queries": [],  # Generated from gaps
        "total_gaps": 0,
    }

    return report


def format_gap(gap_type: str, description: str, severity: str,
               search_query: str = "", resolution_action: str = "") -> dict:
    """Format a single gap entry."""
    return {
        "type": gap_type,
        "description": description,
        "severity": severity,
        "search_query": search_query,
        "resolution_action": resolution_action,
    }


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"Invalid JSON input: {e}"}))
        sys.exit(1)

    extractions = data.get("extractions", [])
    prompts = data.get("prompts", [])
    icp = data.get("icp", None)

    report = create_gap_report(extractions, prompts, icp)

    # If gaps are pre-populated (from Claude's analysis), process them
    raw_gaps = data.get("gaps", [])
    for gap in raw_gaps:
        desc = gap.get("description", "")
        gap_type = gap.get("type") or classify_gap(desc)
        severity = gap.get("severity") or assess_severity(gap_type, desc)
        formatted = format_gap(
            gap_type=gap_type,
            description=desc,
            severity=severity,
            search_query=gap.get("search_query", ""),
            resolution_action=gap.get("resolution_action", ""),
        )
        report["gaps"].append(formatted)

    report["total_gaps"] = len(report["gaps"])
    report["search_queries"] = generate_search_queries(report["gaps"])

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
