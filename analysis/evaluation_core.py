"""
evaluation_core.py - Shared evaluation logic for Smart Test Picker replication package.

Provides the Python evaluation selector (implementing the documented selection rules),
PIT mutation loading, killing-test normalization and resolution, and coverage map I/O.

This is NOT the production Java selector. Agreement was historically checked against
another Python edge-only semantic model for the committed single-method-change cases
(verify_selector_equivalence.py). That model does not execute Java and omits the
NO_COVERAGE branch later present in production selector 2e0954. A separate 21-case
Commons Lang contract test executes the historical Maven plugin. General or current
production-selector equivalence is not claimed.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path


# =============================================================================
# Data Classes
# =============================================================================

@dataclass(frozen=True)
class ResolvedKillingTest:
    raw_pit_id: str
    normalized_id: str
    resolution_mode: str  # "direct" | "base-name-single" | "base-name-multiple"
    coverage_keys: tuple[str, ...]


@dataclass(frozen=True)
class RawMutation:
    mutation_id: str
    mutated_class: str
    mutated_method: str
    method_description: str
    line_number: int
    mutator: str
    indexes: tuple[int, ...] | None
    blocks: tuple[int, ...] | None
    raw_killing_test_ids: tuple[str, ...]
    source_xml: str
    xml_ordinal: int


@dataclass(frozen=True)
class ResolvedMutation:
    mutation_id: str
    mutated_class: str
    mutated_method: str
    method_description: str
    line_number: int
    mutator: str
    indexes: tuple[int, ...] | None
    blocks: tuple[int, ...] | None
    killing_tests: tuple[ResolvedKillingTest, ...]
    source_xml: str
    xml_ordinal: int


# =============================================================================
# Loading
# =============================================================================

def load_json(path: Path) -> dict:
    """Load JSON from .json or .json.gz file."""
    if path.suffix == ".gz":
        with gzip.open(path, "rt", encoding="utf-8") as stream:
            return json.load(stream)
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def load_coverage_map(path: Path) -> dict:
    """Load and validate a coverage map JSON file."""
    data = load_json(path)
    if "testMappings" not in data:
        raise ValueError(f"Coverage map missing 'testMappings' key: {path}")
    if "metadata" not in data:
        raise ValueError(f"Coverage map missing 'metadata' key: {path}")
    return data


def load_oracle_exclusion_ids(repo_root: Path, project_name: str) -> set[str]:
    """Return frozen records excluded from the leaf-test killing oracle.

    Raw PIT artifacts remain unchanged. Exclusions require a separately audited
    record proving that PIT's KILLED outcome cannot be assigned to a runnable
    leaf identity under the evaluation's operational oracle.
    """
    path = repo_root / "analysis" / "oracle_exclusions.json"
    if not path.exists():
        return set()
    data = json.loads(path.read_text(encoding="utf-8"))
    return {
        row["mutationId"]
        for row in data.get("records", [])
        if row.get("project") == project_name
    }


def exclude_non_leaf_oracle_records(mutations, repo_root: Path, project_name: str):
    """Remove audited container-only outcomes from the leaf-test oracle."""
    excluded = load_oracle_exclusion_ids(repo_root, project_name)
    by_canonical_id = {
        _canonicalize_mutation_source_path(mutation.mutation_id, project_name): mutation
        for mutation in mutations
    }
    missing = excluded - set(by_canonical_id)
    if missing:
        raise ValueError(
            f"{project_name}: configured oracle exclusions not present: {sorted(missing)}"
        )
    return [
        mutation for mutation in mutations
        if _canonicalize_mutation_source_path(mutation.mutation_id, project_name) not in excluded
    ]


def _canonicalize_mutation_source_path(mutation_id: str, project_name: str) -> str:
    """Canonicalize the legacy subject-local PIT path used by evaluate_subject."""
    marker = "|ordinal=results/"
    if marker in mutation_id:
        return mutation_id.replace(marker, f"|ordinal={project_name}/results/", 1)
    return mutation_id


def discover_pit_files(repo_root: Path, patterns: list[str]) -> tuple[Path, ...]:
    """Resolve glob patterns, deduplicate, sort, validate."""
    matched = set()
    for pattern in patterns:
        found = list(repo_root.glob(pattern))
        matched.update(found)

    if not matched:
        raise FileNotFoundError(
            f"No PIT files found for patterns: {patterns} (root: {repo_root})"
        )

    # Check for .xml / .xml.gz conflict
    stems = {}
    for p in matched:
        if p.name == "mutations.xml.gz":
            stem = p.parent / "mutations.xml"
        else:
            stem = p
        if stem in stems and stems[stem] != p:
            raise ValueError(
                f"Both .xml and .xml.gz exist for: {stem.relative_to(repo_root)}"
            )
        stems[stem] = p

    # Sort by POSIX relative path
    sorted_files = tuple(sorted(matched, key=lambda p: p.relative_to(repo_root).as_posix()))
    return sorted_files


def _parse_int_list(text: str | None) -> tuple[int, ...] | None:
    """Parse comma-separated integers from PIT XML attributes."""
    if not text or text.strip() == "":
        return None
    try:
        return tuple(sorted(int(x.strip()) for x in text.split(",") if x.strip()))
    except ValueError:
        return None


def _build_mutation_id(
    project_name: str, mutated_class: str, mutated_method: str,
    method_desc: str, line: int, mutator: str,
    indexes: tuple[int, ...] | None, blocks: tuple[int, ...] | None,
    source_xml: str, xml_ordinal: int,
) -> str:
    """Build canonical mutation ID. Includes ordinal as tiebreaker when indexes/blocks are unavailable."""
    idx_str = ",".join(str(i) for i in indexes) if indexes else "unknown"
    blk_str = ",".join(str(b) for b in blocks) if blocks else "unknown"
    # Extract short mutator name
    short_mutator = mutator.split(".")[-1] if "." in mutator else mutator
    base = f"{project_name}|{mutated_class}|{mutated_method}|{method_desc}|{line}|{short_mutator}|indexes={idx_str}|blocks={blk_str}"
    # Add ordinal as tiebreaker when semantic fields alone are not unique
    if indexes is None and blocks is None:
        return f"{base}|ordinal={source_xml}:{xml_ordinal}"
    return base


def load_pit_mutations(
    project_name: str,
    repo_root: Path,
    pit_files: tuple[Path, ...],
) -> list[RawMutation]:
    """Parse KILLED mutations in deterministic file order."""
    mutations = []
    seen_ids: dict[str, RawMutation] = {}

    for pit_file in pit_files:
        relative = pit_file.relative_to(repo_root).as_posix()

        if pit_file.suffix == ".gz":
            with gzip.open(pit_file, "rt", encoding="utf-8") as f:
                tree = ET.parse(f)
        else:
            tree = ET.parse(pit_file)

        for ordinal, mut_elem in enumerate(tree.getroot().findall("mutation")):
            if mut_elem.get("status") != "KILLED":
                continue

            mutated_class = mut_elem.findtext("mutatedClass") or ""
            mutated_method = mut_elem.findtext("mutatedMethod") or ""
            method_desc = mut_elem.findtext("methodDescription") or "(unknown)"
            line = int(mut_elem.findtext("lineNumber") or "0")
            mutator = mut_elem.findtext("mutator") or ""
            indexes = _parse_int_list(mut_elem.findtext("indexes"))
            blocks = _parse_int_list(mut_elem.findtext("blocks"))

            mutation_id = _build_mutation_id(
                project_name, mutated_class, mutated_method,
                method_desc, line, mutator, indexes, blocks,
                relative, ordinal
            )

            # Hard fail on duplicate
            if mutation_id in seen_ids:
                existing = seen_ids[mutation_id]
                raise ValueError(
                    f"Duplicate mutation ID: {mutation_id}\n"
                    f"  First:  {existing.source_xml} ordinal {existing.xml_ordinal}\n"
                    f"  Second: {relative} ordinal {ordinal}"
                )

            # Parse killing tests
            killing_raw = mut_elem.findtext("killingTests") or ""
            raw_ids = tuple(
                t.strip() for t in killing_raw.split("|") if t.strip()
            )

            raw_mut = RawMutation(
                mutation_id=mutation_id,
                mutated_class=mutated_class,
                mutated_method=mutated_method,
                method_description=method_desc,
                line_number=line,
                mutator=mutator,
                indexes=indexes,
                blocks=blocks,
                raw_killing_test_ids=raw_ids,
                source_xml=relative,
                xml_ordinal=ordinal,
            )
            seen_ids[mutation_id] = raw_mut
            mutations.append(raw_mut)

    return mutations


# =============================================================================
# Normalization and Resolution
# =============================================================================

def normalize_pit_test_name(pit_id: str) -> str | None:
    """
    Normalize PIT JUnit Platform unique ID to coverage map format.

    Returns SimpleClassName#methodName or None if unparseable.
    """
    # PIT's built-in JUnit 3/4 plugin reports legacy tests as
    # ``fully.qualified.TestClass.testMethod(fully.qualified.TestClass)``.
    # Normalize that representation before trying Platform unique IDs.
    legacy_match = re.fullmatch(r'(.+)\.([^.()]+)\(([^()]*)\)', pit_id)
    if legacy_match:
        test_class = legacy_match.group(1)
        method = legacy_match.group(2)
        reported_class = legacy_match.group(3)
        if reported_class == test_class:
            return f"{test_class.rsplit('.', 1)[-1]}#{method}"

    class_match = re.search(r'\[class:([^\]]+)\]', pit_id)
    method_match = re.search(r'\[method:([^\]]+)\]', pit_id)
    if not method_match:
        method_match = re.search(r'\[test-template:([^\]]+)\]', pit_id)
    if not class_match or not method_match:
        return None

    fqn = class_match.group(1)
    method = re.sub(r'\(.*\)', '', method_match.group(1))
    simple_class = fqn.split('.')[-1]

    nested_matches = re.findall(r'\[nested-class:([^\]]+)\]', pit_id)
    if nested_matches:
        simple_class = nested_matches[-1]

    return f"{simple_class}#{method}"


def build_base_to_keys(test_mappings: dict) -> dict[str, set[str]]:
    """Build reverse lookup: base name (without hash suffix) -> set of full coverage keys."""
    base_to_keys: dict[str, set[str]] = {}
    for key in test_mappings:
        if '_' in key and len(key.rsplit('_', 1)[-1]) == 7:
            last = key.rsplit('_', 1)[-1]
            if all(c in '0123456789abcdef' for c in last):
                base = key.rsplit('_', 1)[0]
                base_to_keys.setdefault(base, set()).add(key)
                continue
        base_to_keys.setdefault(key, set()).add(key)
    return base_to_keys


def build_class_to_keys(test_mappings: dict, execution_identities: dict) -> dict[str, set[str]]:
    """Build an exact test-class FQN lookup for PIT container test units."""
    class_to_keys: dict[str, set[str]] = {}
    for key, identity in execution_identities.items():
        if key not in test_mappings or not isinstance(identity, dict):
            continue
        test_class = identity.get("testClassFqn")
        if test_class:
            class_to_keys.setdefault(test_class, set()).add(key)
    return class_to_keys


def resolve_killing_tests(
    mutations: list[RawMutation],
    test_mappings: dict,
    base_to_keys: dict[str, set[str]],
    class_to_keys: dict[str, set[str]] | None = None,
) -> list[ResolvedMutation]:
    """Resolve raw PIT killing test IDs to coverage map keys. Returns new list."""
    resolved_mutations = []

    for mut in mutations:
        resolved_tests = []

        for raw_pit_id in mut.raw_killing_test_ids:
            normalized = normalize_pit_test_name(raw_pit_id)
            if normalized is None:
                # Custom JUnit Platform engines may expose a class/container as
                # the executable PIT test unit instead of a leaf method. Map
                # that unit to the exact runnable identities belonging to its
                # class; never infer from a simple class name.
                class_match = re.search(r'\[class:([^\]]+)\]', raw_pit_id)
                class_name = class_match.group(1) if class_match else None
                # PIT's built-in JUnit 4 integration can expose a whole test
                # class (for example a runner/container unit) as the killing
                # identity. Accept only a syntactically exact Java FQN and
                # resolve it through BASE execution metadata.
                if class_name is None and re.fullmatch(
                        r'[A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*)+', raw_pit_id):
                    class_name = raw_pit_id
                container_keys = (class_to_keys or {}).get(class_name or "")
                if not container_keys:
                    raise ValueError(
                        f"Unparseable PIT killing test ID: {raw_pit_id}\n"
                        f"  Mutation: {mut.mutation_id}"
                    )
                keys = tuple(sorted(container_keys))
                normalized = class_name
                mode = "class-container-single" if len(keys) == 1 else "class-container-multiple"

            # Resolve to coverage keys
            elif normalized in test_mappings:
                keys = (normalized,)
                mode = "direct"
            elif normalized in base_to_keys:
                keys = tuple(sorted(base_to_keys[normalized]))
                mode = "base-name-single" if len(keys) == 1 else "base-name-multiple"
            else:
                raise ValueError(
                    f"Unresolved normalized killing test ID: {normalized}\n"
                    f"  Raw PIT ID: {raw_pit_id}\n"
                    f"  Mutation: {mut.mutation_id}"
                )

            resolved_tests.append(ResolvedKillingTest(
                raw_pit_id=raw_pit_id,
                normalized_id=normalized,
                resolution_mode=mode,
                coverage_keys=keys,
            ))

        if not resolved_tests:
            raise ValueError(
                f"KILLED mutation has zero resolved killing tests: {mut.mutation_id}"
            )

        resolved_mutations.append(ResolvedMutation(
            mutation_id=mut.mutation_id,
            mutated_class=mut.mutated_class,
            mutated_method=mut.mutated_method,
            method_description=mut.method_description,
            line_number=mut.line_number,
            mutator=mut.mutator,
            indexes=mut.indexes,
            blocks=mut.blocks,
            killing_tests=tuple(resolved_tests),
            source_xml=mut.source_xml,
            xml_ordinal=mut.xml_ordinal,
        ))

    return resolved_mutations


# =============================================================================
# Selectors
# =============================================================================

def _coverage_lists(coverage: dict, test_name: str) -> tuple[list, list]:
    """Return validated coverage lists, preserving missing/null as empty.

    The production map schema permits missing or null list fields. Any present,
    non-null value must remain a list; malformed values are never interpreted as
    NO_COVERAGE.
    """
    if not isinstance(coverage, dict):
        raise ValueError(f"Coverage entry for {test_name!r} is not an object")
    classes = coverage.get("classes")
    methods = coverage.get("methods")
    if classes is not None and not isinstance(classes, list):
        raise ValueError(f"Coverage classes for {test_name!r} is not a list")
    if methods is not None and not isinstance(methods, list):
        raise ValueError(f"Coverage methods for {test_name!r} is not a list")
    return classes or [], methods or []


def select_original_legacy_edge_only(
    test_mappings: dict, changed_class: str, changed_method: str
) -> set[str]:
    """
    Historical edge-only evaluator semantics for one changed method.

    Select exact C#M method hits. If there are no method hits anywhere for C#M,
    escalate the changed class and select every test whose class footprint
    contains C. This is the production selector's class-level fallback.
    """
    method_fqn = f"{changed_class}#{changed_method}"
    validated = {
        test_name: _coverage_lists(coverage, test_name)
        for test_name, coverage in test_mappings.items()
    }
    method_hits = {test_name for test_name, (_, methods) in validated.items()
                   if method_fqn in methods}
    if method_hits:
        return method_hits
    return {
        test_name for test_name, (classes, _) in validated.items()
        if changed_class in classes
    }


def select_policy(test_mappings: dict, changed_class: str, changed_method: str) -> set[str]:
    """Current adopted 2e0954 single-existing-method policy: U ∪ (H or G).

    U contains only entries for which both coverage lists are missing, null, or
    empty. U membership is structural and never counts as a method hit or
    suppresses the zero-hit escalation to class coverage.
    """
    validated = {
        test_name: _coverage_lists(coverage, test_name)
        for test_name, coverage in test_mappings.items()
    }
    empty = {test_name for test_name, (classes, methods) in validated.items()
             if not classes and not methods}
    method_fqn = f"{changed_class}#{changed_method}"
    method_hits = {test_name for test_name, (_, methods) in validated.items()
                   if method_fqn in methods}
    if method_hits:
        return empty | method_hits
    class_hits = {test_name for test_name, (classes, _) in validated.items()
                  if changed_class in classes}
    return empty | class_hits


def select_original(test_mappings: dict, changed_class: str, changed_method: str) -> set[str]:
    """Compatibility name for the current adopted production policy."""
    return select_policy(test_mappings, changed_class, changed_method)


def select_constructor_only_rule(test_mappings: dict, changed_class: str, changed_method: str) -> set[str]:
    """
    Original UNION constructor-only footprint tests.

    Additionally select T if:
    - C is in T.classes
    - T has at least one C#... method (non-empty footprint)
    - EVERY C#... method is <init> or <clinit>
    """
    selected = select_policy(test_mappings, changed_class, changed_method)

    for test_name, coverage in test_mappings.items():
        if test_name in selected:
            continue

        classes, methods = _coverage_lists(coverage, test_name)

        if changed_class not in classes:
            continue

        class_methods = [m for m in methods if m.startswith(changed_class + "#")]
        if not class_methods:
            continue  # empty footprint -- already handled by original fallback

        all_constructors = all(
            m.endswith("#<init>") or m.endswith("#<clinit>")
            or "#<init>" in m or "#<clinit>" in m
            for m in class_methods
        )
        if all_constructors:
            selected.add(test_name)

    return selected


def select_class_level(test_mappings: dict, changed_class: str, changed_method: str) -> set[str]:
    """
    Class-level baseline: select all tests covering the changed class.

    This is the class-presence upper bound, limited to dependencies
    represented in the coverage map. Cannot recover Type C cases.
    """
    selected = set()
    for test_name, coverage in test_mappings.items():
        classes, methods = _coverage_lists(coverage, test_name)
        if (not classes and not methods) or changed_class in classes:
            selected.add(test_name)
    return selected


def select_class_level_legacy_edge_only(
    test_mappings: dict, changed_class: str, changed_method: str
) -> set[str]:
    """Historical class-presence baseline without structural empty entries."""
    return {
        test_name
        for test_name, coverage in test_mappings.items()
        if changed_class in _coverage_lists(coverage, test_name)[0]
    }


def select_constructor_only_rule_legacy_edge_only(
    test_mappings: dict, changed_class: str, changed_method: str
) -> set[str]:
    """Historical constructor variant built on the legacy edge-only selector."""
    selected = select_original_legacy_edge_only(test_mappings, changed_class, changed_method)
    for test_name, coverage in test_mappings.items():
        classes, methods = _coverage_lists(coverage, test_name)
        if changed_class not in classes:
            continue
        class_methods = [method for method in methods if method.startswith(changed_class + "#")]
        if class_methods and all(
            "#<init>" in method or "#<clinit>" in method for method in class_methods
        ):
            selected.add(test_name)
    return selected


# =============================================================================
# Utilities
# =============================================================================

def aggregate_sha256(root: Path, files: tuple[Path, ...]) -> str:
    """Compute deterministic SHA-256 over sorted relative paths and file contents."""
    digest = hashlib.sha256()
    for path in sorted(files, key=lambda p: p.relative_to(root).as_posix()):
        relative = path.relative_to(root).as_posix().encode("utf-8")
        content = path.read_bytes()
        digest.update(relative)
        digest.update(b"\0")
        digest.update(content)
        digest.update(b"\0")
    return digest.hexdigest()


def file_sha256(path: Path) -> str:
    """Compute SHA-256 of a single file."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def selected_set_sha256(selected: set[str]) -> str:
    """Compute deterministic hash of a selected test set."""
    digest = hashlib.sha256()
    for key in sorted(selected):
        digest.update(key.encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()


def all_coverage_keys(mutation: ResolvedMutation) -> set[str]:
    """Get the union of all coverage keys from all killing tests of a mutation."""
    keys = set()
    for kt in mutation.killing_tests:
        keys.update(kt.coverage_keys)
    return keys


def is_valid_target_tests(value) -> bool:
    """Validate a targetTests string: wildcard pattern(s) or comma-separated FQCNs.

    Valid forms:
      - Package wildcard: org.example.pkg.* (at least 2 segments before .*)
      - FQCN: org.example.ClassName (last segment starts uppercase)
      - Comma-separated mix of the above
    """
    if not isinstance(value, str) or not value.strip():
        return False
    parts = [p.strip() for p in value.split(",")]
    for part in parts:
        if part.endswith(".*"):
            pkg = part[:-2]
            if not pkg or not re.match(r'^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$', pkg):
                return False
        elif re.match(r'^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)*\.[A-Z][A-Za-z0-9_]*$', part):
            pass
        else:
            return False
    return True
