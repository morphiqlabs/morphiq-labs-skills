#!/usr/bin/env python3
"""generate-report.py — Assemble a Delta Report from analysis data.

Usage:
  python3 generate-report.py --data analysis.json --deltas deltas.json [--state-dir morphiq-track/]

With --state-dir, populates raw_results.storage from the latest results path in manifest.json.
"""

import argparse
import json
import os
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


def build_content_queue(analysis: dict, fanout_queue: list = None) -> list:
    """Build content creation queue from gaps + fanout briefs.

    fanout_queue entries (from analyze-fanout.py) already match the PIPELINE.md
    content_creation_queue schema (brief_id, derived_query, etc.) and are
    included directly. Gap-derived entries are transformed to match.
    """
    queue = []

    # Include pre-built fanout briefs directly (they already have brief_id, derived_query, etc.)
    if fanout_queue:
        queue.extend(fanout_queue)

    # Transform content_gaps into queue entries
    gaps = analysis.get("content_gaps", [])
    offset = len(queue)
    for i, gap in enumerate(gaps):
        entry = {
            "brief_id": f"brief-{offset + i + 1:03d}",
            "source_content": gap.get("prompt", ""),
            "derived_query": gap.get("sub_query", gap.get("brief", "")),
            "rationale": gap.get("brief", ""),
            "status": "pending",
            "created_at": datetime.utcnow().strftime("%Y-%m-%d"),
        }
        # Pass through fanout fields when present
        if gap.get("model_origin"):
            entry["model_origin"] = gap["model_origin"]
        if gap.get("prompt_type"):
            entry["prompt_type"] = gap["prompt_type"]
        if gap.get("citation_weight"):
            entry["citation_weight"] = gap["citation_weight"]
        if gap.get("competitor_sources"):
            entry["competitor_sources"] = gap["competitor_sources"]
        queue.append(entry)
    return queue


def generate_delta_report(analysis: dict, deltas: dict, raw_results_path: str = None,
                          fanout_queue: list = None) -> dict:
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
        "content_creation_queue": build_content_queue(analysis, fanout_queue),
        "subquery_brand_appearances": analysis.get("subquery_brand_appearances", {}),
        "run_metadata": {
            "prompts_tested": analysis.get("prompts_tested", 0),
            "providers_queried": list(analysis.get("per_provider", {}).keys()),
            "run_number": analysis.get("run_number", 1),
        },
        "raw_results": {
            "storage": raw_results_path or "",
            "format": "Per-provider raw responses stored separately for audit",
        },
    }

    return report


def main():
    parser = argparse.ArgumentParser(description="Generate Delta Report")
    parser.add_argument("--data", required=True, help="Analysis data JSON")
    parser.add_argument("--deltas", required=True, help="Deltas JSON from diff-results.py")
    parser.add_argument("--state-dir", default=None,
                        help="State directory — populates raw_results.storage from manifest")
    parser.add_argument("--fanout", default=None,
                        help="Fanout analysis JSON from analyze-fanout.py")
    args = parser.parse_args()

    with open(args.data) as f:
        analysis = json.load(f)
    with open(args.deltas) as f:
        deltas = json.load(f)

    # Load fanout analysis (content_creation_queue passed directly, content_gaps merged)
    fanout_queue = None
    if args.fanout:
        with open(args.fanout) as f:
            fanout_data = json.load(f)
        fanout_queue = fanout_data.get("content_creation_queue", [])
        # Also merge content_gaps for any non-queue gap consumers
        existing_gaps = analysis.get("content_gaps", [])
        fanout_gaps = fanout_data.get("content_gaps", [])
        analysis["content_gaps"] = existing_gaps + fanout_gaps

    # Resolve raw_results path from manifest
    raw_results_path = None
    if args.state_dir:
        manifest_path = os.path.join(args.state_dir, "manifest.json")
        if os.path.exists(manifest_path):
            with open(manifest_path) as f:
                manifest = json.load(f)
            runs = manifest.get("runs", [])
            if runs:
                raw_results_path = runs[0].get("results_path")

    report = generate_delta_report(analysis, deltas, raw_results_path, fanout_queue)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
