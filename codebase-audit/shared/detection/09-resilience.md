# Detection Spec 09 — Resilience & Fault Tolerance

**ISO 25010:** Reliability (Fault Tolerance / Recoverability)
**Audit key:** `resilience`
**Static analysis only.** Applies where code calls external dependencies or runs as a
service. A single-process app with no external deps → most items `skipped`.

## How to use this spec (agent instructions)

1. Read `discovery_context`. Identify external-dependency boundaries: HTTP calls, DB/cache
   drivers, message queues, third-party SDKs. If none → skip most of this dimension.
2. Run `signals` to locate those call sites; read the surrounding code to judge protection.
3. Apply `confirm`. Assign `severity` with maturity modifiers. `res_timeouts` holds Medium.
4. Consult `examples/09-resilience.md` only when ambiguous.
5. Emit `AuditResult` JSON per `shared/schema.json`. Score per `shared/scoring.md`.

**Distinction from dim 4:** dim 4 `issue_error_swallowing` = catch-and-hide (bug hiding). Here
`res_fault_handling` = **missing** handling/recovery at a fault-prone dependency boundary.

---

## External-Call Protection

### res_timeouts — External calls have explicit timeouts
- **intent:** A call with no timeout can hang forever, exhausting threads/connections and
  cascading into a full outage.
- **applies_to:** web-api, fullstack, worker-service, frontend-spa, data-ml
- **signals:** `requests\.(get|post)\((?!.*timeout)|httpx\.|urlopen\((?!.*timeout)|
  fetch\((?!.*(signal|AbortController))|socket\.connect\(`; DB/driver clients without a
  connect/query timeout.
- **confirm:** fail if an external/network/DB call has no timeout configured. pass if an
  explicit timeout is set (per-call or client default).
- **severity:** Medium (critical synchronous path → High; holds at all maturities)
- **remediation:** Set explicit connect + read timeouts on every external call.
- **compliance_refs:** ISO25010 Fault Tolerance

### res_retries — Bounded retries with backoff
- **intent:** Retrying transient failures improves reliability, but unbounded/no-backoff
  retries cause retry storms that amplify an outage.
- **applies_to:** web-api, fullstack, worker-service, frontend-spa
- **signals:** manual retry loops (`for .* in range(.*): try:`) with no cap or sleep; retry
  decorators without backoff; `while True: try:` around a call.
- **confirm:** warning if retries are unbounded or lack exponential backoff (+jitter).
  pass for bounded retries with backoff (tenacity/retry libs, or explicit backoff). Info if no
  retries where transient failures are expected.
- **severity:** Medium (prototype → Low)
- **remediation:** Bound retry count; exponential backoff with jitter; cap total time.
- **compliance_refs:** ISO25010 Fault Tolerance

### res_retry_safety — Retries only safe operations
- **intent:** Blindly retrying a non-idempotent write (charge, create) on timeout can execute
  it twice.
- **applies_to:** web-api, fullstack, worker-service
- **signals:** retry wrapper around POST/charge/create/send operations without idempotency
  protection.
- **confirm:** warning if non-idempotent operations are retried without idempotency
  keys/dedup. pass if retries are limited to idempotent ops or protected by an idempotency
  mechanism.
- **severity:** Medium (payment/order ops → High)
- **remediation:** Retry only idempotent ops, or add an idempotency key/dedup before retrying.
- **compliance_refs:** ISO25010 Fault Tolerance; RFC 7231

---

## Failure Handling & Degradation

### res_fault_handling — Dependency calls are guarded
- **intent:** An unguarded dependency call that throws propagates an unhandled failure and
  takes down the whole request/worker.
- **applies_to:** web-api, fullstack, worker-service, frontend-spa
- **signals:** external calls not wrapped in `try/except`/`catch`/`Result` handling; no error
  path for a failed dependency.
- **confirm:** warning if a fault-prone dependency call has no error handling / recovery path.
  pass if failures are caught and handled meaningfully (not swallowed — see dim 4).
