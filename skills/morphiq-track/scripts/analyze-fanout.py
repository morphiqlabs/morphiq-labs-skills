#!/usr/bin/env python3
"""analyze-fanout.py — Workflow C: Compare extracted sub-queries against site pages.

Reads the latest track results, extracts sub-queries, compares against a site page
inventory, identifies unanswered sub-queries, and generates content briefs with
competitive source data.

Usage:
  python3 analyze-fanout.py --state-dir morphiq-track/ [--scan-report scan.json] [--pages pages.json]

Output (stdout): JSON with content_gaps, content_creation_queue, and summary.
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from urllib.parse import urlparse


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SITE_QUERY_RE = re.compile(r"site:(\S+)")

CITATION_WEIGHTS = {
    "site_targeted": 2.0,
    "citation_producing": 1.5,
    "silent": 0.5,
}

PROMPT_TYPE_SEVERITY = {
    # pipeline_type values
    "technical_eval": "high",
    "discovery": "high",
    "recommendation": "medium",
    "comparison": "medium",
    "problem_seeking": "medium",
    "use_case": "low",
    "category": "medium",
    "feature": "low",
    "brand": "low",
    # geo_category fallback values (when pipeline_type is absent)
    "competitor": "medium",
    "organic": "medium",
    "howto": "medium",
    "brand_specific": "low",
    "faq": "low",
}

CITATION_PRODUCING_TERMS = frozenset([
    "pricing", "price", "cost", "plan", "comparison", "compare", "vs",
    "versus", "alternative", "review", "features", "benchmark", "best",
    "top", "ranking", "rated",
])

STOP_WORDS = frozenset([
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "it", "its", "this", "that",
    "these", "those", "what", "which", "who", "whom", "how", "when", "where",
    "why", "not", "no", "so", "if", "then", "than", "too", "very", "just",
    "about", "up", "out", "into", "from", "as",
])


# ---------------------------------------------------------------------------
# Sub-query extraction
# ---------------------------------------------------------------------------

def load_sub_queries(results, domain):
    """Extract and deduplicate sub-queries from track results.

    Each sub-query is annotated with parent prompt, provider, prompt_type,
    and whether it's a site:-scoped query.
    """
    seen = {}
    for result in results:
        for sq in result.get("sub_queries", []):
            if not sq or not sq.strip():
                continue
            key = sq.strip().lower()
            if key not in seen:
                site_match = SITE_QUERY_RE.search(sq)
                is_site_query = bool(site_match)
                site_domain = site_match.group(1) if site_match else None
                is_own_site = (
                    site_domain and domain and
                    site_domain.rstrip("/").lower() == domain.rstrip("/").lower()
                )
                seen[key] = {
                    "query": sq.strip(),
                    "parent_prompt": result.get("prompt_text", ""),
                    "prompt_id": result.get("prompt_id", ""),
                    "provider": result.get("provider", ""),
                    "prompt_type": result.get("pipeline_type", result.get("geo_category", "")),
                    "is_site_query": is_site_query,
                    "is_own_site_query": is_own_site or False,
                    "citation_weight": classify_citation_weight(sq, is_site_query),
                }
    return list(seen.values())


def classify_citation_weight(query, is_site_query):
    """Classify a sub-query as site_targeted, citation_producing, or silent."""
    if is_site_query:
        return "site_targeted"
    tokens = set(query.lower().split())
    if tokens & CITATION_PRODUCING_TERMS:
        return "citation_producing"
    return "silent"


# ---------------------------------------------------------------------------
# Page inventory
# ---------------------------------------------------------------------------

def load_page_inventory(scan_report_path=None, pages_path=None):
    """Build page inventory from scan report or fallback pages JSON."""
    pages = []

    if scan_report_path and os.path.exists(scan_report_path):
        with open(scan_report_path) as f:
            scan = json.load(f)
        for page in scan.get("pages", []):
            url = page.get("url", "")
            pages.append({
                "url": url,
                "page_type": page.get("page_type", ""),
                "title": page.get("title", ""),
                "keywords": extract_keywords_from_url_and_title(
                    url, page.get("title", "")
                ),
            })

    if pages_path and os.path.exists(pages_path):
        with open(pages_path) as f:
            extra = json.load(f)
        existing_urls = {p["url"] for p in pages}
        for page in extra if isinstance(extra, list) else extra.get("pages", []):
            url = page.get("url", "")
            if url and url not in existing_urls:
                pages.append({
                    "url": url,
                    "page_type": page.get("page_type", ""),
                    "title": page.get("title", ""),
                    "keywords": extract_keywords_from_url_and_title(
                        url, page.get("title", "")
                    ),
                })

    return pages


def extract_keywords_from_url_and_title(url, title):
    """Extract keyword tokens from a URL path and page title."""
    tokens = set()
    try:
        path = urlparse(url).path
        segments = path.strip("/").split("/")
        for seg in segments:
            for word in re.split(r"[-_]", seg):
                w = word.lower().strip()
                if w and w not in STOP_WORDS and len(w) > 2:
                    tokens.add(w)
    except Exception:
        pass
    if title:
        for word in re.split(r"\W+", title):
            w = word.lower().strip()
            if w and w not in STOP_WORDS and len(w) > 2:
                tokens.add(w)
    return tokens


# ---------------------------------------------------------------------------
# Simulated query merging
# ---------------------------------------------------------------------------

def merge_simulated_queries(scan_report_path, existing_queries):
    """Merge scan report simulated queries with real extracted sub-queries."""
    if not scan_report_path or not os.path.exists(scan_report_path):
        return existing_queries

    with open(scan_report_path) as f:
        scan = json.load(f)

    fanout = scan.get("query_fanout", {})
    simulated = fanout.get("simulated_queries", [])
    existing_keys = {sq["query"].strip().lower() for sq in existing_queries}
    merged = list(existing_queries)

    for sim in simulated:
        query = sim.get("query", "").strip()
        if not query or query.lower() in existing_keys:
            continue
        is_site = bool(SITE_QUERY_RE.search(query))
        merged.append({
            "query": query,
            "parent_prompt": "(simulated)",
            "prompt_id": "",
            "provider": sim.get("model", "simulated"),
            "prompt_type": sim.get("prompt_type", ""),
            "is_site_query": is_site,
            "is_own_site_query": is_site,
            "citation_weight": sim.get("citation_weight", classify_citation_weight(query, is_site)),
            "source": "scan_simulation",
        })
        existing_keys.add(query.lower())

    return merged


# ---------------------------------------------------------------------------
# Sub-query to page matching
# ---------------------------------------------------------------------------

def tokenize_query(query):
    """Tokenize a sub-query for matching, stripping site: prefix and stop words."""
    cleaned = SITE_QUERY_RE.sub("", query).strip()
    cleaned = re.sub(r"\b\d{4}\b", "", cleaned)  # remove year markers
    tokens = set()
    for word in re.split(r"\W+", cleaned):
        w = word.lower().strip()
        if w and w not in STOP_WORDS and len(w) > 2:
            tokens.add(w)
    return tokens


def match_subquery_to_page(sub_query, pages):
    """Match a sub-query against the page inventory.

    Returns (confidence, best_match_url) where confidence is none/partial/full.
    """
    query_tokens = tokenize_query(sub_query["query"])
    if not query_tokens:
        return "none", None

    best_score = 0
    best_url = None

    for page in pages:
        page_tokens = page["keywords"]
        if not page_tokens:
            continue
        overlap = query_tokens & page_tokens
        score = len(overlap) / len(query_tokens) if query_tokens else 0
        if score > best_score:
            best_score = score
            best_url = page["url"]

    if best_score >= 0.6:
        return "full", best_url
    elif best_score >= 0.3:
        return "partial", best_url
    return "none", None


# ---------------------------------------------------------------------------
# Severity classification
# ---------------------------------------------------------------------------

def classify_unanswered(sub_query):
    """Determine severity of an unanswered sub-query."""
    prompt_type = sub_query.get("prompt_type", "")
    base = PROMPT_TYPE_SEVERITY.get(prompt_type, "medium")

    # Escalation rules
    severity_order = ["low", "medium", "high", "critical"]
    idx = severity_order.index(base)

    if sub_query.get("is_site_query") or sub_query.get("is_own_site_query"):
        idx = min(idx + 1, len(severity_order) - 1)
    if sub_query.get("citation_weight") == "citation_producing":
        idx = min(idx + 1, len(severity_order) - 1)

    return severity_order[idx]


# ---------------------------------------------------------------------------
# Competitor source extraction
# ---------------------------------------------------------------------------

def extract_competitor_sources(results, sub_query, domain):
    """Find competitor citation URLs from the same prompt's results."""
    prompt_id = sub_query.get("prompt_id", "")
    if not prompt_id:
        return []

    competitor_urls = {}
    for result in results:
        if result.get("prompt_id") != prompt_id:
            continue
        for cit in result.get("citations", []):
            url = cit.get("url", "")
            if not url:
                continue
            try:
                cit_domain = urlparse(url).netloc.lower().replace("www.", "")
            except Exception:
                continue
            clean_domain = domain.lower().replace("www.", "") if domain else ""
            if cit_domain and cit_domain != clean_domain:
                if url not in competitor_urls:
                    competitor_urls[url] = {
                        "url": url,
                        "citation_weight": cit.get("citation_weight", 1),
                        "provider": result.get("provider", ""),
                    }
                else:
                    competitor_urls[url]["citation_weight"] += cit.get("citation_weight", 1)

    return sorted(
        competitor_urls.values(),
        key=lambda x: x["citation_weight"],
        reverse=True,
    )[:5]


