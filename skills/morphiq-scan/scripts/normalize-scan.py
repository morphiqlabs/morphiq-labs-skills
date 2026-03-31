"""
normalize-scan.py — Post-processing normalizer for MORPHIQ-SCAN.json

Reads whatever JSON structure morphiq-scan produced and transforms it
into the exact pipeline-compliant schema that morphiq-rank expects.

Usage:
    python normalize-scan.py [path-to-scan-json]

If no path given, reads MORPHIQ-SCAN.json from the current directory.
Writes the normalized output back to the same file.
"""

import json
import sys
import os
from datetime import datetime, timezone


# --- Valid issue IDs (closed set from issue-catalog.md) ---
VALID_ISSUE_IDS = {
    # policy_files
    "policy-no-llms-txt", "policy-weak-llms-txt", "policy-blocks-gptbot",
    "policy-blocks-google-extended", "policy-blocks-anthropic",
    "policy-blocks-perplexity", "policy-no-robots-txt", "policy-invalid-robots-syntax",
    # agentic_readiness
    "agentic-missing-product-schema", "agentic-missing-organization-schema",
    "agentic-missing-article-schema", "agentic-missing-faq-schema",
    "agentic-missing-howto-schema", "agentic-missing-breadcrumb",
    "agentic-no-canonical", "agentic-broken-heading-hierarchy",
    "agentic-weak-meta-description", "agentic-missing-og-tags",
    "agentic-no-semantic-html", "agentic-duplicate-schema",
    # content_quality
    "content-thin-page", "content-low-word-count", "content-no-tldr",
    "content-no-author", "content-unsourced-stats", "content-wrong-citation-format",
    "content-no-expert-quotes", "content-stale-date", "content-thin-faq",
    "content-no-examples", "content-generic-advice", "content-fabricated-examples",
    # chunking_retrieval
    "chunking-broken-heading-hierarchy", "chunking-generic-headings",
    "chunking-overscoped-section", "chunking-buried-answer",
    "chunking-long-paragraphs", "chunking-no-faq-coverage",
    "chunking-no-top-summary", "chunking-missing-query-terms",
    "chunking-weak-local-context", "chunking-poor-paragraph-structure",
    "chunking-prose-instead-of-list", "chunking-unparseable-table",
    "chunking-ambiguous-paragraphs", "chunking-split-supporting-evidence",
    # query_fanout
    "fanout-no-comparison-content", "fanout-no-pricing-content",
    "fanout-no-alternative-content", "fanout-missing-entity-coverage",
    "fanout-wrong-page-type", "fanout-no-site-match", "fanout-stale-temporal",
    "fanout-unanswered-subquery", "fanout-thin-topic-coverage",
    "fanout-no-docs-content",
}

# Category prefixes for ID inference
CATEGORY_FROM_PREFIX = {
    "policy": "policy_files",
    "agentic": "agentic_readiness",
    "content": "content_quality",
    "chunking": "chunking_retrieval",
    "fanout": "query_fanout",
    "visibility": "ai_visibility",
}

VALID_SEVERITIES = {"critical", "high", "medium", "low"}

VALID_PAGE_TYPES = {
    "homepage", "product", "pricing", "blog", "about", "contact",
    "docs", "landing", "comparison", "case-study", "careers", "legal",
    "other", "home", "features", "solutions", "documentation",
}

VALID_PROMPT_TYPES = {
    "brand", "category", "comparison", "discovery", "recommendation",
    "technical_eval", "problem_seeking", "use_case",
}

SCORES_MAX = {
    "agentic_readiness": 45,
    "content_quality": 20,
    "chunking_retrieval": 15,
    "query_fanout": 10,
    "policy_files": 10,
}

# --- Key mapping: common wrong keys → correct keys ---
KEY_ALIASES = {
    # Top-level
    "scan_metadata": None,  # flatten into top-level
    "executive_summary": None,  # discard
    "category_scores": "scores",
    "pages_analyzed": "pages",
    "pages_audited": "pages",
    "critical_findings": None,  # discard
    "recommendations": None,  # discard
    "recommendations_by_category": None,
    "recommendations_priority_order": None,
    "scan_insights": None,
    "next_steps": None,
    "opportunities": None,
    "domain_summary": None,
    "overall_score_breakdown": "scores",
    "scoring_breakdown": "scores",
    # Issue-level
    "issue_id": "id",
    "remediation": "remediation_hint",
    "fix": "remediation_hint",
    "recommendation": "remediation_hint",
    # Score-level
    "score_breakdown": "scores",
}

