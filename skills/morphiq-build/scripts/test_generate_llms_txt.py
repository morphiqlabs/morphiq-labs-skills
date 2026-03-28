#!/usr/bin/env python3
"""Tests for generate-llms-txt.py — URL Discovery layer (Task 1)."""

import unittest
from importlib.machinery import SourceFileLoader
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


if __name__ == "__main__":
    unittest.main()
