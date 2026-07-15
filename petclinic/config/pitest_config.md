# PIT (Pitest) Configuration for Spring PetClinic

## Gradle Plugin

```groovy
plugins {
    id 'info.solidsoft.pitest' version '1.15.0'
}

dependencies {
    pitest 'org.pitest:pitest-junit5-plugin:1.2.1'
}

pitest {
    targetClasses = ['org.springframework.samples.petclinic.*']
    targetTests = ['org.springframework.samples.petclinic.*']
    excludedTestClasses = [
        'org.springframework.samples.petclinic.MySqlIntegrationTests',
        'org.springframework.samples.petclinic.PostgresIntegrationTests',
        'org.springframework.samples.petclinic.PetClinicIntegrationTests',
        'org.springframework.samples.petclinic.system.CrashControllerIntegrationTests'
    ]
    outputFormats = ['XML', 'HTML']
    fullMutationMatrix = true
    mutators = ['DEFAULTS']
    timestampedReports = false
    threads = 4
    jvmArgs = ['-Xmx2g']
}
```

## Key Parameters

| Parameter | Value | Purpose |
|-----------|-------|---------|
| `targetClasses` | `petclinic.*` | All production classes |
| `targetTests` | `petclinic.*` | All test classes in scope |
| `excludedTestClasses` | 4 integration test classes | Require Docker, not unit tests |
| `fullMutationMatrix` | `true` | Continue after first kill to record additional PIT-reported killing tests |
| `mutators` | `DEFAULTS` | Standard PIT mutator set |
| `timestampedReports` | `false` | Fixed output path (no date subdirs) |
| `threads` | `4` | Parallel mutation testing |

## Why fullMutationMatrix=true

Without this flag, PIT stops after the first killing test. With it enabled, PIT continues processing and records additional PIT-reported killing tests within the configured test scope. PIT documents this as a partially supported feature.

## Excluded Test Classes

These are Spring Boot integration tests that require a running database (Docker Compose):
- `MySqlIntegrationTests`  - Testcontainers MySQL
- `PostgresIntegrationTests`  - Testcontainers PostgreSQL
- `PetClinicIntegrationTests`  - Full Spring Boot context
- `CrashControllerIntegrationTests`  - Error handling integration test

They are also excluded from the coverage map. Results apply to the remaining 52-test scope.

## Output Location

```
build/reports/pitest/
|-- mutations.xml       <- Primary output for evaluation
|-- index.html          <- Visual report
`-- org.springframework.samples.petclinic.*/ <- Per-class HTML
```
