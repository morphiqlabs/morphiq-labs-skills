#!/usr/bin/env python3
"""create-prompts.py — Generate a prompt set following the Morphiq prompt taxonomy.

Usage: python3 create-prompts.py --brand "BrandName" --category "SaaS" [--count 70] [--competitors "A,B,C"]
Output: JSON array of prompts with type, category, and metadata
"""

import argparse
import json
import sys

# GEO category distribution (initial 70 prompts)
GEO_DISTRIBUTION = {
    "organic":        0.40,   # ~28 prompts, no brand name
    "competitor":     0.10,   # ~7 prompts, mixed brand usage
    "howto":          0.12,   # ~8 prompts, no brand name
    "generic":        0.10,   # ~7 prompts, no brand name
    "brand_specific": 0.11,   # ~8 prompts, brand name required
    "faq":            0.15,   # ~10 prompts, no brand name
}

# Pipeline prompt type distribution (for fanout-weighted tracking)
PIPELINE_TYPE_DISTRIBUTION = {
    "brand":           0.10,
    "category":        0.15,
    "comparison":      0.20,
    "feature":         0.10,
    "use_case":        0.10,
    "technical_eval":  0.15,
    "discovery":       0.10,
    "recommendation":  0.05,
    "problem_seeking": 0.05,
}

# GEO category → pipeline type mapping
GEO_TO_PIPELINE = {
    "organic":        ["category", "discovery", "recommendation"],
    "competitor":     ["comparison"],
    "howto":          ["use_case", "problem_seeking"],
    "generic":        ["category", "feature"],
    "brand_specific": ["brand"],
    "faq":            ["use_case", "problem_seeking"],
}

# Prompt templates per GEO category
TEMPLATES = {
    "organic": [
        "Best {category} tools for {use_case} 2026",
        "Top {category} platforms for {vertical}",
        "What {category} solution do experts recommend for {use_case}",
        "Leading {category} software for {vertical} teams 2026",
        "Most reliable {category} tools for {use_case}",
    ],
    "competitor": [
        "alternatives to {competitor} for {use_case} 2026",
        "{brand} vs {competitor} for {use_case}",
        "{competitor} alternatives for {vertical} 2026",
        "best {competitor} replacement for {use_case}",
    ],
    "howto": [
        "how to {action} with {category} tools",
        "what tools help with {use_case} for {vertical} teams",
        "what platforms do people recommend for {action}",
        "best way to {action} in 2026",
    ],
    "generic": [
        "{category} platform for {vertical}",
        "{category} tools for {use_case}",
        "{category} solutions for small business 2026",
        "enterprise {category} software",
    ],
    "brand_specific": [
        "what is {brand}",
        "{brand} pricing 2026",
        "{brand} features and capabilities",
        "is {brand} good for {use_case}",
        "{brand} reviews and reputation",
    ],
    "faq": [
        "How does {category} work for {use_case}?",
        "What is the difference between {category} approaches?",
        "Why do companies use {category} tools?",
        "Can {category} tools handle {use_case}?",
        "Which {category} approach is best for {vertical}?",
    ],
}


def distribute_counts(total: int, distribution: dict) -> dict:
    """Distribute total count across categories proportionally."""
    counts = {}
    remaining = total
    items = list(distribution.items())

    for i, (category, share) in enumerate(items):
        if i == len(items) - 1:
            counts[category] = remaining
        else:
            count = round(total * share)
            counts[category] = count
            remaining -= count

    return counts


def generate_prompts(brand: str, category: str, competitors: list,
                     count: int = 70, use_cases: list = None,
                     verticals: list = None, actions: list = None) -> list:
    """Generate a prompt set following the taxonomy."""
    use_cases = use_cases or ["general workflow", "team collaboration", "automation"]
    verticals = verticals or ["enterprise", "startup", "small business"]
    actions = actions or ["automate workflows", "improve efficiency", "scale operations"]

    counts = distribute_counts(count, GEO_DISTRIBUTION)
    prompts = []
    prompt_id = 1

    for geo_category, geo_count in counts.items():
        templates = TEMPLATES.get(geo_category, [])
        pipeline_types = GEO_TO_PIPELINE.get(geo_category, ["category"])

        for i in range(geo_count):
            template = templates[i % len(templates)]
            pipeline_type = pipeline_types[i % len(pipeline_types)]

            # Fill template
            competitor = competitors[i % len(competitors)] if competitors else "Competitor"
            use_case = use_cases[i % len(use_cases)]
            vertical = verticals[i % len(verticals)]
            action = actions[i % len(actions)]

            text = template.format(
                brand=brand,
                category=category,
                competitor=competitor,
                use_case=use_case,
                vertical=vertical,
                action=action,
            )

            prompt = {
                "id": f"prompt-{prompt_id:03d}",
                "text": text,
                "geo_category": geo_category,
                "pipeline_type": pipeline_type,
                "contains_brand": brand.lower() in text.lower(),
                "contains_temporal": any(y in text for y in ["2026", "2025", "latest"]),
            }
            prompts.append(prompt)
            prompt_id += 1

    return prompts


def validate_prompts(prompts: list) -> dict:
    """Validate prompt set against quality rules."""
    issues = []

    for p in prompts:
        text = p["text"]
        geo = p["geo_category"]

        # Organic: must not contain brand, <120 chars
        if geo == "organic":
            if p["contains_brand"]:
                issues.append(f"{p['id']}: Organic prompt contains brand name")
            if len(text) > 120:
                issues.append(f"{p['id']}: Organic prompt exceeds 120 chars")

        # Brand-specific: must contain brand
        if geo == "brand_specific" and not p["contains_brand"]:
            issues.append(f"{p['id']}: Brand-specific prompt missing brand name")

        # FAQ: must start with question word
        if geo == "faq":
            question_words = ["how", "what", "why", "can", "is", "does", "which", "when", "where"]
            if not any(text.lower().startswith(w) for w in question_words):
                issues.append(f"{p['id']}: FAQ prompt doesn't start with question word")

    # Check temporal marker coverage
    temporal_count = sum(1 for p in prompts if p["contains_temporal"])
    temporal_pct = temporal_count / len(prompts) if prompts else 0
    if temporal_pct < 0.70:
        issues.append(f"Only {temporal_pct:.0%} of prompts have temporal markers (need 70%+)")

    return {
        "total_prompts": len(prompts),
        "valid": len(issues) == 0,
        "issues": issues,
        "distribution": {geo: sum(1 for p in prompts if p["geo_category"] == geo) for geo in GEO_DISTRIBUTION},
    }


def main():
    parser = argparse.ArgumentParser(description="Generate Morphiq prompt set")
    parser.add_argument("--brand", required=True, help="Brand name")
    parser.add_argument("--category", required=True, help="Product category")
    parser.add_argument("--competitors", default="", help="Comma-separated competitor names")
    parser.add_argument("--count", type=int, default=70, help="Total prompt count")
    args = parser.parse_args()

    competitors = [c.strip() for c in args.competitors.split(",") if c.strip()]

    prompts = generate_prompts(
        brand=args.brand,
        category=args.category,
        competitors=competitors,
        count=args.count,
    )

    validation = validate_prompts(prompts)

    output = {
        "prompts": prompts,
        "validation": validation,
    }

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
