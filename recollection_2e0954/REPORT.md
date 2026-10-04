# V14.5 single-collector recollection report

## Verdict

**Branch C — NOT ADOPTED.** It was not possible, within the fixed attempts and frozen-population rule, to replace the four original maps with 2e0954 collector outputs. The v14.4/B2 numeric results remain current.

## Collector

STP commit `2e0954b5b590fb0b9da979c28b0d053e4ce9e5c9`, tree `7a61a4933a7f2b6a64aa06e4893ba61c9d26da33`, was built on SapMachine 21.0.12.1+1-LTS. The second build attempt published common, core, Gradle-plugin, and Maven-plugin modules locally. Tests were excluded. Artifact hashes and commands are in `stp_build.json`.

## Subject outcomes

| Subject | Recorded checkout | Outcome | Sessions/map identities | Frozen population | Map comparison |
|---|---|---|---:|---:|---|
| Commons Lang | `8538458e7aeb1455a5942f60fe0b4930da6c5d68` | NOT_RECOLLECTED | 4,697 sessions; no map | 4,692 | unavailable |
| JGraphT | `093b0c5ea006ba5b1d8b7a0212676bf8850cac6b` | NOT_RECOLLECTED | 2,309 sessions; no map | 2,308 | unavailable |
| spring-core | `25838a334c037b68e614f6b571af03a1f6bfec19` | population mismatch | 3,638 map identities | 3,624 | DIFFERENT; 450 normalized identities differ |
| PetClinic | `cbb884f01f7fef663fcff256e303d967494a4f8b` | population mismatch | 56 map identities | 52 | DIFFERENT; 4 normalized identities differ |

The spring-core output consists of 3,624 covered and 14 empty retained sessions. The PetClinic output consists of 52 covered and four empty retained sessions. These demonstrate the 2e0954 empty-session retention behavior, but they fail the task's frozen logical-population gate and are not current evaluation inputs. Full added/removed edge sets and identity sets are in `map_comparison.json`; per-subject environments, commands, timing, failures, skips, hashes, and exact blockers are in each `collection.json` and `BLOCKERS.md`.

## Numeric impact

None. Branch C preserves all v14.4 values, the frozen maps, the 4,010 denominator, selector semantics, constructor rule, and Hibernate exclusion. No v14.5 result files were promoted.

## Verification

The following checks passed after the attempt:

- `python3 -m unittest discover -s analysis/tests` — 68 tests, exit 0.
- `analysis/analyze_failure_modes.py --verify` — exit 0.
- `analysis/verify_selector_equivalence.py --verify` — exit 0.
- `analysis/freeze_artifacts.py --verify` — exit 0.
- `analysis/verify_recollection.py --verify` — exit 0.
- `analysis/v14_4_rederivation/verify_b2.py --verify` — exit 0.

Logs are preserved beside this report. No PIT, mutation, or extension-subject collection was executed.

## Repository state

Evidence payload commit: `d46b1ca064ec69b2d3b8baf06ccf6e7fb6a489cc`. A follow-up commit adds the ignored raw logs and this fixed reference. Tag: `rad1-v14.5`. Push was not performed.

Manual publication command after review:

```bash
git push origin main
git push origin rad1-v14.5
```
