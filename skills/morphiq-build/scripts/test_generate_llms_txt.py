#!/usr/bin/env python3
"""Tests for generate-llms-txt.py — URL Discovery layer (Task 1)."""

import re
import unittest
from importlib.machinery import SourceFileLoader
from urllib.parse import urlparse
import os


def load_module():
    script = os.path.join(os.path.dirname(__file__), "generate-llms-txt.py")
    return SourceFileLoader("gen", script).load_module()


gen = load_module()


class TestNormalizeDomain(unittest.TestCase):
    def test_strips_https(self):
        self.assertEqual(gen.normalize_domain("https://example.com"), "example.com")

    def test_strips_http(self):
        self.assertEqual(gen.normalize_domain("http://example.com"), "example.com")

    def test_strips_trailing_slash(self):
        self.assertEqual(gen.normalize_domain("https://example.com/"), "example.com")

    def test_strips_both(self):
        self.assertEqual(gen.normalize_domain("https://example.com/"), "example.com")

    def test_bare_domain_passthrough(self):
        self.assertEqual(gen.normalize_domain("example.com"), "example.com")

    def test_preserves_subdomain(self):
        self.assertEqual(gen.normalize_domain("https://docs.example.com/"), "docs.example.com")


class TestExtractAnchorUrls(unittest.TestCase):
    def test_extracts_absolute_urls(self):
        html = '<a href="https://example.com/about">About</a><a href="https://example.com/pricing">Pricing</a>'
        urls = gen.extract_anchor_urls(html, "https://example.com")
        self.assertIn("https://example.com/about", urls)
        self.assertIn("https://example.com/pricing", urls)

    def test_resolves_relative_urls(self):
        html = '<a href="/docs">Docs</a><a href="faq">FAQ</a>'
        urls = gen.extract_anchor_urls(html, "https://example.com")
        self.assertIn("https://example.com/docs", urls)
        self.assertIn("https://example.com/faq", urls)

    def test_skips_mailto(self):
        html = '<a href="mailto:hi@example.com">Email</a><a href="https://example.com/about">About</a>'
        urls = gen.extract_anchor_urls(html, "https://example.com")
        self.assertNotIn("mailto:hi@example.com", urls)
        self.assertIn("https://example.com/about", urls)

    def test_skips_tel(self):
        html = '<a href="tel:+1234567890">Call</a>'
        urls = gen.extract_anchor_urls(html, "https://example.com")
        self.assertEqual(len(urls), 0)

    def test_skips_fragment_only(self):
        html = '<a href="#section">Jump</a>'
        urls = gen.extract_anchor_urls(html, "https://example.com")
        self.assertEqual(len(urls), 0)

    def test_deduplicates(self):
        html = '<a href="https://example.com/about">A</a><a href="https://example.com/about">B</a>'
        urls = gen.extract_anchor_urls(html, "https://example.com")
        self.assertEqual(urls.count("https://example.com/about"), 1)

    def test_empty_html(self):
        urls = gen.extract_anchor_urls("", "https://example.com")
        self.assertEqual(urls, [])

    def test_no_href(self):
        html = '<a name="anchor">No href</a>'
        urls = gen.extract_anchor_urls(html, "https://example.com")
        self.assertEqual(urls, [])


class TestParseRobotsSitemaps(unittest.TestCase):
    def test_extracts_sitemap_directives(self):
        robots = "User-agent: *\nDisallow: /private\nSitemap: https://example.com/sitemap.xml\n"
        sitemaps = gen.parse_robots_sitemaps(robots)
        self.assertEqual(sitemaps, ["https://example.com/sitemap.xml"])

    def test_multiple_sitemaps(self):
        robots = "Sitemap: https://example.com/sitemap1.xml\nSitemap: https://example.com/sitemap2.xml\n"
        sitemaps = gen.parse_robots_sitemaps(robots)
        self.assertEqual(len(sitemaps), 2)
        self.assertIn("https://example.com/sitemap1.xml", sitemaps)
        self.assertIn("https://example.com/sitemap2.xml", sitemaps)

    def test_empty_robots(self):
        sitemaps = gen.parse_robots_sitemaps("")
        self.assertEqual(sitemaps, [])

    def test_no_sitemap_directives(self):
        robots = "User-agent: *\nDisallow: /admin\n"
        sitemaps = gen.parse_robots_sitemaps(robots)
        self.assertEqual(sitemaps, [])

    def test_case_insensitive(self):
        robots = "sitemap: https://example.com/sitemap.xml\n"
        sitemaps = gen.parse_robots_sitemaps(robots)
        self.assertEqual(sitemaps, ["https://example.com/sitemap.xml"])


