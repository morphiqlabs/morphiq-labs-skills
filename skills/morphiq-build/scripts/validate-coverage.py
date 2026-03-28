#!/usr/bin/env python3
"""validate-coverage.py — Step 6: Validate fanout coverage of generated content.

Checks whether generated content addresses all triggering sub-queries and meets
the competitive quality floor established in Step 4.

Usage:
  echo '{"content": "...", "sub_queries": [...], "quality_floor": {...}}' | python3 validate-coverage.py

Input (stdin JSON):
  - content: Generated markdown content from Step 5
  - sub_queries: Array of triggering sub-query objects from fanout_context
  - quality_floor: Quality floor object from Step 4 competitive analysis (optional)

Output (stdout): JSON validation report with coverage details and action decision.
"""

import json
import re
import sys


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

STOP_WORDS = frozenset([
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "it", "its", "this", "that",
    "what", "which", "who", "how", "when", "where", "why", "not", "no",
    "so", "if", "then", "than", "too", "very", "just", "about",
])

# Pattern: name-drop citation — "[Source Name](url)" preceded by attribution word
STAT_PATTERN = re.compile(
    r"(?:according to|research from|data from|per|study by|report by|survey by|analysis by)"
    r".*?\[.+?\]\(.+?\).*?\d",
    re.IGNORECASE,
)

# Simpler pattern: any sentence with a number + a markdown link
STAT_SIMPLE_PATTERN = re.compile(
    r"\d[\d,.]*%?\s.*?\[.+?\]\(.+?\)",
    re.IGNORECASE,
)

# Expert quote patterns: name + credential + quote (multiple formats)
QUOTE_PATTERNS = [
    # "As Dr. Jane Smith, VP at Acme, explains: "quote""
    re.compile(
        r'(?:as|says|explains|notes|according to)\s+[\w\s.]{3,40},\s+[\w\s]{3,30}(?:at|of|for)\s+[\w\s]{3,30},'
        r'\s*(?:says|explains|notes|argues|observes|adds|states|warns|suggests)[:\s]*["\u201c]',
        re.IGNORECASE,
    ),
    # "As Dr. Jane Smith, VP at Acme: "quote""
    re.compile(
        r'(?:as|says|explains|notes|according to)\s+[\w\s.]{3,40},\s+[\w\s]{3,30}(?:at|of|for)\s+[\w\s]{3,30}[,:]?\s*["\u201c]',
        re.IGNORECASE,
    ),
    # "Dr. Jane Smith, VP at Acme, explains: "quote"" (no leading verb)
    re.compile(
        r'(?:Dr\.|Mr\.|Ms\.|Prof\.)?\s*\w[\w\s.]{2,30},\s+\w[\w\s]{2,25}(?:at|of|for)\s+\w[\w\s]{2,25},\s*'
        r'(?:says|explains|notes|argues|observes|adds|states|warns|suggests)[:\s]*["\u201c]',
        re.IGNORECASE,
    ),
]


# ---------------------------------------------------------------------------
# Section extraction
# ---------------------------------------------------------------------------

def extract_sections(markdown):
    """Parse markdown into sections by headings.

    Returns list of dicts with heading_level, heading_text, content, word_count.
    """
    lines = markdown.split("\n")
    sections = []
    current_heading = None
    current_level = 0
    current_lines = []

    for line in lines:
        heading_match = re.match(r"^(#{1,6})\s+(.+)$", line)
        if heading_match:
            # Save previous section
            if current_heading is not None:
                content = "\n".join(current_lines).strip()
                sections.append({
                    "heading_level": current_level,
                    "heading_text": current_heading,
                    "content": content,
                    "word_count": len(content.split()),
                })
            current_level = len(heading_match.group(1))
            current_heading = heading_match.group(2).strip()
            current_lines = []
        else:
            current_lines.append(line)

    # Save last section
    if current_heading is not None:
        content = "\n".join(current_lines).strip()
        sections.append({
            "heading_level": current_level,
            "heading_text": current_heading,
            "content": content,
            "word_count": len(content.split()),
        })

    return sections


