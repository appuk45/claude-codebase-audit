# Detection Spec 05 — Architecture & Scalability

**ISO 25010:** Reliability (structural soundness / scalability of the module graph)
**Audit key:** `architecture`
**Static analysis only.** Module-graph / system level — distinct from dim 4 (unit level).
Most judgment-heavy dimension: build a dependency map FIRST, then reason. Do not assume a
specific framework.

## How to use this spec (agent instructions)

1. Read `discovery_context`. Skip items whose `applies_to` doesn't match → `skipped`.
   Small single-module apps: coupling/layering/boundaries usually `skipped`.
2. **Build a module dependency map first**: extract imports
   (`rg -n "^(from|import) |require\(|^import .* from"`), group by top-level package/dir.
   Prefer `madge --circular` (JS/TS) or `pydeps`/`import-linter` (Python) for cycles if
   installed.
3. Detect cycles + layer violations structurally from the map. Then read only the suspect
   boundary files to confirm.
4. Apply `confirm`. Assign `severity` with maturity modifiers.
5. Consult `examples/05-architecture.md` only when ambiguous.
6. Emit `AuditResult` JSON per `shared/schema.json`. Score per `shared/scoring.md`.

This dimension is NOT line-pattern driven — reason about the graph, not regex hits.

---

## Module Structure

### arch_circular_deps — No circular module dependencies
- **intent:** Import cycles are strong coupling — they block reuse, isolated testing, and
  change-impact analysis.
- **applies_to:** web-api, fullstack, worker-service, frontend-spa, library, data-ml
- **signals:** `madge --circular` / `pydeps --show-cycles` / `import-linter`; fallback: build
  the import map and detect back-edges between packages.
- **confirm:** fail for a genuine import cycle between modules/packages. warning for
  same-package cycles resolved lazily. pass if acyclic.
- **severity:** Medium (large/enterprise → High; prototype → Low)
- **remediation:** Break the cycle: extract a shared abstraction, invert a dependency (DIP),
  or move the shared type to a lower layer.
- **compliance_refs:** ISO25010 Modularity/Reliability

### arch_layering — Layer boundaries respected
- **intent:** A layered app must keep dependencies pointing one way (presentation → app →
  domain → infra). Domain importing presentation/infra inverts the architecture.
- **applies_to:** web-api, fullstack, library
- **signals:** domain/core modules importing web/ORM/framework packages
  (`from django|import flask|import requests|from .views|from .api`); views importing other
  views; infra importing domain-and-back.
- **confirm:** fail if a lower/core layer imports an outer layer (dependency inversion of the
  intended direction). pass if dependencies flow inward only.
- **severity:** Medium (prototype → Low)
- **remediation:** Depend inward only; use interfaces/ports at boundaries; move misplaced code.
- **compliance_refs:** ISO25010 Modularity

### arch_module_boundaries — Clear module interfaces
- **intent:** Consumers reaching into another module's internals/private members create
  brittle coupling.
- **applies_to:** web-api, fullstack, library, worker-service
- **signals:** deep imports into internal paths (`from pkg.internal._impl import`,
  `import x/dist/internal/...`); access to `_private` members across modules.
- **confirm:** warning if modules bypass public interfaces to reach internals of another
  module. pass if consumed via a public API surface.
- **severity:** Low (library → Medium; a leaky public API is worse for a library)
- **remediation:** Expose a public interface; keep internals private; import the facade.
- **compliance_refs:** ISO25010 Modularity, Reusability

---

## Coupling & Cohesion

### arch_coupling — No excessive inter-module coupling
- **intent:** A module depending on many others (high efferent coupling) or a package everyone
  depends on (god package) makes change risky.