# Score key aliases (model uses various names for score categories)
SCORE_KEY_ALIASES = {
    "agentic_readiness": "agentic_readiness",
    "agentic": "agentic_readiness",
    "content_quality": "content_quality",
    "content": "content_quality",
    "chunking_retrieval": "chunking_retrieval",
    "chunking": "chunking_retrieval",
    "retrieval": "chunking_retrieval",
    "query_fanout": "query_fanout",
    "fanout": "query_fanout",
    "policy_files": "policy_files",
    "policy": "policy_files",
}


def find_value(data, *keys):
    """Search for a value using multiple possible key names."""
    if not isinstance(data, dict):
        return None
    for key in keys:
        if key in data:
            return data[key]
    return None


def infer_category(issue_id):
    """Infer category from issue ID prefix."""
    if not issue_id or not isinstance(issue_id, str):
        return "agentic_readiness"
    prefix = issue_id.split("-")[0] if "-" in issue_id else ""
    return CATEGORY_FROM_PREFIX.get(prefix, "agentic_readiness")


def fuzzy_match_issue_id(raw_id):
    """Try to match a raw issue ID to a valid one."""
    if not raw_id or not isinstance(raw_id, str):
        return None

    # Direct match
    normalized = raw_id.lower().strip()
    if normalized in VALID_ISSUE_IDS:
        return normalized

    # Try replacing underscores with hyphens
    hyphenated = normalized.replace("_", "-")
    if hyphenated in VALID_ISSUE_IDS:
        return hyphenated

    # Try partial match — find the closest valid ID
    for valid_id in VALID_ISSUE_IDS:
        # Check if the raw ID contains the essential part
        parts = valid_id.split("-", 1)
        if len(parts) == 2 and parts[1] in normalized:
            return valid_id

    return None


def normalize_issue(raw_issue):
    """Normalize a single issue object."""
    if not isinstance(raw_issue, dict):
        return None

    # Get issue ID
    raw_id = find_value(raw_issue, "id", "issue_id", "issueId", "issue")
    if raw_id:
        issue_id = fuzzy_match_issue_id(raw_id) or raw_id
    else:
        return None

    category = find_value(raw_issue, "category", "type", "group")
    if not category:
        category = infer_category(issue_id)
    # Normalize category name
    category = SCORE_KEY_ALIASES.get(category, category) if category else infer_category(issue_id)

    severity = find_value(raw_issue, "severity", "level", "priority")
    if severity and isinstance(severity, str):
        severity = severity.lower()
    if severity not in VALID_SEVERITIES:
        severity = "medium"

    return {
        "id": issue_id,
        "category": category,
        "severity": severity,
        "summary": find_value(raw_issue, "summary", "title", "name", "description") or "",
        "detail": find_value(raw_issue, "detail", "details", "explanation", "message") or "",
        "affected_element": find_value(raw_issue, "affected_element", "element", "selector"),
        "remediation_hint": find_value(
            raw_issue, "remediation_hint", "remediation", "fix", "recommendation", "action"
        ) or "",
    }


def extract_scores(data):
    """Extract category scores from various possible structures."""
    scores = {}

    # Direct scores object
    raw_scores = find_value(data, "scores", "category_scores", "scoring_breakdown",
                            "overall_score_breakdown", "score_breakdown")

    if isinstance(raw_scores, dict):
        for key, val in raw_scores.items():
            normalized_key = SCORE_KEY_ALIASES.get(key.lower().replace(" ", "_"))
            if normalized_key and isinstance(val, (int, float)):
                scores[normalized_key] = int(val)
            elif normalized_key and isinstance(val, dict):
                # Nested object like {score: 12, max: 45}
                score_val = find_value(val, "score", "value", "points", "earned")
                if isinstance(score_val, (int, float)):
                    scores[normalized_key] = int(score_val)
            elif isinstance(val, (int, float)):
                # Try to match by cleaning the key
                clean_key = key.lower().replace(" ", "_").replace("-", "_")
                # Remove common prefixes like "category_1_"
                for prefix in ["category_1_", "category_2_", "category_3_", "category_4_", "category_5_"]:
                    if clean_key.startswith(prefix):
                        clean_key = clean_key[len(prefix):]
                normalized = SCORE_KEY_ALIASES.get(clean_key)
                if normalized:
                    scores[normalized] = int(val)

    # Fill missing scores with 0
    for cat in SCORES_MAX:
        if cat not in scores:
            scores[cat] = 0

    # Clamp scores to max
    for cat in SCORES_MAX:
        scores[cat] = min(scores[cat], SCORES_MAX[cat])

    return scores


