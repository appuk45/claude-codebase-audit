# Detection Spec 01 — Performance

**ISO 25010:** Performance Efficiency (Time Behaviour · Resource Utilization · Capacity)
**Audit key:** `performance`
**Static analysis only** — no runtime measurement. Frontend vitals (LCP/INP/CLS) are
inferred from static signals, not measured.

## How to use this spec (agent instructions)

1. Read `discovery_context`. Skip any item whose `applies_to` shares no archetype with
   `discovery_context.archetypes` → emit that item as `status: "skipped"`.
2. For each applicable item, run its `signals` (ripgrep) against the source to get a
   candidate `file:line` list. Prefer external-tool output (radon, eslint) where noted.
3. Read ONLY the candidate snippets. Apply `confirm` to keep/drop each candidate.
4. Assign `severity`, applying context modifiers from `discovery_context.context.maturity`.
5. Consult `examples/01-performance.md` ONLY when a candidate is ambiguous.
6. Emit `AuditResult` JSON per `shared/schema.json`. Score per `shared/scoring.md`.

`signals` are NON-exhaustive candidate-locators — not the pass/fail rule. `confirm` is the
rule. Reason about the actual framework; do not assume Django/Express.

---

## Time Behaviour

### perf_n_plus_one — No N+1 ORM query patterns
- **intent:** A query issued once per item in a loop turns 1 request into N+1 queries →
  latency scales with row count. Batch via eager-load/join.
- **applies_to:** web-api, fullstack, worker-service, data-ml
- **signals:**
  - `rg -n "for .+ in .+:" ` then within ~8 lines: `rg -n "\.(get|filter|find|findOne|query|execute)\("`
  - `rg -n "\.(map|forEach)\(" ` with `await` + DB/ORM call in body
- **confirm:** fail if an ORM/DB call executes inside a loop body AND no
  `select_related|prefetch_related|join|include|with|DataLoader|IN (` batching precedes the
  loop. pass if batching present.
- **severity:** High (context: stays High at all maturities)
- **remediation:** Eager-load/join before the loop, or batch IDs into one `IN (...)` query.
- **compliance_refs:** ISO25010 Time-Behaviour

### perf_blocking_in_async — No blocking calls on async paths
- **intent:** Sync/blocking calls inside coroutines or event-loop handlers stall the whole
  loop, collapsing concurrency.
- **applies_to:** web-api, fullstack, worker-service
- **signals:**
  - `rg -n "async def" -A 30` then `rg -n "requests\.(get|post)|time\.sleep\(|open\(|\.read\(\)"`
  - JS: `rg -n "\bfs\.(readFileSync|writeFileSync)|execSync\b"` inside `async`
- **confirm:** fail if a blocking HTTP/file/sleep call runs inside `async def`/`async`
  function. `asyncio.sleep`, `httpx`/`aiohttp`, `aiofiles`, `await fs.promises` = pass.
- **severity:** High (prototype/internal → Medium)
- **remediation:** Use async client (`httpx`/`aiohttp`), `asyncio.sleep`, `aiofiles`, or run
  blocking work in a threadpool/executor.
- **compliance_refs:** ISO25010 Time-Behaviour

### perf_loop_io — No expensive I/O inside loops
- **intent:** File/HTTP/DB I/O per loop iteration multiplies round-trips; use bulk ops.
- **applies_to:** web-api, fullstack, worker-service, cli-tool, data-ml
- **signals:** `rg -n "for .+ in .+:|while |\.forEach\(|\.map\("` then within body:
  `rg -n "requests\.|fetch\(|axios\.|open\(|\.read\(|urlopen\("`
- **confirm:** fail if HTTP or file I/O occurs per-iteration and a bulk/batch alternative
  exists. (DB-in-loop → also flag under perf_n_plus_one, not double-counted.)
- **severity:** Medium
- **remediation:** Hoist I/O out of the loop; use bulk/batch APIs or a single read.
- **compliance_refs:** ISO25010 Time-Behaviour