- **severity:** Medium (prototype → Low)
- **remediation:** Wrap dependency calls; handle/transform failures; return a sensible error.
- **compliance_refs:** ISO25010 Fault Tolerance

### res_fallback — Graceful degradation on failure
- **intent:** When a non-critical dependency is down, degrade (cached/default/partial
  response) instead of failing the whole operation.
- **applies_to:** web-api, fullstack, frontend-spa
- **signals:** dependency failure paths that hard-fail the request where a cached/default/
  partial result is feasible; no fallback for optional features.
- **confirm:** warning if a failure in a non-critical dependency hard-fails the whole request
  with no fallback. pass if graceful degradation exists (stale cache, default, skip optional).
- **severity:** Medium (prototype → Low)
- **remediation:** Provide fallbacks (stale cache, defaults, feature skip) for non-critical
  deps.
- **compliance_refs:** ISO25010 Fault Tolerance

### res_circuit_breaker — Circuit breaker on unreliable deps
- **intent:** Hammering a failing dependency wastes resources and delays recovery; a breaker
  fails fast and lets it recover.
- **applies_to:** web-api, fullstack, worker-service
- **signals:** repeated calls to a flaky external dependency with no breaker
  (`circuitbreaker|pybreaker|resilience4j|opossum|CircuitBreaker`) in a service that fans out
  to other services.
- **confirm:** warning (enterprise/microservice) if calls to an unreliable dependency have no
  circuit breaker. skip for simple apps with a single reliable local DB.
- **severity:** Low (enterprise/microservice → Medium)
- **remediation:** Wrap unreliable dependencies in a circuit breaker with fail-fast + recovery.
- **compliance_refs:** ISO25010 Fault Tolerance

### res_bulkhead — Resource isolation
- **intent:** Without isolation, one slow dependency consumes the shared thread/connection
  pool and starves everything.
- **applies_to:** web-api, fullstack, worker-service
- **signals:** a single shared pool for all outbound calls; no per-dependency concurrency
  limits; unbounded thread/task creation per request.
- **confirm:** warning (enterprise) if there is no resource isolation / concurrency cap
  between independent dependencies. skip for small apps.
- **severity:** Low (enterprise → Medium)
- **remediation:** Isolate pools per dependency; cap concurrency; bound task creation.
- **compliance_refs:** ISO25010 Fault Tolerance

---

## Async / Queue Reliability

### res_dlq — Dead-letter & poison-message handling
- **intent:** A message that always fails will be redelivered forever, blocking the queue;
  it must be dead-lettered after bounded attempts.
- **applies_to:** worker-service (and web-api that consumes queues)
- **signals:** message consumers (`consume|subscribe|@task|on_message`) with no
  max-retries/DLQ config; `ack` only on success with infinite redelivery.
- **confirm:** warning if a consumer has no dead-letter / max-attempt handling for poison
  messages. pass if DLQ / bounded attempts configured.
- **severity:** Medium (prototype → Low)
- **remediation:** Configure a DLQ + max delivery attempts; route poison messages aside.
- **compliance_refs:** ISO25010 Fault Tolerance, Recoverability

### res_idempotent_consumer — Idempotent message handling
- **intent:** At-least-once delivery means a message can arrive twice; non-idempotent handling
  double-processes (double-ship, double-charge).
- **applies_to:** worker-service (and web-api consuming queues)
- **signals:** consumers performing writes/side effects keyed only on message arrival, no
  dedup/idempotency key/processed-set.
- **confirm:** warning if a consumer's side effects are not idempotent under redelivery. pass
  if dedup/idempotency is enforced.
- **severity:** Medium (financial/critical → High)
- **remediation:** Dedup by message/idempotency key; make side effects idempotent.
- **compliance_refs:** ISO25010 Fault Tolerance

---

## Cross-references (scored elsewhere — do NOT emit here)

- API-contract idempotency + verb semantics → dim 8.
- Health/readiness checks, graceful shutdown → dim 3 (enterprise).
- Rate limiting as a security control → dim 2.
- Unbounded input/request-body capacity limits → dim 1.
- Catch-and-hide error swallowing (bug hiding) → dim 4.
