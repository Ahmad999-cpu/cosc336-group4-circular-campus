"""The demo data loads (twice, without duplicates) and the Phase 7 matching evaluation runs on it."""
import io
import tempfile
from pathlib import Path

from django.core.management import call_command
from django.test import TestCase

from apps.access.models import User
from apps.catalogue.models import Asset
from apps.matching.models import MatchResultSet
from apps.sustainability.models import EmissionFactor


class DemoDataTests(TestCase):
    def test_seed_is_repeatable(self):
        call_command("seed_demo", stdout=io.StringIO())
        counts = (User.objects.count(), Asset.objects.count(), EmissionFactor.objects.count())
        call_command("seed_demo", stdout=io.StringIO())
        self.assertEqual(counts, (User.objects.count(), Asset.objects.count(), EmissionFactor.objects.count()))
        self.assertTrue(User.objects.filter(email="club@demo.local").exists())
        self.assertGreaterEqual(EmissionFactor.objects.count(), 8)

    def test_matching_evaluation_runs_and_saves_nothing(self):
        call_command("seed_demo", stdout=io.StringIO())
        out = io.StringIO()
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "m.md"
            call_command("evaluate_matching", out=str(path), stdout=out)
            self.assertIn("Hit@1", path.read_text(encoding="utf-8"))
        self.assertIn("| All (25) |", out.getvalue())
        self.assertFalse(MatchResultSet.objects.exists())  # rolled back
