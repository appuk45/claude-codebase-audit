# Detection Spec 11 — Observability

**ISO 25010:** Reliability (Operability / Recoverability support)
**Audit key:** `observability`
**Owns OWASP A09:2025** (Security Logging & Alerting Failures) — dims 2 and 10 point here.
**Static analysis only.** Services-focused; single-process scripts get a reduced subset.

## How to use this spec (agent instructions)

1. Read `discovery_context`. Skip items whose `applies_to` doesn't match → `skipped`.
   Multi-service items (correlation IDs, tracing) skip for a single-service app.
2. Run `signals` to locate logging/telemetry sites; read them to judge quality.
3. Apply `confirm`. Assign `severity`. `obs_pii_in_logs` holds High.
4. Consult `examples/11-observability.md` only when ambiguous.
5. Emit `AuditResult` JSON per `shared/schema.json`. Score per `shared/scoring.md`.

**Boundary:** error responses leaking stacks to clients → dim 2; error swallowing → dim 4;
missing fault handling → dim 9; health-check endpoints → dim 3. Here = logs/metrics/traces.

---

## Sensitive Data

### obs_pii_in_logs — No PII or secrets in logs/telemetry
- **intent:** Logging passwords, tokens, emails, card numbers, or full request bodies creates
  compliance exposure (GDPR/PCI) and turns log storage into a breach target.
- **applies_to:** all backend, fullstack, data-ml
- **signals:** `log.*\b(password|token|secret|ssn|card|cvv|authorization)\b`;
  `log.*request\.(body|data|json)|log.*headers`; logging whole user/objects; DEBUG dumps of
  payloads.
- **confirm:** fail if PII/secrets are written to logs/telemetry in plaintext. pass if
  redacted/masked/hashed or not logged. Non-identifying IDs (user_id) are acceptable.
- **severity:** High (floor:High — compliance)
- **remediation:** Redact/mask at the logger; allowlist safe fields; never log secrets or full
  bodies.
- **compliance_refs:** OWASP A09:2025, CWE-532; GDPR/PCI-DSS

---

## Logging Quality

### obs_structured_logging — Structured logs with consistent schema
- **intent:** Free-text `print`/`console.log` can't be queried, correlated, or aggregated;
  structured JSON with stable fields can.
- **applies_to:** web-api, fullstack, worker-service
- **signals:** `\bprint\(|console\.log\(` used as logging in app code; string-concatenated log
  messages; no logging library/config.
- **confirm:** warning if the service logs via `print`/`console.log` or unstructured strings
  instead of a structured logger. pass for a structured (JSON) logger with a consistent
  schema.
- **severity:** Medium (prototype → Low)
- **remediation:** Use a structured logger (structlog/pino/winston/JSON) with stable typed
  fields.
- **compliance_refs:** ISO25010 Operability

### obs_error_context — Errors logged with context
- **intent:** `log(e)` with no context, stack, or correlation id is nearly useless in an
  incident.
- **applies_to:** web-api, fullstack, worker-service
- **signals:** `except.*:\s*log(ger)?\.(error|warning)\([^)]*\)` without stack/`exc_info`;
  `catch (e) { logger.error(e.message) }` dropping the stack; no request/trace id in error
  logs.
- **confirm:** warning if errors are logged without stack trace and correlating context.
  pass if errors include stack + request/trace id + relevant fields.
- **severity:** Medium (prototype → Low)
- **remediation:** Log `exc_info`/stack + correlation id + operation context on errors.
- **compliance_refs:** ISO25010 Operability; OWASP A09:2025

### obs_log_levels — Correct log levels, no debug noise
- **intent:** DEBUG in production and stray debug prints create cost, noise, and leakage.
- **applies_to:** web-api, fullstack, worker-service
- **signals:** log level hardcoded to DEBUG; `console.log`/`print` debug leftovers;
  everything logged at one level.
- **confirm:** warning if DEBUG is enabled in prod config or debug prints remain. pass for
  env-driven levels used correctly (DEBUG/INFO/WARN/ERROR).
- **severity:** Low
- **remediation:** Drive level from env; default INFO/WARN in prod; remove debug prints.
- **compliance_refs:** ISO25010 Operability

---

## Correlation & Tracing

### obs_correlation_ids — Request/correlation IDs propagated
- **intent:** Without a correlation/request id threaded through logs, you can't reconstruct a
  single request across services.
