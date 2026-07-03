# Detection Spec 04 — Issue Detection

**ISO 25010:** Maintainability (Analysability · Modularity · Modifiability · Testability ·
Reusability)
**Audit key:** `issues`
**Static analysis only.** This dimension is the heaviest external-tool consumer — prefer tool
output, LLM confirms + dedupes. Do not assume a specific framework.

## How to use this spec (agent instructions)

1. Read `discovery_context`. Skip items whose `applies_to` doesn't match → `skipped`.
2. Prefer external-tool candidates where noted (radon, eslint, vulture, jscpd); fall back to
   `signals` (ripgrep) when a tool is absent.
3. Read ONLY candidate snippets. Apply `confirm`. Deduplicate against tool findings so the
   same issue is not double-counted.
4. Thresholds come from config (`issues.complexity_max` default 10,
   `issues.function_loc_max` default 60, `issues.file_loc_max` default 400,
   `issues.nesting_max` default 4). Use these unless overridden.
5. Assign `severity` with maturity modifiers.
6. Consult `examples/04-issues.md` only when ambiguous.
7. Emit `AuditResult` JSON per `shared/schema.json`. Score per `shared/scoring.md`.

**Exclude from all items:** generated/vendored files (`migrations/`, `node_modules/`,
`dist/`, `build/`, `*_pb2.py`, `*.generated.*`, minified files).

---

## Analysability

### issue_complexity — No excessively complex functions
- **intent:** High cyclomatic complexity means many independent paths → hard to understand,
  modify, and test (Analysability, Modifiability, Testability).
- **applies_to:** all
- **signals:** prefer `radon cc -n C --json` (Python), eslint `complexity` rule (JS/TS).
  Fallback: dense `if/elif/for/while/case/&&/||` clusters in one function.
- **confirm:** fail if a function's cyclomatic complexity exceeds `complexity_max`. warning
  just below the threshold. Report the function + score.
- **severity:** Medium (very high, rank E/F → escalate note; prototype → Low)
- **remediation:** Extract helpers, use guard clauses, table-drive branching.
- **compliance_refs:** ISO25010 Analysability/Modifiability/Testability

### issue_long_unit — No over-long functions/files
- **intent:** Long units concentrate too much responsibility and resist comprehension.
- **applies_to:** all
- **signals:** function LOC > `function_loc_max`; file LOC > `file_loc_max` (via `wc -l` /
  tool).
- **confirm:** warning if a function/file exceeds the LOC threshold and is not a
  data table / generated. pass otherwise.
- **severity:** Low (prototype → Info)
- **remediation:** Split into smaller focused units.
- **compliance_refs:** ISO25010 Analysability, Modularity

### issue_deep_nesting — No deep nesting
- **intent:** Deep nesting (arrow anti-pattern) obscures control flow.
- **applies_to:** all
- **signals:** indentation depth / block nesting > `nesting_max` inside a function.
- **confirm:** warning if nesting depth exceeds threshold. pass otherwise.
- **severity:** Low
- **remediation:** Early returns / guard clauses; extract nested blocks.
- **compliance_refs:** ISO25010 Analysability

### issue_dead_code — No unused or unreachable code
- **intent:** Dead code misleads readers and rots.
- **applies_to:** all
- **signals:** prefer `vulture` (Python), eslint `no-unused-vars`/`no-unreachable` (JS/TS).
  Fallback: unused imports, code after `return/raise/throw`.
- **confirm:** fail for clearly unreachable code; warning for unused
  imports/vars/private functions. pass otherwise.
- **severity:** Low
- **remediation:** Remove dead code; keep history in VCS.
- **compliance_refs:** ISO25010 Analysability, Modifiability

### issue_commented_code — No large commented-out code blocks
- **intent:** Commented-out code is noise; VCS already preserves history.
- **applies_to:** all
- **signals:** consecutive comment lines that parse as code (`# .*[=(){};]` / `// .*[=(){};]`,
  3+ lines).
- **confirm:** info if a block of commented-out code (not prose docs) is present.
- **severity:** Info (enterprise → Low)
- **remediation:** Delete; rely on version control.
- **compliance_refs:** ISO25010 Analysability

### issue_todo_debt — Tracked technical-debt markers
- **intent:** Dense TODO/FIXME/HACK/XXX signals unmanaged debt; surface for visibility.
- **applies_to:** all
- **signals:** `rg -n "\b(TODO|FIXME|HACK|XXX|BUG)\b"`.
- **confirm:** info; aggregate count + hotspots. Escalate to Low if FIXME/BUG markers cluster
  in one module.
- **severity:** Info
- **remediation:** Convert markers into tracked issues; resolve or remove.
- **compliance_refs:** ISO25010 Modifiability

---

## Modularity

### issue_god_module — No god class/module
- **intent:** A class/module doing too much (many methods, large LOC, many imports) resists
  independent change and reuse.
- **applies_to:** all
- **signals:** class with many methods / very high LOC; module with very high fan-out of
  imports; mixed unrelated responsibilities.
