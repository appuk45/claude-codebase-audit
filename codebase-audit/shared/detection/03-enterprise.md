# Detection Spec 03 — Enterprise Readiness

**ISO 25010:** Reliability (production readiness / operability of the deployable unit)
**Audit key:** `enterprise`
**Basis:** 12-Factor App + production-readiness practice.
**Static analysis only.** Reason about the actual framework/runtime; do not assume
Django/Express.

## How to use this spec (agent instructions)

1. Read `discovery_context`. This dimension targets long-running services. If
   `archetypes` is only `library`/`cli-tool`/`frontend-spa`/`data-ml` (no server), most items
   are `skipped` — emit them as skipped, don't invent findings.
2. Run each applicable item's `signals` → candidate `file:line` list.
3. Read ONLY candidate snippets. Apply `confirm`. Ignore test/dev-only files
   (`tests/`, `conftest.py`, `*.dev.*`, `docker-compose.override`) for prod-readiness verdicts.
4. Assign `severity` with maturity modifiers.
5. Consult `examples/03-enterprise.md` only when ambiguous.
6. Emit `AuditResult` JSON per `shared/schema.json`. Score per `shared/scoring.md`.

---

## Configuration

### ent_config_env — Config read from environment
- **intent:** Env-specific values (hosts, ports, credentials, URLs, toggles) must come from
  the environment so the same artifact runs across environments (12-Factor III).
- **applies_to:** web-api, fullstack, worker-service, cli-tool
- **signals:** hardcoded env-specific literals — `https?://[a-z0-9.]+` (non-localhost hosts),
  DB DSNs, `port\s*=\s*\d+`, region/bucket names — assigned directly instead of
  `os.environ|os.getenv|process.env|config(`.
- **confirm:** fail if environment-specific config is hardcoded in application code
  (not env/config-driven). pass if read from env/config with sane defaults. Ignore test files.
- **severity:** Medium (prototype/internal → Low)
- **remediation:** Move env-specific values to environment variables / a config layer.
- **compliance_refs:** 12-Factor III (Config), ISO25010 Reliability

### ent_config_validation — Required config validated at startup
- **intent:** Missing/invalid critical config should fail fast at boot, not surface as a
  runtime error mid-request or silently use an unsafe default.
- **applies_to:** web-api, fullstack, worker-service
- **signals:** `os.getenv\(['\"][^'\"]+['\"]\s*,\s*['\"]` (default fallback) on
  security/critical keys; absence of a startup settings/schema validator
  (`pydantic BaseSettings|env schema|assert .*env|required`).
- **confirm:** warning if critical config has silent defaults or no startup validation.
  pass if a settings model / explicit required-var check runs at startup.
- **severity:** Medium
- **remediation:** Validate required config at startup (settings schema); fail fast if absent.
- **compliance_refs:** 12-Factor III, ISO25010 Reliability

---

## Disposability & Lifecycle

### ent_health_checks — Liveness/readiness endpoints
- **intent:** Orchestrators need health/readiness endpoints to route traffic and restart
  unhealthy instances.
- **applies_to:** web-api, fullstack, worker-service
- **signals:** absence of a route matching `/health|/healthz|/readyz|/livez|/ping|/status`
  in route definitions.
- **confirm:** warning if a long-running service exposes no health/readiness endpoint.
  pass if present. readiness should reflect backing-service reachability.
- **severity:** Medium (prototype/internal → Low)
- **remediation:** Add liveness + readiness endpoints; readiness checks critical deps.
- **compliance_refs:** 12-Factor IX (Disposability), ISO25010 Reliability

### ent_graceful_shutdown — Graceful shutdown on signals
- **intent:** On SIGTERM the process should stop accepting work, finish in-flight requests,
  and close resources — avoiding dropped requests/corruption on deploy.
- **applies_to:** web-api, fullstack, worker-service
- **signals:** absence of `signal.signal\(|SIGTERM|SIGINT|atexit|lifespan|
  process.on\(['\"]SIGTERM|@app.on_event\(['\"]shutdown|server.close\(`.
- **confirm:** warning if no signal handling / shutdown hook exists for a long-running
  service (workers, servers). pass if graceful shutdown/draining is wired.
- **severity:** Medium (prototype/internal → Low)
- **remediation:** Handle SIGTERM/SIGINT; drain connections; close DB/queue clients.
- **compliance_refs:** 12-Factor IX, ISO25010 Reliability

### ent_process_manager — Prod entrypoint uses a real server
- **intent:** Dev servers (`runserver`, `flask run`, `app.run(debug=True)`, `next dev`) are
  single-threaded/insecure and must not run production.
- **applies_to:** web-api, fullstack
- **signals:** `manage.py runserver|flask run|app.run\(.*debug\s*=\s*True|
  uvicorn.*reload=True|next dev|npm run dev` in Dockerfile CMD / entrypoint / Procfile.
- **confirm:** fail if the production entrypoint launches a dev server. pass for
  gunicorn/uvicorn workers/waitress/pm2/`next start`.
- **severity:** Medium (prototype → Low)
- **remediation:** Run under a production WSGI/ASGI server or process manager with workers.
- **compliance_refs:** 12-Factor VII/VIII, ISO25010 Reliability

---

## Scalability & Statelessness

