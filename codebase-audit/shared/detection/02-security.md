# Detection Spec 02 — Security

**ISO 25010:** Security
**Audit key:** `security`
**OWASP:** mapped to Top 10:2025 categories (refs per item).
**Static analysis only.** Confirm data-flow by reading candidate snippets; do not assume
Django/Express — reason about the actual framework.

## How to use this spec (agent instructions)

1. Read `discovery_context`. Skip items whose `applies_to` shares no archetype → `skipped`.
2. Run each item's `signals` (ripgrep) → candidate `file:line` list. Prefer external-tool
   output where noted (bandit, semgrep, gitleaks).
3. Read ONLY candidate snippets. Trace whether the value is user-controlled (request params,
   body, headers, path) before confirming. Apply `confirm`.
4. Assign `severity` with maturity modifiers. **Core-vuln items have a High floor** — do NOT
   downgrade them below High regardless of maturity (marked "floor:High").
5. Consult `examples/02-security.md` only when a candidate is ambiguous.
6. Emit `AuditResult` JSON per `shared/schema.json`. Score per `shared/scoring.md`.

`signals` locate candidates; `confirm` (with taint reasoning) is the decision.

---

## A01 — Broken Access Control

### sec_access_control — Auth guard on sensitive routes
- **intent:** Sensitive/non-public endpoints must require authentication, or anyone can
  reach them.
- **applies_to:** web-api, fullstack, worker-service
- **signals:** route/view/controller defs (`@app.route`, `@router.`, `path(`, `def .*view`,
  `app.(get|post|put|delete)`) NOT preceded/decorated by
  `login_required|permission_classes|IsAuthenticated|requireAuth|authenticate|verifyToken|@Auth`.
  Focus on paths like `/admin|/user|/account|/order|/payment|/api`.
- **confirm:** fail if a state-changing or sensitive-data route has no auth
  decorator/middleware in its signature or the ~5 lines above, and isn't an explicitly public
  route (login, health, docs, static).
- **severity:** High (floor:High)
- **remediation:** Add auth middleware/decorator; default-deny, allowlist public routes.
- **compliance_refs:** OWASP A01:2025, CWE-862

