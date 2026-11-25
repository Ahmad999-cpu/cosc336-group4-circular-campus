"""AI feature 1 (optional): registration suggestions from text and photo. Never applied without a click."""
from types import SimpleNamespace
from unittest import mock

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.ai.gateway import AIGateway
from apps.ai.models import AICapability, AIInferenceRecord, AIOutcome, ModelVersion
from apps.ai.result import AIResult
from apps.catalogue import services
from apps.catalogue.models import Asset, TagSource
from apps.common.enums import UserDecision
from apps.common.errors import Forbidden, ValidationFailed

from .factories import World

PNG = (b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
       b"\x00\x00\x00\rIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82")


class SuggestTests(TestCase):
    def setUp(self):
        self.w = World(qty=1)
        ModelVersion.objects.create(capability=AICapability.CLASSIFY, provider="fake", model_name="fake", version="c1",
                                    low_confidence_threshold="0.70").activate()

    def test_text_gives_category_tags_and_serial(self):
        s = services.suggest_details(self.w.custodian, {"name": "HP 27 inch display screen, S/N: CN42X7781"})
        self.assertTrue(s["ok"])
        self.assertEqual(s["category"], self.w.category)  # "Monitors"
        self.assertIn("monitor", s["tags"])
        self.assertEqual(s["serial_number"], "CN42X7781")
        self.assertFalse(s["low"])
        self.assertTrue(AIInferenceRecord.objects.filter(capability=AICapability.CLASSIFY).exists())

    def test_low_confidence_is_flagged(self):
        s = services.suggest_details(self.w.custodian, {"name": "Mystery box"})
        self.assertTrue(s["low"])
        self.assertIsNone(s["category"])

    def test_photo_is_sent_and_unknown_category_dropped(self):
        gw = mock.Mock(spec=AIGateway)
        gw.classify.return_value = AIResult(AIOutcome.OK, value={"category": "Spaceships", "tags": ["x"], "conditionGuess": "fair"}, confidence=0.9)
        photo = SimpleUploadedFile("m.png", PNG, content_type="image/png")
        s = services.suggest_details(self.w.custodian, {"name": ""}, photo=photo, gateway=gw)
        payload = gw.classify.call_args.args[0]
        self.assertEqual(payload["image"]["media_type"], "image/png")
        self.assertIn("Monitors", payload["categories"])
        self.assertIsNone(s["category"])
        self.assertEqual(s["condition"], "FAIR")
        self.assertTrue(s["used_photo"])

    def test_rules(self):
        with self.assertRaises(ValidationFailed):
            services.suggest_details(self.w.custodian, {"name": ""})
        with self.assertRaises(Forbidden):
            services.suggest_details(self.w.requester, {"name": "monitor"})
        ModelVersion.objects.filter(capability=AICapability.CLASSIFY).update(status="DISABLED")
        self.assertFalse(services.suggest_details(self.w.custodian, {"name": "monitor"})["ok"])

    def test_screen_flow_records_what_was_used(self):
        self.client.force_login(self.w.custodian)
        r = self.client.post(reverse("catalogue:suggest"), {"name": "Dell monitor 24 inch"})
        self.assertContains(r, "Suggestions")
        self.assertContains(r, 'data-ai-use="id_category"')
        inf = AIInferenceRecord.objects.get(capability=AICapability.CLASSIFY)
        r = self.client.post(reverse("catalogue:new"), {
            "name": "Dell monitor 24 inch", "category": self.w.category.pk, "owner_department": self.w.cs.pk, "quantity": 1,
            "condition": "GOOD", "location_campus": "Main", "tags": "monitor, 24-inch, spare", "ai_tags": "monitor,24-inch",
            "ai_used": "category,tags", "ai_inference": str(inf.pk)}, HTTP_HX_REQUEST="true")
        self.assertEqual(r.status_code, 200)
        a = Asset.objects.get(name="Dell monitor 24 inch")
        self.assertEqual(dict(a.tags.values_list("tag_text", "source")),
                         {"monitor": TagSource.AI_ACCEPTED, "24-inch": TagSource.AI_ACCEPTED, "spare": TagSource.MANUAL})
        inf.refresh_from_db()
        self.assertEqual((inf.user_decision, inf.decision_reason), (UserDecision.ACCEPTED, "category, tags"))


@override_settings(AI_PROVIDER="anthropic", ANTHROPIC_API_KEY="test-key", ANTHROPIC_MODEL="claude-haiku-5-5")
class AnthropicClassifyTests(TestCase):
    def test_image_block_and_parsing(self):
        from apps.ai.providers.anthropic import Provider
        p = Provider()
        reply = SimpleNamespace(content=[SimpleNamespace(type="text", text='{"category": "IT Equipment / Monitors", "tags": ["monitor"], "confidence": 0.93}')])
        with mock.patch.object(p.client.messages, "create", return_value=reply) as create:
            r = p.classify({"name": "screen", "categories": ["IT Equipment / Monitors"], "image": {"media_type": "image/png", "data": "AAAA"}},
                           SimpleNamespace(provider="fake", model_name="fake"))
        self.assertEqual((r.status, r.confidence), (AIOutcome.OK, 0.93))
        content = create.call_args.kwargs["messages"][0]["content"]
        self.assertEqual(content[0]["type"], "image")
        self.assertNotIn("AAAA", content[1]["text"])  # the image is sent once, as an image block
        with mock.patch.object(p.client.messages, "create", return_value=SimpleNamespace(content=[SimpleNamespace(text="nope")])):
            self.assertEqual(p.classify({"name": "x"}, None).status, AIOutcome.ERROR)
