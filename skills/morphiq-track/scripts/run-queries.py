#!/usr/bin/env python3
"""run-queries.py — Distribute, execute, and aggregate AI provider queries.

Usage:
  Plan mode:     python3 run-queries.py --prompts prompts.json --mode plan
  Execute mode:  python3 run-queries.py --prompts prompts.json --mode execute
  Results mode:  python3 run-queries.py --prompts prompts.json --results results.json --mode results

Modes:
  plan    — Output an execution plan (provider assignments, batching).
  execute — Run all queries against live provider APIs and save results.
  results — Aggregate previously-saved results and compute citation diffs.

Required env vars for execute mode:
  OPENAI_API_KEY, PERPLEXITY_API_KEY, GEMINI_API_KEY, ANTHROPIC_API_KEY

Input file schema (--prompts):
{
  "config": {
    "brand": "...",
    "domain": "...",
    "competitors": ["..."],       // optional
    "output_path": "..."          // optional, default: morphiq-track-results.json
  },
  "prompts": [...]
}
"""

import argparse
import json
import os
import sys
import time
from collections import defaultdict
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from urllib.request import urlopen, Request

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
        "model": "claude-sonnet-4-5-20250514",
        "search_tool": "web_search_20250305",
        "concurrency": 1,  # serialized
        "fallback_models": ["claude-sonnet-4-20250514"],
    },
    "gemini": {
        "model": "gemini-2.5-flash",
        "search_tool": "googleSearch",
        "concurrency": 3,
    },
}


# ── Utility helpers ──────────────────────────────────────────────────────────

def require_env(name):
    """Read a required environment variable or exit."""
    val = os.environ.get(name)
    if not val:
        print(f"ERROR: missing required environment variable {name}", file=sys.stderr)
        sys.exit(1)
    return val


def strip_utm_params(url):
    """Strip UTM and tracking parameters from a URL."""
    try:
        parsed = urlparse(url)
        params = parse_qs(parsed.query, keep_blank_values=True)
        tracking_prefixes = ("utm_", "ref", "fbclid", "gclid", "mc_", "msclkid")
        cleaned = {k: v for k, v in params.items()
                   if not any(k.lower().startswith(p) for p in tracking_prefixes)}
        return urlunparse(parsed._replace(query=urlencode(cleaned, doseq=True)))
    except Exception:
        return url


def deduplicate_citations(citations):
    """Deduplicate citations by URL after stripping tracking params. Adds citation_weight."""
    seen = {}
    for cit in citations:
        url = cit.get("url", "")
        if not url:
            continue
        clean_url = strip_utm_params(url)
        if clean_url in seen:
            seen[clean_url]["citation_weight"] += 1
        else:
            entry = dict(cit)
            entry["url"] = clean_url
            entry["citation_weight"] = 1
            seen[clean_url] = entry
    return list(seen.values())


def resolve_gemini_url(proxy_url, title=""):
    """Resolve vertexaisearch.cloud.google.com redirect URLs."""
    try:
        req = Request(proxy_url)
        req.add_header("User-Agent", "Mozilla/5.0")
        with urlopen(req, timeout=5) as resp:
            real_url = resp.url
            if real_url != proxy_url:
                return {
                    "url": real_url,
                    "title": title,
                    "resolved_domain": urlparse(real_url).netloc,
                }
    except Exception:
        pass
    resolved_domain = title if title else urlparse(proxy_url).netloc
    return {"url": proxy_url, "title": title or resolved_domain, "resolved_domain": resolved_domain}


def query_with_retry(fn, prompt_text, prompt_id, retries=1, delay=2):
    """Retry once on transient failure with a delay."""
    resp = fn(prompt_text, prompt_id)
    if resp.get("error") and retries > 0:
        print(f"  [retry] error, retrying in {delay}s: {resp['error'][:120]}", file=sys.stderr)
        time.sleep(delay)
        resp = fn(prompt_text, prompt_id)
    return resp


# ── Provider query functions ─────────────────────────────────────────────────

