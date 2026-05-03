#!/usr/bin/env python3
"""
00_sample_classes.py — Reproduce/verify stratified sample of classes for PIT evaluation.

Sampling methodology used to produce config/sample_classes.json:
  - Population: All production classes in jgrapht-core covered by ≥1 test
  - Strata: 20 distinct subpackages under org.jgrapht, chosen for algorithmic diversity
  - 1 class per subpackage, chosen via stratified random (seed=42)
  - No LOC cap (range: 83–1310)
  - Eligibility: class has ≥1 test covering it in coverage map

The authoritative sample is config/sample_classes.json (committed to repo).
This script reproduces it deterministically and validates its integrity.

Modes:
  --verify     Validate all sampled classes exist in the project
  (default)    Regenerate sample_classes.json (must match committed version)

Usage:
  python3 00_sample_classes.py --project-dir /path/to/jgrapht --verify
  python3 00_sample_classes.py --project-dir /path/to/jgrapht --output /tmp/test.json
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

SEED = 42
BASE_PKG = "org.jgrapht"
MODULE = "jgrapht-core"
SRC_MAIN = f"{MODULE}/src/main/java/org/jgrapht"

# The 20 subpackages selected for evaluation (one per algorithmic domain).
# Selection criteria: leaf-level or domain-representative packages with
# non-trivial algorithms (≥1 class with mutable method bodies and test coverage).
SAMPLED_SUBPACKAGES = [
    ".",                         # root: utility classes (Graphs)
    "alg/clique",               # clique algorithms
    "alg/clustering",           # clustering algorithms
    "alg/color",                # graph coloring
    "alg/connectivity",         # connectivity inspectors
    "alg/cycle",                # cycle detection
    "alg/drawing/model",        # graph drawing models
    "alg/flow",                 # max-flow algorithms
    "alg/isomorphism",          # graph isomorphism
    "alg/lca",                  # lowest common ancestor
    "alg/linkprediction",       # link prediction indices
    "alg/matching/blossom/v5",  # blossom V matching
    "alg/scoring",              # centrality/scoring
    "alg/shortestpath",         # shortest path algorithms
    "alg/spanning",             # spanning tree algorithms
    "alg/tour",                 # TSP heuristics
    "alg/util",                 # algorithm utilities
    "alg/vertexcover",          # vertex cover algorithms
    "generate/netgen",          # network generators
    "graph/specifics",          # graph implementation specifics
]

# The specific class selected from each subpackage (deterministic, seed=42).
# Order matches SAMPLED_SUBPACKAGES.
SAMPLED_CLASSES = [
    "org.jgrapht.Graphs",
    "org.jgrapht.alg.clique.DegeneracyBronKerboschCliqueFinder",
    "org.jgrapht.alg.clustering.LabelPropagationClustering",
    "org.jgrapht.alg.color.GreedyColoring",
    "org.jgrapht.alg.connectivity.KosarajuStrongConnectivityInspector",
    "org.jgrapht.alg.cycle.SzwarcfiterLauerSimpleCycles",
    "org.jgrapht.alg.drawing.model.ListenableLayoutModel2D",
    "org.jgrapht.alg.flow.PushRelabelMFImpl",
    "org.jgrapht.alg.isomorphism.AHUUnrootedTreeIsomorphismInspector",
    "org.jgrapht.alg.lca.BinaryLiftingLCAFinder",
    "org.jgrapht.alg.linkprediction.LeichtHolmeNewmanIndexLinkPrediction",
    "org.jgrapht.alg.matching.blossom.v5.BlossomVPrimalUpdater",
    "org.jgrapht.alg.scoring.ClosenessCentrality",
    "org.jgrapht.alg.shortestpath.TransitNodeRoutingPrecomputation",
    "org.jgrapht.alg.spanning.EsauWilliamsCapacitatedMinimumSpanningTree",
    "org.jgrapht.alg.tour.ChristofidesThreeHalvesApproxMetricTSP",
    "org.jgrapht.alg.util.UnorderedPair",
    "org.jgrapht.alg.vertexcover.RecursiveExactVCImpl",
    "org.jgrapht.generate.netgen.Distributor",
    "org.jgrapht.graph.specifics.UndirectedSpecifics",
]


def count_loc(path):
    """Count total lines in file (wc -l equivalent)."""
    try:
        with open(path) as f:
            return sum(1 for _ in f)
    except (OSError, UnicodeDecodeError):
        return 0


def get_git_commit(project_dir):
    """Get current HEAD commit hash."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=str(project_dir),
            capture_output=True, text=True
        )
        return result.stdout.strip()
    except Exception:
        return "unknown"


def get_project_version(project_dir):
    """Extract version from pom.xml."""
    pom = project_dir / "pom.xml"
    if pom.exists():
        import xml.etree.ElementTree as ET
        tree = ET.parse(pom)
        ns = {"m": "http://maven.apache.org/POM/4.0.0"}
        ver = tree.getroot().find("m:version", ns)
        if ver is not None:
            return ver.text
    return "unknown"


