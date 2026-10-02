import unittest

from analysis.analyze_failure_modes import (
    causal_mechanism_for,
    footprint_type_for,
)


class FailureClassificationTest(unittest.TestCase):
    def test_single_footprint_type_is_preserved(self):
        self.assertEqual("C", footprint_type_for(["C", "C"]))

    def test_different_killing_test_footprints_are_mixed(self):
        self.assertEqual("MIXED", footprint_type_for(["B", "C"]))

    def test_footprint_does_not_determine_cause(self):
        self.assertEqual(
            "EARLY_EXCEPTION_PROBE_SHADOWING",
            causal_mechanism_for("early-exception-before-probe"),
        )
        self.assertEqual(
            "PRE_TEST_ATTRIBUTION_GAP",
            causal_mechanism_for("pre-test-custom-engine-enhancement"),
        )

    def test_unknown_cause_fails_closed(self):
        with self.assertRaises(ValueError):
            causal_mechanism_for("unknown")


if __name__ == "__main__":
    unittest.main()