# ---------------------------------------------------------------------------
# Brief generation
# ---------------------------------------------------------------------------

def infer_page_type(query):
    """Infer the target page type from a sub-query."""
    q = query.lower()
    if any(t in q for t in ["pricing", "price", "cost", "plan"]):
        return "pricing"
    if any(t in q for t in ["vs", "versus", "compare", "comparison", "alternative"]):
        return "comparison"
    if any(t in q for t in ["feature", "capabilities", "product"]):
        return "product"
    if any(t in q for t in ["how to", "guide", "tutorial", "implement", "setup"]):
        return "docs"
    if any(t in q for t in ["review", "case study", "customer"]):
        return "case-study"
    return "blog"


def build_briefs(unanswered_queries, results, domain):
    """Create content_creation_queue entries from unanswered sub-queries."""
    briefs = []
    queue = []
    now = datetime.utcnow().strftime("%Y-%m-%d")

    for i, sq in enumerate(unanswered_queries):
        severity = classify_unanswered(sq)
        competitor_sources = extract_competitor_sources(results, sq, domain)
        page_type = infer_page_type(sq["query"])
        brief_id = f"brief-{i + 1:03d}"

        gap = {
            "prompt": sq["parent_prompt"],
            "type": "fanout_coverage",
            "priority": severity,
            "brief": f"Create {page_type} content addressing: {sq['query']}",
            "target_page_type": page_type,
            "sub_query": sq["query"],
            "model_origin": sq["provider"],
            "citation_weight": sq["citation_weight"],
            "competitor_sources": competitor_sources,
        }
        briefs.append(gap)

        # source_content: use parent prompt text (the content context that generated the brief)
        source = sq.get("parent_prompt", "")
        if source == "(simulated)":
            source = "(scan simulation)"

        queue_entry = {
            "brief_id": brief_id,
            "source_content": source,
            "derived_query": sq["query"],
            "rationale": _build_rationale(sq),
            "status": "pending",
            "created_at": now,
            "model_origin": sq["provider"],
            "prompt_type": sq["prompt_type"],
            "citation_weight": sq["citation_weight"],
            "competitor_sources": competitor_sources,
        }
        queue.append(queue_entry)

    return briefs, queue