def verify_config(project_dir, config_path):
    """Verify that all classes in sample_classes.json exist and match expectations."""
    if not config_path.exists():
        print(f"ERROR: {config_path} not found")
        sys.exit(1)

    with open(config_path) as f:
        config = json.load(f)

    classes = config["classes"]
    errors = []

    for c in classes:
        fqn = c["fqn"]
        rel_path = fqn.replace(".", "/") + ".java"
        src_file = project_dir / MODULE / "src/main/java" / rel_path
        if not src_file.exists():
            errors.append(f"  MISSING source: {fqn}")
            continue

    # Check consistency with hardcoded list
    config_fqns = [c["fqn"] for c in classes]
    if config_fqns != SAMPLED_CLASSES:
        errors.append("  Class list does not match expected SAMPLED_CLASSES")

    if errors:
        print(f"VERIFICATION FAILED ({len(errors)} issues):")
        for e in errors:
            print(e)
        sys.exit(1)
    else:
        print(f"VERIFICATION PASSED: {len(classes)} classes")
        print(f"  All sources exist in {MODULE}")
        print(f"  Subpackages: {len(set(c['subpkg'] for c in classes))}")
        print(f"  Commit: {config.get('commit', 'unknown')[:12]}")


def generate_sample(project_dir, output_path):
    """Generate sample_classes.json from the fixed class list."""
    classes = []
    for i, fqn in enumerate(SAMPLED_CLASSES):
        subpkg_path = SAMPLED_SUBPACKAGES[i]
        subpkg_label = "(root)" if subpkg_path == "." else subpkg_path.replace("/", ".")

        # Compute LOC
        rel_path = fqn.replace(".", "/") + ".java"
        src_file = project_dir / MODULE / "src/main/java" / rel_path
        if not src_file.exists():
            print(f"ERROR: Source not found: {src_file}")
            sys.exit(1)
        loc = count_loc(src_file)

        # Build targetTests
        if subpkg_path == ".":
            target_tests = f"{BASE_PKG}.*"
        else:
            target_tests = f"{BASE_PKG}.{subpkg_path.replace('/', '.')}.*"

        classes.append({
            "fqn": fqn,
            "subpkg": subpkg_label,
            "loc": loc,
            "targetTests": target_tests,
        })

    config = {
        "project": "JGraphT",
        "version": get_project_version(project_dir),
        "repository": "https://github.com/jgrapht/jgrapht",
        "commit": get_git_commit(project_dir),
        "module": MODULE,
        "sampling": {
            "strategy": "stratified_random",
            "seed": SEED,
            "max_per_package": 3,
            "total_sampled": len(classes),
        },
        "classes": classes,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        # Match original format: top-level indent=2, but classes array uses compact 1-line objects
        f.write("{\n")
        f.write(f'  "project": {json.dumps(config["project"])},\n')
        f.write(f'  "version": {json.dumps(config["version"])},\n')
        f.write(f'  "repository": {json.dumps(config["repository"])},\n')
        f.write(f'  "commit": {json.dumps(config["commit"])},\n')
        f.write(f'  "module": {json.dumps(config["module"])},\n')
        s = config["sampling"]
        f.write('  "sampling": {\n')
        f.write(f'    "strategy": {json.dumps(s["strategy"])},\n')
        f.write(f'    "seed": {s["seed"]},\n')
        f.write(f'    "max_per_package": {s["max_per_package"]},\n')
        f.write(f'    "total_sampled": {s["total_sampled"]}\n')
        f.write('  },\n')
        f.write('  "classes": [\n')
        for i, c in enumerate(config["classes"]):
            comma = "," if i < len(config["classes"]) - 1 else ""
            f.write(f"    {json.dumps(c)}{comma}\n")
        f.write("  ]\n")
        f.write("}\n")

    print(f"Generated sample: {len(classes)} classes from {len(SAMPLED_SUBPACKAGES)} subpackages")
    print(f"Output: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Generate/verify stratified sample for PIT evaluation")
    parser.add_argument("--project-dir", type=Path, required=True,
                        help="Path to jgrapht checkout")
    parser.add_argument("--output", type=Path, default=None,
                        help="Output path (default: ../config/sample_classes.json)")
    parser.add_argument("--verify", action="store_true",
                        help="Verify existing config/sample_classes.json is valid")
    args = parser.parse_args()

    script_dir = Path(__file__).parent
    output_path = args.output or (script_dir.parent / "config" / "sample_classes.json")

    project_dir = args.project_dir
    if not (project_dir / "pom.xml").exists():
        print(f"ERROR: {project_dir}/pom.xml not found")
        sys.exit(1)

    if args.verify:
        verify_config(project_dir, script_dir.parent / "config" / "sample_classes.json")
        return

    generate_sample(project_dir, output_path)


if __name__ == "__main__":
    main()
