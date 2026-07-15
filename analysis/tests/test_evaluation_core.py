"""Unit tests for evaluation_core.py"""

import gzip
import json
import tempfile
import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from analysis.evaluation_core import (
    RawMutation, ResolvedKillingTest, ResolvedMutation,
    normalize_pit_test_name, build_base_to_keys, resolve_killing_tests,
    select_original, select_constructor_only_rule, select_class_level,
    load_json, load_pit_mutations, discover_pit_files,
    selected_set_sha256,
)


class TestSelectors(unittest.TestCase):
    """Tests for the three frozen selector definitions."""

    def setUp(self):
        self.test_mappings = {
            "FooTest#testBar_abc1234": {
                "classes": ["com.example.Foo"],
                "methods": ["com.example.Foo#bar", "com.example.Foo#<init>"]
            },
            "FooTest#testBaz_def5678": {
                "classes": ["com.example.Foo"],
                "methods": ["com.example.Foo#baz"]
            },
            "InitOnlyTest#test_ghi9012": {
                "classes": ["com.example.Foo"],
                "methods": ["com.example.Foo#<init>"]
            },
            "ClassOnlyTest#test_jkl3456": {
                "classes": ["com.example.Foo"],
                "methods": []  # no method info for Foo
            },
            "OtherTest#test_mno7890": {
                "classes": ["com.example.Other"],
                "methods": ["com.example.Other#doSomething"]
            },
            "ClinitTest#test_pqr1234": {
                "classes": ["com.example.Foo"],
                "methods": ["com.example.Foo#<init>", "com.example.Foo#<clinit>"]
            },
            "MixedTest#test_stu5678": {
                "classes": ["com.example.Foo"],
                "methods": ["com.example.Foo#<init>", "com.example.Foo#helper"]
            },
        }

    def test_exact_method_match(self):
        selected = select_original(self.test_mappings, "com.example.Foo", "bar")
        self.assertIn("FooTest#testBar_abc1234", selected)

    def test_class_present_empty_footprint_selected_by_original(self):
        """Class present + no method info for class -> Original selects (fallback)."""
        selected = select_original(self.test_mappings, "com.example.Foo", "bar")
        self.assertIn("ClassOnlyTest#test_jkl3456", selected)

    def test_constructor_only_footprint_skipped_by_original(self):
        """Test with only <init> is NOT selected by Original for method change."""
        selected = select_original(self.test_mappings, "com.example.Foo", "bar")
        self.assertNotIn("InitOnlyTest#test_ghi9012", selected)

    def test_constructor_only_footprint_selected_by_rule(self):
        """Constructor-only rule adds tests with only <init>/<clinit> footprint."""
        selected = select_constructor_only_rule(self.test_mappings, "com.example.Foo", "bar")
        self.assertIn("InitOnlyTest#test_ghi9012", selected)
        self.assertIn("ClinitTest#test_pqr1234", selected)

    def test_non_constructor_non_target_not_selected(self):
        """Test with non-target non-constructor method not selected by either."""
        original = select_original(self.test_mappings, "com.example.Foo", "bar")
        constructor = select_constructor_only_rule(self.test_mappings, "com.example.Foo", "bar")
        # MixedTest has <init> + helper -- not all constructors
        self.assertNotIn("MixedTest#test_stu5678", original)
        self.assertNotIn("MixedTest#test_stu5678", constructor)

    def test_type_c_no_selector_finds(self):
        """Test not covering target class is never selected."""
        original = select_original(self.test_mappings, "com.example.Foo", "bar")
        constructor = select_constructor_only_rule(self.test_mappings, "com.example.Foo", "bar")
        class_level = select_class_level(self.test_mappings, "com.example.Foo", "bar")
        self.assertNotIn("OtherTest#test_mno7890", original)
        self.assertNotIn("OtherTest#test_mno7890", constructor)
        self.assertNotIn("OtherTest#test_mno7890", class_level)

    def test_class_level_selects_all_covering(self):
        """Class-level baseline selects all tests with class in classes list."""
        selected = select_class_level(self.test_mappings, "com.example.Foo", "bar")
        foo_tests = {k for k, v in self.test_mappings.items() if "com.example.Foo" in v["classes"]}
        self.assertEqual(selected, foo_tests)

    def test_constructor_plus_clinit_is_type_a(self):
        """<init> + <clinit> should be treated as constructor-only (Type A)."""
        selected = select_constructor_only_rule(self.test_mappings, "com.example.Foo", "bar")
        self.assertIn("ClinitTest#test_pqr1234", selected)

    def test_constructor_plus_regular_method_is_type_b(self):
        """<init> + regular method should NOT be selected by constructor-only rule."""
        selected = select_constructor_only_rule(self.test_mappings, "com.example.Foo", "bar")
        self.assertNotIn("MixedTest#test_stu5678", selected)

    def test_classPresentNoMethods_invariant(self):
        """Test with class present but no methods IS selected by Original (fallback)."""
        selected = select_original(self.test_mappings, "com.example.Foo", "bar")
        self.assertIn("ClassOnlyTest#test_jkl3456", selected)


