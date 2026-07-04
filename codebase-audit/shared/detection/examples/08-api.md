# Examples 08 — API Design Quality (load on demand only)

FAIL / PASS / false-positive guards. Read a section only when a candidate is ambiguous.
Adapt to the API paradigm (REST vs GraphQL vs gRPC).

---

## api_status_codes

**FAIL — errors and creates returned as 200:**
```python
def create_user(req):
    if not valid(req): return JsonResponse({"error": "bad"}, status=200)  # error as 200
    user = User.create(...)
    return JsonResponse(user, status=200)                                 # should be 201
```
**PASS:**
```python
    if not valid(req): return JsonResponse({...}, status=422)
    return JsonResponse(user, status=201)
```
**FALSE-POSITIVE — GraphQL:** HTTP `200` with a top-level `errors[]` array is the spec-correct
behavior. Do not flag GraphQL 200-with-errors.

---

## api_backward_compat

**FAIL — bare top-level array (not extensible):**
```json
[ {"id":1}, {"id":2} ]      // cannot add pagination/meta later without breaking clients
```
**PASS — object envelope:**
```json
{ "data": [ {"id":1}, {"id":2} ], "meta": { "next": "cursor..." } }
```

---

## api_http_methods

**FAIL — GET with side effects:**
```python
@app.get("/orders/{id}/delete")     # GET that mutates -> unsafe, cacheable, prefetchable
def delete_order(id): db.delete(id)
```
**PASS:**
```python
@app.delete("/orders/{id}")
def delete_order(id): db.delete(id)
```

---

## api_idempotency

**FAIL — critical POST, no idempotency:**
```python
@app.post("/charge")
def charge(req):
    stripe.charge(req.amount)        # client retry after timeout -> double charge
```
**PASS — idempotency key:**
```python
@app.post("/charge")
def charge(req):
    key = req.headers["Idempotency-Key"]
    if seen(key): return prior_result(key)
    ...
```
**FALSE-POSITIVE — a naturally idempotent read-modify PUT that sets absolute state** (not
append/increment) is already idempotent; don't flag.

---

## api_error_format

**FAIL — inconsistent / raw errors:**
```python
return HttpResponse("something broke", status=500)     # bare string
return JsonResponse({"msg": "no"}, status=400)          # different shape elsewhere
```
**PASS — one structured schema everywhere:**
```json
{ "error": { "code": "VALIDATION_ERROR", "message": "Email invalid",
             "details": [ { "field": "email", "issue": "format" } ] } }
```
