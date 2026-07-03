# Examples 03 — Enterprise Readiness (load on demand only)

FAIL / PASS / false-positive guards. Read a section only when a candidate is ambiguous.
Always ignore test/dev-only files when judging production readiness.

---

## ent_config_env

**FAIL — hardcoded env-specific config:**
```python
DATABASE_URL = "postgres://prod-db.internal:5432/app"
STRIPE_ENV = "live"
```
**PASS — from environment:**
```python
DATABASE_URL = os.environ["DATABASE_URL"]
```
**FALSE-POSITIVE — constant that is not environment-specific (a fixed public API contract):**
```python
GITHUB_API = "https://api.github.com"   # same across all envs; not a deploy config
```

---

## ent_process_manager

**FAIL — dev server as prod entrypoint (Dockerfile):**
```dockerfile
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
```
**PASS:**
```dockerfile
CMD ["gunicorn", "app.wsgi", "--workers", "4", "--bind", "0.0.0.0:8000"]
```
**FALSE-POSITIVE — `runserver` inside a docs/dev compose override or a Makefile `dev`
target:** not the production entrypoint → do not flag.

---

## ent_statelessness

**FAIL — session/state in local memory or disk:**
```python
SESSIONS = {}                                  # in-process session store
def login(user): SESSIONS[user.id] = token     # lost on restart, breaks multi-instance
```
**PASS — externalized:**
```python
redis.setex(f"session:{user.id}", ttl, token)
```
**FALSE-POSITIVE — in-memory cache used purely as a rebuildable performance cache (not the
source of truth), correctly repopulated on miss:** acceptable → lower to Info or skip.

---

## ent_migrations

**FAIL — schema auto-created at runtime:**
```python
Base.metadata.create_all(engine)     # no migration history; unsafe for prod evolution
# or TypeORM:  synchronize: true
```
**PASS — versioned migrations:**
```
alembic/versions/0007_add_orders_index.py   (with upgrade() and downgrade())
```
**FALSE-POSITIVE — `create_all` guarded to test/CI setup only (conftest, test fixtures):**
do not flag; that is a test convenience, not the prod schema path.

---

## ent_graceful_shutdown

**FAIL — no signal handling in a worker loop:**
```python
while True:
    job = queue.get()
    process(job)            # SIGTERM kills mid-job -> lost/partial work
```
**PASS — drains on signal:**
```python
stop = threading.Event()
signal.signal(signal.SIGTERM, lambda *_: stop.set())
while not stop.is_set():
    job = queue.get(timeout=1)
    if job: process(job)
```
