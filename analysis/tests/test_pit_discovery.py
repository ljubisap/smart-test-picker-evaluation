"""
test_pit_discovery.py -- Regression test for PIT file discovery with absolute paths.

Verifies that JGraphT evaluation scripts can discover and load PIT mutations
from a results directory outside the repository root (absolute path).
"""

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from analysis.evaluation_core import load_pit_mutations, load_coverage_map, build_base_to_keys, resolve_killing_tests, is_valid_target_tests


class TestPitDiscoveryAbsolutePath(unittest.TestCase):
    """Test that PIT file loading works with absolute paths outside REPO_ROOT."""

    def setUp(self):
        """Copy a subset of PIT files to a temp directory."""
        self.tmpdir = Path(tempfile.mkdtemp())
        # Copy one class's PIT results
        src = REPO_ROOT / "jgrapht" / "results" / "per-class" / "org.jgrapht.alg.color.GreedyColoring"
        dst = self.tmpdir / "per-class" / "org.jgrapht.alg.color.GreedyColoring"
        shutil.copytree(src, dst)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_glob_discovery_outside_repo(self):
        """PIT files in /tmp should be discoverable and loadable."""
        pit_base = self.tmpdir / "per-class"
        pit_files = sorted(
            list(pit_base.glob("*/mutations.xml")) + list(pit_base.glob("*/mutations.xml.gz")),
            key=lambda p: p.as_posix()
        )
        self.assertTrue(len(pit_files) > 0, "Should find at least one mutations.xml")

        # load_pit_mutations needs a root for relative path computation
        pit_root = self.tmpdir
        raw = load_pit_mutations("jgrapht", pit_root, tuple(pit_files))
        self.assertTrue(len(raw) > 0, "Should parse KILLED mutations from external path")

    def test_resolve_with_external_pit_and_repo_coverage(self):
        """External PIT + repo coverage map should resolve killing tests."""
        pit_base = self.tmpdir / "per-class"
        pit_files = sorted(
            list(pit_base.glob("*/mutations.xml")) + list(pit_base.glob("*/mutations.xml.gz")),
            key=lambda p: p.as_posix()
        )
        pit_root = self.tmpdir
        raw = load_pit_mutations("jgrapht", pit_root, tuple(pit_files))

        # Load canonical coverage map
        map_path = REPO_ROOT / "jgrapht" / "results" / "test-coverage-map.json.gz"
        coverage_data = load_coverage_map(map_path)
        test_mappings = coverage_data["testMappings"]
        base_to_keys = build_base_to_keys(test_mappings)

        # Should resolve without crashing
        resolved = resolve_killing_tests(raw, test_mappings, base_to_keys)
        self.assertTrue(len(resolved) > 0)


class TestSampleClassesConfig(unittest.TestCase):
    """Validate that all sample_classes.json files have required fields."""

    REQUIRED_FIELDS = {"fqn", "targetTests", "loc"}
    SUBPACKAGE_FIELDS = {"subpackage", "subpkg"}  # projects use one or the other

    def _check_project(self, project_name, config_path, require_tests_field=False):
        with open(config_path) as f:
            config = json.load(f)
        classes = config.get("classes", [])
        self.assertTrue(len(classes) > 0, f"{project_name}: no classes")
        fqns = set()
        for i, cls in enumerate(classes):
            for field in self.REQUIRED_FIELDS:
                self.assertIn(field, cls, f"{project_name} class {i} ({cls.get('fqn','?')}): missing '{field}'")
            has_subpkg = bool(self.SUBPACKAGE_FIELDS & set(cls.keys()))
            self.assertTrue(has_subpkg, f"{project_name} class {i} ({cls.get('fqn','?')}): missing subpackage/subpkg")
            # loc must be positive integer
            self.assertIsInstance(cls["loc"], int, f"{project_name} {cls['fqn']}: loc not int")
            self.assertGreater(cls["loc"], 0, f"{project_name} {cls['fqn']}: loc must be positive")
            # targetTests must be a valid package wildcard or FQCN list
            tt = cls["targetTests"]
            self.assertTrue(is_valid_target_tests(tt), f"{project_name} {cls['fqn']}: targetTests '{tt}' is not valid (must be pkg.* wildcard or comma-separated FQCNs)")
            # fqn uniqueness
            self.assertNotIn(cls["fqn"], fqns, f"{project_name}: duplicate fqn {cls['fqn']}")
            fqns.add(cls["fqn"])
            # tests field (required for spring-core)
            if require_tests_field:
                self.assertIn("tests", cls, f"{project_name} {cls['fqn']}: missing 'tests'")
                self.assertIsInstance(cls["tests"], int, f"{project_name} {cls['fqn']}: tests not int")
                self.assertGreater(cls["tests"], 0, f"{project_name} {cls['fqn']}: tests must be positive")

    def test_commons_lang_config(self):
        self._check_project("commons-lang", REPO_ROOT / "commons-lang" / "config" / "sample_classes.json")

    def test_jgrapht_config(self):
        self._check_project("jgrapht", REPO_ROOT / "jgrapht" / "config" / "sample_classes.json")

    def test_spring_core_config(self):
        self._check_project("spring-core", REPO_ROOT / "spring-core" / "config" / "sample_classes.json", require_tests_field=True)


class TestTargetTestsValidation(unittest.TestCase):
    """Unit tests for is_valid_target_tests validation function."""

    def test_valid_wildcard(self):
        self.assertTrue(is_valid_target_tests("org.springframework.core.*"))
        self.assertTrue(is_valid_target_tests("org.apache.commons.lang3.arch.*"))
        self.assertTrue(is_valid_target_tests("org.jgrapht.alg.color.*"))

    def test_valid_fqcn(self):
        self.assertTrue(is_valid_target_tests("org.jgrapht.GraphsTest"))
        self.assertTrue(is_valid_target_tests("org.jgrapht.GraphsTest,org.jgrapht.GraphTestsTest,org.jgrapht.GraphMetricsTest"))

    def test_invalid_bare_wildcard(self):
        self.assertFalse(is_valid_target_tests(".*"))

    def test_invalid_double_dot(self):
        self.assertFalse(is_valid_target_tests("a..B"))
        self.assertFalse(is_valid_target_tests("org..Bad"))

    def test_invalid_no_wildcard_no_uppercase(self):
        self.assertFalse(is_valid_target_tests("abc.def.ghi"))

    def test_invalid_trailing_dot(self):
        self.assertFalse(is_valid_target_tests("org.springframework."))

    def test_invalid_empty(self):
        self.assertFalse(is_valid_target_tests(""))
        self.assertFalse(is_valid_target_tests(None))
        self.assertFalse(is_valid_target_tests(123))

    def test_invalid_single_segment_wildcard(self):
        self.assertFalse(is_valid_target_tests("org.*"))


if __name__ == "__main__":
    unittest.main()
