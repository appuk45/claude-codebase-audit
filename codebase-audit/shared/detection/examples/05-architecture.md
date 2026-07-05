# Examples 05 — Architecture (load on demand only)

FAIL / PASS / false-positive guards. Read a section only when a candidate is ambiguous.
Reason about the module graph, not single lines.

---

## arch_circular_deps

**FAIL — genuine cycle:**
```
orders/service.py   imports  billing/service.py
billing/service.py  imports  orders/service.py     # A <-> B cycle
```
**PASS — dependency inverted via a shared abstraction:**
```
orders/service.py   imports  billing/ports.py (interface)
billing/service.py  imports  billing/ports.py
# concrete wiring happens at the composition root
```
**FALSE-POSITIVE — a type-only / lazy import used solely to break the cycle at runtime
(`if TYPE_CHECKING:` import, function-local import):** lower severity or skip; the cycle is
already mitigated.

---

## arch_layering

**FAIL — domain imports the web/framework layer (inverted):**
```python
# domain/pricing.py  (should be framework-free)
from myapp.api.views import serialize_price     # core depends on presentation
from django.http import JsonResponse
```
**PASS — dependencies flow inward:**
```python
# domain/pricing.py has no web/ORM imports; api layer calls domain
from domain.pricing import compute_price        # api -> domain (inward)
```

---

## arch_separation_concerns

**FAIL — fat controller (HTTP + SQL + business rules entangled):**
```python
def checkout(request):
    cur.execute("SELECT price FROM items WHERE id=%s", [request.POST["id"]])  # SQL in view
    total = row.price * 1.2 - discount_logic(request.user)                    # business rule
    return render(request, "ok.html", {"total": total})                      # presentation
```
**PASS — layered:**
```python
def checkout(request):
    total = checkout_service.total_for(request.user, request.POST["id"])   # thin handler
    return render(request, "ok.html", {"total": total})
```
**FALSE-POSITIVE — a tiny CRUD endpoint with no real business logic:** a 3-line pass-through
handler is fine; don't force layering on trivial code.

---

## arch_dependency_direction

**FAIL — core constructs concrete infra directly:**
```python
class OrderService:
    def __init__(self):
        self.db = psycopg2.connect(DSN)     # hardwired concrete; untestable, unswappable
```
**PASS — injected abstraction:**
```python
class OrderService:
    def __init__(self, repo: OrderRepository):   # depends on interface, injected
        self.repo = repo
```

---

## arch_scalability_bottleneck

**FAIL — heavy work inline on request path:**
```python
def create_report(request):
    pdf = render_huge_pdf(data)     # seconds of CPU, blocks the worker
    email.send(user, pdf)           # sync external call too
    return JsonResponse({"ok": True})
```
**PASS — offloaded:**
```python
def create_report(request):
    task_queue.enqueue(build_and_email_report, user.id, params)   # returns fast
    return JsonResponse({"status": "queued"}, status=202)
```
**FALSE-POSITIVE — a background worker/cron that is SUPPOSED to do heavy work synchronously:**
not a hot path → do not flag.