class TestNormalization(unittest.TestCase):

    def test_regular_method(self):
        pit_id = "[engine:junit-jupiter]/[class:com.example.FooTest]/[method:testBar()]"
        self.assertEqual(normalize_pit_test_name(pit_id), "FooTest#testBar")

    def test_nested_class(self):
        pit_id = "[engine:junit-jupiter]/[class:com.example.Outer]/[nested-class:Inner]/[method:test()]"
        self.assertEqual(normalize_pit_test_name(pit_id), "Inner#test")

    def test_parameterized(self):
        pit_id = "[engine:junit-jupiter]/[class:com.example.FooTest]/[test-template:testParam(int)]/[test-template-invocation:#1]"
        self.assertEqual(normalize_pit_test_name(pit_id), "FooTest#testParam")

    def test_unparseable_returns_none(self):
        self.assertIsNone(normalize_pit_test_name("some garbage"))

    def test_parameterized_multiple_coverage_keys(self):
        """One normalized ID can map to multiple hash-suffixed coverage keys."""
        test_mappings = {
            "FooTest#testParam_aaa1111": {"classes": [], "methods": []},
            "FooTest#testParam_bbb2222": {"classes": [], "methods": []},
        }
        base_to_keys = build_base_to_keys(test_mappings)
        self.assertEqual(len(base_to_keys["FooTest#testParam"]), 2)


class TestResolution(unittest.TestCase):

    def test_unparseable_pit_id_hard_fail(self):
        raw = [RawMutation(
            mutation_id="test|Foo|bar|(V)|1|Mutator|indexes=unknown|blocks=unknown",
            mutated_class="Foo", mutated_method="bar",
            method_description="(V)", line_number=1, mutator="Mutator",
            indexes=None, blocks=None,
            raw_killing_test_ids=("garbage_not_parseable",),
            source_xml="test.xml", xml_ordinal=0,
        )]
        with self.assertRaises(ValueError):
            resolve_killing_tests(raw, {}, {})

    def test_unresolved_normalized_hard_fail(self):
        pit_id = "[engine:junit-jupiter]/[class:com.example.FooTest]/[method:testBar()]"
        raw = [RawMutation(
            mutation_id="test|Foo|bar|(V)|1|Mutator|indexes=unknown|blocks=unknown",
            mutated_class="Foo", mutated_method="bar",
            method_description="(V)", line_number=1, mutator="Mutator",
            indexes=None, blocks=None,
            raw_killing_test_ids=(pit_id,),
            source_xml="test.xml", xml_ordinal=0,
        )]
        # Empty maps -- nothing to resolve to
        with self.assertRaises(ValueError):
            resolve_killing_tests(raw, {}, {})

    def test_one_pit_id_resolves_to_multiple_entries_different_types(self):
        """One PIT killing ID -> two coverage entries with different footprints."""
        test_mappings = {
            "FooTest#testParam_aaa1111": {
                "classes": ["com.example.Foo"],
                "methods": ["com.example.Foo#<init>"]  # Type A
            },
            "FooTest#testParam_bbb2222": {
                "classes": ["com.example.Foo"],
                "methods": ["com.example.Foo#<init>", "com.example.Foo#helper"]  # Type B
            },
        }
        base_to_keys = build_base_to_keys(test_mappings)
        pit_id = "[engine:junit-jupiter]/[class:com.example.FooTest]/[method:testParam()]"

        raw = [RawMutation(
            mutation_id="test|com.example.Foo|bar|(V)|1|Mutator|indexes=unknown|blocks=unknown",
            mutated_class="com.example.Foo", mutated_method="bar",
            method_description="(V)", line_number=1, mutator="Mutator",
            indexes=None, blocks=None,
            raw_killing_test_ids=(pit_id,),
            source_xml="test.xml", xml_ordinal=0,
        )]

        resolved = resolve_killing_tests(raw, test_mappings, base_to_keys)
        self.assertEqual(len(resolved), 1)
        kt = resolved[0].killing_tests[0]
        self.assertEqual(kt.resolution_mode, "base-name-multiple")
        self.assertEqual(len(kt.coverage_keys), 2)


class TestLoadJson(unittest.TestCase):

    def test_plain_json(self):
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
            json.dump({"key": "value"}, f)
            path = Path(f.name)
        try:
            result = load_json(path)
            self.assertEqual(result, {"key": "value"})
        finally:
            path.unlink()

    def test_gzip_json(self):
        data = {"key": "value"}
        with tempfile.NamedTemporaryFile(suffix=".json.gz", delete=False) as f:
            path = Path(f.name)
        try:
            with gzip.open(path, "wt", encoding="utf-8") as gz:
                json.dump(data, gz)
            result = load_json(path)
            self.assertEqual(result, {"key": "value"})
        finally:
            path.unlink()

    def test_plain_and_gz_produce_same_content(self):
        data = {"tests": [1, 2, 3], "nested": {"a": "b"}}
        with tempfile.TemporaryDirectory() as td:
            plain = Path(td) / "data.json"
            gz = Path(td) / "data.json.gz"
            plain.write_text(json.dumps(data))
            with gzip.open(gz, "wt", encoding="utf-8") as f:
                json.dump(data, f)
            self.assertEqual(load_json(plain), load_json(gz))


class TestSelectedSetHash(unittest.TestCase):

    def test_deterministic(self):
        s1 = selected_set_sha256({"b", "a", "c"})
        s2 = selected_set_sha256({"c", "a", "b"})
        self.assertEqual(s1, s2)

    def test_different_sets_different_hash(self):
        s1 = selected_set_sha256({"a", "b"})
        s2 = selected_set_sha256({"a", "c"})
        self.assertNotEqual(s1, s2)


if __name__ == "__main__":
    unittest.main()