### ent_statelessness — No local state that breaks horizontal scale
- **intent:** In-process/on-disk state (local session store, in-memory cache as
  source-of-truth, local file uploads) breaks when >1 instance runs behind a load balancer.
- **applies_to:** web-api, fullstack, worker-service
- **signals:** `FileSystemSessionStore|session.*filesystem|global \w+ =\s*\{\}|
  in-memory|local_cache\s*=|open\(.*['\"]w|save\(.*/tmp|MemoryStorage`.
- **confirm:** fail if request/session state or uploaded data is stored in process memory or
  local disk as the source of truth. pass for shared store (Redis/DB/object storage).
- **severity:** Medium (single-instance prototype → Low)
- **remediation:** Externalize sessions/cache/uploads to shared backing services.
- **compliance_refs:** 12-Factor VI (Stateless Processes), ISO25010 Reliability

### ent_backing_services — Backing services attached via config
- **intent:** Databases, caches, queues, and object stores should be attachable resources
  addressed by config URL, swappable without code change (12-Factor IV).
- **applies_to:** web-api, fullstack, worker-service
- **signals:** hardcoded backing-service hosts (`localhost:5432|127.0.0.1:6379|
  amqp://localhost`) in application code rather than a config-provided URL.
- **confirm:** warning if a backing service endpoint is hardcoded rather than config-driven.
  pass if provided via env/config URL.
- **severity:** Low (prototype → Info)
- **remediation:** Address backing services by config URL; no hardcoded hosts.
- **compliance_refs:** 12-Factor IV (Backing Services), ISO25010 Reliability

---

## Dev/Prod Parity & Release

### ent_env_parity — No dev/prod divergence in code
- **intent:** Branching business logic on environment, hardcoded localhost, or dev-only
  datastores (sqlite for prod) causes "works in dev, breaks in prod".
- **applies_to:** web-api, fullstack, worker-service
- **signals:** `if .*(DEBUG|DEV|LOCAL)\b` gating non-trivial logic; `sqlite` as the primary
  DB in app config; `localhost|127.0.0.1` in non-test code.
- **confirm:** warning if execution paths diverge by environment beyond config values, or a
  dev datastore is wired as the primary. pass if parity maintained via config only.
- **severity:** Low (prototype → Info)
- **remediation:** Keep dev/prod differences in config, not code branches; match datastores.
- **compliance_refs:** 12-Factor X (Dev/Prod Parity), ISO25010 Reliability

### ent_migrations — Versioned, reversible schema migrations
- **intent:** Schema changes must be versioned migrations (not manual SQL or auto-create at
  runtime) so deploys/rollbacks are safe and repeatable.
- **applies_to:** web-api, fullstack, worker-service, data-ml
- **signals:** ORM models present but no migrations dir (`migrations/|alembic/|
  prisma/migrations|knex migrations`); `create_all\(|synchronize:\s*true|db.create_all` at
  runtime.
- **confirm:** fail if the schema is auto-created at runtime (`create_all`/`synchronize:true`)
  or there are models with no migration history. warning if migrations exist but are
  irreversible. pass for versioned reversible migrations.
- **severity:** Medium (prototype → Low)
- **remediation:** Use a migration tool; version + make migrations reversible; no runtime
  auto-create in prod.
- **compliance_refs:** ISO25010 Reliability (Maturity)

### ent_build_release_run — Build separated from run
- **intent:** Installing deps / compiling assets at container start (not build time) slows
  and destabilizes releases (12-Factor V).
- **applies_to:** web-api, fullstack, worker-service
- **signals:** `pip install|npm install|npm run build|go build` inside a container
  `CMD`/`ENTRYPOINT` or process start command rather than the build stage.
- **confirm:** warning if dependency install / asset build happens at runtime start.
  pass if done in the build stage.
- **severity:** Low
- **remediation:** Move install/build to the image build; runtime only executes.
- **compliance_refs:** 12-Factor V (Build/Release/Run), ISO25010 Reliability

### ent_feature_flags — Rollout-sensitive changes gated
- **intent:** Feature flags/config toggles enable safe progressive rollout and quick
  disable without redeploy. (Advisory — absence is not a defect for small apps.)
- **applies_to:** web-api, fullstack
- **signals:** absence of any flag mechanism (`flag|toggle|LaunchDarkly|unleash|
  is_enabled\(`) in a codebase with risky/large surface.
- **confirm:** warning (info at low maturity) if a large/enterprise app has no flag mechanism
  for rollout control. pass/skip otherwise.
- **severity:** Low (prototype/internal → Info; enterprise → Low)
- **remediation:** Introduce feature flags for risky changes and progressive rollout.
- **compliance_refs:** ISO25010 Reliability (Availability)

---

## Cross-references (scored elsewhere — do NOT emit here)

- Secrets in code/config → dim 2 (security).
- Structured logging / metrics / tracing / log-to-stdout → dim 11 (observability).
- Retries, timeouts, circuit breakers, idempotency, graceful degradation → dim 9 (resilience).
- Dependency pinning / lockfiles / CVEs → dim 6 (dependencies).
- Resource leaks (unclosed files/connections) → dim 4 (issues).
- API versioning / compatibility → dim 8 (API).
- Container/K8s probes, resource limits, non-root → dim 10 (container & IaC).
