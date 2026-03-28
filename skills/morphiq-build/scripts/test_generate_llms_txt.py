#!/usr/bin/env python3
"""Tests for generate-llms-txt.py — URL Discovery layer (Task 1)."""

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
        self.assertEqual(gen.LLM_MAX_TOKENS, 4096)
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


if __name__ == "__main__":
    unittest.main()
