#!/usr/bin/env python3
"""create-from-prompt.py — Generate content structure from a user prompt.

Usage: python3 create-from-prompt.py --topic "topic" [--brand "brand"] [--icp "icp"]
Output: JSON content structure with sections, requirements, and metadata template

Note: Actual content generation is done by Claude using this structure
as a blueprint. This script creates the scaffold that Claude fills in.
"""

import argparse
import json
import re
import sys

COMPARATIVE_SIGNALS = ["vs", "versus", "compared to", "best", "compare", "top", "alternative", "which"]

CONTENT_REQUIREMENTS = {
    "word_count": {"min": 1200, "max": 1600},
    "h2_sections": {"min": 5, "max": 7},
    "faq_count": {"min": 3, "max": 5},
    "statistics_min": 3,
    "expert_quotes_min": 1,
}


def detect_content_type(topic: str) -> str:
    """Detect the content type from the topic."""
    topic_lower = topic.lower()

    if any(w in topic_lower for w in ["how to", "guide", "tutorial", "step"]):
        return "howto"
    if any(w in topic_lower for w in COMPARATIVE_SIGNALS):
        return "comparison"
    if any(w in topic_lower for w in ["what is", "explain", "definition"]):
        return "explainer"
    if any(w in topic_lower for w in ["review", "opinion"]):
        return "review"
    return "article"


def detect_comparative_intent(topic: str) -> bool:
    """Check if topic has comparative intent."""
    return any(signal in topic.lower() for signal in COMPARATIVE_SIGNALS)


def generate_section_outline(topic: str, content_type: str, comparative: bool, brand: str = "") -> list:
    """Generate a section outline based on content type."""
    sections = []

    # Always start with intro
    sections.append({
        "type": "intro",
        "heading_level": 2,
        "suggested_heading": f"Introduction",
        "requirements": ["Direct answer in first paragraph", "Context and scope"],
    })

    if content_type == "comparison":
        sections.extend([
            {"type": "overview", "heading_level": 2, "suggested_heading": "Quick Comparison Overview", "requirements": ["Comparison table", "Key differentiators"]},
            {"type": "entity_analysis", "heading_level": 2, "suggested_heading": f"{brand} — Features & Strengths" if brand else "Option A Analysis", "requirements": ["Feature breakdown", "Pricing if available", "Best for use case"]},
            {"type": "entity_analysis", "heading_level": 2, "suggested_heading": "Competitor Analysis", "requirements": ["Same structure as above per competitor"]},
            {"type": "use_cases", "heading_level": 2, "suggested_heading": "Best For: Use Case Breakdown", "requirements": ["Specific scenarios", "Recommendation per scenario"]},
        ])
    elif content_type == "howto":
        sections.extend([
            {"type": "prerequisites", "heading_level": 2, "suggested_heading": "Before You Start", "requirements": ["Prerequisites list", "Required tools"]},
            {"type": "steps", "heading_level": 2, "suggested_heading": "Step-by-Step Process", "requirements": ["Numbered steps", "Each step self-contained"]},
            {"type": "tips", "heading_level": 2, "suggested_heading": "Best Practices & Tips", "requirements": ["Expert insights", "Common pitfalls"]},
        ])
    else:
        sections.extend([
            {"type": "core_topic", "heading_level": 2, "suggested_heading": "Core Concepts", "requirements": ["Direct answer opening", "Statistics with citations"]},
            {"type": "deep_dive", "heading_level": 2, "suggested_heading": "Deep Dive", "requirements": ["Expert quotes", "Real examples"]},
            {"type": "practical", "heading_level": 2, "suggested_heading": "Practical Application", "requirements": ["Actionable steps", "Tool recommendations"]},
            {"type": "trends", "heading_level": 2, "suggested_heading": "Current Landscape & Trends", "requirements": ["2026 data", "Industry direction"]},
        ])

    # Always end with conclusion + FAQ
    sections.append({
        "type": "conclusion", "heading_level": 2, "suggested_heading": "Bottom Line",
        "requirements": ["Clear recommendation", "Summary of key points"],
    })
    sections.append({
        "type": "faq", "heading_level": 2, "suggested_heading": "Frequently Asked Questions",
        "requirements": [f"{CONTENT_REQUIREMENTS['faq_count']['min']}–{CONTENT_REQUIREMENTS['faq_count']['max']} Q&As as H3/H4"],
    })

    return sections


def create_content_scaffold(topic: str, brand: str = "", icp: str = "",
                           source_urls: list = None) -> dict:
    """Create the full content scaffold."""
    content_type = detect_content_type(topic)
    comparative = detect_comparative_intent(topic)
    sections = generate_section_outline(topic, content_type, comparative, brand)

    scaffold = {
        "topic": topic,
        "content_type": content_type,
        "comparative_intent": comparative,
        "brand": brand,
        "icp": icp,
        "source_urls": source_urls or [],
        "requirements": {
            "word_count": CONTENT_REQUIREMENTS["word_count"],
            "structure": {
                "h1_title": True,
                "tldr": True,
                "author_byline": True,
                "h2_sections": CONTENT_REQUIREMENTS["h2_sections"],
                "comparison_table": comparative,
                "faq_section": True,
                "sources_section": True,
            },
            "content_quality": {
                "min_statistics": CONTENT_REQUIREMENTS["statistics_min"],
                "min_expert_quotes": CONTENT_REQUIREMENTS["expert_quotes_min"],
                "citation_format": "name-drop + link (e.g., According to [Source](url), ...)",
                "no_fabricated_examples": True,
            },
            "brand_positioning": "comparative" if comparative else ("authority" if brand else "neutral"),
        },
        "sections": sections,
        "metadata_template": {
            "title": "",
            "meta_description": "150–160 characters",
            "author": {"name": "", "credentials": ""},
            "last_updated": "",
            "sources": [],
        },
    }

    return scaffold


def main():
    parser = argparse.ArgumentParser(description="Generate content scaffold from prompt")
    parser.add_argument("--topic", required=True, help="Content topic or question")
    parser.add_argument("--brand", default="", help="Brand name for positioning")
    parser.add_argument("--icp", default="", help="Ideal Customer Profile description")
    parser.add_argument("--sources", default="", help="Comma-separated source URLs")
    args = parser.parse_args()

    sources = [s.strip() for s in args.sources.split(",") if s.strip()]

    scaffold = create_content_scaffold(
        topic=args.topic,
        brand=args.brand,
        icp=args.icp,
        source_urls=sources,
    )

    print(json.dumps(scaffold, indent=2))


if __name__ == "__main__":
    main()
