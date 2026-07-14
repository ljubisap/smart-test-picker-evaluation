#!/usr/bin/env python3
"""
00_sample_classes.py  --  Document class sampling strategy for Spring PetClinic.

PetClinic is a small project (14 production classes with mutations).
No sampling is applied  --  ALL classes are included in the evaluation.

Modes:
  --verify   Validate that config/sample_classes.json matches expected classes
  (default)  Print the sampling rationale and class list

Usage:
  python3 00_sample_classes.py
  python3 00_sample_classes.py --verify
"""

import argparse
import json
import sys
from pathlib import Path

EXPECTED_CLASSES = [
    "org.springframework.samples.petclinic.model.BaseEntity",
    "org.springframework.samples.petclinic.model.NamedEntity",
    "org.springframework.samples.petclinic.model.Person",
    "org.springframework.samples.petclinic.owner.Owner",
    "org.springframework.samples.petclinic.owner.OwnerController",
    "org.springframework.samples.petclinic.owner.Pet",
    "org.springframework.samples.petclinic.owner.PetController",
    "org.springframework.samples.petclinic.owner.PetTypeFormatter",
    "org.springframework.samples.petclinic.owner.PetValidator",
    "org.springframework.samples.petclinic.owner.Visit",
    "org.springframework.samples.petclinic.owner.VisitController",
    "org.springframework.samples.petclinic.vet.Vet",
    "org.springframework.samples.petclinic.vet.VetController",
    "org.springframework.samples.petclinic.vet.Vets",
]


def main():
    parser = argparse.ArgumentParser(description="PetClinic class sampling (all classes)")
    parser.add_argument("--verify", action="store_true",
                        help="Verify config/sample_classes.json matches expected")
    args = parser.parse_args()

    script_dir = Path(__file__).parent
    config_path = script_dir.parent / "config" / "sample_classes.json"

    if args.verify:
        if not config_path.exists():
            print(f"ERROR: {config_path} not found")
            sys.exit(1)

        with open(config_path) as f:
            data = json.load(f)

        actual_fqns = sorted(c["fqn"] for c in data["classes"])
        expected_fqns = sorted(EXPECTED_CLASSES)

        if actual_fqns == expected_fqns:
            print(f"PASS: sample_classes.json contains all {len(actual_fqns)} expected classes")
            print(f"  Strategy: {data['sampling']['strategy']}")
            print(f"  Commit: {data['commit'][:12]}")
        else:
            missing = set(expected_fqns) - set(actual_fqns)
            extra = set(actual_fqns) - set(expected_fqns)
            print("FAIL: class list mismatch")
            if missing:
                print(f"  Missing: {missing}")
            if extra:
                print(f"  Extra: {extra}")
            sys.exit(1)
    else:
        print("Spring PetClinic  --  Class Sampling Strategy")
        print("=" * 50)
        print()
        print("Strategy: ALL CLASSES (no sampling)")
        print()
        print("Rationale:")
        print("  PetClinic is a small project with only 14 production classes")
        print("  that have KILLED mutations. Including all of them is tractable")
        print("  and provides complete coverage of the evaluation space.")
        print()
        print("  Note: PIT targets 17 classes total, but 3 system/config classes")
        print("  have only SURVIVED/NO_COVERAGE mutations. Safety evaluation")
        print("  uses only KILLED mutations, so the effective set is 14 classes.")
        print()
        print("Classes (14):")
        for fqn in EXPECTED_CLASSES:
            pkg = fqn.rsplit(".", 1)[0].split(".")[-1]
            name = fqn.rsplit(".", 1)[1]
            print(f"  [{pkg}] {name}")
        print()
        print("Subpackages represented:")
        pkgs = sorted(set(c.split(".")[-2] for c in EXPECTED_CLASSES))
        for pkg in pkgs:
            count = sum(1 for c in EXPECTED_CLASSES if f".{pkg}." in c)
            print(f"  {pkg}: {count} classes")


if __name__ == "__main__":
    main()