def _build_rationale(sq):
    """Build a human-readable rationale for a content brief."""
    parts = []
    if sq.get("is_own_site_query"):
        parts.append(f"site:-scoped query found nothing on the audited domain")
    parts.append(f"Sub-query from '{sq['parent_prompt'][:80]}'")
    parts.append(f"model: {sq['provider']}")
    parts.append(f"weight: {sq['citation_weight']}")
    return " — ".join(parts)


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def analyze_fanout(state_dir, scan_report_path=None, pages_path=None):
    """Run the full Workflow C fanout analysis pipeline."""

    # 1. Load latest track results from state directory
    manifest_path = os.path.join(state_dir, "manifest.json")
    if not os.path.exists(manifest_path):
        print(json.dumps({"error": "No manifest.json found in state directory"}),
              file=sys.stderr)
        sys.exit(1)

    with open(manifest_path) as f:
        manifest = json.load(f)

    runs = manifest.get("runs", [])
    if not runs:
        print(json.dumps({"error": "No runs found in manifest"}),
              file=sys.stderr)
        sys.exit(1)

    latest_run = runs[0]
    results_path = latest_run.get("results_path", "")

    # Resolve results path relative to parent of state_dir
    if not os.path.isabs(results_path):
        base = os.path.dirname(state_dir.rstrip("/"))
        results_path = os.path.join(base, results_path)

    if not os.path.exists(results_path):
        print(json.dumps({"error": f"Results file not found: {results_path}"}),
              file=sys.stderr)
        sys.exit(1)

    with open(results_path) as f:
        track_data = json.load(f)

    results = track_data.get("results", [])
    domain = track_data.get("config", {}).get("domain", "")

    # 2. Extract sub-queries
    sub_queries = load_sub_queries(results, domain)

    # 3. Merge with scan simulated queries
    sub_queries = merge_simulated_queries(scan_report_path, sub_queries)

    # 4. Load page inventory
    pages = load_page_inventory(scan_report_path, pages_path)

    # 5. Match sub-queries against pages
    answered = []
    unanswered = []
    for sq in sub_queries:
        confidence, matched_url = match_subquery_to_page(sq, pages)
        sq["match_confidence"] = confidence
        sq["matched_url"] = matched_url
        if confidence in ("full", "partial"):
            answered.append(sq)
        else:
            unanswered.append(sq)

    # 6. Sort unanswered by severity (high first) and citation weight
    weight_order = {"site_targeted": 0, "citation_producing": 1, "silent": 2}
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    unanswered.sort(key=lambda sq: (
        severity_order.get(classify_unanswered(sq), 3),
        weight_order.get(sq.get("citation_weight", "silent"), 2),
    ))

    # 7. Build briefs and content creation queue
    content_gaps, content_creation_queue = build_briefs(unanswered, results, domain)

    # 8. Identify providers with/without sub-query support
    providers_with = set()
    providers_without = set()
    for r in results:
        provider = r.get("provider", "")
        if r.get("sub_queries"):
            providers_with.add(provider)
        else:
            providers_without.add(provider)

    # 9. Assemble output
    output = {
        "content_gaps": content_gaps,
        "content_creation_queue": content_creation_queue,
        "summary": {
            "total_sub_queries": len(sub_queries),
            "unique_sub_queries": len(sub_queries),
            "answered": len(answered),
            "unanswered": len(unanswered),
            "briefs_generated": len(content_creation_queue),
            "providers_with_sub_queries": sorted(providers_with),
            "providers_without": sorted(providers_without - providers_with),
        },
    }

    return output


def main():
    parser = argparse.ArgumentParser(
        description="Workflow C: Analyze query fanout coverage and generate content briefs"
    )
    parser.add_argument(
        "--state-dir", required=True,
        help="State directory (morphiq-track/) containing manifest.json"
    )
    parser.add_argument(
        "--scan-report", default=None,
        help="Scan Report JSON for page inventory and simulated queries"
    )
    parser.add_argument(
        "--pages", default=None,
        help="Fallback page inventory JSON"
    )
    args = parser.parse_args()

    output = analyze_fanout(args.state_dir, args.scan_report, args.pages)
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
