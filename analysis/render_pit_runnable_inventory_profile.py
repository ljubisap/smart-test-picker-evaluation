#!/usr/bin/env python3
"""Render a PIT Maven profile with exact BASE-proven runnable test classes.

This translates a frozen STP runnable inventory into PIT ``targetTests``
entries. Exact class names prevent PIT's test discovery from treating compiled
helpers or generated classes admitted by a broad package glob as tests.
"""

import argparse
import gzip
import hashlib
import json
from pathlib import Path
from xml.sax.saxutils import escape


parser = argparse.ArgumentParser()
parser.add_argument("--coverage-map", type=Path, required=True)
parser.add_argument("--profile", type=Path, required=True)
parser.add_argument("--output", type=Path, required=True)
parser.add_argument("--manifest", type=Path, required=True)
parser.add_argument("--expected-identities", type=int)
parser.add_argument("--expected-classes", type=int)
args = parser.parse_args()


def read_json(path: Path):
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as stream:
        return json.load(stream)


coverage = read_json(args.coverage_map)
identities = coverage.get("executionIdentities", {})
if not isinstance(identities, dict) or not identities:
    raise SystemExit("coverage map has no executionIdentities")

test_classes = sorted(
    {
        record["testClassFqn"]
        for record in identities.values()
        if isinstance(record, dict) and record.get("testClassFqn")
    }
)
if args.expected_identities is not None and len(identities) != args.expected_identities:
    raise SystemExit(
        f"expected {args.expected_identities} identities, found {len(identities)}"
    )
if args.expected_classes is not None and len(test_classes) != args.expected_classes:
    raise SystemExit(
        f"expected {args.expected_classes} classes, found {len(test_classes)}"
    )

profile = args.profile.read_text(encoding="utf-8")
needle = "<targetTests><param>${pitest.targetTests}</param></targetTests>"
if profile.count(needle) != 1:
    raise SystemExit(f"expected exactly one targetTests placeholder in {args.profile}")

replacement = "<targetTests>\n" + "\n".join(
    f"            <param>{escape(name)}</param>" for name in test_classes
) + "\n          </targetTests>"
rendered = profile.replace(needle, replacement)
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(rendered, encoding="utf-8")

map_sha256 = hashlib.sha256(args.coverage_map.read_bytes()).hexdigest()
profile_sha256 = hashlib.sha256(rendered.encode("utf-8")).hexdigest()
manifest = {
    "sourceCoverageMap": str(args.coverage_map),
    "sourceCoverageMapSha256": map_sha256,
    "runnableIdentityCount": len(identities),
    "runnableTestClassCount": len(test_classes),
    "testClasses": test_classes,
    "renderedProfile": str(args.output),
    "renderedProfileSha256": profile_sha256,
}
args.manifest.parent.mkdir(parents=True, exist_ok=True)
args.manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
