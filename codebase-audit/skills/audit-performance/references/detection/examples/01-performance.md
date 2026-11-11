# Examples 01 — Performance (load on demand only)

Curated positive (FAIL / true-positive) vs negative (PASS / false-positive) snippets.
Read a section ONLY when a candidate for that item is ambiguous. Do not load by default.

---

## perf_n_plus_one

**FAIL — query inside loop, no batching (Python/Django):**
```python
orders = Order.objects.filter(user=user)      # 1 query
for order in orders:
    print(order.customer.name)                # +1 query per order  -> N+1
```

**PASS — eager-loaded:**
```python
orders = Order.objects.filter(user=user).select_related("customer")
for order in orders:
    print(order.customer.name)                # 0 extra queries
```

**FAIL — JS/TS ORM in map:**
```ts
await Promise.all(ids.map(id => db.user.findUnique({ where: { id } })));  // N queries
```
**PASS — single batched query:**
```ts
await db.user.findMany({ where: { id: { in: ids } } });                    // 1 query
```

**FALSE-POSITIVE (do NOT flag)** — loop calls a pure in-memory function, no DB/IO:
```python
for order in orders:
    total += order.amount * TAX               # arithmetic only, not a query
```

---

## perf_blocking_in_async

**FAIL — blocking HTTP + sleep inside coroutine:**
```python
async def handler(request):
    r = requests.get(url)        # blocking -> stalls event loop
    time.sleep(2)                # blocking sleep
    return r.json()
```
**PASS — async equivalents:**
```python
async def handler(request):
    async with httpx.AsyncClient() as c:
        r = await c.get(url)
    await asyncio.sleep(2)
    return r.json()
```
**PASS — blocking work offloaded to executor:**
```python
async def handler(request):
    result = await loop.run_in_executor(None, cpu_heavy, data)   # not on loop thread
    return result
```

---

## perf_pagination

**FAIL — full collection returned:**
```python
def list_orders(request):
    return JsonResponse(list(Order.objects.all().values()))   # unbounded
```
**PASS — paginated with max size:**
```python
def list_orders(request):
    page = int(request.GET.get("page", 1))
    size = min(int(request.GET.get("size", 50)), 100)          # enforced max
    qs = Order.objects.all()[(page-1)*size : page*size]
    return JsonResponse(list(qs.values()), safe=False)
```
**FALSE-POSITIVE** — `.all()` used only for a count/aggregate, not returned as rows:
```python
count = Order.objects.all().count()                            # SQL COUNT, not materialized
```

---

## perf_unbounded_memory

**FAIL — whole file into memory:**
```python
data = open("huge.csv").read().splitlines()    # loads entire file
```
**PASS — streamed:**
```python
with open("huge.csv") as f:
    for line in f:                              # lazy, constant memory
        process(line)
```
