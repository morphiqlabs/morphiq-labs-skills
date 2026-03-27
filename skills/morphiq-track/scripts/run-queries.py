#!/usr/bin/env python3
"""run-queries.py — Distribute prompts across AI providers and structure results.

Usage:
  Plan mode:    python3 run-queries.py --prompts prompts.json --mode plan
  Results mode: python3 run-queries.py --prompts prompts.json --results results.json --mode results

Design pattern: This script creates the execution plan and structures results.
The Claude Code agent reads the plan and executes each query using its built-in
web search and API tools. After gathering responses, the agent feeds them back
through --mode results for aggregation and citation diffing.
"""

import argparse
import json
import sys
from collections import defaultdict

# Default provider configurations. Model names are recommended defaults —
# the agent should use the latest available version at runtime.
PROVIDERS = {
    "openai": {
        "model": "gpt-4o",
        "search_tool": "web_search",
        "concurrency": "full",
        "config": {"search_context_size": "high"},
    },
    "perplexity": {
        "model": "sonar-pro",
        "search_tool": "native",
        "concurrency": 2,
    },
    "anthropic": {
        "model": "claude-sonnet-4-5",
        "search_tool": "web_search_20250305",
        "concurrency": 1,  # serialized
    },
    "gemini": {
        "model": "gemini-3-flash-preview",
        "search_tool": "googleSearch",
        "concurrency": 3,
        "fallback_models": ["gemini-2.5-flash", "gemini-2.5-flash-lite"],
    },
}


def distribute_prompts(prompts: list, provider_names: list = None) -> dict:
    """Distribute prompts evenly across providers."""
    providers = provider_names or list(PROVIDERS.keys())
    distribution = defaultdict(list)

    for i, prompt in enumerate(prompts):
        provider = providers[i % len(providers)]
        distribution[provider].append(prompt)

    return dict(distribution)


def create_query_plan(prompts: list, provider_names: list = None) -> dict:
    """Create a query execution plan with provider assignments."""
    distribution = distribute_prompts(prompts, provider_names)

    plan = {
        "total_prompts": len(prompts),
        "providers": {},
        "execution_order": [],
    }

    for provider, assigned_prompts in distribution.items():
        config = PROVIDERS.get(provider, {})
        concurrency = config.get("concurrency", 1)

        plan["providers"][provider] = {
            "model": config.get("model", "unknown"),
            "prompt_count": len(assigned_prompts),
            "concurrency": concurrency,
            "prompts": [p["id"] for p in assigned_prompts],
        }

        # Build execution batches
        if isinstance(concurrency, int):
            for batch_start in range(0, len(assigned_prompts), concurrency):
                batch = assigned_prompts[batch_start:batch_start + concurrency]
                plan["execution_order"].append({
                    "provider": provider,
                    "batch": [p["id"] for p in batch],
                })
        else:
            # Full concurrency — single batch
            plan["execution_order"].append({
                "provider": provider,
                "batch": [p["id"] for p in assigned_prompts],
            })

    return plan


def structure_result(prompt_id: str, provider: str, response_text: str,
                     citations: list = None, sub_queries: list = None) -> dict:
    """Structure a single query result for analysis."""
    return {
        "prompt_id": prompt_id,
        "provider": provider,
        "model": PROVIDERS.get(provider, {}).get("model", "unknown"),
        "response": {
            "text": response_text,
            "word_count": len(response_text.split()),
        },
        "citations": citations or [],
        "sub_queries": sub_queries or [],
        "analysis": None,  # Populated by GPT-5.2 analysis step
    }


def aggregate_results(results: list) -> dict:
    """Aggregate query results into a summary."""
    by_provider = defaultdict(list)
    for r in results:
        by_provider[r["provider"]].append(r)

    summary = {
        "total_queries": len(results),
        "successful": sum(1 for r in results if r["response"]["text"]),
        "failed": sum(1 for r in results if not r["response"]["text"]),
        "by_provider": {},
    }

    for provider, provider_results in by_provider.items():
        successful = [r for r in provider_results if r["response"]["text"]]
        summary["by_provider"][provider] = {
            "total": len(provider_results),
            "successful": len(successful),
            "avg_citations": sum(len(r["citations"]) for r in successful) / max(len(successful), 1),
            "avg_sub_queries": sum(len(r["sub_queries"]) for r in successful) / max(len(successful), 1),
        }

    return summary


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


def main():
    parser = argparse.ArgumentParser(description="Distribute prompts and structure results")
    parser.add_argument("--prompts", required=True, help="Path to prompts JSON file")
    parser.add_argument("--output", default="-", help="Output path (- for stdout)")
    parser.add_argument("--providers", default="", help="Comma-separated provider names (default: all)")
    parser.add_argument("--mode", default="plan", choices=["plan", "results"],
                        help="plan: output execution plan. results: aggregate results + diff citations")
    parser.add_argument("--results", default=None, help="Path to results JSON (for --mode results)")
    parser.add_argument("--previous-citations", default=None,
                        help="Path to previous citations JSON (for citation diffing)")
    args = parser.parse_args()

    with open(args.prompts) as f:
        data = json.load(f)

    prompts = data.get("prompts", data) if isinstance(data, dict) else data
    providers = [p.strip() for p in args.providers.split(",") if p.strip()] or None

    if args.mode == "plan":
        plan = create_query_plan(prompts, providers)
        output = json.dumps(plan, indent=2)
    else:
        # Results mode: aggregate and optionally diff citations
        results_data = []
        if args.results:
            with open(args.results) as f:
                results_data = json.load(f)
            if isinstance(results_data, dict):
                results_data = results_data.get("results", [])

        summary = aggregate_results(results_data)

        # Citation diffing
        current_citations = []
        for r in results_data:
            for c in r.get("citations", []):
                c.setdefault("provider", r.get("provider", ""))
                c.setdefault("prompt", r.get("prompt_id", ""))
                current_citations.append(c)

        citation_diff = None
        if args.previous_citations:
            with open(args.previous_citations) as f:
                previous_citations = json.load(f)
            if isinstance(previous_citations, dict):
                previous_citations = previous_citations.get("citations", [])
            citation_diff = diff_citations(current_citations, previous_citations)

        output = json.dumps({
            "summary": summary,
            "current_citations": current_citations,
            "citation_diff": citation_diff,
        }, indent=2)

    if args.output == "-":
        print(output)
    else:
        with open(args.output, "w") as f:
            f.write(output)


if __name__ == "__main__":
    main()