# ---------------------------------------------------------------------------
# Sub-query matching
# ---------------------------------------------------------------------------

def tokenize(text):
    """Extract meaningful tokens from text, excluding stop words."""
    tokens = set()
    for word in re.split(r"\W+", text):
        w = word.lower().strip()
        if w and w not in STOP_WORDS and len(w) > 2:
            tokens.add(w)
    return tokens


def match_query_to_section(sub_query_text, sections):
    """Fuzzy match a sub-query against section headings and content.

    Returns (best_section, confidence_score) where confidence_score is 0-1.
    """
    query_tokens = tokenize(sub_query_text)
    # Strip site: prefix for matching
    cleaned = re.sub(r"site:\S+\s*", "", sub_query_text)
    cleaned = re.sub(r"\b\d{4}\b", "", cleaned)  # remove year markers
    query_tokens_cleaned = tokenize(cleaned)

    if not query_tokens_cleaned:
        return None, 0.0

    best_section = None
    best_score = 0.0

    for section in sections:
        if section["heading_level"] > 4:
            continue

        heading_tokens = tokenize(section["heading_text"])
        content_tokens = tokenize(section["content"][:500])
        combined_tokens = heading_tokens | content_tokens

        # Heading match is weighted higher
        heading_overlap = len(query_tokens_cleaned & heading_tokens)
        content_overlap = len(query_tokens_cleaned & combined_tokens)

        heading_score = heading_overlap / len(query_tokens_cleaned) if query_tokens_cleaned else 0
        content_score = content_overlap / len(query_tokens_cleaned) if query_tokens_cleaned else 0

        # Combined: heading match counts double
        score = (heading_score * 0.6) + (content_score * 0.4)

        if score > best_score:
            best_score = score
            best_section = section

    return best_section, best_score


def check_direct_answer(section, sub_query_text):
    """Check if a section contains a substantive answer (not just a mention)."""
    if not section:
        return False
    # Must have at least 50 words
    if section["word_count"] < 50:
        return False
    # Must contain some key terms from the query
    query_tokens = tokenize(re.sub(r"site:\S+\s*", "", sub_query_text))
    content_tokens = tokenize(section["content"][:1000])
    overlap = len(query_tokens & content_tokens)
    return overlap >= max(1, len(query_tokens) * 0.3)


# ---------------------------------------------------------------------------
# Quality floor checking
# ---------------------------------------------------------------------------

def count_statistics(markdown):
    """Count statistics with source attribution in the content.

    Uses the stricter STAT_PATTERN (attribution phrase + link + number) as primary.
    Falls back to STAT_SIMPLE_PATTERN only if primary finds nothing.
    """
    primary = len(STAT_PATTERN.findall(markdown))
    if primary > 0:
        return primary
    return len(STAT_SIMPLE_PATTERN.findall(markdown))


def count_expert_quotes(markdown):
    """Count expert quotes with in-text attribution."""
    count = 0
    for line in markdown.split("\n"):
        for pattern in QUOTE_PATTERNS:
            if pattern.search(line):
                count += 1
                break  # count each line at most once
    return count


def count_sections(sections):
    """Count H2 and H3 sections."""
    return sum(1 for s in sections if s["heading_level"] in (2, 3))


def check_quality_floor(markdown, sections, quality_floor):
    """Check content against the competitive quality floor."""
    if not quality_floor:
        return True, {}

    stats_found = count_statistics(markdown)
    quotes_found = count_expert_quotes(markdown)
    sections_found = count_sections(sections)

    min_stats = quality_floor.get("min_statistics", 3)
    min_quotes = quality_floor.get("min_expert_quotes", 1)
    min_sections = quality_floor.get("min_sections", 5)

    details = {
        "statistics": {
            "required": min_stats,
            "found": stats_found,
            "met": stats_found >= min_stats,
        },
        "expert_quotes": {
            "required": min_quotes,
            "found": quotes_found,
            "met": quotes_found >= min_quotes,
        },
        "sections": {
            "required": min_sections,
            "found": sections_found,
            "met": sections_found >= min_sections,
        },
    }

    all_met = all(d["met"] for d in details.values())
    return all_met, details