class TestExtractUrlsFromSitemap(unittest.TestCase):
    def test_parses_standard_sitemap_xml(self):
        xml = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://example.com/</loc></url>
  <url><loc>https://example.com/about</loc></url>
</urlset>"""
        urls = gen.extract_urls_from_sitemap(xml)
        self.assertEqual(len(urls), 2)
        self.assertIn("https://example.com/", urls)
        self.assertIn("https://example.com/about", urls)

    def test_regex_fallback_on_broken_xml(self):
        broken = "<urlset><url><loc>https://example.com/page1</loc></url><url><loc>https://example.com/page2</loc>"
        urls = gen.extract_urls_from_sitemap(broken)
        self.assertIn("https://example.com/page1", urls)

    def test_empty_content(self):
        urls = gen.extract_urls_from_sitemap("")
        self.assertEqual(urls, [])

    def test_sitemap_index(self):
        xml = """<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap><loc>https://example.com/sitemap-posts.xml</loc></sitemap>
</sitemapindex>"""
        urls = gen.extract_urls_from_sitemap(xml)
        self.assertIn("https://example.com/sitemap-posts.xml", urls)


class TestFindDocsBase(unittest.TestCase):
    def test_finds_docs_url(self):
        urls = [
            "https://example.com/",
            "https://example.com/about",
            "https://example.com/docs",
            "https://example.com/pricing",
        ]
        result = gen.find_docs_base(urls, "example.com")
        self.assertEqual(result, "https://example.com/docs")

    def test_finds_documentation_url(self):
        urls = [
            "https://example.com/",
            "https://example.com/documentation/getting-started",
        ]
        result = gen.find_docs_base(urls, "example.com")
        self.assertEqual(result, "https://example.com/documentation/getting-started")

    def test_returns_none_when_absent(self):
        urls = [
            "https://example.com/",
            "https://example.com/about",
            "https://example.com/pricing",
        ]
        result = gen.find_docs_base(urls, "example.com")
        self.assertIsNone(result)

    def test_empty_urls(self):
        result = gen.find_docs_base([], "example.com")
        self.assertIsNone(result)

    def test_finds_api_reference(self):
        urls = [
            "https://example.com/",
            "https://example.com/api/v1/overview",
        ]
        result = gen.find_docs_base(urls, "example.com")
        self.assertEqual(result, "https://example.com/api/v1/overview")

    def test_prefers_shorter_docs_path(self):
        urls = [
            "https://example.com/docs/advanced/topic",
            "https://example.com/docs",
        ]
        result = gen.find_docs_base(urls, "example.com")
        self.assertEqual(result, "https://example.com/docs")


class TestFetchUrl(unittest.TestCase):
    def test_returns_tuple(self):
        # fetch_url with a definitely-invalid URL returns (0, "")
        status, body = gen.fetch_url("http://this-domain-does-not-exist-xyz.invalid/")
        self.assertEqual(status, 0)
        self.assertEqual(body, "")

    def test_signature(self):
        # Verify it accepts timeout kwarg without error
        import inspect
        sig = inspect.signature(gen.fetch_url)
        self.assertIn("timeout", sig.parameters)


class TestConstants(unittest.TestCase):
    def test_constants_defined(self):
        self.assertEqual(gen.MAX_CONTEXT_CHARS, 24000)
        self.assertEqual(gen.DEEP_SCRAPE_LIMIT, 4)
        self.assertEqual(gen.DEEP_CHAR_LIMIT, 3000)
        self.assertEqual(gen.SHALLOW_CHAR_LIMIT, 900)
        self.assertEqual(gen.SIZE_BUDGET_KB, 100)
        self.assertEqual(gen.MAX_SITEMAP_URLS, 80)
        self.assertIn("/docs", gen.DOCS_PATH_PATTERNS)
        self.assertIn("/api", gen.DOCS_PATH_PATTERNS)
        self.assertEqual(len(gen.DOCS_PATH_PATTERNS), 7)


# ── Task 2: URL Scoring, Classification & Page Scraping ─────────────────────


class TestClassifyUrl(unittest.TestCase):
    def test_home_root(self):
        self.assertEqual(gen.classify_url("https://example.com/", "example.com"), "home")

    def test_home_empty_path(self):
        self.assertEqual(gen.classify_url("https://example.com", "example.com"), "home")

    def test_pricing(self):
        self.assertEqual(gen.classify_url("https://example.com/pricing", "example.com"), "pricing")

    def test_blog_subpath(self):
        self.assertEqual(gen.classify_url("https://example.com/blog/some-post", "example.com"), "blog")

    def test_other_unknown_path(self):
        self.assertEqual(gen.classify_url("https://example.com/random-page", "example.com"), "other")

    def test_security(self):
        self.assertEqual(gen.classify_url("https://example.com/security", "example.com"), "security")

    def test_legal_privacy(self):
        self.assertEqual(gen.classify_url("https://example.com/privacy", "example.com"), "legal")

    def test_case_insensitive(self):
        self.assertEqual(gen.classify_url("https://example.com/Pricing", "example.com"), "pricing")

    def test_docs(self):
        self.assertEqual(gen.classify_url("https://example.com/docs/getting-started", "example.com"), "docs")

    def test_comparison_vs(self):
        self.assertEqual(gen.classify_url("https://example.com/vs/competitor", "example.com"), "comparison")

    def test_changelog(self):
        self.assertEqual(gen.classify_url("https://example.com/changelog", "example.com"), "changelog")


class TestScoreUrl(unittest.TestCase):
    def test_home_scores_highest(self):
        home_score = gen.score_url("https://example.com/", "example.com")
        other_score = gen.score_url("https://example.com/random-page", "example.com")
        self.assertGreater(home_score, other_score)

    def test_nav_urls_boost(self):
        url = "https://example.com/about"
        score_without = gen.score_url(url, "example.com", nav_urls=None)
        score_with = gen.score_url(url, "example.com", nav_urls={url})
        self.assertEqual(score_with, score_without + 20)

    def test_deep_path_penalty(self):
        shallow = gen.score_url("https://example.com/blog", "example.com")
        deep = gen.score_url("https://example.com/blog/2024/01/my-post", "example.com")
        self.assertGreater(shallow, deep)

    def test_canonical_path_bonus(self):
        # A URL with <=1 path segments should get +10 canonical bonus
        score = gen.score_url("https://example.com/pricing", "example.com")
        # pricing base = 90, canonical bonus +10 = 100
        self.assertEqual(score, 100)

    def test_none_nav_urls(self):
        # Should not crash with nav_urls=None
        score = gen.score_url("https://example.com/pricing", "example.com")
        self.assertIsInstance(score, int)

    def test_home_base_score(self):
        score = gen.score_url("https://example.com/", "example.com")
        # home=100, canonical bonus +10 = 110
        self.assertEqual(score, 110)


class TestExtractPageText(unittest.TestCase):
    def test_strips_scripts_and_styles(self):
        html = "<html><head><style>body{color:red}</style></head><body><script>alert(1)</script><p>Hello world</p></body></html>"
        text = gen.extract_page_text(html)
        self.assertIn("Hello world", text)
        self.assertNotIn("alert", text)
        self.assertNotIn("color:red", text)

    def test_respects_max_chars(self):
        html = "<p>A long paragraph with many characters that should be truncated.</p>"
        text = gen.extract_page_text(html, max_chars=10)
        self.assertLessEqual(len(text), 10)

    def test_empty_html(self):
        text = gen.extract_page_text("")
        self.assertEqual(text, "")

    def test_skips_noscript(self):
        html = "<body><noscript>Enable JS</noscript><p>Content</p></body>"
        text = gen.extract_page_text(html)
        self.assertNotIn("Enable JS", text)
        self.assertIn("Content", text)

    def test_skips_svg(self):
        html = "<body><svg><text>Icon</text></svg><p>Visible</p></body>"
        text = gen.extract_page_text(html)
        self.assertNotIn("Icon", text)
        self.assertIn("Visible", text)


class TestExtractHeadings(unittest.TestCase):
    def test_extracts_h1_through_h3(self):
        html = "<h1>Title</h1><h2>Subtitle</h2><h3>Section</h3>"
        headings = gen.extract_headings(html)
        self.assertEqual(headings, ["Title", "Subtitle", "Section"])

    def test_ignores_h4_and_beyond(self):
        html = "<h1>Keep</h1><h4>Skip</h4><h5>Skip2</h5><h6>Skip3</h6>"
        headings = gen.extract_headings(html)
        self.assertEqual(headings, ["Keep"])

    def test_strips_inner_html(self):
        html = '<h1><span class="highlight">Bold</span> Title</h1>'
        headings = gen.extract_headings(html)
        self.assertEqual(headings, ["Bold Title"])

    def test_empty_html(self):
        headings = gen.extract_headings("")
        self.assertEqual(headings, [])

    def test_multiline_heading(self):
        html = "<h2>\n  Spaced Heading\n</h2>"
        headings = gen.extract_headings(html)
        self.assertEqual(headings, ["Spaced Heading"])


# ── Task 3: Context Collection Orchestrator ──────────────────────────────────

mod = gen  # alias for patching


class TestBuildEvidence(unittest.TestCase):
    def _make_pages(self, texts, urls=None):
        """Helper: build scraped_pages list from text strings."""
        pages = []
        for i, t in enumerate(texts):
            url = (urls[i] if urls else f"https://example.com/page{i}")
            pages.append({
                "url": url,
                "text": t,
                "headings": [w for w in t.split(". ") if len(w.split()) <= 5],
                "tier": "deep",
            })
        return pages

    def test_extracts_date_literals(self):
        pages = self._make_pages(["Founded in 2019. Updated March 2024."])
        allowed = ["https://example.com/"]
        ev = gen.build_evidence(pages, allowed)
        self.assertGreater(len(ev["date_literals"]), 0)

    def test_extracts_price_literals(self):
        pages = self._make_pages(["Pro plan at $49/mo. Enterprise from $199/mo."])
        allowed = ["https://example.com/"]
        ev = gen.build_evidence(pages, allowed)
        self.assertGreater(len(ev["price_literals"]), 0)

    def test_extracts_facts(self):
        pages = self._make_pages(["15,000+ customers worldwide"])
        allowed = ["https://example.com/"]
        ev = gen.build_evidence(pages, allowed)
        self.assertGreater(len(ev["facts"]), 0)

    def test_caps_allowed_urls(self):
        pages = self._make_pages(["Some text"])
        allowed = [f"https://example.com/p{i}" for i in range(100)]
        ev = gen.build_evidence(pages, allowed)
        self.assertLessEqual(len(ev["allowed_urls"]), gen.MAX_SITEMAP_URLS)

    def test_extracts_key_terms(self):
        pages = [{
            "url": "https://example.com/",
            "text": "hello",
            "headings": ["Getting Started Guide", "API Reference Docs", "X"],
            "tier": "deep",
        }]
        ev = gen.build_evidence(pages, ["https://example.com/"])
        # "Getting Started Guide" (3 words) and "API Reference Docs" (3 words) qualify
        # "X" (1 word) does not
        self.assertGreater(len(ev["key_terms"]), 0)
        for term in ev["key_terms"]:
            words = term.split()
            self.assertGreaterEqual(len(words), 2)
            self.assertLessEqual(len(words), 5)


class TestCollectLlmsContext(unittest.TestCase):
    """Tests for collect_llms_context — mock fetch_url to avoid real HTTP."""

    DOMAIN = "example.com"
    ROOT = "https://example.com"

    HOMEPAGE_HTML = """<html><head><title>Example</title></head><body>
    <h1>Welcome to Example</h1>
    <a href="/pricing">Pricing</a>
    <a href="/about">About</a>
    <a href="/docs">Docs</a>
    <a href="https://other.com/external">External</a>
    <p>Example is a platform with 5,000+ customers. Founded in 2020.</p>
    </body></html>"""

    ROBOTS_TXT = "User-agent: *\nSitemap: https://example.com/sitemap.xml\n"

    SITEMAP_XML = """<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
      <url><loc>https://example.com/</loc></url>
      <url><loc>https://example.com/pricing</loc></url>
      <url><loc>https://example.com/about</loc></url>
      <url><loc>https://example.com/docs</loc></url>
      <url><loc>https://example.com/blog/post-1</loc></url>
      <url><loc>https://other.com/cross-domain</loc></url>
    </urlset>"""

    PRICING_HTML = "<html><body><h1>Pricing</h1><p>Pro plan at $49/mo.</p></body></html>"
    ABOUT_HTML = "<html><body><h1>About Us</h1><p>Founded in 2018.</p></body></html>"
    DOCS_HTML = "<html><body><h1>Documentation</h1><a href='/docs/getting-started'>Start</a><p>Guide content here.</p></body></html>"
    BLOG_HTML = "<html><body><h1>Blog Post</h1><p>Some blog content.</p></body></html>"

    def _mock_fetch(self, url, timeout=15):
        """Return canned responses for known URLs."""
        responses = {
            "https://example.com": (200, self.HOMEPAGE_HTML),
            "https://example.com/": (200, self.HOMEPAGE_HTML),
            "https://example.com/robots.txt": (200, self.ROBOTS_TXT),
            "https://example.com/sitemap.xml": (200, self.SITEMAP_XML),
            "https://example.com/pricing": (200, self.PRICING_HTML),
            "https://example.com/about": (200, self.ABOUT_HTML),
            "https://example.com/docs": (200, self.DOCS_HTML),
            "https://example.com/docs/getting-started": (200, "<html><body><h2>Getting Started</h2><p>Step 1...</p></body></html>"),
            "https://example.com/blog/post-1": (200, self.BLOG_HTML),
        }
        return responses.get(url, (0, ""))

    def setUp(self):
        self._orig_fetch = mod.fetch_url
        mod.fetch_url = self._mock_fetch

    def tearDown(self):
        mod.fetch_url = self._orig_fetch

    def test_builds_context_dict_structure(self):
        ctx = gen.collect_llms_context("https://example.com")
        required_keys = [
            "root_url", "domain", "docs_base", "all_urls",
            "ranked_urls", "scraped_pages", "evidence", "homepage_html",
        ]
        for key in required_keys:
            self.assertIn(key, ctx, f"Missing key: {key}")

    def test_scopes_urls_to_domain(self):
        ctx = gen.collect_llms_context("https://example.com")
        for url in ctx["all_urls"]:
            parsed = urlparse(url)
            self.assertEqual(parsed.netloc, self.DOMAIN,
                             f"Cross-domain URL found: {url}")

    def test_two_tier_scraping(self):
        ctx = gen.collect_llms_context("https://example.com")
        tiers = {p["tier"] for p in ctx["scraped_pages"]}
        # With our mock data we have enough pages for both tiers
        # At minimum we must have deep tier (homepage always deep)
        self.assertIn("deep", tiers)

    def test_homepage_always_deep(self):
        ctx = gen.collect_llms_context("https://example.com")
        homepage_pages = [
            p for p in ctx["scraped_pages"]
            if p["url"] in ("https://example.com", "https://example.com/")
        ]
        self.assertGreater(len(homepage_pages), 0, "Homepage not in scraped_pages")
        for p in homepage_pages:
            self.assertEqual(p["tier"], "deep")


# ── Task 4: System Prompt & User Prompt Construction ──────────────────────────


class TestBuildSystemPrompt(unittest.TestCase):
    def test_contains_identity_block(self):
        prompt = gen.build_system_prompt()
        self.assertIn("<identity>", prompt)
        self.assertIn("</identity>", prompt)

    def test_contains_all_14_sections(self):
        prompt = gen.build_system_prompt()
        expected_keywords = [
            "Overview",
            "Who",       # "Who We Serve" or "Who we serve"
            "Products",
            "Solutions",
            "Key Resources",
            "FAQs",
            "Security",
            "Pricing",
            "Policies",
            "Sitemap",
            "Citation",
        ]
        for kw in expected_keywords:
            self.assertIn(kw, prompt, f"Missing section keyword: {kw}")

    def test_contains_validation_instructions(self):
        prompt = gen.build_system_prompt()
        self.assertIn("alidation", prompt)  # "Validation" or "validation"

    def test_output_format_instruction(self):
        prompt = gen.build_system_prompt()
        self.assertIn("```llms.txt", prompt)


class TestBuildUserPrompt(unittest.TestCase):
    def _sample_context(self):
        return {
            "root_url": "https://ramp.com",
            "domain": "ramp.com",
            "docs_base": "https://ramp.com/docs",
            "ranked_urls": ["https://ramp.com/", "https://ramp.com/pricing"],
            "scraped_pages": [
                {
                    "url": "https://ramp.com/",
                    "text": "Ramp is the corporate card.",
                    "headings": ["Ramp"],
                    "tier": "deep",
                },
            ],
            "evidence": {
                "allowed_urls": ["https://ramp.com/", "https://ramp.com/pricing"],
                "date_literals": ["2019"],
                "price_literals": ["free to start"],
                "headings": ["Ramp"],
                "facts": ["15,000+ businesses"],
                "key_terms": ["corporate card"],
            },
        }

    def _sample_brand(self):
        return {
            "name": "Ramp",
            "tagline": "The corporate card that helps you spend less",
        }

    def test_contains_runtime_inputs(self):
        prompt = gen.build_user_prompt(self._sample_context(), self._sample_brand())
        self.assertIn("<runtime_inputs>", prompt)
        self.assertIn("ramp.com", prompt)

    def test_contains_canonical_urls(self):
        prompt = gen.build_user_prompt(self._sample_context(), self._sample_brand())
        self.assertIn("<canonical_source_urls>", prompt)

    def test_includes_scraped_content(self):
        prompt = gen.build_user_prompt(self._sample_context(), self._sample_brand())
        self.assertIn("Ramp is the corporate card.", prompt)

    def test_includes_evidence(self):
        prompt = gen.build_user_prompt(self._sample_context(), self._sample_brand())
        self.assertIn("Grounding Evidence", prompt)

    def test_includes_hard_requirements(self):
        prompt = gen.build_user_prompt(self._sample_context(), self._sample_brand())
        self.assertIn("Hard Requirements", prompt)


# ── Task 5: LLM Call with Multi-Provider Fallback ─────────────────────────────


# ── Task 6: Output Validation ───────────────────────────────────────────────


class TestExtractFencedBlock(unittest.TestCase):
    def test_extracts_content(self):
        raw = 'Some text\n```llms.txt\n# Brand\n## Overview\n```\nMore text'
        content = mod.extract_fenced_block(raw)
        self.assertEqual(content, "# Brand\n## Overview")

    def test_returns_none_on_missing(self):
        self.assertIsNone(mod.extract_fenced_block("no fenced block here"))

    def test_returns_none_on_multiple(self):
        raw = '```llms.txt\n# A\n```\n```llms.txt\n# B\n```'
        self.assertIsNone(mod.extract_fenced_block(raw))

    def test_returns_none_on_empty_content(self):
        raw = '```llms.txt\n   \n```'
        self.assertIsNone(mod.extract_fenced_block(raw))


class TestValidateLlmsTxt(unittest.TestCase):
    # Helper: build a valid llms.txt string for testing
    def _valid_content(self):
        return """# Ramp