def query_openai(prompt_text, prompt_id):
    """Query OpenAI with web search. Extracts sub-queries from web_search_call items."""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=require_env("OPENAI_API_KEY"))
        response = client.responses.create(
            model=PROVIDERS["openai"]["model"],
            tools=[{"type": "web_search", "search_context_size": "high"}],
            input=prompt_text,
        )
        text = ""
        citations = []
        sub_queries = []
        for item in response.output:
            item_type = getattr(item, "type", None)
            if item_type == "web_search_call":
                q = getattr(item, "query", None) or getattr(item, "search_query", None)
                if q:
                    sub_queries.append(q)
            if hasattr(item, "content"):
                for c in item.content:
                    if hasattr(c, "text"):
                        text += c.text
                    if hasattr(c, "annotations"):
                        for ann in c.annotations:
                            if hasattr(ann, "url"):
                                citations.append({"url": ann.url, "title": getattr(ann, "title", "")})
        citations = deduplicate_citations(citations)
        return {"text": text, "citations": citations, "sub_queries": sub_queries}
    except Exception as e:
        return {"text": "", "citations": [], "sub_queries": [], "error": str(e)}


def query_perplexity(prompt_text, prompt_id):
    """Query Perplexity Sonar Pro. Extracts Perplexity-specific citations."""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=require_env("PERPLEXITY_API_KEY"), base_url="https://api.perplexity.ai")
        response = client.chat.completions.create(
            model=PROVIDERS["perplexity"]["model"],
            messages=[{"role": "user", "content": prompt_text}],
        )
        text = response.choices[0].message.content if response.choices else ""
        citations = []

        # Perplexity citations are non-standard — check multiple access paths
        raw_citations = None
        if hasattr(response, "citations") and response.citations:
            raw_citations = response.citations
        if not raw_citations and hasattr(response, "model_extra") and response.model_extra:
            raw_citations = response.model_extra.get("citations", [])
        if not raw_citations:
            resp_dict = getattr(response, "__dict__", {})
            raw_citations = resp_dict.get("citations", [])
        if not raw_citations and response.choices:
            msg = response.choices[0].message
            if hasattr(msg, "model_extra") and msg.model_extra:
                raw_citations = msg.model_extra.get("citations", [])

        # Debug: log response structure
        print(f"  [perplexity] response type: {type(response).__name__}", file=sys.stderr)
        if hasattr(response, "model_extra") and response.model_extra:
            print(f"  [perplexity] model_extra keys: {list(response.model_extra.keys())}", file=sys.stderr)

        if raw_citations:
            for url in raw_citations:
                if isinstance(url, str):
                    citations.append({"url": url, "title": ""})
                elif isinstance(url, dict):
                    citations.append({"url": url.get("url", ""), "title": url.get("title", "")})

        citations = deduplicate_citations(citations)
        return {"text": text, "citations": citations, "sub_queries": []}
    except Exception as e:
        return {"text": "", "citations": [], "sub_queries": [], "error": str(e)}


def query_gemini(prompt_text, prompt_id):
    """Query Gemini with Google Search grounding. Resolves proxy URLs."""
    try:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=require_env("GEMINI_API_KEY"))
        response = client.models.generate_content(
            model=PROVIDERS["gemini"]["model"],
            contents=prompt_text,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
            ),
        )
        text = response.text if response.text else ""
        citations = []
        if response.candidates and response.candidates[0].grounding_metadata:
            gm = response.candidates[0].grounding_metadata
            if hasattr(gm, "grounding_chunks") and gm.grounding_chunks:
                for chunk in gm.grounding_chunks:
                    if hasattr(chunk, "web") and chunk.web:
                        proxy_url = chunk.web.uri
                        title = getattr(chunk.web, "title", "")
                        if "vertexaisearch.cloud.google.com" in (proxy_url or ""):
                            citations.append(resolve_gemini_url(proxy_url, title))
                        else:
                            citations.append({"url": proxy_url, "title": title})
        citations = deduplicate_citations(citations)
        return {"text": text, "citations": citations, "sub_queries": []}
    except Exception as e:
        return {"text": "", "citations": [], "sub_queries": [], "error": str(e)}


