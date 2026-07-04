# Detection Spec 08 — API Design Quality

**ISO 25010:** Compatibility (Interoperability)
**Audit key:** `api`
**Static analysis only.** Applies only to services that expose an API.

## How to use this spec (agent instructions)

1. Read `discovery_context`. If no archetype in {web-api, fullstack} and no API surface is
   found → skip the whole dimension (all items `skipped`).
2. **Detect the API paradigm first**: REST, GraphQL, or gRPC. Adapt every item:
   - REST → URL/header versioning, HTTP status codes, verbs.
   - GraphQL → single endpoint, schema deprecation (not URL versioning), `errors[]` array is
     correct, HTTP 200 with error payload is normal.
   - gRPC → proto contracts, gRPC status codes, backward-compatible proto evolution.
3. Locate route/schema definitions, read them, apply `confirm`.
4. Assign `severity` with maturity modifiers. status-codes/error-format/idempotency hold.
5. Consult `examples/08-api.md` only when ambiguous.
6. Emit `AuditResult` JSON per `shared/schema.json`. Score per `shared/scoring.md`.

---

## Contract & Versioning

### api_versioning — API is versioned
- **intent:** Without versioning, any change risks breaking existing clients.
- **applies_to:** web-api, fullstack
- **signals:** routes lacking a version segment (`/v1|/v2|/api/v`) or version header/media
  type; GraphQL without a deprecation strategy; proto without package versioning.
- **confirm:** warning if a public/external API has no versioning strategy. skip/Info for
  a purely internal service where clients deploy in lockstep.
- **severity:** Medium (internal lockstep → Low)
- **remediation:** Version via URL path or header (REST); schema deprecation (GraphQL);
  versioned proto packages (gRPC).
- **compliance_refs:** ISO25010 Compatibility (Replaceability)

### api_backward_compat — Responses are extensibility-safe
- **intent:** Returning a bare top-level array, or removing/renaming fields, breaks clients on
  the next change. Top-level objects extend safely.
- **applies_to:** web-api, fullstack
- **signals:** handlers returning a bare JSON array as the top-level body; field
  removals/renames vs a prior schema; response shape varying by branch.
- **confirm:** warning if responses use a bare top-level array (no envelope) or make
  non-additive changes without a version bump. pass for extensible object envelopes.
- **severity:** Medium (prototype → Low)
- **remediation:** Wrap collections in an object (`{ "data": [...], "meta": {...} }`); make
  only additive changes within a version.
- **compliance_refs:** ISO25010 Compatibility

### api_contract_docs — Machine-readable contract exists
- **intent:** An OpenAPI/GraphQL-schema/proto contract is the single source of truth for
  clients, docs, and SDKs.
- **applies_to:** web-api, fullstack
- **signals:** absence of `openapi|swagger|*.proto|schema.graphql` or a framework schema
  generator.
- **confirm:** warning if a public API ships no machine-readable contract. pass if present
  (hand-written or generated).
- **severity:** Low (enterprise/public API → Medium)
- **remediation:** Publish an OpenAPI/GraphQL/proto contract; keep it in sync with code.
- **compliance_refs:** ISO25010 Interoperability

---

## HTTP / Protocol Semantics

### api_status_codes — Correct status codes
- **intent:** Returning 200 for errors, creations, and empties defeats HTTP semantics and
  confuses clients and caches.
- **applies_to:** web-api, fullstack
- **signals:** create endpoints returning 200 not 201; errors returned as `200` with an
  error body; missing `204` for empty; `500` for validation (should be 400/422); no `429`
  for rate limits.
- **confirm:** fail if error/success semantics are wrong (e.g. errors returned as 200).
  warning for suboptimal-but-not-wrong codes. (GraphQL: 200 + `errors[]` is correct — don't
  flag.)
- **severity:** Medium (holds — contract correctness; prototype → Low)
- **remediation:** Map outcomes to correct codes (201/204/400/401/403/404/409/422/429/5xx).
- **compliance_refs:** ISO25010 Interoperability

### api_http_methods — Correct verb semantics
- **intent:** GET must be safe (no side effects); PUT idempotent; POST creates; DELETE
  removes. Misuse breaks caching, retries, and client expectations.
