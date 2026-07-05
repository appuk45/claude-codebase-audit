# Detection Spec 10 — Container & IaC Security

**ISO 25010:** Portability (Installability) — security-flavored infrastructure hardening
**Audit key:** `container_iac`
**Static analysis only.** Runs only when infrastructure-as-code exists.

## How to use this spec (agent instructions)

1. Read `discovery_context`. If `has_iac == false` → skip the whole dimension.
2. Run only the sub-groups whose artifacts exist:
   - `has_docker` → Dockerfile items.
   - `has_k8s` → Kubernetes items.
   - `has_terraform` → Terraform/cloud items.
   Emit items for absent sub-groups as `skipped`.
3. Prefer scanner output: `trivy config` / `checkov -d .` / `hadolint` (Dockerfile) /
   `tfsec`. Interpret + dedupe. Fallback: parse Dockerfile/manifests/`.tf` directly.
4. Apply `confirm`. Assign `severity`. **Security items do NOT relax with maturity** — hold
   their level; only hardening/probes/logging drop at prototype.
5. Consult `examples/10-container-iac.md` only when ambiguous.
6. Emit `AuditResult` JSON per `shared/schema.json`. Score per `shared/scoring.md`.

---

## Dockerfile (has_docker)

### iac_container_nonroot — Container runs as non-root
- **intent:** A container running as root escalates the blast radius of any escape or app
  compromise to host-level.
- **applies_to:** has_docker
- **signals:** Dockerfile with no `USER` directive (defaults to root); `USER root` as the
  final user; running the app process as uid 0.
- **confirm:** fail if the final runtime stage runs as root (no non-root `USER`). pass if it
  switches to a non-root user (or uses a distroless/rootless base).
- **severity:** High (holds)
- **remediation:** Create + `USER` a non-root user for the runtime stage; set
  `runAsNonRoot`.
- **compliance_refs:** CIS Docker 4.1, CWE-250

### iac_base_image_pinning — Base image pinned & minimal
- **intent:** `latest` (or a floating tag) makes builds non-reproducible and can pull a
  compromised image; fat bases enlarge the attack surface.
- **applies_to:** has_docker
- **signals:** `FROM .*:latest|FROM [^@:]+$` (no tag); no digest pin; heavyweight base where a
  slim/distroless would do.
- **confirm:** warning if the base image is unpinned/`latest` or unnecessarily large. pass for
  a pinned (tag or `@sha256`) minimal base.
- **severity:** Medium (prototype → Low)
- **remediation:** Pin base by version + digest; use slim/distroless.
- **compliance_refs:** CIS Docker 4.2

### iac_image_secrets — No secrets baked into the image
- **intent:** Secrets in `ENV`, build args, or copied files persist in image layers and leak
  to anyone who pulls the image.
- **applies_to:** has_docker
- **signals:** `ENV .*(SECRET|TOKEN|PASSWORD|KEY)=|ARG .*(SECRET|KEY)|
  COPY .*\.env|ADD .*(id_rsa|\.pem)`.
- **confirm:** fail if a secret is set via ENV/ARG or a secret file is copied into the image.
  pass if secrets are injected at runtime (mounted/env at deploy) and build secrets use
  `--mount=type=secret`.
- **severity:** High (holds)
- **remediation:** Inject secrets at runtime; use BuildKit secret mounts; never bake secrets.
- **compliance_refs:** CIS Docker 4.10, CWE-798

### iac_image_hardening — Image is hardened
- **intent:** Multi-stage builds, minimal packages, a healthcheck, and no `curl | bash`
  reduce attack surface and improve operability.
- **applies_to:** has_docker
- **signals:** single-stage build shipping build tools; `RUN .*curl.*\| ?(ba)?sh`;
  `apt-get install` without cleanup; no `HEALTHCHECK`; running as PID 1 without an init.
- **confirm:** warning for missing multi-stage/minimization, `curl | bash`, or no healthcheck.
  pass if hardened.
- **severity:** Low (enterprise → Medium)
- **remediation:** Multi-stage build; install only runtime deps; add HEALTHCHECK; avoid
  piping remote scripts to a shell.
- **compliance_refs:** CIS Docker 4.x

---

## Kubernetes (has_k8s)

### iac_k8s_security_context — Hardened securityContext
- **intent:** Without a restrictive securityContext, pods can run privileged, as root, with
  writable root FS and full capabilities — trivially exploitable.
- **applies_to:** has_k8s
- **signals:** `privileged:\s*true|allowPrivilegeEscalation:\s*true`; missing
  `runAsNonRoot:\s*true`; no `readOnlyRootFilesystem`; capabilities not dropped;
  `hostNetwork|hostPID|hostPath` misuse.
- **confirm:** fail for `privileged: true`, root, or privilege escalation allowed. warning for
  missing readOnlyRootFilesystem / capability drop. pass if hardened.
- **severity:** High (holds)
- **remediation:** Set `runAsNonRoot`, `allowPrivilegeEscalation: false`,
  `readOnlyRootFilesystem: true`, `drop: [ALL]` capabilities.
- **compliance_refs:** CIS Kubernetes 5.2, CWE-250

