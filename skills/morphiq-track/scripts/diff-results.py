#!/usr/bin/env python3
"""diff-results.py — Compare two analysis snapshots and compute deltas.

Usage: python3 diff-results.py --current current.json --previous previous.json
Output: JSON delta report with significant changes flagged
"""

import argparse
import json
import sys

SIGNIFICANCE_THRESHOLD = 5  # Minimum point change to flag


def compute_delta(current: float, previous: float) -> dict:
    """Compute delta between two values."""
    delta = current - previous
    return {
        "current": current,
        "previous": previous,
        "delta": round(delta, 1),
        "significant": abs(delta) >= SIGNIFICANCE_THRESHOLD,
    }


def diff_scores(current: dict, previous: dict) -> dict:
    """Diff Technical Score dimensions."""
    dimensions = ["schema", "metadata", "faq", "content"]
    result = {}

    for dim in dimensions:
        curr_val = current.get(dim, 0)
        prev_val = previous.get(dim, 0)
        result[dim] = compute_delta(curr_val, prev_val)

    # Overall Technical Score
    curr_total = current.get("total", sum(current.get(d, 0) for d in dimensions))
    prev_total = previous.get("total", sum(previous.get(d, 0) for d in dimensions))
    result["overall"] = compute_delta(curr_total, prev_total)

    return result


def diff_geo(current: dict, previous: dict) -> dict:
    """Diff GEO Score and per-provider visibility."""
    result = {}

    # Overall GEO
    result["overall"] = compute_delta(
        current.get("geo_score", 0),
        previous.get("geo_score", 0)
    )

    # Intent-weighted GEO
    result["weighted"] = compute_delta(
        current.get("weighted_geo", 0),
        previous.get("weighted_geo", 0)
    )

    # Per-provider
    providers = set(list(current.get("per_provider", {}).keys()) +
                   list(previous.get("per_provider", {}).keys()))
    result["per_provider"] = {}
    for provider in providers:
        result["per_provider"][provider] = compute_delta(
            current.get("per_provider", {}).get(provider, 0),
            previous.get("per_provider", {}).get(provider, 0)
        )

    return result


def diff_sov(current: dict, previous: dict) -> dict:
    """Diff Share of Voice metrics."""
    sov_types = ["mention_sov", "fanout_weighted_sov", "influence_sov", "conversion_gap"]
    result = {}

    for sov_type in sov_types:
        result[sov_type] = compute_delta(
            current.get(sov_type, 0),
            previous.get(sov_type, 0)
        )

    # Per-competitor SoV
    competitors = set(list(current.get("competitors", {}).keys()) +
                     list(previous.get("competitors", {}).keys()))
    result["competitors"] = {}
    for comp in competitors:
        result["competitors"][comp] = compute_delta(
            current.get("competitors", {}).get(comp, 0),
            previous.get("competitors", {}).get(comp, 0)
        )

    return result


def diff_citations(current_citations: list, previous_citations: list) -> dict:
    """Compute gained/lost/stable citations between two runs.

    Each citation is a dict with keys: url, provider, prompt, prompt_type.
    Comparison uses the (url, provider, prompt) triple as the unique key.
    """
    def citation_key(c):
        return (c.get("url", ""), c.get("provider", ""), c.get("prompt", ""))

    current_set = {citation_key(c) for c in current_citations}
    previous_set = {citation_key(c) for c in previous_citations}

    gained_keys = current_set - previous_set
    lost_keys = previous_set - current_set
    stable_keys = current_set & previous_set

    current_by_key = {citation_key(c): c for c in current_citations}
    previous_by_key = {citation_key(c): c for c in previous_citations}

    return {
        "gained": [current_by_key[k] for k in gained_keys if k in current_by_key],
        "lost": [previous_by_key[k] for k in lost_keys if k in previous_by_key],
        "stable": [current_by_key[k] for k in stable_keys if k in current_by_key],
        "total_current": len(current_citations),
        "total_previous": len(previous_citations),
        "net": len(gained_keys) - len(lost_keys),
    }


