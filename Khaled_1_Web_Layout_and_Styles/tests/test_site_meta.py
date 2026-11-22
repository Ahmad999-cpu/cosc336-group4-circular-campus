"""Favicon, link-preview tags, robots.txt and sitemap.xml for the public site."""
from django.contrib.staticfiles import finders
from django.test import TestCase
from django.urls import reverse


class SiteMetaTests(TestCase):
    def test_brand_files_exist(self):
        for f in ("favicon.ico", "favicon.svg", "apple-touch-icon.png", "og-image.jpg"):
            self.assertTrue(finders.find(f"img/brand/{f}"), f)

    def test_public_pages_have_icons_and_preview_tags(self):
        for name in ("web:home", "guest:how", "guest:blueprint", "guest:pricing", "guest:contact", "sustainability:calculator"):
            html = self.client.get(reverse(name)).content.decode()
            self.assertIn('rel="icon"', html, name)
            self.assertIn('rel="apple-touch-icon"', html, name)
            self.assertIn('property="og:title"', html, name)
            self.assertIn('content="http://testserver/static/img/brand/og-image.jpg"', html, name)
            self.assertIn('name="twitter:card" content="summary_large_image"', html, name)

    def test_sign_in_page_has_favicon(self):
        self.assertContains(self.client.get(reverse("access:login")), 'rel="icon"')

    def test_robots(self):
        r = self.client.get("/robots.txt")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r["Content-Type"], "text/plain; charset=utf-8")
        body = r.content.decode()
        for line in ("User-agent: *", "Disallow: /assets/", "Disallow: /admin/", "Allow: /impact/calculator/",
                     "Sitemap: http://testserver/sitemap.xml"):
            self.assertIn(line, body)
        self.assertNotIn("Disallow: /pricing/", body)

    def test_sitemap_lists_only_public_pages(self):
        r = self.client.get("/sitemap.xml")
        self.assertEqual(r.status_code, 200)
        body = r.content.decode()
        for path in ("/", "/how-it-works/", "/institution-blueprint/", "/impact/calculator/", "/pricing/", "/contact/"):
            self.assertIn(f"<loc>http://testserver{path}</loc>", body)
        self.assertEqual(body.count("<url>"), 6)
        self.assertNotIn("/assets/", body)

    def test_root_favicon_redirects_to_the_real_file(self):
        r = self.client.get("/favicon.ico")
        self.assertEqual(r.status_code, 301)
        self.assertEqual(r["Location"], "/static/img/brand/favicon.ico")