- **applies_to:** web-api, fullstack
- **signals:** state mutation inside `GET` handlers; `POST` used for reads; `GET` endpoints
  named `/create|/update|/delete`.
- **confirm:** fail if a GET has side effects or verbs are semantically misused. pass for
  correct verb usage.
- **severity:** Medium (prototype → Low)
- **remediation:** Use verbs per semantics; no side effects on GET.
- **compliance_refs:** ISO25010 Interoperability

### api_idempotency — Idempotent writes where required
- **intent:** PUT/DELETE must be idempotent; unprotected POST for critical ops
  (payments/orders) double-charges on client retry. (Contract-level; retry mechanics → dim9.)
- **applies_to:** web-api, fullstack
- **signals:** PUT handlers that behave non-idempotently (append/increment); critical POST
  endpoints with no `Idempotency-Key`/dedup.
- **confirm:** warning if PUT is non-idempotent or a critical create lacks idempotency
  protection. pass otherwise.
- **severity:** Medium (holds for payment/order ops; low-risk → Low)
- **remediation:** Make PUT idempotent; accept an `Idempotency-Key` for retry-safe POST.
- **compliance_refs:** ISO25010 Interoperability; RFC 7231

---

## Consistency & Structure

### api_error_format — Consistent structured errors
- **intent:** Inconsistent or raw error bodies (plain strings, HTML, varying shapes) make
  robust client handling impossible.
- **applies_to:** web-api, fullstack
- **signals:** error responses as bare strings/HTML; different error shapes across endpoints;
  no machine-readable error code.
- **confirm:** warning if error responses lack a consistent structured shape
  (code + message [+ details]). pass for a uniform error envelope (e.g. RFC 9457
  problem+json).
- **severity:** Medium (prototype → Low)
- **remediation:** Adopt one error schema (code, message, details); apply everywhere.
- **compliance_refs:** ISO25010 Interoperability; RFC 9457

### api_pagination_consistency — Consistent pagination contract
- **intent:** List endpoints should share one pagination scheme + metadata so clients page
  uniformly. (Shape/contract here; unbounded-query performance → dim1.)
- **applies_to:** web-api, fullstack
- **signals:** list endpoints with mixed/ad-hoc paging params
  (`page` here, `offset` there, none elsewhere); no total/next metadata.
- **confirm:** warning if pagination params/response metadata are inconsistent across list
  endpoints. pass for a uniform scheme (cursor or offset) with metadata.
- **severity:** Low
- **remediation:** Standardize one pagination scheme + metadata envelope across endpoints.
- **compliance_refs:** ISO25010 Interoperability

### api_naming_consistency — Consistent naming
- **intent:** Mixed resource naming and field casing (`snake_case` vs `camelCase`) raise
  client integration cost.
- **applies_to:** web-api, fullstack
- **signals:** singular vs plural resource paths mixed; verb-y resource paths; response field
  casing inconsistent across endpoints.
- **confirm:** warning if resource naming or field casing is inconsistent across the API.
  pass if consistent.
- **severity:** Low
- **remediation:** Use plural nouns for collections; one field-casing convention everywhere.
- **compliance_refs:** ISO25010 Interoperability

### api_deprecation — Deprecations are signaled
- **intent:** Removing endpoints without a deprecation signal breaks clients abruptly.
- **applies_to:** web-api, fullstack
- **signals:** removed/renamed endpoints vs docs with no `Deprecation`/`Sunset` header or
  documented notice; GraphQL fields removed without `@deprecated`.
- **confirm:** info if there is no deprecation-signaling mechanism for a public API.
- **severity:** Info (enterprise/public → Low)
- **remediation:** Signal deprecations (`Deprecation`/`Sunset` headers, `@deprecated`, docs +
  migration path).
- **compliance_refs:** ISO25010 Compatibility (Replaceability)

---

## Cross-references (scored elsewhere — do NOT emit here)

- Unbounded queries / pagination performance → dim 1.
- Auth on endpoints, rate limiting → dim 2 (security).
- Retries, timeouts, circuit breakers, retry mechanics → dim 9 (resilience).
- Response compression → dim 1.
