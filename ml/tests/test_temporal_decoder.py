import unittest

from chatsl_ml.temporal_decoder import TemporalSignDecoder


def window(
    motion: float,
    label: str | None = None,
    confidence: float = 0.0,
) -> dict:
    prediction = (
        {"label": label, "confidence": confidence}
        if label is not None
        else None
    )
    return {
        "accepted": prediction is not None,
        "prediction": prediction,
        "quality": {"motion_score": motion},
    }


class TemporalSignDecoderTests(unittest.TestCase):
    def test_idle_windows_do_not_commit(self):
        decoder = TemporalSignDecoder()

        for _ in range(5):
            update = decoder.update(window(0.005, "yanlis", 0.99))

        self.assertEqual(update.phase, "idle")
        self.assertIsNone(update.committed)

    def test_commits_winner_when_motion_ends(self):
        decoder = TemporalSignDecoder()

        decoder.update(window(0.05, "selam", 0.72))
        decoder.update(window(0.06, "selam", 0.81))
        decoder.update(window(0.04, "evet", 0.55))
        update = decoder.update(window(0.01))

        self.assertEqual(update.committed["label"], "selam")
        self.assertEqual(update.committed["votes"], 2)

    def test_high_confidence_single_window_can_commit(self):
        decoder = TemporalSignDecoder()

        decoder.update(window(0.06, "tamam", 0.93))
        update = decoder.update(window(0.01))

        self.assertEqual(update.committed["label"], "tamam")

    def test_same_label_can_repeat_after_a_quiet_release_window(self):
        decoder = TemporalSignDecoder()

        decoder.update(window(0.06, "evet", 0.95))
        first = decoder.update(window(0.01))
        decoder.update(window(0.01))
        decoder.update(window(0.06, "evet", 0.96))
        repeated = decoder.update(window(0.01))

        self.assertEqual(first.committed["label"], "evet")
        self.assertEqual(repeated.committed["label"], "evet")


if __name__ == "__main__":
    unittest.main()