def query_anthropic(prompt_text, prompt_id):
    """Query Anthropic Claude with web search. Model fallback chain."""
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=require_env("ANTHROPIC_API_KEY"))

        models = [PROVIDERS["anthropic"]["model"]] + PROVIDERS["anthropic"].get("fallback_models", [])
        response = None
        last_error = None

        for model_id in models:
            try:
                print(f"  [anthropic] trying {model_id}...", file=sys.stderr)
                response = client.messages.create(
                    model=model_id,
                    max_tokens=4096,
                    tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 5}],
                    messages=[{"role": "user", "content": prompt_text}],
                )
                print(f"  [anthropic] {model_id} succeeded", file=sys.stderr)
                break
            except Exception as e:
                last_error = e
                print(f"  [anthropic] {model_id} failed: {e}", file=sys.stderr)
                continue

        if response is None:
            raise last_error

        text = ""
        citations = []
        sub_queries = []
        for block in response.content:
            block_type = getattr(block, "type", "")

            if block_type == "text":
                text += block.text
                if hasattr(block, "citations") and block.citations:
                    for cit in block.citations:
                        url = getattr(cit, "url", None)
                        if url:
                            citations.append({"url": url, "title": getattr(cit, "title", "")})

            elif block_type == "web_search_tool_result":
                if hasattr(block, "content") and block.content:
                    for item in block.content:
                        url = getattr(item, "url", None)
                        if url:
                            citations.append({"url": url, "title": getattr(item, "title", "")})

            elif block_type == "server_tool_use":
                if getattr(block, "name", "") == "web_search":
                    input_data = getattr(block, "input", {})
                    q = input_data.get("query", "")
                    if q:
                        sub_queries.append(q)

        citations = deduplicate_citations(citations)
        return {"text": text, "citations": citations, "sub_queries": sub_queries}
    except Exception as e:
        return {"text": "", "citations": [], "sub_queries": [], "error": str(e)}


# ── Analysis ─────────────────────────────────────────────────────────────────

def analyze_response(text, brand, domain, competitors=None):
    """Analyze a response for brand mentions. All values caller-supplied."""
    text_lower = text.lower()
    brand_lower = brand.lower()
    domain_lower = domain.lower()

    mentioned = brand_lower in text_lower or domain_lower in text_lower

    mention_type = None
    if mentioned:
        if any(phrase in text_lower for phrase in [
            f"recommend {brand_lower}", f"{brand_lower} is the best",
            f"we recommend {brand_lower}", f"suggest {brand_lower}",
        ]):
            mention_type = "recommendation"
        elif text_lower.count(brand_lower) >= 2:
            mention_type = "named_mention"
        else:
            mention_type = "passing_reference"

    sentiment = "Neutral"
    if mentioned:
        positive_words = ["excellent", "best", "great", "recommended", "leading",
                          "innovative", "powerful", "top"]
        negative_words = ["poor", "lacking", "limited", "avoid", "not recommended", "weak"]
        pos_count = sum(1 for w in positive_words if w in text_lower)
        neg_count = sum(1 for w in negative_words if w in text_lower)
        if pos_count > neg_count:
            sentiment = "Positive"
        elif neg_count > pos_count:
            sentiment = "Negative"

    position = None
    for line in text.split("\n"):
        if brand_lower in line.lower():
            stripped = line.strip()
            if stripped and stripped[0].isdigit():
                try:
                    position = int(stripped.split(".")[0].strip())
                except ValueError:
                    pass
            break

    competitors_found = set()
    if competitors:
        for comp in competitors:
            if comp.lower() in text_lower:
                competitors_found.add(comp)

    return {
        "brand_mentioned": mentioned,
        "mention_type": mention_type,
        "brand_position": position,
        "sentiment": sentiment,
        "competitors_mentioned": list(competitors_found),
        "domain_cited": domain_lower in text_lower,
    }


