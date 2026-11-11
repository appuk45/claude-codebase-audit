# Examples 09 — Resilience & Fault Tolerance (load on demand only)

FAIL / PASS / false-positive guards. Read a section only when a candidate is ambiguous.

---

## res_timeouts

**FAIL — no timeout (can hang forever):**
```python
r = requests.get(url)                      # blocks indefinitely if the peer stalls
resp = await fetch(url)                     # no AbortController/signal
```
**PASS:**
```python
r = requests.get(url, timeout=(3, 10))     # connect, read
resp = await fetch(url, { signal: AbortSignal.timeout(5000) })
```
**FALSE-POSITIVE — a client configured with a default timeout at construction**, then reused:
don't require a per-call timeout if the client already enforces one.

---

## res_retries

**FAIL — unbounded, no backoff (retry storm):**
```python
while True:
    try: return call()
    except: continue                        # hammers a failing dep forever
```
**PASS — bounded + backoff:**
```python
@retry(stop=stop_after_attempt(4), wait=wait_exponential_jitter())
def call(): ...
```

---

## res_retry_safety

**FAIL — retrying a non-idempotent write:**
```python
@retry(stop=stop_after_attempt(3))
def charge(amount): payments.charge(amount)   # a timed-out-but-succeeded call double charges
```
**PASS — idempotency-protected or read-only:**
```python
@retry(stop=stop_after_attempt(3))
def charge(amount, key): payments.charge(amount, idempotency_key=key)
```

---

## res_fault_handling vs res_fallback

**FAIL — unguarded dependency + no degradation:**
```python
def home(req):
    recs = reco_service.get(req.user)      # if reco is down, whole page 500s
    return render(recs)
```
**PASS — guarded with fallback:**
```python
def home(req):
    try:
        recs = reco_service.get(req.user, timeout=1)
    except RecoError:
        recs = cached_popular()             # graceful degradation, page still renders
    return render(recs)
```

---

## res_circuit_breaker

**FALSE-POSITIVE — a single local, reliable primary database:** you don't need a circuit
breaker around your own Postgres for a simple CRUD app. Flag breakers for **unreliable
external / cross-service** dependencies in enterprise/microservice contexts, not every call.

---

## res_dlq

**FAIL — infinite redelivery of poison messages:**
```python
def on_message(msg):
    process(msg)          # raises forever on a bad msg; never acked -> redelivered endlessly
```
**PASS — bounded + DLQ:**
```python
# queue configured with max-receive-count -> dead-letter queue;
# consumer acks after handling, poison messages routed to DLQ after N attempts
```
