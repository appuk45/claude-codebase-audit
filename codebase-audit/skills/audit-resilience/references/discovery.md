# Discovery — stack detection + archetype classification

Run these commands against the current working directory and assemble a
`discovery_context` JSON object. If a command yields nothing, record an empty
array / false. Do not skip commands.

## Always-excluded paths

Never count or audit these — they hold installed agent skills (including this audit's own
engine and specs), tool state, or generated/vendored code:
`.agents/ .claude/ .codex/ .cursor/ .windsurf/ .kiro/ .github/skills/ .codebase-audit/
node_modules/ __pycache__/ .venv/ venv/ dist/ build/ .git/`.
Pass them (plus config `ignore` globs) to every dimension as ignore paths. With ripgrep,
add `--glob '!<dir>/**'` for each.

## Commands

```bash
# Shared exclusion filter for the commands below
EXCL='(^|/)(\.agents|\.claude|\.codex|\.cursor|\.windsurf|\.kiro|\.github/skills|\.codebase-audit|node_modules|__pycache__|\.venv|venv|dist|build|\.git)/'
GREP_EXCL="--exclude-dir=.agents --exclude-dir=.claude --exclude-dir=.codex --exclude-dir=.cursor --exclude-dir=.windsurf --exclude-dir=.kiro --exclude-dir=.codebase-audit --exclude-dir=node_modules --exclude-dir=.venv --exclude-dir=venv --exclude-dir=.git"

# Language counts
find . -name "*.py" | grep -vE "$EXCL" | wc -l
find . \( -name "*.ts" -o -name "*.tsx" \) | grep -vE "$EXCL" | wc -l
find . -name "*.js" | grep -vE "$EXCL" | wc -l

# Framework hints
grep -rlE $GREP_EXCL "from django|import django" . --include="*.py" 2>/dev/null | head -3
grep -rl $GREP_EXCL "from fastapi" . --include="*.py" 2>/dev/null | head -3
grep -rl $GREP_EXCL "from flask" . --include="*.py" 2>/dev/null | head -3
cat package.json 2>/dev/null

# IaC
find . \( -name "Dockerfile" -o -name "docker-compose*.y*ml" \) 2>/dev/null | grep -vE "$EXCL"
find . -name "*.tf" 2>/dev/null | grep -vE "$EXCL" | head -5
find . \( -path "*/k8s/*.y*ml" -o -path "*/kubernetes/*.y*ml" -o -name "*deployment*.y*ml" \) 2>/dev/null | grep -vE "$EXCL" | head -5

# CI
ls .github/workflows/ 2>/dev/null; ls Jenkinsfile .gitlab-ci.yml 2>/dev/null

# Manifests + entry points
ls requirements.txt pyproject.toml poetry.lock package.json package-lock.json uv.lock 2>/dev/null
ls manage.py wsgi.py asgi.py main.py index.js server.js 2>/dev/null

# Total lines (for scoring)
find . \( -name "*.py" -o -name "*.ts" -o -name "*.tsx" -o -name "*.js" \) \
  | grep -vE "$EXCL" | tr '\n' '\0' | xargs -0 cat 2>/dev/null | wc -l
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