# ── Plan mode (unchanged) ───────────────────────────────────────────────────

def distribute_prompts(prompts, provider_names=None):
    """Distribute prompts evenly across providers."""
    providers = provider_names or list(PROVIDERS.keys())
    distribution = defaultdict(list)
    for i, prompt in enumerate(prompts):
        distribution[providers[i % len(providers)]].append(prompt)
    return dict(distribution)


def create_query_plan(prompts, provider_names=None):
    """Create a query execution plan with provider assignments."""
    distribution = distribute_prompts(prompts, provider_names)
    plan = {"total_prompts": len(prompts), "providers": {}, "execution_order": []}

    for provider, assigned_prompts in distribution.items():
        config = PROVIDERS.get(provider, {})
        concurrency = config.get("concurrency", 1)
        plan["providers"][provider] = {
            "model": config.get("model", "unknown"),
            "prompt_count": len(assigned_prompts),
            "concurrency": concurrency,
            "prompts": [p["id"] for p in assigned_prompts],
        }
        if isinstance(concurrency, int):
            for batch_start in range(0, len(assigned_prompts), concurrency):
                batch = assigned_prompts[batch_start:batch_start + concurrency]
                plan["execution_order"].append({"provider": provider, "batch": [p["id"] for p in batch]})
        else:
            plan["execution_order"].append({"provider": provider, "batch": [p["id"] for p in assigned_prompts]})

    return plan


# ── Results mode (unchanged) ─────────────────────────────────────────────────

def aggregate_results(results):
    """Aggregate query results into a summary."""
    by_provider = defaultdict(list)
    for r in results:
        by_provider[r["provider"]].append(r)

    summary = {
        "total_queries": len(results),
        "successful": sum(1 for r in results if r.get("response_text")),
        "failed": sum(1 for r in results if not r.get("response_text")),
        "by_provider": {},
    }
    for provider, provider_results in by_provider.items():
        successful = [r for r in provider_results if r.get("response_text")]
        summary["by_provider"][provider] = {
            "total": len(provider_results),
            "successful": len(successful),
            "avg_citations": sum(len(r.get("citations", [])) for r in successful) / max(len(successful), 1),
            "avg_sub_queries": sum(len(r.get("sub_queries", [])) for r in successful) / max(len(successful), 1),
        }
    return summary


def diff_citations(current_citations, previous_citations):
    """Compute gained/lost/stable citations between two runs."""
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


# ── Execute mode ─────────────────────────────────────────────────────────────

