# Detection Spec 06 — Dependencies & Supply Chain

**ISO 25010:** Security
**Audit key:** `dependencies`
**OWASP:** A03:2025 (Software Supply Chain Failures) + SCVS.
**Static analysis only.** Heaviest external-tool consumer. Includes licensing/SBOM.

## How to use this spec (agent instructions)

1. Read `discovery_context`. If `manifest_files` is empty (no deps) → skip the whole
   dimension (all items `skipped`).
2. Prefer scanner output where noted: `osv-scanner`, `grype`, `npm audit --json`,
   `pip-audit`/`safety`, `gitleaks`, `trivy`. Fall back to manifest/lockfile parsing when a
   tool is absent.
3. Interpret tool output: dedupe, map CVE severity, judge licenses. Read manifests/lockfiles
   directly for pinning/lockfile/source checks.
4. Distinguish **dev vs runtime** deps — dev-only vulnerabilities are lower severity.
5. Assign `severity` with maturity modifiers. `dep_known_cves` + `dep_git_secrets` hold their
   floor.
6. Consult `examples/06-dependencies.md` only when ambiguous.
7. Emit `AuditResult` JSON per `shared/schema.json`. Score per `shared/scoring.md`.

---

## Known Vulnerabilities

### dep_known_cves — No dependencies with known CVEs
- **intent:** Dependencies with published CVEs (especially CISA KEV — exploited in the wild)
  are the most common breach vector.
- **applies_to:** any archetype with `manifest_files`
- **signals:** prefer `osv-scanner --json` / `grype -o json` / `npm audit --json` /
  `pip-audit -f json`. Map each advisory to a finding.
- **confirm:** fail per dependency with a known CVE reachable in the runtime dependency tree.
  KEV-listed / critical CVEs → High. Dev-only deps → one level lower.
- **severity:** High (floor:High for runtime critical/KEV; dev-only → Medium)
- **remediation:** Upgrade to a patched version; if none, replace or apply a mitigation.
- **compliance_refs:** OWASP A03:2025, CWE-1395, CWE-937

### dep_outdated_unmaintained — No majorly outdated / abandoned deps
- **intent:** Deps several majors behind or unmaintained (no releases in years, archived)
  accrue latent CVEs and block upgrades.
- **applies_to:** any archetype with `manifest_files`
- **signals:** manifest versions far behind latest; packages flagged archived/deprecated;
  `npm outdated` / `pip list --outdated`.
- **confirm:** warning if a runtime dependency is majors behind, EOL, deprecated, or
  unmaintained. pass if reasonably current.
- **severity:** Medium (prototype/internal → Low)
- **remediation:** Plan upgrades; replace abandoned packages.
- **compliance_refs:** OWASP A03:2025

---

## Integrity & Pinning

### dep_lockfile — Lockfile committed, CI uses frozen install
- **intent:** A committed lockfile guarantees reproducible, identical resolved versions
  everywhere; `npm install` (vs `npm ci`) can silently drift or pull a compromised update.
- **applies_to:** any archetype with `manifest_files`
- **signals:** absence of a committed lockfile
  (`package-lock.json|yarn.lock|pnpm-lock.yaml|poetry.lock|Pipfile.lock|uv.lock`);
  CI using `npm install`/`pip install` without frozen/`ci`.
- **confirm:** fail if no lockfile is committed for an app. warning if CI does non-frozen
  installs. pass if lockfile present + `npm ci`/`--frozen-lockfile`/`pip-sync`.
- **severity:** Medium (prototype → Low; library publishing a range → skip lockfile-required)
- **remediation:** Commit the lockfile; use `npm ci` / `--frozen-lockfile` / `pip-sync` in CI.
- **compliance_refs:** OWASP A03:2025, SCVS

### dep_pinning — Version constraints are bounded
- **intent:** Floating specifiers (`*`, `latest`, unbounded ranges) let a new (possibly
  malicious) release land without review.
- **applies_to:** any archetype with `manifest_files`
- **signals:** `"[^"]+":\s*"\*"|:\s*"latest"|>=?\s*[0-9]` without an upper bound on critical
  deps in the manifest.
- **confirm:** warning if runtime deps use `*`/`latest`/unbounded ranges. pass for pinned or
  bounded (`~`/`^` with a lockfile) constraints.
- **severity:** Medium (prototype → Low)
- **remediation:** Pin or bound versions; rely on the lockfile for exact resolution.
- **compliance_refs:** OWASP A03:2025, SCVS

### dep_source_integrity — Deps from trusted sources over https
- **intent:** Packages pulled from arbitrary git/http URLs or non-official registries bypass
  integrity checks and registry security.