def extract_pages(data):
    """Extract pages array from various possible structures."""
    raw_pages = find_value(data, "pages", "pages_analyzed", "pages_audited",
                           "page_results", "page_scores", "audited_pages")

    if not isinstance(raw_pages, list):
        return []

    normalized_pages = []
    for raw_page in raw_pages:
        if not isinstance(raw_page, dict):
            continue

        url = find_value(raw_page, "url", "page_url", "link", "href") or ""
        page_type = find_value(raw_page, "page_type", "type", "pageType") or "other"
        if page_type not in VALID_PAGE_TYPES:
            page_type = "other"

        title = find_value(raw_page, "title", "page_title", "name") or ""
        score = find_value(raw_page, "score", "page_score", "total_score") or 0
        if isinstance(score, (int, float)):
            score = max(0, min(100, int(score)))
        else:
            score = 0

        # Extract issues
        raw_issues = find_value(raw_page, "issues", "findings", "problems", "errors") or []
        issues = []
        for raw_issue in raw_issues:
            normalized = normalize_issue(raw_issue)
            if normalized:
                issues.append(normalized)

        # Extract schema info
        schema_detected = find_value(raw_page, "schema_detected", "schemas_found",
                                     "detected_schemas", "schemas") or []
        schema_missing = find_value(raw_page, "schema_missing", "missing_schemas",
                                    "schemas_missing", "expected_schemas") or []

        if not isinstance(schema_detected, list):
            schema_detected = []
        if not isinstance(schema_missing, list):
            schema_missing = []

        # Extract meta
        raw_meta = find_value(raw_page, "meta", "metadata", "page_meta") or {}
        if not isinstance(raw_meta, dict):
            raw_meta = {}

        meta = {
            "title_length": find_value(raw_meta, "title_length", "titleLength") or 0,
            "description_length": find_value(raw_meta, "description_length", "descriptionLength", "meta_description_length") or 0,
            "og_image": bool(find_value(raw_meta, "og_image", "ogImage", "has_og_image")),
            "canonical": find_value(raw_meta, "canonical", "canonical_url", "canonicalUrl"),
            "h1_count": find_value(raw_meta, "h1_count", "h1Count", "h1_tags") or 0,
            "heading_hierarchy_valid": bool(find_value(raw_meta, "heading_hierarchy_valid", "headingHierarchyValid", "valid_hierarchy")),
            "word_count": find_value(raw_meta, "word_count", "wordCount", "words") or 0,
        }

        normalized_pages.append({
            "url": url,
            "page_type": page_type,
            "title": title,
            "score": score,
            "issues": issues,
            "schema_detected": schema_detected,
            "schema_missing": schema_missing,
            "meta": meta,
        })

    return normalized_pages


def extract_policy_files(data):
    """Extract policy_files section."""
    raw = find_value(data, "policy_files", "policies", "policy")

    if isinstance(raw, dict) and ("robots_txt" in raw or "llms_txt" in raw):
        # Already in correct shape, just ensure all fields exist
        robots = raw.get("robots_txt", {})
        llms = raw.get("llms_txt", {})
    else:
        robots = {}
        llms = {}

    # Normalize robots_txt
    robots_issues = robots.get("issues", [])
    normalized_robots_issues = []
    for issue in robots_issues:
        n = normalize_issue(issue)
        if n:
            normalized_robots_issues.append(n)

    # Normalize llms_txt
    llms_issues = llms.get("issues", [])
    normalized_llms_issues = []
    for issue in llms_issues:
        n = normalize_issue(issue)
        if n:
            normalized_llms_issues.append(n)

    return {
        "robots_txt": {
            "exists": bool(robots.get("exists", False)),
            "allows_ai_crawlers": bool(robots.get("allows_ai_crawlers", False)),
            "blocked_agents": robots.get("blocked_agents", []),
            "issues": normalized_robots_issues,
        },
        "llms_txt": {
            "exists": bool(llms.get("exists", False)),
            "valid": bool(llms.get("valid", False)),
            "issues": normalized_llms_issues,
        },
    }