def execute_queries(prompts, config):
    """Execute all queries against live provider APIs."""
    brand = config["brand"]
    domain = config["domain"]
    competitors = config.get("competitors", [])
    output_path = config.get("output_path", "morphiq-track-results.json")

    providers = list(PROVIDERS.keys())
    query_funcs = {
        "openai": query_openai,
        "perplexity": query_perplexity,
        "gemini": query_gemini,
        "anthropic": query_anthropic,
    }

    print(f"Brand: {brand} | Domain: {domain} | Competitors: {len(competitors)}", file=sys.stderr)
    print(f"Output: {output_path}", file=sys.stderr)

    results = []
    total = len(prompts)

    for i, prompt in enumerate(prompts):
        provider = providers[i % len(providers)]
        prompt_text = prompt["text"]
        prompt_id = prompt["id"]

        print(f"[{i+1}/{total}] {provider}: {prompt_text[:80]}...", file=sys.stderr)

        resp = query_with_retry(query_funcs[provider], prompt_text, prompt_id, retries=1, delay=2)

        analysis = analyze_response(resp.get("text", ""), brand, domain, competitors)

        cited = any(domain in c.get("url", "") for c in resp.get("citations", []))
        if cited:
            analysis["domain_cited"] = True

        result = {
            "prompt_id": prompt_id,
            "prompt_text": prompt_text,
            "geo_category": prompt.get("geo_category", ""),
            "pipeline_type": prompt.get("pipeline_type", ""),
            "provider": provider,
            "response_text": resp.get("text", ""),  # full text, never truncated
            "citations": resp.get("citations", []),
            "sub_queries": resp.get("sub_queries", []),
            "analysis": analysis,
            "error": resp.get("error"),
        }
        results.append(result)

        if provider == "anthropic":
            time.sleep(1)
        elif provider == "perplexity":
            time.sleep(0.5)

    with open(output_path, "w") as f:
        json.dump({
            "config": {"brand": brand, "domain": domain, "competitors": competitors},
            "results": results,
            "total": len(results),
        }, f, indent=2)

    # Summary
    mentioned = sum(1 for r in results if r["analysis"]["brand_mentioned"])
    cited_count = sum(1 for r in results if r["analysis"]["domain_cited"])
    errors = sum(1 for r in results if r.get("error"))
    by_provider = {}
    for r in results:
        p = r["provider"]
        by_provider.setdefault(p, {"total": 0, "errors": 0, "mentioned": 0, "sub_queries": 0})
        by_provider[p]["total"] += 1
        if r.get("error"):
            by_provider[p]["errors"] += 1
        if r["analysis"]["brand_mentioned"]:
            by_provider[p]["mentioned"] += 1
        by_provider[p]["sub_queries"] += len(r.get("sub_queries", []))

    print(f"\n=== SUMMARY ({brand}) ===", file=sys.stderr)
    print(f"Total queries: {len(results)}", file=sys.stderr)
    print(f"Brand mentioned: {mentioned}/{len(results)} ({mentioned/len(results)*100:.1f}%)", file=sys.stderr)
    print(f"Domain cited: {cited_count}/{len(results)} ({cited_count/len(results)*100:.1f}%)", file=sys.stderr)
    print(f"Errors: {errors}", file=sys.stderr)
    for p, stats in sorted(by_provider.items()):
        print(f"  {p}: {stats['total']} queries, {stats['errors']} errors, "
              f"{stats['mentioned']} mentions, {stats['sub_queries']} sub-queries", file=sys.stderr)
    print(f"Results saved to {output_path}", file=sys.stderr)

    return results


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Distribute, execute, and aggregate AI provider queries")
    parser.add_argument("--prompts", required=True, help="Path to prompts JSON file with config block")
    parser.add_argument("--output", default="-", help="Output path for plan/results mode (- for stdout)")
    parser.add_argument("--providers", default="", help="Comma-separated provider names (default: all)")
    parser.add_argument("--mode", default="plan", choices=["plan", "execute", "results"],
                        help="plan: output execution plan. execute: run queries. results: aggregate + diff")
    parser.add_argument("--results", default=None, help="Path to results JSON (for --mode results)")
    parser.add_argument("--previous-citations", default=None,
                        help="Path to previous citations JSON (for citation diffing)")
    args = parser.parse_args()

    with open(args.prompts) as f:
        data = json.load(f)

    prompts = data.get("prompts", data) if isinstance(data, dict) else data
    config = data.get("config", {}) if isinstance(data, dict) else {}
    providers_filter = [p.strip() for p in args.providers.split(",") if p.strip()] or None

    if args.mode == "plan":
        plan = create_query_plan(prompts, providers_filter)
        output = json.dumps(plan, indent=2)

    elif args.mode == "execute":
        if not config.get("brand") or not config.get("domain"):
            print("ERROR: prompts file must have config.brand and config.domain", file=sys.stderr)
            sys.exit(1)
        execute_queries(prompts, config)
        return

    else:
        results_data = []
        if args.results:
            with open(args.results) as f:
                results_data = json.load(f)
            if isinstance(results_data, dict):
                results_data = results_data.get("results", [])

        summary = aggregate_results(results_data)

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

        output = json.dumps({"summary": summary, "current_citations": current_citations,
                             "citation_diff": citation_diff}, indent=2)

    if args.output == "-":
        print(output)
    else:
        with open(args.output, "w") as f:
            f.write(output)


if __name__ == "__main__":
    main()