- **applies_to:** any archetype with `manifest_files`
- **signals:** `git\+https?://|http://|file:|github:|"registry":\s*"http://"` deps;
  non-official/private registry without integrity.
- **confirm:** warning if runtime deps come from raw git/http/file sources without a pinned
  commit + integrity. pass for registry deps over https with lockfile hashes.
- **severity:** Medium (pinned git commit → Low)
- **remediation:** Use the official registry over https; pin git deps to a commit hash.
- **compliance_refs:** OWASP A03:2025

---

## Malicious-Package Surface

### dep_install_scripts — No hostile lifecycle scripts
- **intent:** `postinstall`/`preinstall` hooks (npm) and `setup.py` exec run arbitrary code
  at install — a repeated supply-chain attack vector.
- **applies_to:** js/ts, python (setup.py)
- **signals:** `"(pre|post)install":` in package.json (own or noted for deps);
  network/shell in `setup.py`; obfuscated install scripts.
- **confirm:** warning if the project or a dependency runs non-obvious code in an install
  hook. Escalate if it does network/shell/obfuscated work. pass if none / benign.
- **severity:** Medium (obfuscated/network → High)
- **remediation:** Audit install scripts; use `--ignore-scripts` where feasible; vet deps.
- **compliance_refs:** OWASP A03:2025, CWE-506

### dep_typosquat — No suspicious / low-trust packages
- **intent:** Typosquatted or newly-published low-trust packages impersonate popular ones to
  inject malware.
- **applies_to:** js/ts, python
- **signals:** package names one edit-distance from popular packages
  (`reqeusts`, `loadsh`, `expresss`); very new / near-zero-download deps; unscoped clones of
  scoped packages.
- **confirm:** warning if a dependency name looks like a typosquat of a well-known package or
  is an untrusted lookalike. pass otherwise. (Heuristic — flag for human review, don't hard
  fail.)
- **severity:** Low (clear typosquat of a critical dep → Medium)
- **remediation:** Verify the intended package name/publisher; remove impostors.
- **compliance_refs:** OWASP A03:2025, CWE-1357

---

## Secrets in History

### dep_git_secrets — No secrets in git history
- **intent:** A secret committed then "removed" still lives in git history and is compromised.
  (Distinct from dim 2, which scans current source.)
- **applies_to:** any git repository
- **signals:** prefer `gitleaks detect --report-format json`. Fallback:
  `git log -p` scan for key/token patterns in historical diffs.
- **confirm:** fail per real secret found anywhere in git history (not a placeholder/test
  fixture). pass if history is clean.
- **severity:** High (floor:High)
- **remediation:** Rotate the exposed secret immediately; purge history
  (`git filter-repo`/BFG); move to a secret manager.
- **compliance_refs:** OWASP A03:2025 / A04:2025, CWE-798

---

## Licensing & Inventory

### dep_license_compliance — No license conflicts
- **intent:** Strong-copyleft (GPL/AGPL) deps in proprietary/closed distribution, or
  missing/unknown/changed licenses, create legal + supply-chain risk.
- **applies_to:** any archetype with `manifest_files`
- **signals:** dependency licenses (from SBOM / `license-checker` / `pip-licenses`) that are
  GPL/AGPL/unknown/none, or a license change vs a prior audit.
- **confirm:** warning if a dependency's license conflicts with the project's distribution
  model, is missing, or is unknown. pass if all licenses are known + compatible.
- **severity:** Medium (internal-only tool → Low; commercial distribution → hold Medium)
- **remediation:** Replace incompatible-license deps; record allowed licenses in policy.
- **compliance_refs:** OWASP A03:2025 (license integrity), SCVS

### dep_sbom — Dependency inventory / SBOM available
- **intent:** An SBOM (CycloneDX/SPDX) lets you instantly answer "are we affected by CVE-X".
  Advisory — expected at enterprise maturity.
- **applies_to:** enterprise / production maturity with `manifest_files`
- **signals:** absence of any SBOM artifact / generation step
  (`cyclonedx|spdx|syft|sbom` in CI).
- **confirm:** info (Low at enterprise) if no SBOM is generated. skip for
  prototype/small apps.
- **severity:** Info (enterprise → Low)
- **remediation:** Generate an SBOM in CI (Syft/CycloneDX); store with build artifacts.
- **compliance_refs:** OWASP SCVS, A03:2025

---

## Cross-references (scored elsewhere — do NOT emit here)

- Secrets in **current source** (not history) → dim 2 (security).
- Container **base-image** CVEs / OS packages → dim 10 (container & IaC, trivy on image).
- Insecure use of a dependency in app code (e.g. calling it unsafely) → dim 2.
