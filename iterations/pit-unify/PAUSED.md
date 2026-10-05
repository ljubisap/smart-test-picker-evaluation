# Paused at the user's request

On 2026-10-05 the user explicitly requested a pause before continuing spring-core.

- JGraphT completed all 20 class jobs; its matrices and logs remain preserved.
- The initial spring-core attempt reached AbstractResource after seven failed jobs. The campaign log remains at `campaigns.log`.
- The orchestrator (PID 42219), PIT launcher (55307), and coverage minion (55313) were stopped with termination signals. The interrupted AbstractResource job is not a completed result and must not be counted as a project failure or a timeout.
- No new jobs or retries were started after the pause request. The interrupted JVM has no resumable checkpoint; continuation requires a new targeted attempt.
- Before resuming, investigate missing runtime project JARs in the recorded spring-core PIT classpath. Prior testClasses/pitClasspath tasks did not materialize the runtime main/test-fixtures JARs. Preserve initial failed-attempt evidence before any infrastructure retry; do not modify source, tests, scope, or PIT settings.

Resume only on the user's instruction. No commit or push was performed for this pause.

## Resumed

The user subsequently explicitly authorized continuing spring-core and the remaining
iteration. `scripts/resume_spring.py` preserved the interrupted attempt, completed
the runtime prerequisites, and executed all 22 documented jobs. See
`pit/spring-core/campaign.json` and `spring-resume.log`; this file records the earlier
pause, not the current execution state.