- **applies_to:** web-api, fullstack, worker-service (multi-service)
- **signals:** no request-id/correlation-id middleware; downstream calls not forwarding an
  `X-Request-ID`/`traceparent`; logs without a request id field.
- **confirm:** warning (multi-service) if requests aren't tagged with a correlation id
  propagated downstream and logged. skip for a single standalone service.
- **severity:** Medium (single-service → Low)
- **remediation:** Generate a correlation id at the edge; propagate via header; log it.
- **compliance_refs:** ISO25010 Operability

### obs_tracing — Distributed tracing instrumented
- **intent:** Spans across services reveal latency and failure paths that logs alone can't.
- **applies_to:** web-api, fullstack, worker-service (multi-service)
- **signals:** no OpenTelemetry/tracing SDK; no span instrumentation on service boundaries.
- **confirm:** info/warning (enterprise/microservice) if there is no distributed tracing.
  skip for a monolith/simple app.
- **severity:** Low (enterprise/microservice → Medium)
- **remediation:** Instrument with OpenTelemetry; propagate trace context; export spans.
- **compliance_refs:** ISO25010 Operability

---

## Metrics, Monitoring & Audit

### obs_metrics — Key metrics exposed
- **intent:** Metrics (request rate, errors, duration — RED) detect problems before users do;
  logs alone are expensive and slow for this.
- **applies_to:** web-api, fullstack, worker-service
- **signals:** no metrics endpoint/exporter (`/metrics`, prometheus_client, StatsD, OTel
  metrics); no RED/business metrics emitted.
- **confirm:** warning if the service exposes no operational metrics. pass if RED (and key
  business) metrics are emitted.
- **severity:** Low (enterprise → Medium)
- **remediation:** Expose RED metrics (Prometheus/OTel); add key business counters.
- **compliance_refs:** ISO25010 Operability

### obs_security_event_logging — Security events are logged
- **intent:** Failing to log authn/authz failures and input-validation failures means attacks
  go undetected (OWASP A09).
- **applies_to:** web-api, fullstack
- **signals:** auth/permission failure paths that don't log; no log on access-control denial,
  login failure, or rejected input at security boundaries.
- **confirm:** warning if security-relevant events (auth success/failure, access denial,
  validation failures) are not logged in a detectable, structured way. pass if they are.
- **severity:** Medium (enterprise/regulated → High)
- **remediation:** Log security events with enough context for detection + alerting; feed a
  SIEM.
- **compliance_refs:** OWASP A09:2025, CWE-778

### obs_monitoring_alerting — Errors reach a monitoring system
- **intent:** Errors only on stdout are invisible; they must reach an error tracker /
  monitoring system so someone can be alerted.
- **applies_to:** web-api, fullstack, worker-service
- **signals:** no error-tracking/monitoring integration (Sentry/Rollbar/OTel/APM); exceptions
  only printed/logged locally.
- **confirm:** info/warning if there is no error-reporting/alerting integration. pass if
  errors are shipped to a monitoring/alerting system.
- **severity:** Low (enterprise → Medium)
- **remediation:** Integrate an error tracker / APM; define alerts on error-rate + SLOs.
- **compliance_refs:** OWASP A09:2025; ISO25010 Operability

### obs_audit_trail — Privileged actions are audited
- **intent:** Sensitive/privileged actions (role changes, data exports, deletions) need a
  tamper-evident record for compliance + forensics.
- **applies_to:** web-api, fullstack
- **signals:** admin/privileged/state-changing actions with no audit-log write (who, what,
  when, target).
- **confirm:** warning (enterprise/regulated) if privileged actions are not recorded to an
  audit trail. skip for simple apps with no privileged operations.
- **severity:** Low (regulated/enterprise → Medium)
- **remediation:** Record privileged actions (actor, action, target, timestamp) to an audit
  log.
- **compliance_refs:** OWASP A09:2025; ISO25010 Operability

---

## Cross-references (scored elsewhere — do NOT emit here)

- Stack traces / secrets leaked in error **responses** to clients → dim 2 (`sec_error_leakage`).
- Catch-and-hide error swallowing → dim 4.
- Missing fault handling / recovery at dependency boundaries → dim 9.
- Health/readiness endpoints → dim 3; K8s probe wiring → dim 10.
- PII handling at rest / GDPR data lifecycle → deferred v2 (here = PII in logs/telemetry only).
