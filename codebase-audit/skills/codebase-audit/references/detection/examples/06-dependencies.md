# Examples 06 — Dependencies & Supply Chain (load on demand only)

FAIL / PASS / false-positive guards. Read a section only when a candidate is ambiguous.
Always separate dev vs runtime dependencies.

---

## dep_known_cves

**FAIL — runtime dep with a critical CVE (osv-scanner):**
```
lodash@4.17.11  ->  CVE-2019-10744 (prototype pollution, Critical)   [runtime]
```
**PASS — patched:**
```
lodash@4.17.21   (no known advisories)
```
**FALSE-POSITIVE / lower severity — vuln only in a dev/build dependency not shipped to
production** (e.g. a test runner, a bundler plugin): drop one severity level; note it's
dev-only.

---

## dep_lockfile

**FAIL — no committed lockfile:**
```
package.json present, package-lock.json / yarn.lock ABSENT and not gitignored-by-mistake
CI runs:  npm install            # can drift / pull a fresh compromised patch
```
**PASS:**
```
package-lock.json committed;  CI runs:  npm ci   (frozen)
```
**FALSE-POSITIVE — a published LIBRARY** intentionally ships version ranges and no app
lockfile requirement: don't fail lockfile-required for a library artifact; a lockfile for its
own CI is still fine.

---

## dep_pinning

**FAIL — floating versions:**
```json
{ "dependencies": { "express": "*", "left-pad": "latest" } }
```
**PASS — bounded + lockfile:**
```json
{ "dependencies": { "express": "^4.19.2" } }   // with committed package-lock.json
```

---

## dep_source_integrity

**FAIL — raw git / http source:**
```json
{ "dependencies": { "acme": "git+http://random-host/acme.git" } }
```
**PASS — registry https, or git pinned to a commit:**
```json
{ "dependencies": { "acme": "git+https://github.com/org/acme.git#a1b2c3d" } }
```

---

## dep_git_secrets

**FAIL — secret in history (gitleaks):**
```
commit 9f2c... config.py:  AWS_SECRET = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
(even if a later commit removed it — still in history, still compromised)
```
**FALSE-POSITIVE — test fixture / documented example key** (`EXAMPLE`, `1234`, dummy in a
tests/ path): don't flag obvious non-secrets. Real, high-entropy, live-looking creds only.

---

## dep_license_compliance

**FAIL — copyleft in proprietary distribution:**
```
some-lib  ->  GPL-3.0     (project is closed-source commercial SaaS shipped to customers)
```
**FALSE-POSITIVE — permissive licenses flagged by a noisy scanner** (MIT/BSD/Apache-2.0 are
fine for almost all models); an AGPL dep used only as an internal, non-distributed tool is
lower risk. Judge against the project's actual distribution model.
