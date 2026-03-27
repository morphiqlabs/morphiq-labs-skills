#!/usr/bin/env python3
"""score-page.py — Compute per-page Technical Score (0–100) from extracted metadata.

Usage: echo '<json>' | python3 score-page.py
   or: python3 score-page.py < metadata.json

Input: JSON with fields from extract-meta.py
Output: JSON with dimension scores and total Technical Score
"""

import json
import sys

AEO_RELEVANT_TYPES = {
    "Organization", "WebSite", "Product", "Service", "Article", "BlogPosting",
    "FAQPage", "BreadcrumbList", "HowTo", "SoftwareApplication", "CollectionPage",
    "WebApplication", "OfferCatalog", "VideoObject", "ItemList", "Review",
    "Person", "AboutPage"
}

SUBTYPE_MAP = {
    "NewsArticle": "Article",
    "TechArticle": "Article",
    "MobileApplication": "SoftwareApplication",
    "LocalBusiness": "Organization",
}


def score_schema(meta: dict) -> dict:
    """Schema dimension: 40 points max (J1–J4)."""
    scores = {}

    # J1 — Present (10 pts)
    jsonld_count = meta.get("jsonld_count", 0)
    scores["j1_present"] = 10 if jsonld_count > 0 else 0

    # J2a — Valid Structure (4 pts)
    # J2b — Required Properties (4 pts)
    # These require parsing actual JSON-LD blocks — score based on presence
    jsonld_blocks = meta.get("jsonld_blocks", [])
    if isinstance(jsonld_blocks, list) and len(jsonld_blocks) > 0:
        valid_count = 0
        for block in jsonld_blocks:
            if isinstance(block, dict) and "@context" in block and "@type" in block:
                valid_count += 1
        scores["j2a_valid_structure"] = 4 if valid_count == len(jsonld_blocks) else int(4 * valid_count / max(len(jsonld_blocks), 1))
        scores["j2b_required_properties"] = 4 if valid_count > 0 else 0
    else:
        scores["j2a_valid_structure"] = 4 if jsonld_count > 0 else 0
        scores["j2b_required_properties"] = 4 if jsonld_count > 0 else 0

    # J3 — Relevant Type (11 pts)
    schema_types = meta.get("schema_types", [])
    if schema_types:
        resolved_types = set()
        for t in schema_types:
            resolved = SUBTYPE_MAP.get(t, t)
            resolved_types.add(resolved)
        relevant = resolved_types & AEO_RELEVANT_TYPES
        scores["j3_relevant_type"] = 11 if len(relevant) > 0 else 0
    else:
        scores["j3_relevant_type"] = 11 if jsonld_count > 0 else 0

    # J4 — Coverage (11 pts)
    expected_schemas = meta.get("expected_schemas", [])
    present_schemas = meta.get("present_schemas", [])
    if expected_schemas:
        covered = sum(1 for s in expected_schemas if s in present_schemas)
        scores["j4_coverage"] = 11 if covered == len(expected_schemas) else int(11 * covered / len(expected_schemas))
    else:
        scores["j4_coverage"] = 11 if jsonld_count > 0 else 0

    total = sum(scores.values())
    return {"scores": scores, "total": min(total, 40), "max": 40}


def score_metadata(meta: dict) -> dict:
    """Metadata dimension: 30 points max (M1–M5)."""
    scores = {}

    # M1 — Title (8 pts)
    title = meta.get("title", "")
    scores["m1_title"] = 8 if title and len(title.strip()) > 0 else 0

    # M2 — Description (8 pts)
    desc = meta.get("meta_description", "")
    scores["m2_description"] = 8 if desc and len(desc.strip()) > 0 else 0

    # M3 — Canonical (6 pts)
    canonical = meta.get("canonical", "")
    scores["m3_canonical"] = 6 if canonical and len(canonical.strip()) > 0 else 0

    # M4 — Open Graph (4 pts)
    og_title = meta.get("og_title", "")
    og_desc = meta.get("og_description", "")
    scores["m4_open_graph"] = 4 if (og_title or og_desc) else 0

    # M5 — Twitter Cards (4 pts)
    tw_card = meta.get("twitter_card", "")
    tw_title = meta.get("twitter_title", "")
    scores["m5_twitter"] = 4 if (tw_card or tw_title) else 0

    total = sum(scores.values())
    return {"scores": scores, "total": min(total, 30), "max": 30}


def score_faq(meta: dict) -> dict:
    """FAQ dimension: 20 points max, linear scale."""
    faq_count = meta.get("faq_count", 0)
    is_marketing = meta.get("is_marketing_page", True)

    if not is_marketing:
        return {"faq_count": faq_count, "total": 0, "max": 0, "excluded": True}

    points = min(faq_count * 5, 20)
    return {"faq_count": faq_count, "total": points, "max": 20, "excluded": False}


def score_content(meta: dict) -> dict:
    """Content dimension: 10 points max (C1–C2)."""
    scores = {}

    # C1 — Word Count (5 pts)
    word_count = meta.get("word_count", 0)
    scores["c1_word_count"] = 5 if word_count >= 300 else 0

    # C2 — Paragraphs (5 pts)
    p_count = meta.get("paragraph_count", 0)
    scores["c2_paragraphs"] = 5 if p_count >= 3 else 0

    total = sum(scores.values())
    return {"scores": scores, "total": min(total, 10), "max": 10}


def compute_technical_score(meta: dict) -> dict:
    """Compute the full per-page Technical Score (0–100)."""
    schema = score_schema(meta)
    metadata = score_metadata(meta)
    faq = score_faq(meta)
    content = score_content(meta)

    faq_max = faq["max"]
    total_max = 40 + 30 + faq_max + 10
    total_score = schema["total"] + metadata["total"] + faq["total"] + content["total"]

    # Normalize to 0–100 if FAQ is excluded (non-marketing page)
    if faq_max == 0:
        normalized = round((total_score / 80) * 100) if total_score > 0 else 0
    else:
        normalized = total_score

    # Rating
    if normalized >= 85:
        rating = "Excellent"
    elif normalized >= 70:
        rating = "Good"
    elif normalized >= 50:
        rating = "Needs Improvement"
    else:
        rating = "Poor"

    return {
        "url": meta.get("url", ""),
        "technical_score": normalized,
        "rating": rating,
        "dimensions": {
            "schema": schema,
            "metadata": metadata,
            "faq": faq,
            "content": content
        },
        "raw_total": total_score,
        "max_possible": total_max
    }


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"Invalid JSON input: {e}"}))
        sys.exit(1)

    result = compute_technical_score(data)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
