# Requirements

## Operating System

Tested on:
- macOS 14.x (Apple Silicon, primary development)
- Linux (Ubuntu 22.04, CI)

Should work on any Unix-like OS with the tools below. Windows users: use WSL2.

## Software

| Tool | Version | Verified | Purpose |
|------|---------|----------|---------|
| Java | OpenJDK 21.0.2+ | `java -version` | Build and test execution |
| Maven | 3.9.6+ | `mvn --version` | Build tool for commons-lang |
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

1. Clone Apache Commons Lang:
   ```bash
   git clone https://github.com/apache/commons-lang.git
   cd commons-lang
   git checkout 8538458e7aeb1455a5942f60fe0b4930da6c5d68
   ```

2. Add profiles to `pom.xml` (inside `<profiles>` section):
   - Smart Test Picker profile: enables JaCoCo per-test instrumentation
   - PIT profile: see `config/pit_profile.xml`

3. Ensure `.gitattributes` contains:
   ```
   *.java diff=java
   ```

## Hardware

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| RAM | 8 GB | 16 GB |
| CPU | 4 cores | 8 cores |
| Disk | 2 GB free | 5 GB free |

**Time estimates:**
| Step | Duration |
|------|----------|
| Coverage map generation (Step 1) | ~10 minutes |
| PIT mutation testing (Step 2) | ~15-30 minutes (21 classes sequentially) |
| Evaluation + baselines (Steps 3-4) | < 10 seconds |
| **Total** | **~25-40 minutes** |

## Python Dependencies

No external packages required  - all scripts use only the Python standard library:
- `argparse`, `json`, `xml.etree.ElementTree`, `pathlib`, `subprocess`
- `random`, `re`, `collections`, `shutil`, `time`, `datetime`

No `requirements.txt` or virtual environment needed.