### perf_handler_compute — No heavy sync compute in request handler
- **intent:** CPU-bound work (large sorts, crypto, image/PDF processing, huge JSON) inline
  in a request handler blocks the worker and inflates tail latency.
- **applies_to:** web-api, fullstack
- **signals:** `rg -n "def .*(view|handler|route|controller|resolver)"` regions containing
  `rg -n "sorted\(|hashlib|bcrypt|Image\.|PdfReader|json\.dumps\(.{200,}"`
- **confirm:** fail if clearly heavy synchronous compute runs on the request path with no
  offload to a queue/worker/cache. warning if borderline.
- **severity:** Medium (enterprise → High)
- **remediation:** Offload to a background job/queue, precompute, or cache the result.
- **compliance_refs:** ISO25010 Time-Behaviour

---

## Resource Utilization

### perf_pagination — List endpoints are paginated
- **intent:** Returning an entire collection grows unbounded with data → memory + latency
  blowups.
- **applies_to:** web-api, fullstack
- **signals:** `rg -n "\.objects\.all\(\)|\.find\(\{\}\)|SELECT \*|return .*\.all\("` in
  route/view/controller/serializer files.
- **confirm:** fail if a list endpoint returns a full collection with no
  `limit|offset|page|cursor|paginate|slice`. warning if paginated but no max page size.
- **severity:** High no-pagination · Medium no-max (prototype/internal → one level down)
- **remediation:** Add limit/offset or cursor pagination; enforce a max page size.
- **compliance_refs:** ISO25010 Resource-Utilization, Capacity

### perf_unbounded_memory — No large datasets loaded whole into memory
- **intent:** Materializing a large table/file into memory risks OOM and GC pressure.
- **applies_to:** web-api, fullstack, worker-service, data-ml
- **signals:** `rg -n "\.all\(\)|\.readlines\(\)|\.read\(\)|list\(.*\.objects|find\(\{\}\)"`
- **confirm:** fail if a potentially large query/file is fully materialized (assigned + not
  streamed/iterated lazily/chunked). pass for lazy querysets, streaming, chunked reads.
- **severity:** Medium (data-ml pipelines → High if unbounded)
- **remediation:** Stream/iterate lazily, chunk, or `.iterator()`/generators.
- **compliance_refs:** ISO25010 Resource-Utilization

### perf_caching — Repeated expensive calls are cached
- **intent:** Recomputing the same query/HTTP call across requests wastes resources; caching
  cuts load. Missing stampede protection can collapse the DB on cache expiry.
- **applies_to:** web-api, fullstack, worker-service
- **signals:** identical query/HTTP call appearing 3+ times; absence of
  `rg -n "cache|lru_cache|redis|memcache|@cache"`
- **confirm:** warning if the same expensive call recurs 3+ times with no cache. pass if
  cache decorator/layer present. note stampede risk if cache set without lock/coalescing.
- **severity:** Medium (prototype/internal → Low)
- **remediation:** Add caching (in-proc/Redis); use request coalescing or cache warming.
- **compliance_refs:** ISO25010 Resource-Utilization

### perf_connection_pool — DB/HTTP clients pool connections
- **intent:** Opening a new DB/HTTP connection per request exhausts sockets and adds
  handshake latency.
- **applies_to:** web-api, fullstack, worker-service
- **signals:** `rg -n "connect\(|createConnection|new Client\(|requests\.get\("` inside
  per-request handlers; absence of pool config / module-level client.
- **confirm:** fail if a new connection/client is created per request instead of a shared
  pool/session. pass if pooled client or framework-managed pool is used.
- **severity:** Medium (prototype/internal → Low)
- **remediation:** Use a connection pool / persistent session created once at startup.
- **compliance_refs:** ISO25010 Resource-Utilization

### perf_indexes — Filtered/sorted/joined columns are indexed
- **intent:** Queries filtering/sorting on unindexed columns force full scans.
- **applies_to:** web-api, fullstack, data-ml
- **signals:** model fields used in `filter/order_by/where/join`; model defs lacking
  `db_index=True|index=True|Meta.indexes|@Index`.