def generate_flagged_actions(technical_delta: dict, geo_delta: dict, sov_delta: dict) -> list:
    """Generate flagged actions based on significant deltas."""
    actions = []

    # Technical regression
    tech_overall = technical_delta.get("overall", {})
    if tech_overall.get("significant") and tech_overall.get("delta", 0) < 0:
        actions.append({
            "type": "technical_regression",
            "summary": f"Technical score dropped by {abs(tech_overall['delta'])} points",
            "severity": "high" if abs(tech_overall["delta"]) >= 10 else "medium",
            "feed_to_rank": True,
        })

    # GEO visibility drop
    geo_overall = geo_delta.get("overall", {})
    if geo_overall.get("significant") and geo_overall.get("delta", 0) < 0:
        actions.append({
            "type": "visibility_drop",
            "summary": f"GEO visibility declined by {abs(geo_overall['delta'])} points",
            "severity": "high",
            "feed_to_rank": True,
        })

    # Per-provider regression (>10 points)
    for provider, delta in geo_delta.get("per_provider", {}).items():
        if delta.get("delta", 0) < -10:
            actions.append({
                "type": "provider_regression",
                "summary": f"{provider} visibility dropped by {abs(delta['delta'])} points",
                "provider": provider,
                "severity": "medium",
                "feed_to_rank": True,
            })

    # SoV drops
    mention_sov = sov_delta.get("mention_sov", {})
    if mention_sov.get("significant") and mention_sov.get("delta", 0) < 0:
        actions.append({
            "type": "sov_drop",
            "summary": f"Mention SoV dropped by {abs(mention_sov['delta'])}%",
            "severity": "high",
            "feed_to_rank": True,
        })

    # Conversion gap widening
    conv_gap = sov_delta.get("conversion_gap", {})
    if conv_gap.get("current", 0) > 20:
        actions.append({
            "type": "conversion_gap",
            "summary": f"Conversion gap is {conv_gap['current']} points — brand researched but not cited",
            "severity": "medium",
            "feed_to_rank": True,
        })

    # Competitor gains
    for comp, delta in sov_delta.get("competitors", {}).items():
        if delta.get("delta", 0) > 5:
            actions.append({
                "type": "competitor_gain",
                "summary": f"{comp} gained {delta['delta']}% SoV",
                "competitor": comp,
                "severity": "medium",
                "feed_to_rank": True,
            })

    # Positive signals (citation opportunities)
    if geo_overall.get("significant") and geo_overall.get("delta", 0) > 0:
        actions.append({
            "type": "citation_opportunity",
            "summary": f"GEO visibility improved by {geo_overall['delta']} points",
            "severity": "info",
            "feed_to_rank": False,
        })

    return actions


def main():
    parser = argparse.ArgumentParser(description="Compare analysis snapshots")
    parser.add_argument("--current", required=True, help="Current snapshot JSON")
    parser.add_argument("--previous", required=True, help="Previous snapshot JSON")
    args = parser.parse_args()

    with open(args.current) as f:
        current = json.load(f)
    with open(args.previous) as f:
        previous = json.load(f)

    technical_delta = diff_scores(
        current.get("technical_scores", {}),
        previous.get("technical_scores", {})
    )
    geo_delta = diff_geo(current, previous)
    sov_delta = diff_sov(
        current.get("share_of_voice", {}),
        previous.get("share_of_voice", {})
    )

    # Citation-level diff
    citation_delta = diff_citations(
        current.get("citations", []),
        previous.get("citations", [])
    )

    flagged_actions = generate_flagged_actions(technical_delta, geo_delta, sov_delta)

    # Add citation-based flagged actions
    if citation_delta["net"] < 0:
        flagged_actions.append({
            "type": "citation_loss",
            "summary": f"Lost {abs(citation_delta['net'])} net citations this run",
            "severity": "high" if abs(citation_delta["net"]) >= 3 else "medium",
            "feed_to_rank": True,
        })
    if citation_delta["net"] > 0:
        flagged_actions.append({
            "type": "citation_gain",
            "summary": f"Gained {citation_delta['net']} net citations this run",
            "severity": "info",
            "feed_to_rank": False,
        })

    report = {
        "technical_deltas": technical_delta,
        "geo_deltas": geo_delta,
        "sov_deltas": sov_delta,
        "citation_deltas": citation_delta,
        "flagged_actions": flagged_actions,
        "summary": {
            "significant_changes": sum(
                1 for d in [technical_delta.get("overall", {}),
                           geo_delta.get("overall", {}),
                           sov_delta.get("mention_sov", {})]
                if d.get("significant")
            ),
            "citations_gained": len(citation_delta.get("gained", [])),
            "citations_lost": len(citation_delta.get("lost", [])),
            "citations_net": citation_delta.get("net", 0),
            "actions_count": len(flagged_actions),
            "feed_to_rank_count": sum(1 for a in flagged_actions if a.get("feed_to_rank")),
        }
    }

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