### sec_authorization — Function/object-level authorization
- **intent:** Authenticated ≠ authorized. Missing per-object/per-role checks → IDOR/BOLA
  (user reads another user's record by changing an ID).
- **applies_to:** web-api, fullstack
- **signals:** handlers fetching by user-supplied id (`objects.get(pk=|findById(req.params`)
  with no ownership/role check (`request.user ==|is_staff|is_superuser|role|owner|IsAdminUser|
  can(`).
- **confirm:** fail if a record is fetched by client-supplied id and returned/mutated with no
  ownership or role check. warning if only route-level auth exists for admin actions.
- **severity:** High (floor:High)
- **remediation:** Enforce object ownership + role checks server-side on every access.
- **compliance_refs:** OWASP A01:2025, CWE-639, CWE-285

### sec_ssrf — No server-side request forgery
- **intent:** Fetching a user-supplied URL server-side lets attackers reach internal
  services / cloud metadata.
- **applies_to:** web-api, fullstack, worker-service
- **signals:** `requests.(get|post)\(|urlopen\(|fetch\(|axios\.|httpx\.` where the URL arg
  derives from `request.|req.(query|body|params)|input`.
- **confirm:** fail if a server-side HTTP/file fetch uses a user-controlled URL with no
  allowlist/scheme+host validation. pass if validated against an allowlist.
- **severity:** High (floor:High)
- **remediation:** Allowlist hosts/schemes; block private/link-local ranges; no raw user URL.
- **compliance_refs:** OWASP A01:2025 (SSRF), CWE-918

### sec_path_traversal — No user input in filesystem paths
- **intent:** User input in file paths enables `../` traversal to read/write arbitrary files.
- **applies_to:** web-api, fullstack, cli-tool, worker-service
- **signals:** `open\(|os\.path\.join\(|Path\(|readFile\(|sendFile\(|send_file\(` with a
  request-derived component.
- **confirm:** fail if a filesystem path is built from user input without normalization +
  containment check (resolve + verify inside base dir). pass if sanitized/allowlisted.
- **severity:** High (floor:High)
- **remediation:** Resolve realpath and assert it stays within an allowed base directory.
- **compliance_refs:** OWASP A01:2025, CWE-22

### sec_cors — No permissive CORS
- **intent:** `Access-Control-Allow-Origin: *` combined with credentials exposes
  authenticated data cross-origin.
- **applies_to:** web-api, fullstack
- **signals:** `CORS_ALLOW_ALL_ORIGINS\s*=\s*True|Access-Control-Allow-Origin.*\*|
  origin:\s*['\"]\*['\"]|cors\(\)` with credentials enabled.
- **confirm:** fail if wildcard origin is combined with credentials/cookies. warning if
  wildcard on an authenticated API. pass if explicit origin allowlist.
- **severity:** Medium (prototype/internal → Low)
- **remediation:** Set an explicit origin allowlist; never wildcard with credentials.
- **compliance_refs:** OWASP A01:2025, CWE-942

---

## A02 — Security Misconfiguration

### sec_misconfig — No dangerous configuration
- **intent:** Debug mode, default/example credentials, and verbose errors in production leak
  internals and grant access.
- **applies_to:** web-api, fullstack, worker-service, cli-tool
- **signals:** `DEBUG\s*=\s*True|SECRET_KEY\s*=\s*['\"](dev|changeme|secret|test)|
  password\s*=\s*['\"](admin|password|changeme)|NODE_ENV.*development` not gated on env var.
- **confirm:** fail if debug/default-creds/insecure defaults are hardcoded and not
  environment-gated. pass if driven by env with secure defaults.
- **severity:** High (floor:High for default creds; DEBUG → High, prototype → Medium)
- **remediation:** Drive config from env; secure production defaults; no default creds.
- **compliance_refs:** OWASP A02:2025, CWE-16, CWE-1188

### sec_security_headers — Security response headers present
- **intent:** Missing CSP/HSTS/X-Frame-Options/X-Content-Type-Options leaves clients open to
  clickjacking, MIME sniffing, protocol downgrade.
- **applies_to:** web-api, fullstack
- **signals:** absence of `Content-Security-Policy|Strict-Transport-Security|X-Frame-Options|
  X-Content-Type-Options|helmet\(|SecurityMiddleware` in app/middleware config.
- **confirm:** warning if a browser-facing app sets no security headers / helmet.
- **severity:** Low (enterprise public app → Medium)
- **remediation:** Add a security-headers middleware (helmet / SecurityMiddleware / CSP).
- **compliance_refs:** OWASP A02:2025, CWE-693

### sec_error_leakage — No sensitive info in error responses
- **intent:** Returning stack traces / SQL / secrets in error responses aids attackers.
  (Also OWASP A10 — mishandling exceptional conditions.)
- **applies_to:** web-api, fullstack
- **signals:** `traceback|str(e)|e.message|.stack` written into HTTP response bodies;
  framework debug error pages enabled in prod.
- **confirm:** fail if raw exception/stack detail is returned to clients. pass if generic
  error + server-side logging.
- **severity:** Medium (prototype/internal → Low)
- **remediation:** Return generic error messages; log details server-side only.
- **compliance_refs:** OWASP A02:2025 / A10:2025, CWE-209

---

## A04 — Cryptographic Failures

### sec_weak_crypto — No weak cryptography on secrets
- **intent:** MD5/SHA1/DES/RC4 and fast unsalted hashes are broken for passwords/tokens.
- **applies_to:** all archetypes
- **signals:** `hashlib\.(md5|sha1)\(|MD5|SHA1|DES|RC4|createHash\(['\"](md5|sha1)` in
  security context (password/token/secret nearby).
- **confirm:** fail if a weak algorithm hashes/encrypts a secret, or passwords stored with a
  fast/unsalted hash. pass for bcrypt/argon2/scrypt/PBKDF2 + AES-GCM.
- **severity:** High (floor:High)
- **remediation:** Use argon2/bcrypt/scrypt for passwords; AES-GCM for encryption.
- **compliance_refs:** OWASP A04:2025, CWE-327, CWE-916

### sec_hardcoded_secrets — No secrets in source
- **intent:** API keys/tokens/passwords committed in source are compromised the moment they
  are pushed.
- **applies_to:** all archetypes
- **signals:** high-entropy strings assigned to `key|secret|token|password|api_key`;
  `AKIA[0-9A-Z]{16}|-----BEGIN .*PRIVATE KEY-----|sk_live_|ghp_`. Prefer gitleaks output.
- **confirm:** fail if a real secret literal is present in source (not a placeholder/env
  read). pass for `os.environ|process.env|vault|secret manager` references.
- **severity:** High (floor:High)
- **remediation:** Move to env/secret manager; rotate the exposed secret. (Git-history
  exposure is scored in dim6.)
- **compliance_refs:** OWASP A04:2025, CWE-798

### sec_tls_verification — Transport security not disabled
- **intent:** Disabling cert verification or using plaintext transport enables MITM.
- **applies_to:** web-api, fullstack, worker-service, cli-tool
- **signals:** `verify\s*=\s*False|rejectUnauthorized:\s*false|CURLOPT_SSL_VERIFYPEER.*0|
  ssl._create_unverified|http://` for sensitive endpoints.
- **confirm:** fail if TLS verification is disabled or credentials/PII sent over plaintext
  http. pass for verified https.
- **severity:** High (internal-only non-sensitive → Medium)
- **remediation:** Enable cert verification; use https everywhere for sensitive data.
- **compliance_refs:** OWASP A04:2025, CWE-295

---

## A05 — Injection

### sec_injection — No injection vulnerabilities
- **intent:** Untrusted input concatenated into SQL/NoSQL/shell/template/LDAP lets attackers
  execute arbitrary commands/queries.
- **applies_to:** all archetypes
- **signals:** `execute\(f['\"]|execute\(['\"].*%|cursor\.execute\(.*\+|os\.system\(|
  subprocess\..*shell=True|eval\(|render_template_string\(|\.raw\(`; JS template-literal SQL.
- **confirm:** fail if user input reaches an interpreter/query without parameterization or
  safe API. pass for parameterized queries / ORM binding / `shell=False` with arg list.
- **severity:** High (floor:High)
- **remediation:** Parameterized queries / prepared statements; avoid shell; no eval on input.
- **compliance_refs:** OWASP A05:2025, CWE-89, CWE-78, CWE-94

### sec_xss — No cross-site scripting
- **intent:** Rendering unescaped user input into HTML/DOM executes attacker scripts.
- **applies_to:** web-api, fullstack, frontend-spa
- **signals:** `mark_safe\(|\|safe|dangerouslySetInnerHTML|\.innerHTML\s*=|
  render_template_string\(|v-html` fed by user input; autoescape disabled.
- **confirm:** fail if user-controlled data is written to HTML/DOM without escaping/sanitize.
  pass for escaped template output / sanitizer (DOMPurify).
- **severity:** High (floor:High)
- **remediation:** Escape by default; sanitize any raw HTML; avoid `innerHTML`/`v-html` on
  user data.
- **compliance_refs:** OWASP A05:2025, CWE-79

---

## A07 — Authentication Failures

### sec_auth_hardening — Auth endpoints hardened
- **intent:** Login/register/reset without rate-limiting enable brute force; weak JWT config
  (no `exp`, `alg=none`, weak secret) enables token forgery/replay.
- **applies_to:** web-api, fullstack
- **signals:** auth routes (`login|signin|register|password.?reset|token`) with no
  `ratelimit|throttle|limiter`; `jwt.encode\(` with no `exp`; `algorithm.*none`; `exp` > 24h
  for access tokens; weak/hardcoded JWT secret.
- **confirm:** fail if auth endpoints lack rate limiting OR JWTs lack `exp`/use `alg=none`/
  use a weak secret. warning for over-long token lifetimes / weak password policy.
- **severity:** High (floor:High)
- **remediation:** Rate-limit auth routes; JWT with short `exp`, strong secret, fixed alg;
  enforce password policy + lockout.
- **compliance_refs:** OWASP A07:2025, CWE-307, CWE-347, CWE-521

---

## A08 — Software / Data Integrity Failures

### sec_deserialization — No unsafe deserialization
- **intent:** Deserializing untrusted data with `pickle`/`yaml.load`/`eval` yields remote
  code execution.
- **applies_to:** all archetypes
- **signals:** `pickle\.loads\(|yaml\.load\((?!.*SafeLoader)|marshal\.loads\(|eval\(|
  cPickle|unserialize\(` fed by request/file/network data.
- **confirm:** fail if untrusted data is deserialized via an unsafe API. pass for
  `yaml.safe_load`, `json.loads`, schema-validated parsing.
- **severity:** High (floor:High)
- **remediation:** Use `yaml.safe_load`/JSON with schema validation; never unpickle untrusted
  data.
- **compliance_refs:** OWASP A08:2025, CWE-502

---

## Cross-references (scored in other dimensions — do NOT emit here)

- Vulnerable/outdated dependencies, CVEs, SBOM, secrets in **git history** → dim 6 (dependencies).
- Security logging & alerting failures (OWASP A09) → dim 11 (observability).
- Mishandling exceptional conditions (OWASP A10) broadly → dim 9 (resilience); the
  response-leakage slice is `sec_error_leakage` above.
- PII handling / encryption-at-rest / GDPR → deferred (v2); PII-in-logs → dim 11.
