# Examples 10 — Container & IaC Security (load on demand only)

FAIL / PASS / false-positive guards. Read a section only when a candidate is ambiguous.
Only evaluate sub-groups whose artifacts exist (Dockerfile / K8s / Terraform).

---

## iac_container_nonroot

**FAIL — no USER (runs as root):**
```dockerfile
FROM python:3.12-slim
COPY . /app
CMD ["python", "app.py"]        # implicit root
```
**PASS — non-root runtime:**
```dockerfile
FROM python:3.12-slim
RUN useradd -m appuser
COPY . /app
USER appuser
CMD ["python", "app.py"]
```
**FALSE-POSITIVE — `USER root` in a BUILD stage** of a multi-stage build (installing deps),
where the FINAL stage switches to non-root: judge only the final runtime stage. Distroless
`nonroot` bases are already non-root.

---

## iac_image_secrets

**FAIL — secret baked into the image:**
```dockerfile
ENV AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG    # persists in image layer
COPY .env /app/.env
```
**PASS — injected at runtime / build secret mount:**
```dockerfile
RUN --mount=type=secret,id=npmrc npm ci           # not persisted in the layer
# runtime env supplied by the orchestrator, not baked in
```

---

## iac_k8s_security_context

**FAIL — privileged / root:**
```yaml
securityContext:
  privileged: true
  runAsUser: 0
```
**PASS — hardened:**
```yaml
securityContext:
  runAsNonRoot: true
  allowPrivilegeEscalation: false
  readOnlyRootFilesystem: true
  capabilities: { drop: ["ALL"] }
```

---

## iac_public_exposure

**FAIL — world-open sensitive port:**
```hcl
ingress {
  from_port = 22            # SSH
  cidr_blocks = ["0.0.0.0/0"]
}
```
**PASS — scoped:**
```hcl
ingress { from_port = 22  cidr_blocks = [var.bastion_cidr] }
```
**FALSE-POSITIVE — an intentionally public static-asset CDN bucket / a public web port (443)
behind a WAF:** verify intent; a public HTTPS app port is expected, a public SSH/DB port is
not.

---

## iac_iam_least_privilege

**FAIL — wildcard policy:**
```hcl
statement { actions = ["*"]  resources = ["*"] }     # god-mode
```
**PASS — scoped:**
```hcl
statement {
  actions   = ["s3:GetObject"]
  resources = ["arn:aws:s3:::my-bucket/*"]
}
```

---

## iac_iac_secrets

**FAIL — hardcoded credential in .tf:**
```hcl
resource "aws_db_instance" "db" {
  password = "SuperSecret123!"          # in code + state
}
```
**PASS — from a variable / secret manager:**
```hcl
resource "aws_db_instance" "db" {
  password = data.aws_secretsmanager_secret_version.db.secret_string
}
```