def extract_query_fanout(data):
    """Extract query_fanout section."""
    raw = find_value(data, "query_fanout", "fanout", "query_coverage")

    if not isinstance(raw, dict):
        return {
            "simulated_queries": [],
            "fanout_depth": {"total_subqueries": 0, "by_model": {}, "by_prompt_type": {}},
            "coverage_score": 0,
            "gaps": [],
            "suggested_content": [],
        }

    # Normalize simulated_queries
    raw_queries = raw.get("simulated_queries", [])
    queries = []
    for q in raw_queries:
        if not isinstance(q, dict):
            continue
        query_text = find_value(q, "query", "text", "question") or ""
        model = find_value(q, "model", "model_origin", "source") or "all"
        prompt_type = find_value(q, "prompt_type", "type", "promptType") or "brand"
        citation_weight = find_value(q, "citation_weight", "weight", "citationWeight") or "silent"
        page_type_source = find_value(q, "page_type_source", "pageType", "target_page")

        queries.append({
            "query": query_text,
            "model": model,
            "prompt_type": prompt_type,
            "citation_weight": citation_weight,
            "page_type_source": page_type_source,
        })

    # Normalize fanout_depth
    raw_depth = raw.get("fanout_depth", {})
    if not isinstance(raw_depth, dict):
        raw_depth = {}

    fanout_depth = {
        "total_subqueries": raw_depth.get("total_subqueries", len(queries)),
        "by_model": raw_depth.get("by_model", {}),
        "by_prompt_type": raw_depth.get("by_prompt_type", {}),
    }

    # Normalize suggested_content
    raw_suggestions = raw.get("suggested_content", [])
    suggestions = []
    for s in raw_suggestions:
        if not isinstance(s, dict):
            continue
        suggestions.append({
            "query": find_value(s, "query", "text", "question") or "",
            "model_origin": find_value(s, "model_origin", "model", "source") or "all",
            "prompt_type": find_value(s, "prompt_type", "type") or "brand",
            "suggestion": find_value(s, "suggestion", "recommendation", "action") or "",
            "rationale": find_value(s, "rationale", "reason", "why") or "",
        })

    return {
        "simulated_queries": queries,
        "fanout_depth": fanout_depth,
        "coverage_score": raw.get("coverage_score", 0),
        "gaps": raw.get("gaps", []),
        "suggested_content": suggestions,
    }


def collect_orphan_issues(data, already_assigned):
    """Find issues in flat top-level arrays that weren't assigned to pages."""
    orphans = []
    for key in ["issues", "findings", "critical_findings", "all_issues",
                 "issues_detected", "critical_issues"]:
        raw = data.get(key, [])
        if isinstance(raw, list):
            for item in raw:
                if isinstance(item, dict):
                    n = normalize_issue(item)
                    if n and n["id"] not in already_assigned:
                        orphans.append(n)
    return orphans


def normalize_scan(data):
    """Main normalization: transform any scan output into the correct schema."""
    # Handle nested scan_metadata
    metadata = data.get("scan_metadata", {})
    if isinstance(metadata, dict):
        # Pull fields up from scan_metadata
        for key in ["domain", "generated_at", "pages_scanned", "overall_score"]:
            if key not in data and key in metadata:
                data[key] = metadata[key]

    # Extract domain
    domain = find_value(data, "domain", "site", "url", "target", "website") or ""
    if domain.startswith("http"):
        # Extract domain from URL
        from urllib.parse import urlparse
        domain = urlparse(domain).netloc or domain

    # Extract overall score
    overall_score = find_value(data, "overall_score", "total_score", "score", "aggregate_score") or 0
    if isinstance(overall_score, (int, float)):
        overall_score = max(0, min(100, int(overall_score)))
    else:
        overall_score = 0

    # Extract pages
    pages = extract_pages(data)
    pages_scanned = find_value(data, "pages_scanned", "total_pages", "page_count") or len(pages)

    # Extract scores
    scores = extract_scores(data)

    # If overall_score is 0 but we have scores, compute it
    if overall_score == 0 and any(v > 0 for v in scores.values()):
        overall_score = sum(scores.values())

    # Extract policy and fanout
    policy_files = extract_policy_files(data)
    query_fanout = extract_query_fanout(data)

    # Collect orphan issues (flat arrays) and assign to pages
    assigned_ids = set()
    for page in pages:
        for issue in page.get("issues", []):
            assigned_ids.add(issue["id"])
    for issue in policy_files["robots_txt"]["issues"]:
        assigned_ids.add(issue["id"])
    for issue in policy_files["llms_txt"]["issues"]:
        assigned_ids.add(issue["id"])

    orphans = collect_orphan_issues(data, assigned_ids)
    if orphans and pages:
        # Assign orphan issues to pages by URL match or first page
        for orphan in orphans:
            # Policy issues go to policy section
            if orphan["id"].startswith("policy-"):
                if "llms" in orphan["id"]:
                    policy_files["llms_txt"]["issues"].append(orphan)
                else:
                    policy_files["robots_txt"]["issues"].append(orphan)
            else:
                # Assign to first page (homepage) as fallback
                pages[0]["issues"].append(orphan)

    # Extract generated_at
    generated_at = find_value(data, "generated_at", "timestamp", "date", "created_at")
    if not generated_at:
        generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    return {
        "schema_version": data.get("schema_version", "1.0"),
        "generated_at": generated_at,
        "domain": domain,
        "pages_scanned": int(pages_scanned),
        "overall_score": overall_score,
        "scores": scores,
        "scores_max": dict(SCORES_MAX),
        "pages": pages,
        "policy_files": policy_files,
        "query_fanout": query_fanout,
    }