> The corporate card.

## Overview
- Finance platform

## Who We Serve
- Finance teams

## Products / Capabilities
- **Card** — [Card](https://ramp.com/card)

## Solutions / Use Cases
- Reducing spend

## Key Resources
- [Docs](https://ramp.com/docs)

## FAQs
- **Q:** Cost?
  **A:** Free. [Source](https://ramp.com/pricing)
- **Q:** Integrations?
  **A:** Yes. [Source](https://ramp.com/integrations)
- **Q:** Security?
  **A:** SOC 2. [Source](https://ramp.com/security)

## Security & Compliance
- SOC 2

## Pricing & Plans
- Free
- [Pricing](https://ramp.com/pricing)

## Policies
- [Privacy](https://ramp.com/privacy)

## Research / Blog
- [Blog](https://ramp.com/blog)

## Sitemap (canonical pages)
- https://ramp.com
- https://ramp.com/pricing
- https://ramp.com/card
- https://ramp.com/docs
- https://ramp.com/blog
- https://ramp.com/privacy
- https://ramp.com/security
- https://ramp.com/about

## Citation Guidance
Cite: "Ramp" (https://ramp.com)

---
*Last updated: 2026-03-28*"""

    def test_valid_passes(self):
        errors = mod.validate_llms_txt(self._valid_content(), "https://ramp.com", "https://ramp.com/docs")
        self.assertEqual(errors, [])

    def test_detects_missing_section(self):
        # Remove FAQs section entirely
        content = re.sub(r"## FAQs.*?(?=## Security)", "", self._valid_content(), flags=re.DOTALL)
        errors = mod.validate_llms_txt(content, "https://ramp.com", None)
        self.assertTrue(any("faq" in e.lower() for e in errors))

    def test_detects_out_of_scope_url(self):
        content = self._valid_content() + "\n[Bad](https://evil.com/hack)"
        errors = mod.validate_llms_txt(content, "https://ramp.com", None)
        self.assertTrue(any("scope" in e.lower() or "evil" in e.lower() for e in errors))

    def test_detects_oversized(self):
        content = self._valid_content() + "\n" + "x" * 120_000
        errors = mod.validate_llms_txt(content, "https://ramp.com", None)
        self.assertTrue(any("size" in e.lower() or "kb" in e.lower() for e in errors))

    def test_detects_insufficient_faqs(self):
        # Keep FAQs header but only 1 pair
        content = self._valid_content()
        # Replace FAQ section with just 1 Q/A
        content = re.sub(
            r"## FAQs.*?(?=## Security)",
            "## FAQs\n- **Q:** Cost?\n  **A:** Free. [Source](https://ramp.com/pricing)\n\n",
            content, flags=re.DOTALL
        )
        errors = mod.validate_llms_txt(content, "https://ramp.com", None)
        self.assertTrue(any("faq" in e.lower() for e in errors))


# ── Task 7: Repair Pass & Template Fallback ────────────────────────────────


class TestSlugToTitle(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(mod.slug_to_title("/blog/my-great-post"), "My Great Post")

    def test_empty(self):
        self.assertEqual(mod.slug_to_title("/"), "Page")

    def test_underscores(self):
        self.assertEqual(mod.slug_to_title("/docs/getting_started"), "Getting Started")


class TestBuildLlmsTxtTemplate(unittest.TestCase):
    def _sample_context(self):
        return {
            "root_url": "https://ramp.com",
            "domain": "ramp.com",
            "docs_base": "https://ramp.com/docs",
            "ranked_urls": [
                "https://ramp.com/", "https://ramp.com/pricing",
                "https://ramp.com/docs", "https://ramp.com/blog",
                "https://ramp.com/about", "https://ramp.com/security",
                "https://ramp.com/privacy", "https://ramp.com/terms",
                "https://ramp.com/corporate-card", "https://ramp.com/features",
                "https://ramp.com/solutions", "https://ramp.com/customers",
            ],
            "scraped_pages": [
                {"url": "https://ramp.com/", "text": "Ramp helps businesses save 5% on spend. 15,000+ businesses trust Ramp. Finance automation platform.", "headings": ["Ramp — Save time and money"], "tier": "deep"},
                {"url": "https://ramp.com/pricing", "text": "Free to start. No annual fees. Pro at $49/mo.", "headings": ["Pricing"], "tier": "deep"},
            ],
            "evidence": {
                "allowed_urls": ["https://ramp.com/", "https://ramp.com/pricing", "https://ramp.com/docs",
                                  "https://ramp.com/blog", "https://ramp.com/about", "https://ramp.com/security",
                                  "https://ramp.com/privacy", "https://ramp.com/terms", "https://ramp.com/corporate-card"],
                "date_literals": [],
                "price_literals": ["Free to start", "$49/mo"],
                "headings": ["Ramp — Save time and money", "Pricing"],
                "facts": ["15,000+ businesses"],
                "key_terms": ["corporate card"],
            },
        }

    def test_contains_all_required_sections(self):
        template = mod.build_llms_txt_template(self._sample_context(), {"name": "Ramp", "tagline": "Save time and money"})
        self.assertIn("# Ramp", template)
        self.assertIn("## Overview", template)
        self.assertIn("## Who We Serve", template)
        self.assertIn("## Products", template)
        self.assertIn("## FAQs", template)
        self.assertIn("## Security", template)
        self.assertIn("## Pricing", template)
        self.assertIn("## Policies", template)
        self.assertIn("## Sitemap", template)
        self.assertIn("## Citation Guidance", template)
        self.assertIn("Last updated", template)

    def test_no_populate_markers(self):
        template = mod.build_llms_txt_template(self._sample_context(), {"name": "Ramp", "tagline": ""})
        self.assertNotIn("POPULATE", template)
        self.assertNotIn("<!--", template)

    def test_uses_real_urls(self):
        template = mod.build_llms_txt_template(self._sample_context(), {"name": "Ramp", "tagline": ""})
        self.assertIn("ramp.com", template)

    def test_faqs_have_correct_format(self):
        template = mod.build_llms_txt_template(self._sample_context(), {"name": "Ramp", "tagline": ""})
        self.assertIn("**Q:**", template)
        self.assertIn("**A:**", template)
        self.assertIn("[Source]", template)


# ── Task 8: Main Orchestrator & CLI ────────────────────────────────────────


class TestDetectBrand(unittest.TestCase):
    def test_extracts_from_title_with_separator(self):
        html = '<html><head><title>Ramp — The Corporate Card</title></head></html>'
        brand = mod.detect_brand_from_homepage(html, "ramp.com")
        self.assertEqual(brand["name"], "Ramp")
        self.assertIn("Corporate Card", brand["tagline"])

    def test_prefers_og_site_name(self):
        html = '<html><head><title>Page Title</title><meta property="og:site_name" content="BrandName"></head></html>'
        brand = mod.detect_brand_from_homepage(html, "example.com")
        self.assertEqual(brand["name"], "BrandName")

    def test_falls_back_to_domain(self):
        html = '<html><body>Hello</body></html>'
        brand = mod.detect_brand_from_homepage(html, "example.com")
        self.assertEqual(brand["name"], "example.com")

    def test_meta_description_as_tagline(self):
        html = '<html><head><meta name="description" content="Best platform ever"></head></html>'
        brand = mod.detect_brand_from_homepage(html, "example.com")
        self.assertEqual(brand["tagline"], "Best platform ever")


class TestRunCollect(unittest.TestCase):
    """Tests for the collect mode — context collection + prompt + template."""

    def setUp(self):
        self.mod = load_module()
        self._orig_fetch = self.mod.fetch_url
        responses = {
            "https://example.com": (200, '<html><head><title>ExCo \u2014 Platform</title></head><body><h1>ExCo</h1><a href="/pricing">P</a><a href="/docs">D</a></body></html>'),
            "https://example.com/robots.txt": (200, "Sitemap: https://example.com/sitemap.xml"),
            "https://example.com/sitemap.xml": (200, '<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + ''.join(f'<url><loc>https://example.com/p{i}</loc></url>' for i in range(12)) + '</urlset>'),
            "https://example.com/pricing": (200, '<h1>Pricing</h1><p>Free. Pro $49/mo.</p>'),
            "https://example.com/docs": (200, '<h1>Docs</h1><p>Get started.</p>'),
        }
        self.mod.fetch_url = lambda url, timeout=15: responses.get(url, (404, ""))

    def tearDown(self):
        self.mod.fetch_url = self._orig_fetch

    def test_returns_all_keys(self):
        result = self.mod.run_collect("https://example.com", brand_info={"name": "ExCo", "tagline": "Platform"})
        self.assertIn("context", result)
        self.assertIn("brand_info", result)
        self.assertIn("system_prompt", result)
        self.assertIn("user_prompt", result)
        self.assertIn("template_fallback", result)

    def test_auto_detects_brand(self):
        result = self.mod.run_collect("https://example.com")
        self.assertEqual(result["brand_info"]["name"], "ExCo")

    def test_template_has_no_populate_markers(self):
        result = self.mod.run_collect("https://example.com")
        self.assertNotIn("POPULATE", result["template_fallback"])
        self.assertNotIn("<!--", result["template_fallback"])

    def test_context_excludes_homepage_html(self):
        result = self.mod.run_collect("https://example.com")
        self.assertNotIn("homepage_html", result["context"])

    def test_system_prompt_has_14_sections(self):
        result = self.mod.run_collect("https://example.com")
        for section in ["Overview", "Who We Serve", "Products", "Solutions",
                        "Key Resources", "FAQs", "Security", "Pricing", "Policies"]:
            self.assertIn(section, result["system_prompt"])


class TestRunValidate(unittest.TestCase):
    """Tests for the validate mode."""

    def _valid_content(self):
        return """# Ramp

> The corporate card.

## Overview
- Finance platform

## Who We Serve
- Finance teams

## Products / Capabilities
- **Card** \u2014 [Card](https://ramp.com/card)

## Solutions / Use Cases
- Reducing spend

## Key Resources
- [Docs](https://ramp.com/docs)

## FAQs
- **Q:** Cost?
  **A:** Free. [Source](https://ramp.com/pricing)
- **Q:** Integrations?
  **A:** Yes. [Source](https://ramp.com/integrations)
- **Q:** Security?
  **A:** SOC 2. [Source](https://ramp.com/security)

## Security & Compliance
- SOC 2

## Pricing & Plans
- Free
- [Pricing](https://ramp.com/pricing)

## Policies
- [Privacy](https://ramp.com/privacy)

## Research / Blog
- [Blog](https://ramp.com/blog)

## Sitemap (canonical pages)
- https://ramp.com
- https://ramp.com/pricing
- https://ramp.com/card
- https://ramp.com/docs
- https://ramp.com/blog
- https://ramp.com/privacy
- https://ramp.com/security
- https://ramp.com/about

## Citation Guidance
Cite: "Ramp" (https://ramp.com)

---
*Last updated: 2026-03-28*"""

    def test_valid_returns_true(self):
        result = gen.run_validate(self._valid_content(), "https://ramp.com", "https://ramp.com/docs")
        self.assertTrue(result["valid"])
        self.assertEqual(result["errors"], [])

    def test_invalid_returns_errors(self):
        content = self._valid_content().replace("## FAQs", "## Questions")
        result = gen.run_validate(content, "https://ramp.com")
        self.assertFalse(result["valid"])
        self.assertGreater(len(result["errors"]), 0)


class TestRunTemplate(unittest.TestCase):
    """Tests for the template mode."""

    def setUp(self):
        self.mod = load_module()
        self._orig_fetch = self.mod.fetch_url
        responses = {
            "https://example.com": (200, '<html><head><title>ExCo</title></head><body><h1>ExCo does things.</h1></body></html>'),
            "https://example.com/robots.txt": (200, ""),
            "https://example.com/sitemap.xml": (200, '<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + ''.join(f'<url><loc>https://example.com/p{i}</loc></url>' for i in range(10)) + '</urlset>'),
        }
        self.mod.fetch_url = lambda url, timeout=15: responses.get(url, (404, ""))

    def tearDown(self):
        self.mod.fetch_url = self._orig_fetch

    def test_returns_string(self):
        result = self.mod.run_template("https://example.com")
        self.assertIsInstance(result, str)
        self.assertIn("## Overview", result)

    def test_no_populate_markers(self):
        result = self.mod.run_template("https://example.com")
        self.assertNotIn("POPULATE", result)
        self.assertNotIn("<!--", result)


if __name__ == "__main__":
    unittest.main()
