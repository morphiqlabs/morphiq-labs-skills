#!/usr/bin/env python3
"""generate-report.py — Assemble a Delta Report from analysis data.

Usage: python3 generate-report.py --data analysis.json --deltas deltas.json
Output: Delta Report JSON matching PIPELINE.md §4 contract
"""

import argparse
import json
import sys
from datetime import datetime


def build_sov_section(analysis: dict) -> dict:
    """Build the 3-tier SoV section."""
    sov = analysis.get("share_of_voice", {})
    return {
        "mention_sov": {
            "current": sov.get("mention_sov", 0),
            "previous": sov.get("previous_mention_sov", 0),
            "delta": sov.get("mention_sov", 0) - sov.get("previous_mention_sov", 0),
        },
        "fanout_weighted_sov": {
            "current": sov.get("fanout_weighted_sov", 0),
            "previous": sov.get("previous_fanout_weighted_sov", 0),
            "delta": sov.get("fanout_weighted_sov", 0) - sov.get("previous_fanout_weighted_sov", 0),
        },
        "influence_sov": {
            "current": sov.get("influence_sov", 0),
            "previous": sov.get("previous_influence_sov", 0),
            "delta": sov.get("influence_sov", 0) - sov.get("previous_influence_sov", 0),
        },
        "conversion_gap": sov.get("influence_sov", 0) - sov.get("citation_sov", 0),
    }


def build_citation_section(analysis: dict) -> dict:
    """Build citation tracking section."""
    citations = analysis.get("citations", {})
    return {
        "gained": citations.get("gained", []),
        "lost": citations.get("lost", []),
        "stable": citations.get("stable", []),
        "total_current": len(citations.get("gained", [])) + len(citations.get("stable", [])),
    }


def build_provider_section(analysis: dict) -> dict:
    """Build per-provider performance breakdown."""
    providers = analysis.get("per_provider", {})
    result = {}
    for provider, data in providers.items():
        result[provider] = {
            "mention_rate": data.get("mention_rate", 0),
            "avg_position": data.get("avg_position", 0),
            "citation_count": data.get("citation_count", 0),
            "prompts_tested": data.get("prompts_tested", 0),
        }
    return result


def build_competitor_section(analysis: dict) -> dict:
    """Build competitor mentions section."""
    competitors = analysis.get("competitors", [])
    return {
        "tracked": [
            {
                "name": c.get("name", ""),
                "visibility": c.get("visibility", 0),
                "position": c.get("position", 0),
                "sentiment": c.get("sentiment", "Neutral"),
                "mentions": c.get("mentions", 0),
            }
            for c in competitors
        ],
        "count": len(competitors),
    }


def build_content_queue(analysis: dict) -> list:
    """Build content creation queue from gaps."""
    gaps = analysis.get("content_gaps", [])
    queue = []
    for gap in gaps:
        queue.append({
            "prompt": gap.get("prompt", ""),
            "gap_type": gap.get("type", "content"),
            "priority": gap.get("priority", "medium"),
            "brief": gap.get("brief", ""),
            "target_page_type": gap.get("target_page_type", "blog"),
        })
    return queue


def generate_delta_report(analysis: dict, deltas: dict) -> dict:
    """Generate the full Delta Report."""
    report = {
        "schema_version": "1.0",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "domain": analysis.get("domain", ""),
        "scores": {
            "technical_score": {
                "current": analysis.get("technical_score", 0),
                "delta": deltas.get("technical_deltas", {}).get("overall", {}).get("delta", 0),
            },
            "geo_score": {
                "current": analysis.get("geo_score", 0),
                "delta": deltas.get("geo_deltas", {}).get("overall", {}).get("delta", 0),
            },
            "weighted_geo": {
                "current": analysis.get("weighted_geo", 0),
                "delta": deltas.get("geo_deltas", {}).get("weighted", {}).get("delta", 0),
            },
        },
        "share_of_voice": build_sov_section(analysis),
        "citations": build_citation_section(analysis),
        "per_provider": build_provider_section(analysis),
        "competitors": build_competitor_section(analysis),
        "flagged_actions": deltas.get("flagged_actions", []),
        "content_creation_queue": build_content_queue(analysis),
        "subquery_brand_appearances": analysis.get("subquery_brand_appearances", {}),
        "run_metadata": {
            "prompts_tested": analysis.get("prompts_tested", 0),
            "providers_queried": list(analysis.get("per_provider", {}).keys()),
            "run_number": analysis.get("run_number", 1),
        },
    }

    return report


def main():
    parser = argparse.ArgumentParser(description="Generate Delta Report")
    parser.add_argument("--data", required=True, help="Analysis data JSON")
    parser.add_argument("--deltas", required=True, help="Deltas JSON from diff-results.py")
    args = parser.parse_args()

    with open(args.data) as f:
        analysis = json.load(f)
    with open(args.deltas) as f:
        deltas = json.load(f)

    report = generate_delta_report(analysis, deltas)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
