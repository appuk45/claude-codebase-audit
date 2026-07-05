# Examples 11 — Observability (load on demand only)

FAIL / PASS / false-positive guards. Read a section only when a candidate is ambiguous.

---

## obs_pii_in_logs

**FAIL — PII / secrets in logs:**
```python
logger.info("login user=%s pw=%s", email, password)     # password + email in logs
logger.debug("request body: %s", request.json())          # may contain PII / card data
```
**PASS — redacted / safe fields only:**
```python
logger.info("login", extra={"user_id": user.id, "result": "ok"})   # non-identifying id
logger.info("charge", extra={"card_last4": pan[-4:]})               # masked
```
**FALSE-POSITIVE — logging a non-identifying id or an already-masked value** (`user_id`,
`card_last4`, hashed token) is acceptable — do not flag.

---

## obs_structured_logging

**FAIL — print as logging:**
```python
print("order created", order_id)            # unqueryable, no level, no schema
```
**PASS — structured logger:**
```python
logger.info("order_created", extra={"order_id": order_id, "amount": amount})
```
**FALSE-POSITIVE — `print` in a CLI tool whose stdout IS the product output** (a CLI printing
results to the user) is not logging — don't flag CLI user-facing output.

---

## obs_error_context

**FAIL — error logged without stack/context:**
```python
except Exception as e:
    logger.error(e)                          # no stack, no request id, no operation context
```
**PASS — full context:**
```python
except Exception:
    logger.exception("charge_failed", extra={"request_id": rid, "order_id": oid})
```

---

## obs_correlation_ids

**FAIL — no correlation id threaded:**
```python
# each service logs independently; a request can't be traced across hops
logger.info("processing")                    # which request? unknown
```
**PASS — id generated at edge, propagated, logged:**
```python
rid = request.headers.get("X-Request-ID") or uuid4().hex
logger.info("processing", extra={"request_id": rid})
downstream.get(url, headers={"X-Request-ID": rid})
```
**FALSE-POSITIVE — a single standalone service / monolith with no downstream calls:** lower to
Info or skip; correlation IDs matter most across service hops.

---

## obs_security_event_logging

**FAIL — auth failure not logged:**
```python
if not user.check_password(pw):
    return 401                               # silent; attacks invisible to detection
```
**PASS — security event recorded:**
```python
if not user.check_password(pw):
    logger.warning("auth_failure", extra={"user_id": user.id, "ip": ip, "request_id": rid})
    return 401
```
