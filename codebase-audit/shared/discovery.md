# Discovery — stack detection + archetype classification

Run these commands against the current working directory and assemble a
`discovery_context` JSON object. If a command yields nothing, record an empty
array / false. Do not skip commands.

## Commands

```bash
# Language counts
find . -name "*.py"  | grep -vE "__pycache__|\.venv" | wc -l
find . \( -name "*.ts" -o -name "*.tsx" \) | grep -v node_modules | wc -l
find . -name "*.js"  | grep -vE "node_modules|dist" | wc -l

# Framework hints
grep -rlE "from django|import django" . --include="*.py" 2>/dev/null | head -3
grep -rl "from fastapi" . --include="*.py" 2>/dev/null | head -3
grep -rl "from flask" . --include="*.py" 2>/dev/null | head -3
cat package.json 2>/dev/null

# IaC
find . \( -name "Dockerfile" -o -name "docker-compose*.y*ml" \) 2>/dev/null
find . -name "*.tf" 2>/dev/null | head -5
find . \( -path "*/k8s/*.y*ml" -o -path "*/kubernetes/*.y*ml" -o -name "*deployment*.y*ml" \) 2>/dev/null | head -5

# CI
ls .github/workflows/ 2>/dev/null; ls Jenkinsfile .gitlab-ci.yml 2>/dev/null

# Manifests + entry points
ls requirements.txt pyproject.toml poetry.lock package.json package-lock.json uv.lock 2>/dev/null
ls manage.py wsgi.py asgi.py main.py index.js server.js 2>/dev/null

# Total lines (for scoring)
find . \( -name "*.py" -o -name "*.ts" -o -name "*.tsx" -o -name "*.js" \) \
  | grep -vE "node_modules|__pycache__|\.venv|dist" | xargs wc -l 2>/dev/null | tail -1
```

## Archetype classification (spec §5a.1)

Assign one or more archetypes to `archetypes` using these heuristics:

- **web-api**: server framework (Django/FastAPI/Flask/Express/Fastify) + route/controller
  dirs, no significant frontend build.
- **frontend-spa**: React/Vue/Svelte/Angular deps + a build config (vite/webpack/next), UI
  components, no owned backend.
- **fullstack**: both a server framework AND a frontend build present.
- **cli-tool**: `__main__`, `argparse`/`click`/`commander`, a `bin`/console-scripts entry,
  output to stdout as the product.
- **library**: a published package manifest (name/version, `packages`/`exports`) with no
  server entry point.
- **data-ml**: notebooks, `pandas`/`numpy`/`torch`/`sklearn`, pipeline/training scripts.
- **worker-service**: queue/consumer frameworks (celery/rq/kafka/`@task`/consumer loops),
  long-running non-HTTP process.

## Output schema

```json
{
  "languages": ["python"],
  "framework": "django",
  "archetypes": ["web-api"],
  "file_count": 142,
  "total_lines": 8420,
  "has_docker": true,
  "has_k8s": false,
  "has_terraform": false,
  "has_iac": true,
  "has_ci": true,
  "manifest_files": ["requirements.txt", "pyproject.toml"],
  "entry_points": ["manage.py", "wsgi.py"],
  "context": { "maturity": "production" }
}
```

`context.maturity` defaults to `production`; override from `.codebase-audit.yml`.
