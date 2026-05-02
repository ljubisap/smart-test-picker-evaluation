# Requirements

## Software

| Tool | Version | Purpose |
|------|---------|---------|
| Java | 17+ | Build and test execution |
| Maven | 3.9+ | Build tool for commons-lang |
| Python | 3.9+ | Evaluation scripts |
| Git | 2.x | Change detection |

## Maven Plugins (automatically downloaded)

| Plugin | Version | Purpose |
|--------|---------|---------|
| PIT (pitest-maven) | 1.17.4 | Mutation testing |
| pitest-junit5-plugin | 1.2.1 | JUnit 5 support for PIT |
| Smart Test Picker | 0.1.11 | Per-test coverage map generation |

## Smart Test Picker Installation

The Smart Test Picker Maven plugin must be installed in the local Maven repository:

```bash
cd /path/to/smart-test-picker-working
./gradlew :smart-test-picker-maven:publishToMavenLocal
```

This installs `io.github.ljubisap:smart-test-picker-maven:0.1.11` to `~/.m2/repository/`.

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

- Minimum: 8 GB RAM, 4 CPU cores
- PIT run time: ~5 minutes (21 classes, 772 mutations)
- Coverage map generation: ~10 minutes (full test suite)

## Python Dependencies

No external packages required — scripts use only the Python standard library.
