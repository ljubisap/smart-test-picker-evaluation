# Requirements  - Spring PetClinic Evaluation

## Software

| Component | Version | Purpose |
|-----------|---------|---------|
| OpenJDK | 21+ | Build & run PetClinic |
| Gradle | 8.5+ (via wrapper) | Build system |
| Python | 3.10+ | Evaluation scripts |
| Git | 2.40+ | Version control |

## Smart Test Picker Plugin

The plugin must be published to `mavenLocal` before running Step 1:

```bash
cd /path/to/smart-test-picker-working
git checkout 70b3984626eb  # pinned for this evaluation (corrected collector)
./gradlew publishToMavenLocal
```

Required: version 0.1.0 (commit 70b3984626eb) with per-test JaCoCo instrumentation.

## Spring PetClinic Checkout

```bash
git clone https://github.com/spring-projects/spring-petclinic.git
cd spring-petclinic
git checkout e4a6ebe3139f6b2bf5303b362bc5856d86c46a6f
```

The `build.gradle` must include:
- Smart Test Picker plugin configuration (for Step 1)
- PIT Gradle plugin `info.solidsoft.pitest` version 1.15.0 (for Step 2)

See `config/pitest_config.md` for the exact PIT configuration block.

## Hardware

| | Minimum | Tested On |
|---|---------|-----------|
| RAM | 4 GB | 16 GB (MacBook Pro M3) |
| Disk | 1 GB free | SSD |
| CPU | 2 cores | 8 cores (Apple M3) |

## Time Estimates

| Step | Duration | Notes |
|------|----------|-------|
| Step 1: Coverage map | ~1 min | 52 tests with JaCoCo |
| Step 2: PIT | ~2 min | 139 mutations x 52 tests |
| Step 3: Evaluate | <1 sec | Pure computation |
| Step 4: Baselines | <1 sec | Pure computation |
| **Total** | **~3-4 min** | |

## Python Dependencies

None beyond stdlib. Scripts use only: `argparse`, `json`, `xml.etree.ElementTree`, `re`, `pathlib`, `subprocess`, `random`, `collections`.

## Platform Tested

- macOS 15.4 (Apple Silicon, M3)
- Not tested on Linux/Windows but expected to work (no OS-specific code)