### iac_k8s_resource_limits — Requests & limits set
- **intent:** No CPU/memory limits lets one pod starve the node (noisy neighbor / resource
  DoS).
- **applies_to:** has_k8s
- **signals:** container specs with no `resources.requests`/`resources.limits`.
- **confirm:** warning if CPU/memory requests + limits are unset. pass if both defined.
- **severity:** Medium (prototype → Low)
- **remediation:** Set resource requests + limits per container.
- **compliance_refs:** CIS Kubernetes 5.x

### iac_k8s_probes — Liveness/readiness probes wired
- **intent:** Without probes, K8s can't restart hung pods or gate traffic to unready ones.
  (App endpoint existence is dim 3; here = the manifest wiring.)
- **applies_to:** has_k8s
- **signals:** Deployment/Pod specs with no `livenessProbe`/`readinessProbe`.
- **confirm:** warning if probes are not configured in the manifest. pass if wired.
- **severity:** Low (prototype → Info)
- **remediation:** Add liveness + readiness probes pointing at the app's health endpoints.
- **compliance_refs:** CIS Kubernetes 5.x; ISO25010 Reliability

---

## Terraform / Cloud IaC (has_terraform)

### iac_public_exposure — No unintended public exposure
- **intent:** World-open ingress and public storage/DB are the most common cloud breach cause.
- **applies_to:** has_terraform
- **signals:** `cidr_blocks\s*=\s*\["0\.0\.0\.0/0"\]` on sensitive ports; `acl\s*=\s*
  "public-read"`; `publicly_accessible\s*=\s*true`; public S3/bucket policies.
- **confirm:** fail if a sensitive resource (admin/SSH/DB port, storage bucket) is exposed to
  `0.0.0.0/0` / public without justification. pass if scoped. (An intentionally public CDN
  bucket for static assets is fine — verify intent.)
- **severity:** High (holds)
- **remediation:** Restrict CIDRs to known ranges; make storage private; front public assets
  with a CDN/bucket policy scoped to reads.
- **compliance_refs:** CIS AWS/Cloud, CWE-284

### iac_iam_least_privilege — Least-privilege IAM
- **intent:** Wildcard permissions grant far more than needed; a compromised principal then
  owns everything.
- **applies_to:** has_terraform
- **signals:** `"Action":\s*"\*"|"Resource":\s*"\*"|Effect.*Allow.*\*`; `*FullAccess`
  managed policies attached broadly.
- **confirm:** fail if IAM policies use wildcard action/resource where scoping is feasible.
  warning for broad managed policies. pass for scoped least-privilege.
- **severity:** High (holds)
- **remediation:** Scope actions + resources to the minimum required; avoid `*`.
- **compliance_refs:** CIS AWS IAM, CWE-269

### iac_encryption — Encryption at rest & in transit
- **intent:** Unencrypted volumes/storage/DB expose data on disk/snapshot theft; plaintext
  transport exposes it in flight.
- **applies_to:** has_terraform
- **signals:** storage/volume/DB resources with `encrypted\s*=\s*false` or no encryption
  config; load balancers/endpoints allowing plaintext.
- **confirm:** warning if data-at-rest encryption is disabled/absent or transport allows
  plaintext for sensitive resources. pass if encrypted.
- **severity:** Medium (regulated/enterprise → High)
- **remediation:** Enable encryption at rest (KMS) + enforce TLS in transit.
- **compliance_refs:** CIS Cloud, CWE-311

### iac_iac_secrets — No secrets in IaC or state
- **intent:** Hardcoded credentials in `.tf` files or unencrypted remote state leak secrets to
  anyone with repo/state access.
- **applies_to:** has_terraform
- **signals:** `password\s*=\s*"|secret\s*=\s*"|access_key\s*=\s*"` literals in `.tf`;
  local/unencrypted backend state.
- **confirm:** fail for hardcoded secrets in IaC. warning for unencrypted remote state. pass
  if secrets come from a secret manager/variables and state is encrypted.
- **severity:** High (holds)
- **remediation:** Use a secret manager / sensitive variables; encrypt remote state.
- **compliance_refs:** CIS Cloud, CWE-798

### iac_cloud_logging — Audit logging enabled
- **intent:** Without audit/flow/access logs, incidents can't be detected or investigated.
- **applies_to:** has_terraform
- **signals:** absence of CloudTrail/audit-log/flow-log/bucket-logging resources for
  key services.
- **confirm:** warning if audit/flow/access logging is not enabled for key resources. pass if
  configured.
- **severity:** Low (enterprise/regulated → Medium)
- **remediation:** Enable CloudTrail/flow logs/access logging; ship to a retained store.
- **compliance_refs:** CIS Cloud; OWASP A09:2025 (adjacent)

---

## Cross-references (scored elsewhere — do NOT emit here)

- Application dependency CVEs + base-image package CVEs → dim 6 (trivy image/deps mode).
- Secrets in application source → dim 2; secrets in git history → dim 6.
- App health-endpoint existence → dim 3 (here = K8s probe wiring only).
- CI/CD pipeline security (workflow perms, pinned actions) → dim 6 (supply chain).
