# Requirements — Spring Framework (spring-core)

## Software

| Tool | Version | Verified | Purpose |
|------|---------|----------|---------|
| Java | OpenJDK 21+ (SapMachine) | `java -version` | Build and test execution |
| Gradle | 8.14+ (via wrapper) | `./gradlew --version` | Build tool |
| Python | 3.10+ | `python3 --version` | Evaluation scripts |
| Git | 2.39+ | `git --version` | Change detection |
| Maven | 3.9+ | `mvn --version` | PIT jar download only |

## Smart Test Picker Installation

```bash
cd /path/to/smart-test-picker-working
git checkout sap/main
./gradlew publishToMavenLocal
```

Installs `com.sap.oss.smart-test-picker:smart-test-picker:0.1.0` to `~/.m2/repository/`.

Verify:
```bash
ls ~/.m2/repository/com/sap/oss/smart-test-picker/smart-test-picker/0.1.0/
```

## PIT Dependencies (auto-downloaded)

| Artifact | Version | Purpose |
|----------|---------|---------|
| pitest-command-line | 1.17.4 | PIT CLI execution |
| pitest | 1.17.4 | Core mutation engine |
| pitest-entry | 1.17.4 | Entry point |
| pitest-junit5-plugin | 1.2.1 | JUnit 5 support |
| commons-text | 1.12.0 | XML report formatting |
| commons-lang3 | 3.14.0 | Required by commons-text |

## Hardware

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| RAM | 8 GB | 16 GB |
| CPU | 4 cores | 8 cores |
| Disk | 5 GB free | 10 GB free |

**Time estimates:**
| Step | Duration |
|------|----------|
| Coverage map generation (Step 1) | ~3 minutes |
| PIT mutation testing (Step 2) | ~15 minutes |
| Evaluation + baselines (Steps 3-4) | < 1 second |
| **Total** | **~20 minutes** |

## Python Dependencies

No external packages required — all scripts use only the Python standard library.