# ---------------------------------------------------------------------------
# Revision instruction generation
# ---------------------------------------------------------------------------

def generate_revision_instructions(missing_queries, unmet_floor):
    """Create specific additive instructions for Step 5 revision."""
    instructions = []

    for mq in missing_queries:
        instructions.append(
            f"Add a dedicated H2 or H3 section addressing: \"{mq['sub_query']}\". "
            f"Include at least 50 words with a direct answer."
        )

    if unmet_floor:
        for metric, detail in unmet_floor.items():
            if not detail.get("met", True):
                gap = detail["required"] - detail["found"]
                instructions.append(
                    f"Add {gap} more {metric.replace('_', ' ')} "
                    f"(have {detail['found']}, need {detail['required']})."
                )

    return instructions


# ---------------------------------------------------------------------------
# Main validation
# ---------------------------------------------------------------------------

def validate_coverage(content, sub_queries, quality_floor=None):
    """Run full coverage validation on generated content."""
    sections = extract_sections(content)

    details = []
    addressed = 0
    missing_queries = []

    for sq in sub_queries:
        query_text = sq if isinstance(sq, str) else sq.get("query", "")
        citation_weight = sq.get("citation_weight", "silent") if isinstance(sq, dict) else "silent"

        best_section, score = match_query_to_section(query_text, sections)
        has_answer = check_direct_answer(best_section, query_text)

        if score >= 0.4 and has_answer:
            addressed += 1
            details.append({
                "sub_query": query_text,
                "citation_weight": citation_weight,
                "status": "addressed",
                "matched_section": best_section["heading_text"] if best_section else None,
                "has_direct_answer": True,
            })
        else:
            missing_queries.append({"sub_query": query_text, "citation_weight": citation_weight})
            suggestion = f"Add a section addressing: {query_text}"
            if best_section and score >= 0.2:
                suggestion = (
                    f"Expand section \"{best_section['heading_text']}\" to address "
                    f"\"{query_text}\" with a substantive answer"
                )
            details.append({
                "sub_query": query_text,
                "citation_weight": citation_weight,
                "status": "missing",
                "matched_section": best_section["heading_text"] if best_section else None,
                "suggestion": suggestion,
            })

    total = len(sub_queries)
    coverage_pct = (addressed / total * 100) if total > 0 else 100

    floor_met, floor_details = check_quality_floor(content, sections, quality_floor)

    # Decision logic: quality floor failure always triggers revise
    if not floor_met:
        action = "revise"
    elif coverage_pct >= 100:
        action = "pass"
    elif coverage_pct >= 80:
        action = "pass_with_warnings"
    else:
        action = "revise"

    result = {
        "validation": {
            "total_sub_queries": total,
            "addressed": addressed,
            "missing": total - addressed,
            "coverage_pct": round(coverage_pct, 1),
            "details": details,
            "quality_floor_met": floor_met,
            "quality_floor_details": floor_details if quality_floor else {},
            "action": action,
        }
    }

    if action == "revise":
        unmet = {k: v for k, v in floor_details.items() if not v.get("met", True)} if floor_details else {}
        result["revision_instructions"] = generate_revision_instructions(missing_queries, unmet)

    return result


def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"Invalid JSON input: {e}"}), file=sys.stderr)
        sys.exit(1)

    content = input_data.get("content", "")
    sub_queries = input_data.get("sub_queries", [])
    quality_floor = input_data.get("quality_floor", None)

    if not content:
        print(json.dumps({"error": "No content provided"}), file=sys.stderr)
        sys.exit(1)

    if not sub_queries:
        print(json.dumps({
            "validation": {
                "total_sub_queries": 0,
                "addressed": 0,
                "missing": 0,
                "coverage_pct": 100,
                "details": [],
                "quality_floor_met": True,
                "quality_floor_details": {},
                "action": "pass",
            }
        }))
        sys.exit(0)

    result = validate_coverage(content, sub_queries, quality_floor)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
