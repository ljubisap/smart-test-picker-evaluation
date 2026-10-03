# Commands

All Gradle/PIT JVMs used JDK 21, `--max-workers=8`, and `-XX:ActiveProcessorCount=8` where applicable.

1. Create a detached clean worktree at `a95dd44cf654131e984682687cf1b2ec5d3e34cd`:

   `git worktree add --detach /private/tmp/hibernate-p0.wazyj9/subject a95dd44cf654131e984682687cf1b2ec5d3e34cd`

2. Run `:hibernate-core:pitest` with the diagnostic init script
   `/private/tmp/hibernate-p0.wazyj9/pit-export.init.gradle`. The script pins
   PIT 1.17.4, JUnit 5 plugin 1.2.1, the one target production class and test
   class, `DEFAULTS`, `fullMutationMatrix=true`, `+EXPORT`, and eight threads:

   `JAVA_HOME=/Library/Java/JavaVirtualMachines/sapmachine-21.jdk/Contents/Home GRADLE_USER_HOME=/Users/D061177/work/issta/.gradle-hibernate-pit-jdk21 JAVA_TOOL_OPTIONS=-XX:ActiveProcessorCount=8 ./gradlew --no-daemon --max-workers=8 -Porm.jdk.min=21 -I /private/tmp/hibernate-p0.wazyj9/pit-export.init.gradle :hibernate-core:pitest`
3. Identify export `mutants/35` by method descriptor, line 180, index 28, block 9, and `NullReturnValsMutator`.
4. Run each pristine method with the same JDK/cache/CPU prefix, the lifecycle
   init script, the native enhanced engine enabled, and one of these exact
   selectors:

   - `--tests org.hibernate.orm.test.bytecode.enhancement.merge.MergeEnhancedDetachedOrphanRemovalTest.testMergeDetachedOrphanRemoval`
   - `--tests org.hibernate.orm.test.bytecode.enhancement.merge.MergeEnhancedDetachedOrphanRemovalTest.testMergeDetachedNonEmptyCollection`
5. Replace only the isolated worktree's compiled production class with the
   PIT-exported mutant, exclude `:hibernate-core:compileJava`, and repeat both
   exact method selectors through `:hibernate-core:test`.
6. Run the class selector
   `--tests org.hibernate.orm.test.bytecode.enhancement.merge.MergeEnhancedDetachedOrphanRemovalTest`
   against the same mutant.

The exact shell commands and lifecycle output are retained in the `raw/` logs and the task transcript; no source file was edited.
