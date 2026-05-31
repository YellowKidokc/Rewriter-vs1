import unittest

from app.core.change_guard import analyze_candidate


class ChangeGuardTests(unittest.TestCase):
    def test_flags_changed_numbers_and_dates(self) -> None:
        report = analyze_candidate(
            "The model reached 6.35 sigma in 2025.",
            "The model reached 7.00 sigma in 2024.",
        )
        self.assertEqual(report.meaning_risk, "high")
        self.assertTrue(any("number" in warning for warning in report.warnings))
        self.assertTrue(any("year/date" in warning for warning in report.warnings))

    def test_flags_claim_strength_increase(self) -> None:
        report = analyze_candidate(
            "The result suggests a structural relationship.",
            "The result proves a structural relationship.",
        )
        self.assertEqual(report.claim_strength_risk, "high")
        self.assertTrue(any("Claim strength increased" in warning for warning in report.warnings))

    def test_flags_lost_protected_terms(self) -> None:
        report = analyze_candidate(
            "Grace and Noether remain explicit in the proof layer.",
            "The proof layer remains explicit.",
        )
        self.assertEqual(report.meaning_risk, "medium")
        self.assertTrue(any("protected term" in warning for warning in report.warnings))


if __name__ == "__main__":
    unittest.main()
