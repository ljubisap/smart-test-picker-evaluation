# Requirements

## Operating System

Tested on:
- macOS 14.x (Apple Silicon, primary development)
- Linux (Ubuntu 22.04, CI)

Should work on any Unix-like OS with the tools below. Windows users: use WSL2.

## Software

| Tool | Version | Verified | Purpose |
|------|---------|----------|---------|
| Java | OpenJDK 21 (SapMachine) | `java -version` | Build and test execution |
| Maven | 3.8.6+ | `mvn --version` | Build tool for JGraphT (no wrapper) |
| Python | 3.10+ | `python3 --version` | Evaluation scripts |
| Git | 2.39+ | `git --version` | Change detection, diff |

## Maven Plugins (automatically downloaded)

| Plugin | Version | Purpose |
|--------|---------|---------|
| PIT (pitest-maven) | 1.17.4 | Mutation testing |
| pitest-junit5-plugin | 1.2.1 | JUnit 5 support for PIT |
| Smart Test Picker | 0.1.0 | Per-test coverage map generation |

## Smart Test Picker Installation

The Smart Test Picker Maven plugin must be installed in the local Maven repository:

```bash
cd /path/to/smart-test-picker-working
git checkout 70b3984626eb  # pinned for this evaluation (corrected collector)
./gradlew :smart-test-picker-maven:publishToMavenLocal
```

This installs `com.sap.oss.smart-test-picker:smart-test-picker-maven:0.1.0` to `~/.m2/repository/`.

Verify installation:
```bash
ls ~/.m2/repository/com/sap/oss/smart-test-picker/smart-test-picker-maven/0.1.0/
```

## Subject Project Setup

1. Clone JGraphT:
   ```bash
   git clone https://github.com/jgrapht/jgrapht.git
   cd jgrapht
   git checkout 719212a1fe0bbbf62210159f50920a71e80b73ed
   ```

2. Add profiles to `jgrapht-core/pom.xml` (inside `<profiles>` section):
   - Smart Test Picker coverage profile: see `config/coverage_profile.xml`
   - PIT mutation profile: see `config/pit_profile.xml`

3. Add `junit-platform.properties` to `jgrapht-core/src/test/resources/`:
   ```
   junit.jupiter.extensions.autodetection.enabled=true
   ```

4. Ensure `.gitattributes` in the project root contains:
   ```
   *.java diff=java
   ```

## JPMS Considerations

JGraphT uses the Java Module System (`module-info.java`). Key adaptations:
- `useModulePath=false` in maven-surefire-plugin for test execution
- `--add-opens` for all sampled packages in PIT profile (reflective access)
- Parallel test execution disabled for per-test coverage accuracy

## Hardware

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| RAM | 8 GB | 16 GB |
| CPU | 4 cores | 8 cores |
| Disk | 5 GB free | 10 GB free |

**Time estimates:**
| Step | Duration |
|------|----------|
| Coverage map generation (Step 1) | ~7 minutes |
| PIT mutation testing (Step 2) | ~45 minutes (BlossomVPrimalUpdater alone: ~25 min) |
| Evaluation + baselines (Steps 3-4) | < 10 seconds |
| **Total** | **~55 minutes** |

## Python Dependencies

No external packages required  - all scripts use only the Python standard library:
- `argparse`, `json`, `xml.etree.ElementTree`, `pathlib`, `subprocess`
- `random`, `re`, `collections`, `gzip`, `time`, `datetime`

No `requirements.txt` or virtual environment needed.
