# Spring Security false-negative analysis

The JDK 21 campaign produced 340 KILLED mutants. STP missed ten. Every
missed mutant removes an `Assert` call on an exceptional input path. On the
pristine BASE execution, the assertion throws before JaCoCo reaches a later
probe that would mark the enclosing method. PIT's removal of that call allows
execution to continue, so the test detects the mutation even though the
pristine per-test map lacks the mutated method relation.

The existing A/B/C taxonomy is applied unchanged:

- **Type A:** the killing test lacks the mutated method but covers only the
  mutated class constructor; the constructor-only rule recovers it.
- **Type B:** the killing test lacks the mutated method but has other
  non-constructor coverage in the mutated class.
- **Type C:** the killing test has no footprint for the mutated class.

| Class | Method | Line | Killing-test condition | Type | Mitigated |
|---|---|---:|---|:---:|:---:|
| `RoleHierarchyImpl` | `withRolePrefix` | 130 | null role prefix | C | no |
| `DefaultAuthenticationEventPublisher` | `setAdditionalExceptionMappings` | 174 | empty map | B | no |
| `DefaultAuthenticationEventPublisher` | `setDefaultAuthenticationFailureEvent` | 193 | null event class | B | no |
| `AbstractUserDetailsAuthenticationProvider` | `afterPropertiesSet` | 127 | missing user cache | B | no |
| `AuthorityAuthorizationManager` | `hasAnyAuthority` | 122 | empty/null authorities | C | no |
| `AuthorityAuthorizationManager` | `hasAnyRole` | 108 | null role prefix | C | no |
| `AuthorityAuthorizationManager` | `hasAuthority` | 83 | null authority | C | no |
| `AuthorityAuthorizationManager` | `hasRole` | 69 | null role | C | no |
| `AuthorizationManagerBeforeMethodInterceptor` | `setAuthorizationEventPublisher` | 216 | null publisher | A | yes |
| `MapBasedAttributes2GrantedAuthoritiesMapper` | `setAttributes2grantedAuthoritiesMap` | 85 | empty map | A | yes |

All ten use PIT's `VoidMethodCallMutator` to remove the assertion invocation.
The raw mutation identity, PIT killing identities, exact coverage footprint,
and classifier evidence are retained in `results/aggregated/mutation_results.json`
and the repository-wide `results/failure_taxonomy.json`.

`InMemoryUserDetailsManager#updateUser` initially appeared unsafe only because
the evaluation model omitted the production selector's zero-method-hit class
escalation. Mandatory selector-equivalence verification detected that defect;
the corrected evaluator selects 18 class-covering tests exactly as the frozen
Java selector does. It is not counted as a false negative.

Spring Security therefore introduces additional observations of the already
defined early-exception/probe-shadowing mechanism, but no `NEW_TYPE`.
