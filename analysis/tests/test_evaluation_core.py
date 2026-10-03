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
    normalize_pit_test_name, build_base_to_keys, build_class_to_keys, resolve_killing_tests,
    select_original, select_original_legacy_edge_only,
    select_constructor_only_rule, select_class_level,
    load_json, load_pit_mutations, discover_pit_files,
    selected_set_sha256, exclude_non_leaf_oracle_records,
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

    def test_class_present_empty_footprint_not_selected_when_method_hit_exists(self):
        """An exact hit suppresses global class escalation."""
        selected = select_original(self.test_mappings, "com.example.Foo", "bar")
        self.assertNotIn("ClassOnlyTest#test_jkl3456", selected)

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

    def test_zero_hit_escalates_to_all_class_footprints(self):
        """No exact method hit selects every test covering the changed class."""
        selected = select_original(self.test_mappings, "com.example.Foo", "missing")
        self.assertIn("ClassOnlyTest#test_jkl3456", selected)
        self.assertIn("MixedTest#test_stu5678", selected)


class TestAdoptedNoCoveragePolicy(unittest.TestCase):
    def test_method_hit_union_empty(self):
        mappings = {
            "hit": {"classes": ["C"], "methods": ["C#m"]},
            "empty": {"classes": [], "methods": []},
            "other": {"classes": ["D"], "methods": ["D#n"]},
        }
        self.assertEqual(select_original(mappings, "C", "m"), {"hit", "empty"})

    def test_zero_method_hit_unions_class_and_empty(self):
        mappings = {
            "class": {"classes": ["C"], "methods": ["C#other"]},
            "empty": {"classes": None, "methods": None},
        }
        self.assertEqual(select_original(mappings, "C", "m"), {"class", "empty"})

    def test_zero_method_and_class_hits_still_selects_empty(self):
        mappings = {
            "empty": {},
            "other": {"classes": ["D"], "methods": ["D#n"]},
        }
        self.assertEqual(select_original(mappings, "C", "m"), {"empty"})

    def test_all_missing_null_empty_combinations_are_u(self):
        absent = object()
        values = [absent, None, []]
        mappings = {}
        expected = set()
        for left_index, classes in enumerate(values):
            for right_index, methods in enumerate(values):
                key = f"u-{left_index}-{right_index}"
                entry = {}
                if classes is not absent:
                    entry["classes"] = classes
                if methods is not absent:
                    entry["methods"] = methods
                mappings[key] = entry
                expected.add(key)
        self.assertEqual(select_original(mappings, "C", "m"), expected)

    def test_one_empty_list_other_nonempty_is_not_u(self):
        mappings = {
            "classes-only": {"classes": ["D"], "methods": []},
            "methods-only": {"classes": [], "methods": ["D#n"]},
        }
        self.assertEqual(select_original(mappings, "C", "m"), set())

    def test_type_c_with_other_coverage_is_not_u(self):
        mappings = {"type-c": {"classes": ["D"], "methods": ["D#n"]}}
        self.assertEqual(select_original(mappings, "C", "m"), set())

    def test_constructor_rule_not_u_recovers_constructor_only(self):
        mappings = {
            "hit": {"classes": ["C"], "methods": ["C#m"]},
            "ctor": {"classes": ["C"], "methods": ["C#<init>"]},
        }
        self.assertNotIn("ctor", select_original(mappings, "C", "m"))
        self.assertIn("ctor", select_constructor_only_rule(mappings, "C", "m"))

    def test_overloads_share_name_level_key(self):
        mappings = {"hit": {"classes": ["C"], "methods": ["C#m"]}}
        self.assertEqual(select_original(mappings, "C", "m"), {"hit"})

    def test_malformed_non_list_values_raise(self):
        with self.assertRaises(ValueError):
            select_original({"bad": {"classes": "C", "methods": []}}, "C", "m")
        with self.assertRaises(ValueError):
            select_original({"bad": {"classes": [], "methods": "C#m"}}, "C", "m")

    def test_control_without_empty_entries_equals_legacy(self):
        mappings = {
            "hit": {"classes": ["C"], "methods": ["C#m"]},
            "other": {"classes": ["D"], "methods": ["D#n"]},
        }
        self.assertEqual(
            select_original(mappings, "C", "m"),
            select_original_legacy_edge_only(mappings, "C", "m"),
        )

    def test_five_spring_security_records_flip_via_six_empty_killers(self):
        root = Path(__file__).resolve().parents[2]
        with gzip.open(root / "spring-security/results/test-coverage-map.json.gz", "rt") as stream:
            mappings = json.load(stream)["testMappings"]
        sensitivity = json.loads(
            (root / "analysis/v14_4_checks/no_coverage_sensitivity.json").read_text()
        )
        records = sensitivity["recordsWhoseStpInclusivenessChanges"]
        self.assertEqual(len(records), 5)
        killers = set()
        for record in records:
            new = select_original(mappings, record["mutatedClass"], record["mutatedMethod"])
            legacy = select_original_legacy_edge_only(
                mappings, record["mutatedClass"], record["mutatedMethod"]
            )
            record_killers = set(record["newlySelectedKillingTests"])
            killers.update(record_killers)
            self.assertTrue(new & record_killers)
            self.assertFalse(legacy & record_killers)
            for killer in record_killers:
                self.assertFalse(mappings[killer].get("classes"))
                self.assertFalse(mappings[killer].get("methods"))
        self.assertEqual(len(killers), 6)


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

    def test_junit3_legacy_identifier(self):
        pit_id = (
            "org.joda.time.TestDateTimeUtils.testSystemMillis"
            "(org.joda.time.TestDateTimeUtils)"
        )
        self.assertEqual(
            normalize_pit_test_name(pit_id),
            "TestDateTimeUtils#testSystemMillis",
        )

    def test_junit3_legacy_identifier_rejects_mismatched_class(self):
        pit_id = "example.FooTest.testThing(example.OtherTest)"
        self.assertIsNone(normalize_pit_test_name(pit_id))

    def test_parameterized_multiple_coverage_keys(self):
        """One normalized ID can map to multiple hash-suffixed coverage keys."""
        test_mappings = {
            "FooTest#testParam_aaa1111": {"classes": [], "methods": []},
            "FooTest#testParam_bbb2222": {"classes": [], "methods": []},
        }
        base_to_keys = build_base_to_keys(test_mappings)
        self.assertEqual(len(base_to_keys["FooTest#testParam"]), 2)