- **confirm:** warning if a single class/module concentrates many unrelated responsibilities
  (methods/LOC well above peers). pass otherwise.
- **severity:** Medium (prototype → Low)
- **remediation:** Split by responsibility; extract cohesive units.
- **compliance_refs:** ISO25010 Modularity, Reusability

---

## Modifiability

### issue_duplication — No significant duplicated code
- **intent:** Copy-paste blocks cause inconsistent fixes and multiply defects.
- **applies_to:** all
- **signals:** prefer `jscpd` if available; fallback: near-identical multi-line blocks
  recurring across files.
- **confirm:** warning if a non-trivial block (>~10 lines) is duplicated 2+ times and not a
  generated artifact. pass otherwise.
- **severity:** Medium (prototype → Low)
- **remediation:** Extract a shared function/module.
- **compliance_refs:** ISO25010 Modifiability, Reusability

### issue_error_swallowing — No silently swallowed errors
- **intent:** Catching and discarding exceptions hides bugs and produces silent failures.
  (Distinct from dim9: this is about *hiding* errors, not fault-tolerance strategy.)
- **applies_to:** all
- **signals:** `except.*:\s*pass|except.*:\s*\.\.\.|catch\s*\([^)]*\)\s*\{\s*\}|
  except Exception:\s*pass|catch\s*\{\s*\}`.
- **confirm:** fail if an exception is caught and neither handled, logged, nor re-raised.
  pass if logged/handled/re-raised, or an intentional-ignore with a justifying comment.
- **severity:** Medium (prototype → Low)
- **remediation:** Log/handle/re-raise; narrow the caught type; document intentional ignores.
- **compliance_refs:** ISO25010 Modifiability; OWASP A10:2025 (adjacent)

### issue_mutable_default — No mutable default argument / shared mutable state bug
- **intent:** Python mutable default args (`def f(x=[])`) and shared mutable module state
  cause subtle cross-call bugs.
- **applies_to:** all
- **signals:** `def \w+\([^)]*=\s*(\[\]|\{\}|set\(\))` (Python); module-level mutable
  shared across calls.
- **confirm:** fail for mutable default arguments. warning for shared mutable module state
  mutated per call. pass otherwise.
- **severity:** Medium (this is a latent correctness bug; holds at all maturities → floor:Low)
- **remediation:** Default to `None`, create the container inside the function.
- **compliance_refs:** ISO25010 Modifiability; CWE-1188 (adjacent)

### issue_global_state — Limited mutable global state
- **intent:** Mutable globals/singletons create hidden coupling and hurt testability.
- **applies_to:** all
- **signals:** module-level mutable vars reassigned across functions; `global ` statements;
  singleton patterns holding request/user state.
- **confirm:** warning if mutable global state is used for cross-function coordination in a
  way that impedes testing. pass for constants/config.
- **severity:** Low
- **remediation:** Pass state explicitly / inject dependencies.
- **compliance_refs:** ISO25010 Modularity, Testability

### issue_type_safety — Type annotations present (typed stacks)
- **intent:** Missing types / pervasive `any` removes a key maintainability + refactor-safety
  net.
- **applies_to:** typed stacks — TypeScript, typed Python (has `mypy`/type hints elsewhere)
- **signals:** TS `:\s*any\b|@ts-ignore|@ts-nocheck`; Python public functions with no
  annotations in a project that otherwise uses typing.
- **confirm:** warning if public APIs lack types or overuse `any`/`@ts-ignore`. skip for
  untyped-by-convention codebases (no typing anywhere) or dynamic scripts.
- **severity:** Low (enterprise → Medium)
- **remediation:** Add type annotations; replace `any` with precise types; avoid `@ts-ignore`.
- **compliance_refs:** ISO25010 Analysability, Modifiability

---

## Correctness Smell

### issue_resource_leak — Resources are closed
- **intent:** Files/connections/sockets opened without guaranteed close leak handles and
  connections.
- **applies_to:** web-api, fullstack, worker-service, cli-tool, data-ml
- **signals:** `open\(|socket\(|connect\(|createReadStream\(|requests.Session\(` not inside a
  `with`/`try...finally`/`using`/`defer close` and not closed.
- **confirm:** fail if an opened resource has no guaranteed close (context manager / finally /
  close call). pass if managed.
- **severity:** Medium (prototype → Low)
- **remediation:** Use context managers / `try...finally` / `using` / `defer` to close.
- **compliance_refs:** ISO25010 Reliability/Modifiability; CWE-772

---

## Cross-references (scored elsewhere — do NOT emit here)

- Performance anti-patterns (N+1, loops I/O, unbounded memory) → dim 1.
- Security-relevant bugs (injection, unsafe deser) → dim 2.
- Circular imports, layering violations, coupling/cohesion at module graph level → dim 5.
- Fault-tolerance error handling (retries, timeouts, fallbacks) → dim 9.
- Test coverage / test quality → deferred v2 (audit-testing).
