# Examples 04 — Issue Detection (load on demand only)

FAIL / PASS / false-positive guards. Read a section only when a candidate is ambiguous.
Always exclude generated/vendored/minified files.

---

## issue_error_swallowing

**FAIL — exception swallowed:**
```python
try:
    charge_card(order)
except Exception:
    pass                      # failure hidden; card may not be charged, no signal
```
**PASS — handled/logged/re-raised:**
```python
try:
    charge_card(order)
except PaymentError as e:
    logger.exception("charge failed")
    raise
```
**FALSE-POSITIVE — intentional ignore, narrow + documented:**
```python
try:
    os.remove(tmp)
except FileNotFoundError:
    pass                      # already gone; safe to ignore (documented, specific type)
```
Do not flag a narrow, commented, intentional ignore. Flag broad silent `except Exception: pass`.

---

## issue_mutable_default

**FAIL — mutable default arg (classic latent bug):**
```python
def add_item(item, bucket=[]):     # bucket shared across ALL calls
    bucket.append(item)
    return bucket
```
**PASS:**
```python
def add_item(item, bucket=None):
    bucket = [] if bucket is None else bucket
    bucket.append(item)
    return bucket
```

---

## issue_dead_code

**FAIL — unreachable + unused:**
```python
def f(x):
    return x
    log.info("done")          # unreachable
import os                       # never used
```
**FALSE-POSITIVE — import with a side effect / framework registration:**
```python
import app.signals             # registers handlers on import; "unused" but required
from . import models           # side-effectful model registration
```
Do not flag side-effect imports, `__init__` re-exports, or framework-required symbols.

---

## issue_complexity

**FAIL — high cyclomatic complexity (radon rank D):**
```python
def route(req):                # 15+ branches: nested if/elif over method, role, state...
    if req.method == "GET":
        if req.user.is_admin:
            if req.query.get("all"):
                ...             # many more branches
```
**PASS — decomposed:**
```python
def route(req):
    handler = HANDLERS.get((req.method, req.role), default_handler)
    return handler(req)
```
**FALSE-POSITIVE — a flat dispatch table / big but linear match with no real branching
depth:** high line count but low complexity → judge by complexity score, not length.

---

## issue_resource_leak

**FAIL — file/connection not closed:**
```python
f = open(path)
data = f.read()               # no close(); leaks on exception
```
**PASS — context managed:**
```python
with open(path) as f:
    data = f.read()
```
**FALSE-POSITIVE — resource handed to a caller that owns closing (documented ownership
transfer), or a long-lived module-level pooled client intentionally kept open:** don't flag.