- **applies_to:** web-api, fullstack, worker-service, frontend-spa
- **signals:** modules with very high import fan-out; a single module imported by nearly
  everything holding unrelated logic; frequent feature-envy (module A mostly using B's data).
- **confirm:** warning if a module has abnormally high coupling vs peers or acts as a
  god-package hub. pass otherwise.
- **severity:** Medium (prototype → Low)
- **remediation:** Split the hub by responsibility; introduce interfaces; reduce fan-out.
- **compliance_refs:** ISO25010 Modularity

### arch_cohesion — Modules grouped by responsibility
- **intent:** Low-cohesion "junk drawer" modules (`utils`, `misc`, `helpers`, `common`)
  accumulating unrelated code are hard to navigate and reuse.
- **applies_to:** all
- **signals:** large `utils/misc/common/helpers` modules with unrelated functions; files
  mixing several unrelated concerns.
- **confirm:** warning if a module groups unrelated responsibilities (low cohesion). pass for
  focused modules. A small shared-utils file is fine.
- **severity:** Low
- **remediation:** Regroup by domain/feature; split grab-bag modules.
- **compliance_refs:** ISO25010 Modularity, Reusability

### arch_separation_concerns — Business logic separated from I/O/presentation
- **intent:** Fat controllers/views mixing HTTP parsing, SQL, and business rules can't be
  tested or reused and resist change.
- **applies_to:** web-api, fullstack, frontend-spa
- **signals:** raw SQL / ORM queries / HTTP calls inside view/controller/route handlers;
  business rules embedded in templates/components; DB access from UI components.
- **confirm:** fail if substantial business logic + persistence + presentation are entangled
  in one handler/component. warning if partially mixed. pass if layered
  (handler → service → repository).
- **severity:** Medium (prototype → Low)
- **remediation:** Extract service/domain + repository layers; keep handlers thin.
- **compliance_refs:** ISO25010 Modularity, Analysability

---

## Dependency Direction

### arch_dependency_direction — Depend on abstractions (DIP)
- **intent:** High-level policy hardwired to concrete infrastructure (DB driver, HTTP client,
  framework) can't be swapped or tested; DI over hardcoded construction.
- **applies_to:** web-api, fullstack, library
- **signals:** domain/service code directly constructing concretes
  (`psycopg2.connect(|SomeClient(|new ConcreteRepo()`) instead of receiving an
  interface/dependency; no injection seams.
- **confirm:** warning if core logic depends on and constructs concrete infra directly with
  no abstraction/injection seam. pass if depends on interfaces / injected deps.
- **severity:** Medium (prototype/small → Low)
- **remediation:** Depend on interfaces; inject implementations at composition root.
- **compliance_refs:** ISO25010 Modularity, Modifiability

---

## Scalability

### arch_scalability_bottleneck — No structural bottleneck in hot path
- **intent:** Synchronous cross-service calls, monolithic multi-step transactions, and heavy
  work done inline (not queued) limit throughput and create contention under load.
- **applies_to:** web-api, fullstack, worker-service
- **signals:** chains of synchronous service/HTTP calls in a request path; a single DB
  transaction spanning many unrelated writes; heavy jobs (email, report, image) run inline
  instead of enqueued; a global lock/semaphore on a hot path.
- **confirm:** warning if the hot path has a clear scalability bottleneck (sync fan-out,
  mega-transaction, inline heavy work, global lock). pass if async/queued/partitioned.
- **severity:** Medium (enterprise/high-traffic → High; prototype → Low)
- **remediation:** Offload heavy work to queues; split transactions; parallelize/cache;
  remove hot-path global locks.
- **compliance_refs:** ISO25010 Reliability, Performance Efficiency (Capacity)

---

## Consistency

### arch_pattern_consistency — Consistent cross-cutting patterns
- **intent:** Multiple ways to do the same cross-cutting thing (three HTTP clients, mixed
  sync/async styles, ad-hoc config access) raises cognitive load and bugs.
- **applies_to:** all backend, fullstack, frontend-spa
- **signals:** several different HTTP clients (`requests` + `httpx` + `urllib`) or config
  access styles across the codebase; inconsistent error-handling conventions.
- **confirm:** warning if cross-cutting concerns are implemented inconsistently across the
  codebase without reason. pass if conventions are consistent.
- **severity:** Low
- **remediation:** Standardize on one client/convention; wrap cross-cutting concerns.
- **compliance_refs:** ISO25010 Analysability, Modifiability

---

## Cross-references (scored elsewhere — do NOT emit here)

- Statelessness / horizontal-scaling readiness → dim 3 (enterprise).
- Unit complexity, god-class, global-state smell → dim 4 (issues).
- Performance anti-patterns (N+1, pagination, caching, connection pool) → dim 1.
- Retries, timeouts, circuit breakers, bulkheads, fallbacks → dim 9 (resilience).
- API contract, versioning, backward compatibility → dim 8 (API).
- Container/orchestration scaling, resource limits → dim 10 (container & IaC).