def validate(result):
    """Validate the normalized output and print warnings."""
    warnings = []

    required_top = ["schema_version", "generated_at", "domain", "pages_scanned",
                    "overall_score", "scores", "scores_max", "pages",
                    "policy_files", "query_fanout"]
    for key in required_top:
        if key not in result:
            warnings.append(f"Missing top-level key: {key}")

    if not result.get("pages"):
        warnings.append("No pages found — pages array is empty")

    # Check issue IDs
    invalid_ids = []
    for page in result.get("pages", []):
        for issue in page.get("issues", []):
            if issue["id"] not in VALID_ISSUE_IDS:
                invalid_ids.append(issue["id"])

    for section in ["robots_txt", "llms_txt"]:
        for issue in result.get("policy_files", {}).get(section, {}).get("issues", []):
            if issue["id"] not in VALID_ISSUE_IDS:
                invalid_ids.append(issue["id"])

    if invalid_ids:
        warnings.append(f"Invalid issue IDs (not in catalog): {invalid_ids}")

    # Check score totals
    score_sum = sum(result.get("scores", {}).values())
    overall = result.get("overall_score", 0)
    if score_sum > 0 and abs(score_sum - overall) > 2:
        warnings.append(f"Score mismatch: sum({score_sum}) != overall({overall})")

    return warnings


def main():
    # Determine file path
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
    else:
        filepath = "MORPHIQ-SCAN.json"

    if not os.path.exists(filepath):
        print(f"Error: {filepath} not found")
        sys.exit(1)

    # Read
    with open(filepath, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    print(f"Read {filepath} ({len(json.dumps(raw_data))} chars)")

    # Check if already compliant
    expected_keys = {"schema_version", "generated_at", "domain", "pages_scanned",
                     "overall_score", "scores", "scores_max", "pages",
                     "policy_files", "query_fanout"}
    actual_keys = set(raw_data.keys())
    if actual_keys == expected_keys:
        print("JSON already has correct top-level structure — validating...")
        warnings = validate(raw_data)
        if warnings:
            print(f"Validation warnings ({len(warnings)}):")
            for w in warnings:
                print(f"  - {w}")
        else:
            print("All checks passed — no normalization needed.")
        return

    print(f"Non-compliant structure detected. Keys found: {sorted(actual_keys)}")
    print(f"Expected keys: {sorted(expected_keys)}")
    print("Normalizing...")

    # Normalize
    result = normalize_scan(raw_data)

    # Validate
    warnings = validate(result)

    # Write
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    total_issues = sum(len(p.get("issues", [])) for p in result.get("pages", []))
    total_issues += len(result["policy_files"]["robots_txt"]["issues"])
    total_issues += len(result["policy_files"]["llms_txt"]["issues"])

    print(f"\nNormalized output written to {filepath}")
    print(f"  Domain: {result['domain']}")
    print(f"  Score: {result['overall_score']}/100")
    print(f"  Pages: {result['pages_scanned']}")
    print(f"  Issues: {total_issues}")
    print(f"  Scores: {result['scores']}")

    if warnings:
        print(f"\nWarnings ({len(warnings)}):")
        for w in warnings:
            print(f"  ⚠ {w}")
    else:
        print("\nAll validation checks passed.")


if __name__ == "__main__":
    main()
