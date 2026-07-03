# Examples 02 — Security (load on demand only)

FAIL / PASS / false-positive guards for ambiguity-prone security items. Read a section only
when a candidate is ambiguous. The key question for most items: **is the value
user-controlled?**

---

## sec_injection

**FAIL — user input concatenated into SQL:**
```python
cursor.execute(f"SELECT * FROM users WHERE name = '{request.GET['name']}'")
```
**PASS — parameterized:**
```python
cursor.execute("SELECT * FROM users WHERE name = %s", [request.GET["name"]])
```
**FALSE-POSITIVE — f-string SQL with only trusted constants (no user input):**
```python
cursor.execute(f"SELECT * FROM {TABLE_NAME} LIMIT {PAGE_SIZE}")   # both are code constants
```
Flag only if a component is user-controlled. Prefer bandit/semgrep candidates.

**FAIL — shell injection:**
```python
os.system(f"ping {request.args['host']}")
```
**PASS:**
```python
subprocess.run(["ping", host], shell=False)
```

---

## sec_hardcoded_secrets

**FAIL — real secret literal:**
```python
STRIPE_KEY = "sk_live_51H8x... "
AWS = "AKIAIOSFODNN7EXAMPLE"
```
**PASS — read from environment:**
```python
STRIPE_KEY = os.environ["STRIPE_KEY"]
```
**FALSE-POSITIVE — placeholder / obvious non-secret:**
```python
API_KEY = "your-api-key-here"      # placeholder
SECRET = ""                        # empty default overridden by env
```
Judge by entropy + context; do not flag placeholders, examples, or env reads.

---

## sec_weak_crypto

**FAIL — MD5 on a password:**
```python
hashed = hashlib.md5(password.encode()).hexdigest()
```
**PASS — argon2/bcrypt:**
```python
hashed = argon2.PasswordHasher().hash(password)
```
**FALSE-POSITIVE — MD5 for a non-security checksum (cache key, ETag):**
```python
etag = hashlib.md5(file_bytes).hexdigest()   # integrity/cache, not a secret
```
Flag MD5/SHA1 only in a security context (password/token/signature).

---

## sec_deserialization

**FAIL — untrusted pickle / unsafe yaml:**
```python
obj = pickle.loads(request.body)
cfg = yaml.load(user_file)                    # no SafeLoader
```
**PASS:**
```python
cfg = yaml.safe_load(user_file)
data = json.loads(request.body)               # then schema-validate
```
**FALSE-POSITIVE — pickle of trusted, local, developer-controlled data (e.g. an ML model
file shipped with the app):** lower to Info/skip if source is not attacker-reachable.

---

## sec_access_control

**FAIL — sensitive route, no auth:**
```python
@app.route("/admin/users")
def admin_users():                            # no auth decorator
    return jsonify(User.query.all())
```
**PASS:**
```python
@app.route("/admin/users")
@login_required
@admin_required
def admin_users():
    ...
```
**FALSE-POSITIVE — intentionally public route:** `/health`, `/login`, `/`, static, docs —
do not flag.

---

## sec_authorization (IDOR/BOLA)

**FAIL — fetch by client id, no ownership check:**
```python
def get_invoice(request, invoice_id):
    return Invoice.objects.get(pk=invoice_id)          # any user can read any invoice
```
**PASS — scoped to the caller:**
```python
def get_invoice(request, invoice_id):
    return Invoice.objects.get(pk=invoice_id, owner=request.user)
```
