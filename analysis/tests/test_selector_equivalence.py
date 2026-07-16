"""
test_selector_equivalence.py -- Unit tests for verify_selector_equivalence.py

Tests the dataset-wide verifier AND proves it detects the two known general
semantic divergences between Python select_original and Java TestSelector:

1. Python-only per-test fallback: when method hits exist but a test has class
   presence without any method entries for that class, Python selects it but
   Java does not.

2. Java zero-hit escalation: when NO test covers C#M at method level, Java
   escalates to class-level for all tests covering C, while Python only selects
   tests with no C#* methods.
"""

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from analysis.evaluation_core import select_original
from analysis.verify_selector_equivalence import java_semantic_select


class TestJavaSemanticModel(unittest.TestCase):
    """Test the java_semantic_select function directly."""

    def test_method_hit_exact_match(self):
        """When method hits exist, both selectors agree on method-matched tests."""
        tm = {
            "TestA_abc1234": {
                "classes": ["com.example.Foo"],
                "methods": ["com.example.Foo#doWork", "com.example.Foo#helper"],
            },
            "TestB_def5678": {
                "classes": ["com.example.Foo"],
                "methods": ["com.example.Foo#helper"],
            },
        }
        java = java_semantic_select(tm, "com.example.Foo", "doWork")
        python = select_original(tm, "com.example.Foo", "doWork")
        # Both should select only TestA (covers Foo#doWork)
        self.assertEqual(java, {"TestA_abc1234"})
        self.assertEqual(python, {"TestA_abc1234"})
        self.assertEqual(java, python)

    def test_class_level_fallback_no_methods(self):
        """When a test has class presence but no method entries, Python's per-test
        fallback selects it; Java does not (because method hits exist elsewhere)."""
        tm = {
            "TestA_abc1234": {
                "classes": ["com.example.Foo"],
                "methods": ["com.example.Foo#doWork"],
            },
            "TestB_def5678": {
                "classes": ["com.example.Foo"],
                "methods": [],  # No method info for Foo
            },
        }
        java = java_semantic_select(tm, "com.example.Foo", "doWork")
        python = select_original(tm, "com.example.Foo", "doWork")

        # Java: TestA matches via method hit. No escalation (hits > 0).
        # TestB is NOT selected (class-level fallback doesn't apply in Java here).
        self.assertEqual(java, {"TestA_abc1234"})

        # Python: TestA via method match. TestB via per-test fallback (Foo in classes,
        # no Foo# methods for this test).
        self.assertEqual(python, {"TestA_abc1234", "TestB_def5678"})

        # DIVERGENCE: Python is a superset
        self.assertNotEqual(java, python)
        self.assertTrue(python.issuperset(java))
        self.assertEqual(python - java, {"TestB_def5678"})

    def test_java_escalation_zero_hits(self):
        """When NO test covers C#M, Java escalates to all tests covering C.
        Python only selects tests where C is present but has no C# methods."""
        tm = {
            "TestA_abc1234": {
                "classes": ["com.example.Foo"],
                "methods": ["com.example.Foo#otherMethod"],
            },
            "TestB_def5678": {
                "classes": ["com.example.Foo"],
                "methods": [],  # No method info
            },
            "TestC_ghi9012": {
                "classes": ["com.example.Bar"],
                "methods": ["com.example.Bar#something"],
            },
        }
        java = java_semantic_select(tm, "com.example.Foo", "missingMethod")
        python = select_original(tm, "com.example.Foo", "missingMethod")

        # Java: zero method hits for Foo#missingMethod -> escalate to class-level.
        # ALL tests covering Foo are selected: TestA and TestB.
        self.assertEqual(java, {"TestA_abc1234", "TestB_def5678"})

        # Python: Foo#missingMethod not in any test's methods.
        # TestA: Foo in classes, but has Foo#otherMethod -> NOT selected (has method info).
        # TestB: Foo in classes, no Foo# methods -> selected via per-test fallback.
        self.assertEqual(python, {"TestB_def5678"})

        # DIVERGENCE: Java is a superset
        self.assertNotEqual(java, python)
        self.assertTrue(java.issuperset(python))
        self.assertEqual(java - python, {"TestA_abc1234"})

    def test_no_coverage_at_all(self):
        """When no test covers the class at all, both return empty."""
        tm = {
            "TestX_abc1234": {
                "classes": ["com.example.Other"],
                "methods": ["com.example.Other#foo"],
            },
        }
        java = java_semantic_select(tm, "com.example.Missing", "method")
        python = select_original(tm, "com.example.Missing", "method")
        self.assertEqual(java, set())
        self.assertEqual(python, set())

    def test_constructor_only_footprint(self):
        """Test with constructor-only footprint -- both behave the same when
        method hits exist for the changed method elsewhere."""
        tm = {
            "TestA_abc1234": {
                "classes": ["com.example.Foo"],
                "methods": ["com.example.Foo#doWork"],
            },
            "TestB_def5678": {
                "classes": ["com.example.Foo"],
                "methods": ["com.example.Foo#<init>"],
            },
        }
        java = java_semantic_select(tm, "com.example.Foo", "doWork")
        python = select_original(tm, "com.example.Foo", "doWork")

        # Java: TestA has method hit. No escalation. TestB not selected.
        self.assertEqual(java, {"TestA_abc1234"})

        # Python: TestA via method match. TestB: Foo in classes, HAS Foo#<init>
        # method entry -> NOT selected (has method info for Foo).
        self.assertEqual(python, {"TestA_abc1234"})

        # No divergence for this case
        self.assertEqual(java, python)


class TestDatasetVerification(unittest.TestCase):
    """Test that the full dataset verification runs and produces expected structure."""

    def test_report_structure(self):
        """Verify the committed report has required fields."""
        report_path = REPO_ROOT / "results" / "selector_equivalence.json"
        if not report_path.exists():
            self.skipTest("selector_equivalence.json not yet generated")

        with open(report_path) as f:
            report = json.load(f)

        self.assertIn("mutationOccurrences", report)
        self.assertIn("uniqueSelectorCases", report)
        self.assertIn("exactMatches", report)
        self.assertIn("mismatches", report)
        self.assertIn("mutationOccurrencesWithMethodHits", report)
        self.assertIn("mutationOccurrencesWithZeroMethodHits", report)
        self.assertIn("mutationOccurrencesWithPythonOnlyFallback", report)
        self.assertIn("byProject", report)
        self.assertIn("differences", report)

        # For our dataset: all matches, no mismatches
        self.assertEqual(report["mismatches"], 0)
        self.assertEqual(report["exactMatches"], report["mutationOccurrences"])
        self.assertEqual(report["mutationOccurrencesWithZeroMethodHits"], 0)
        self.assertEqual(report["mutationOccurrencesWithPythonOnlyFallback"], 0)


import json

if __name__ == "__main__":
    unittest.main()