class TestResolution(unittest.TestCase):

    def test_class_container_resolves_by_exact_execution_identity_fqn(self):
        test_mappings = {
            "FooTest#first_aaa1111": {"classes": [], "methods": []},
            "FooTest#second_bbb2222": {"classes": [], "methods": []},
        }
        identities = {
            key: {"testClassFqn": "com.example.FooTest"}
            for key in test_mappings
        }
        pit_id = "[engine:custom]/[class:com.example.FooTest]"
        raw = [RawMutation(
            mutation_id="test|Foo|bar|(V)|1|Mutator|indexes=unknown|blocks=unknown",
            mutated_class="Foo", mutated_method="bar", method_description="(V)",
            line_number=1, mutator="Mutator", indexes=None, blocks=None,
            raw_killing_test_ids=(pit_id,), source_xml="test.xml", xml_ordinal=0,
        )]
        resolved = resolve_killing_tests(
            raw, test_mappings, build_base_to_keys(test_mappings),
            build_class_to_keys(test_mappings, identities),
        )
        killing = resolved[0].killing_tests[0]
        self.assertEqual(killing.resolution_mode, "class-container-multiple")
        self.assertEqual(set(killing.coverage_keys), set(test_mappings))

    def test_legacy_junit4_class_container_resolves_by_exact_fqn(self):
        test_mappings = {
            "RatingsTest#testRatings_aaa1111": {"classes": [], "methods": []},
        }
        identities = {
            "RatingsTest#testRatings_aaa1111": {
                "testClassFqn": "com.example.RatingsTest"
            }
        }
        raw = [RawMutation(
            mutation_id="test|Foo|bar|(V)|1|Mutator|indexes=unknown|blocks=unknown",
            mutated_class="Foo", mutated_method="bar", method_description="(V)",
            line_number=1, mutator="Mutator", indexes=None, blocks=None,
            raw_killing_test_ids=("com.example.RatingsTest",),
            source_xml="test.xml", xml_ordinal=0,
        )]
        resolved = resolve_killing_tests(
            raw, test_mappings, build_base_to_keys(test_mappings),
            build_class_to_keys(test_mappings, identities),
        )
        killing = resolved[0].killing_tests[0]
        self.assertEqual(killing.normalized_id, "com.example.RatingsTest")
        self.assertEqual(killing.coverage_keys, ("RatingsTest#testRatings_aaa1111",))

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


class TestOracleExclusions(unittest.TestCase):

    def test_excludes_only_audited_project_record(self):
        first = ResolvedMutation(
            mutation_id="keep", mutated_class="Foo", mutated_method="a",
            method_description="()V", line_number=1, mutator="M",
            indexes=None, blocks=None, killing_tests=(), source_xml="x", xml_ordinal=1,
        )
        second = ResolvedMutation(
            mutation_id="exclude", mutated_class="Foo", mutated_method="b",
            method_description="()V", line_number=2, mutator="M",
            indexes=None, blocks=None, killing_tests=(), source_xml="x", xml_ordinal=2,
        )
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "analysis").mkdir()
            (root / "analysis" / "oracle_exclusions.json").write_text(json.dumps({
                "records": [{"project": "subject", "mutationId": "exclude"}]
            }))
            result = exclude_non_leaf_oracle_records([first, second], root, "subject")
        self.assertEqual([mutation.mutation_id for mutation in result], ["keep"])

    def test_fails_closed_for_stale_exclusion(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "analysis").mkdir()
            (root / "analysis" / "oracle_exclusions.json").write_text(json.dumps({
                "records": [{"project": "subject", "mutationId": "missing"}]
            }))
            with self.assertRaisesRegex(ValueError, "configured oracle exclusions not present"):
                exclude_non_leaf_oracle_records([], root, "subject")

    def test_subject_local_legacy_path_matches_canonical_exclusion(self):
        mutation = ResolvedMutation(
            mutation_id="subject|Foo|m|()V|1|M|indexes=unknown|blocks=unknown|ordinal=results/per-class/Foo/mutations.xml:1",
            mutated_class="Foo", mutated_method="m", method_description="()V",
            line_number=1, mutator="M", indexes=None, blocks=None,
            killing_tests=(), source_xml="results/per-class/Foo/mutations.xml", xml_ordinal=1,
        )
        canonical = mutation.mutation_id.replace("ordinal=results/", "ordinal=subject/results/")
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "analysis").mkdir()
            (root / "analysis" / "oracle_exclusions.json").write_text(json.dumps({
                "records": [{"project": "subject", "mutationId": canonical}]
            }))
            self.assertEqual(exclude_non_leaf_oracle_records([mutation], root, "subject"), [])


if __name__ == "__main__":
    unittest.main()
