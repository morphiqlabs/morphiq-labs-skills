# Scan Output Contract

This defines the exact JSON structure for `MORPHIQ-SCAN.json`. The downstream pipeline (morphiq-rank) depends on these exact keys and shapes.

## Top-Level Keys

```json
{
  "schema_version": "1.0",
  "generated_at": "ISO-8601 timestamp",
  "domain": "example.com",
  "pages_scanned": 12,
  "overall_score": 62,
  "scores": { ... },
  "scores_max": { ... },
  "pages": [ ... ],
  "policy_files": { ... },
  "query_fanout": { ... }
}
```

Only these top-level keys. Do not add `critical_findings`, `summary_and_recommendations`, or any other keys — they break the downstream pipeline.

## scores / scores_max

```json
"scores": {
  "agentic_readiness": 26,
  "content_quality": 14,
  "chunking_retrieval": 10,
  "query_fanout": 6,
  "policy_files": 6
},
"scores_max": {
  "agentic_readiness": 45,
  "content_quality": 20,
  "chunking_retrieval": 15,
  "query_fanout": 10,
  "policy_files": 10
}
```

## pages[]

Each page object:

```json
{
  "url": "https://example.com/product",
  "page_type": "product",
  "title": "Example Product",
  "score": 58,
  "issues": [ ... ],
  "schema_detected": ["Organization"],
  "schema_missing": ["Product", "FAQPage", "BreadcrumbList"],
  "meta": {
    "title_length": 42,
    "description_length": 148,
    "og_image": true,
    "canonical": "https://example.com/product",
    "h1_count": 1,
    "heading_hierarchy_valid": true,
    "word_count": 620
  }
}
```

## issues[]

Each issue object:

```json
{
  "id": "agentic-missing-product-schema",
  "category": "agentic_readiness",
  "severity": "high",
  "summary": "No Product schema detected",
  "detail": "This product page has no JSON-LD Product markup.",
  "affected_element": null,
  "remediation_hint": "Add Product schema with name, description, offers"
}
```

## policy_files

```json
"policy_files": {
  "robots_txt": {
    "exists": true,
    "allows_ai_crawlers": false,
    "blocked_agents": ["GPTBot", "Google-Extended"],
    "issues": [ ... ]
  },
  "llms_txt": {
    "exists": false,
    "valid": false,
    "issues": [ ... ]
  }
}
```

## query_fanout

```json
"query_fanout": {
  "simulated_queries": [
    {
      "query": "Example Company pricing",
      "model": "gpt-5.4",
      "prompt_type": "category",
      "citation_weight": "citation_producing",
      "page_type_source": "pricing"
    }
  ],
  "fanout_depth": {
    "total_subqueries": 12,
    "by_model": { "gpt-5.4": 5, "claude": 2, "gemini": 5 },
    "by_prompt_type": { "brand": 2, "category": 4, "comparison": 6 }
  },
  "coverage_score": 6,
  "gaps": [ "No pricing page found" ],
  "suggested_content": [
    {
      "query": "Example Company vs competitors",
      "model_origin": "all",
      "prompt_type": "comparison",
      "suggestion": "Create a comparison page",
      "rationale": "LLMs chain comparison queries — no content exists"
    }
  ]
}
```

## Issue IDs — Closed Set

Use ONLY these IDs. Do not invent IDs like `J001`, `SCHEMA-001`, or `content-thin-secondary-pages`.

| Category | Valid IDs |
|---|---|
| `policy_files` | `policy-no-llms-txt`, `policy-weak-llms-txt`, `policy-blocks-gptbot`, `policy-blocks-google-extended`, `policy-blocks-anthropic`, `policy-blocks-perplexity`, `policy-no-robots-txt`, `policy-invalid-robots-syntax` |
| `agentic_readiness` | `agentic-missing-product-schema`, `agentic-missing-organization-schema`, `agentic-missing-article-schema`, `agentic-missing-faq-schema`, `agentic-missing-howto-schema`, `agentic-missing-breadcrumb`, `agentic-no-canonical`, `agentic-broken-heading-hierarchy`, `agentic-weak-meta-description`, `agentic-missing-og-tags`, `agentic-no-semantic-html`, `agentic-duplicate-schema` |
| `content_quality` | `content-thin-page`, `content-low-word-count`, `content-no-tldr`, `content-no-author`, `content-unsourced-stats`, `content-wrong-citation-format`, `content-no-expert-quotes`, `content-stale-date`, `content-thin-faq`, `content-no-examples`, `content-generic-advice` |
| `chunking_retrieval` | `chunking-broken-heading-hierarchy`, `chunking-generic-headings`, `chunking-overscoped-section`, `chunking-buried-answer`, `chunking-long-paragraphs`, `chunking-no-faq-coverage`, `chunking-no-top-summary`, `chunking-missing-query-terms` |
| `query_fanout` | `fanout-no-comparison-content`, `fanout-no-pricing-content`, `fanout-no-alternative-content`, `fanout-missing-entity-coverage`, `fanout-wrong-page-type`, `fanout-no-site-match`, `fanout-unanswered-subquery`, `fanout-thin-topic-coverage`, `fanout-no-docs-content` |

## Writing Rules

Write `MORPHIQ-SCAN.json` to the workspace root using a direct file-write tool call.

Do not:
- Use shell heredocs (`cat > file.json << 'EOF'`)
- Run a Python script to generate the file
- Write to `/tmp/` or any non-workspace path

A site scoring ~60/100 typically has 15–25 issues. Fewer than 10 usually means something was missed — re-check each page.
