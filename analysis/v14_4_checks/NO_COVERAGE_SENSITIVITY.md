# NO_COVERAGE sensitivity (Part B)

Non-canonical frozen-data analysis. Every variant unions structural empty-footprint entries matching the 2e0954 condition. It does not replace canonical results.

| Subject | Empty | STP inclusive | Mean selected | Selected % | Constructor inclusive | Class inclusive | Random MC / analytical |
|---|---:|---:|---:|---:|---:|---:|---:|
| commons-lang | 0 | 771/772 (99.87%) | 17.01 | 0.36% | 771/772 | 771/772 | 2.03% / 2.02% |
| jgrapht | 1 | 516/517 (99.81%) | 88.70 | 3.84% | 517/517 | 517/517 | 33.90% / 33.94% |
| spring-core | 0 | 443/454 (97.58%) | 80.63 | 2.22% | 447/454 | 454/454 | 17.37% / 17.36% |
| petclinic | 0 | 94/94 (100.00%) | 9.72 | 18.70% | 94/94 | 94/94 | 35.97% / 35.88% |
| flink | 1 | 349/349 (100.00%) | 37.23 | 5.60% | 349/349 | 349/349 | 19.84% / 19.88% |
| spring-security | 23 | 335/340 (98.53%) | 59.86 | 4.16% | 337/340 | 340/340 | 22.88% / 22.89% |
| hibernate | 0 | 400/401 (99.75%) | 297.25 | 27.05% | 400/401 | 401/401 | 71.33% / 71.30% |
| quarkus | 9 | 1083/1083 (100.00%) | 269.65 | 39.42% | 1083/1083 | 1083/1083 | 72.85% / 72.88% |

Records changing STP inclusiveness: **5**.

- `spring-security` `org.springframework.security.access.hierarchicalroles.RoleHierarchyImpl#withRolePrefix`: 9 → 32; footprint `C`, cause `EARLY_EXCEPTION_PROBE_SHADOWING`; newly selected killer(s): RoleHierarchyImplTests#testBuilderThrowIllegalArgumentExceptionWhenPrefixRoleNull_5894d6c.
- `spring-security` `org.springframework.security.authorization.AuthorityAuthorizationManager#hasAnyAuthority`: 65 → 88; footprint `C`, cause `EARLY_EXCEPTION_PROBE_SHADOWING`; newly selected killer(s): AuthorityAuthorizationManagerTests#hasAnyAuthorityWhenEmptyThenException_4acbb6d, AuthorityAuthorizationManagerTests#hasAnyAuthorityWhenNullThenException_666eb63.
- `spring-security` `org.springframework.security.authorization.AuthorityAuthorizationManager#hasAnyRole`: 63 → 86; footprint `C`, cause `EARLY_EXCEPTION_PROBE_SHADOWING`; newly selected killer(s): AuthorityAuthorizationManagerTests#hasAnyRoleWhenCustomRolePrefixNullThenException_224748b.
- `spring-security` `org.springframework.security.authorization.AuthorityAuthorizationManager#hasAuthority`: 14 → 37; footprint `C`, cause `EARLY_EXCEPTION_PROBE_SHADOWING`; newly selected killer(s): AuthorityAuthorizationManagerTests#hasAuthorityWhenNullThenException_5281bf4.
- `spring-security` `org.springframework.security.authorization.AuthorityAuthorizationManager#hasRole`: 7 → 30; footprint `C`, cause `EARLY_EXCEPTION_PROBE_SHADOWING`; newly selected killer(s): AuthorityAuthorizationManagerTests#hasRoleWhenNullThenException_85c3cde.

## Delta against v14.1 table precision

| Subject | Selector | Δ inclusive | Δ mean selected | Δ selected percentage points | Δ reduction percentage points |
|---|---|---:|---:|---:|---:|
| commons-lang | stpNc | +0 | +0 | +0 | +0 |
| commons-lang | constructorOnlyNc | +0 | +0 | +0 | +0 |
| commons-lang | classLevelNc | +0 | +0 | +0 | +0 |
| jgrapht | stpNc | +0 | +1 | +0.0433275563258235 | -0.0433275563258271 |
| jgrapht | constructorOnlyNc | +0 | +1 | +0.0433275563258235 | -0.0433275563258271 |
| jgrapht | classLevelNc | +0 | +1 | +0.0433275563258235 | -0.0433275563258271 |
| spring-core | stpNc | +0 | +0 | +0 | +0 |
| spring-core | constructorOnlyNc | +0 | +0 | +0 | +0 |
| spring-core | classLevelNc | +0 | +0 | +0 | +0 |
| petclinic | stpNc | +0 | +0 | +0 | +0 |
| petclinic | constructorOnlyNc | +0 | +0 | +0 | +0 |
| petclinic | classLevelNc | +0 | +0 | +0 | +0 |
| flink | stpNc | +0 | +1 | +0.150375939849624 | -0.150375939849624 |
| flink | constructorOnlyNc | +0 | +1 | +0.150375939849624 | -0.150375939849624 |
| flink | classLevelNc | +0 | +1 | +0.150375939849624 | -0.150375939849624 |
| spring-security | stpNc | +5 | +23 | +1.59722222222222 | -1.59722222222223 |
| spring-security | constructorOnlyNc | +5 | +23 | +1.59722222222222 | -1.59722222222221 |
| spring-security | classLevelNc | +5 | +23 | +1.59722222222222 | -1.59722222222221 |
| hibernate | stpNc | +0 | +0 | +0 | +0 |
| hibernate | constructorOnlyNc | +0 | +0 | +0 | +0 |
| hibernate | classLevelNc | +0 | +0 | +0 | +0 |
| quarkus | stpNc | +0 | +9 | +1.31578947368421 | -1.31578947368421 |
| quarkus | constructorOnlyNc | +0 | +9 | +1.31578947368421 | -1.31578947368421 |
| quarkus | classLevelNc | +0 | +9 | +1.31578947368421 | -1.31578947368422 |

Full-precision source values are in `no_coverage_sensitivity.json`. Random baseline: 1,000 trials, seed 42, same per-record seeding formula as `analysis/evaluate_subject.py:53–84`, with variant STP budgets.
