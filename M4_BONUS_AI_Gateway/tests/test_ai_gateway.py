import time

from django.test import TestCase

from apps.ai import gateway as gw
from apps.ai.models import AICapability, AIInferenceRecord, AIOutcome, ModelVersion
from apps.ai.providers.fake import Provider as Fake


class SlowProvider(Fake):
    def classify(self, payload, mv):
        time.sleep(2)
        return super().classify(payload, mv)


class GatewayTests(TestCase):
    def setUp(self):
        ModelVersion.objects.create(capability=AICapability.CLASSIFY, provider="fake", model_name="fake",
                                    version="t", low_confidence_threshold="0.70").activate()

    def test_ok_and_logged(self):
        r = gw.AIGateway(Fake()).classify({"name": "24-inch monitor", "email": "x@y.z", "categories": ["IT Equipment / Monitors"]})
        self.assertEqual(r.status, AIOutcome.OK)
        self.assertEqual(r.value["category"], "IT Equipment / Monitors")
        self.assertTrue(AIInferenceRecord.objects.filter(pk=r.inference_id).exists())

    def test_low_confidence_is_flagged(self):
        self.assertEqual(gw.AIGateway(Fake()).classify({"name": "thing"}).status, AIOutcome.LOW_CONFIDENCE)

    def test_disabled_model_means_unavailable(self):
        ModelVersion.objects.get(capability=AICapability.CLASSIFY).disable()
        self.assertEqual(gw.AIGateway(Fake()).classify({"name": "monitor"}).status, AIOutcome.UNAVAILABLE)

    def test_timeout_returns_quickly(self):
        old = gw.TIME_LIMITS[AICapability.CLASSIFY]
        gw.TIME_LIMITS[AICapability.CLASSIFY] = 0.3
        try:
            start = time.monotonic()
            r = gw.AIGateway(SlowProvider()).classify({"name": "monitor"})
            self.assertEqual(r.status, AIOutcome.TIMEOUT)
            self.assertLess(time.monotonic() - start, 1.5)
        finally:
            gw.TIME_LIMITS[AICapability.CLASSIFY] = old

    def test_personal_fields_are_removed(self):
        self.assertNotIn("email", gw._redact({"name": "a", "email": "x"}))
