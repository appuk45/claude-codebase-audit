# Scoring & CI Gating (authoritative rules; implemented in `engine/`)

## Display score (per dimension)
`score = max(0, min(10, 10 − (H×2.0 + M×0.8 + L×0.3) / max(total_lines, 1) × 1000))`,
rounded to 1 dp. Info findings carry weight 0. **Display only** — labeled "indicative".

## Skip handling (spec §9a.1)
- A **fully-skipped** dimension (every checklist item `skipped`) scores **N/A** and is
  **excluded** from the overall average — it does NOT contribute a 10.
- **Overall score** = average of applicable (non-N/A) dimension scores.
- **Pass rate** per dimension = `passed / (total − skipped)` — applicable items only.

## CI gate (authoritative — NOT the score)
Count raw severities across all dimensions; compare to config thresholds. A `null`
threshold means ignore. Suppressions (`checklist_id@file`) are removed before counting.
Any breach → exit 1; otherwise exit 0. Implemented in `engine/gate.py`.

The engine is the single source of these computations; skills must call
`python -m engine.cli`, never re-implement the math.
