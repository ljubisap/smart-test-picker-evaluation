# Container lifecycle evidence

The exact PIT export fails before a runnable test method is invoked.

`BytecodeEnhancedTestEngine.discover()` calls `doDiscover()`. For a class annotated with `@BytecodeEnhanced`, `doDiscover()` calls `enhanceTestClass()` and constructs replacement descriptors before execution of the leaf descriptors. With mutant 35 installed, enhancement of `Leaf` calls the mutated `BiDirectionalAssociationHandler#target`, receives `null`, and later throws at `entityType`.

All three mutant selectors—each method separately and the class container—produce the same synthetic Gradle/JUnit result:

```text
P0_LEAF_START ... name=initializationError
P0_LEAF_FINISH ... name=initializationError result=FAILURE
TypeNotPresentException
  caused by ClassNotFoundException at BytecodeEnhancedClassUtils.java:250
  caused by EnhancementException at EnhancerImpl.java:163
  caused by NullPointerException at BiDirectionalAssociationHandler.java:265
```

Neither real method name receives `P0_LEAF_START` under the mutant. The XML contains one `initializationError`, not either source leaf. On pristine bytecode, each exact method selector starts and finishes the named leaf successfully. This corroborates PIT's `numberOfTestsRun=0`: the detecting activity is engine discovery/enhancement associated with the class container.

The method selector is still causally relevant—it causes JUnit to discover the containing enhanced class—but it does not make the selected leaf an independently demonstrated killing test. The leaf-level oracle therefore cannot assign the container failure to either descendant.