- **confirm:** warning if a column used in filter/sort/join has no index declared. pass if
  indexed (or DB-managed).
- **severity:** Low (enterprise high-traffic → Medium)
- **remediation:** Add `db_index=True` / composite index on hot filter+sort columns.
- **compliance_refs:** ISO25010 Time-Behaviour

### perf_response_compression — Large API responses are compressed
- **intent:** Uncompressed large JSON responses waste bandwidth and raise latency.
- **applies_to:** web-api, fullstack
- **signals:** absence of `rg -n "gzip|brotli|compression|GZipMiddleware|compress\("` in
  app/middleware config for an API that returns large payloads.
- **confirm:** warning if no response compression configured and endpoints return large
  collections. pass if compression middleware present.
- **severity:** Low
- **remediation:** Enable gzip/brotli response compression at the app or proxy layer.
- **compliance_refs:** ISO25010 Resource-Utilization

---

## Capacity

### perf_bounded_inputs — Page size / upload / batch sizes are bounded
- **intent:** Unbounded request bodies, uploads, or batch sizes let one request exhaust
  memory/CPU → a capacity/DoS risk.
- **applies_to:** web-api, fullstack
- **signals:** `rg -n "page_size|limit|max_length|MAX_|body-parser|upload"`; absence of
  max caps on user-supplied sizes.
- **confirm:** fail if user-controlled page size / batch / upload has no enforced maximum.
  pass if caps present (request-body limit, max page size, max batch).
- **severity:** Medium (enterprise → High; overlaps security DoS)
- **remediation:** Enforce max page size, request-body size limits, and batch caps.
- **compliance_refs:** ISO25010 Capacity, OWASP API4:2023 (Unrestricted Resource Consumption)

---

## Frontend (static proxies — apply only to frontend archetypes)

### perf_fe_bundle — No oversized initial JS bundle / missing code-splitting
- **applies_to:** frontend-spa, fullstack
- **signals:** single large entry with no dynamic `import()`; heavy deps (`moment`,
  `lodash` full) in initial chunk; no route-level splitting.
- **confirm:** warning if no code-splitting/lazy routes and heavy deps loaded upfront.
- **severity:** Medium (prototype → Low)
- **remediation:** Route-based code splitting, dynamic imports, tree-shakeable deps.
- **compliance_refs:** ISO25010 Resource-Utilization (proxy for LCP/INP)

### perf_fe_render_blocking — No render-blocking scripts/CSS in head
- **applies_to:** frontend-spa
- **signals:** `rg -n "<script (?!.*(async|defer))[^>]*src"` in head; blocking `<link
  rel=stylesheet>` for non-critical CSS.
- **confirm:** warning if head scripts lack `async`/`defer` or non-critical CSS blocks render.
- **severity:** Low
- **remediation:** `defer`/`async` scripts; inline critical CSS, lazy-load the rest.
- **compliance_refs:** ISO25010 Time-Behaviour (proxy for LCP)

### perf_fe_images — Images lazy-loaded, sized, cacheable
- **applies_to:** frontend-spa
- **signals:** `<img>` without `loading="lazy"` (below fold) or without width/height;
  non-hashed static asset names.
- **confirm:** warning if below-fold images not lazy-loaded or missing explicit dimensions
  (CLS risk).
- **severity:** Low
- **remediation:** `loading="lazy"`, explicit width/height, modern formats, hashed caching.
- **compliance_refs:** ISO25010 Resource-Utilization (proxy for CLS)

### perf_fe_virtualization — Long lists virtualized
- **applies_to:** frontend-spa
- **signals:** `.map(` rendering large arrays into DOM with no windowing lib
  (`react-window|virtual|virtualized`).
- **confirm:** warning if potentially large lists render every item with no virtualization.
- **severity:** Low
- **remediation:** Virtualize/window long lists.
- **compliance_refs:** ISO25010 Time-Behaviour (proxy for INP)
