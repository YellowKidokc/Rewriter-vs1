# Prompt Suite v2 — Architecture

## Execution Order

These prompts form a pipeline. They are not independent — each one feeds the next.

```
                    ┌──────────────────────┐
                    │  SECTION DIAGNOSIS   │  ← Run first, per section
                    │  (section_diagnosis) │
                    └──────────┬───────────┘
                               │
                    identifies priority sentences
                               │
                    ┌──────────▼───────────┐
                    │  SENTENCE REWRITE    │  ← Run per sentence, in order
                    │  (iterative_rewrite) │
                    └──────────┬───────────┘
                               │
                    generates candidates A/B/C
                               │
                    ┌──────────▼───────────┐
                    │  CLAIM CONTROL       │  ← Run per candidate, before acceptance
                    │  (claim_control)     │
                    └──────────┬───────────┘
                               │
                    passes or flags each candidate
                               │
                    ┌──────────▼───────────┐
                    │  HUMAN DECISION      │  ← Accept / Reject / Unchanged / Review
                    │  (the GUI)           │
                    └──────────┬───────────┘
                               │
                    draft updates, next sentence
                               │
              ┌────────────────▼─────────────────┐
              │  After all sentences are done:    │
              │                                   │
              │  SEO METADATA  ← from final draft │
              │  HANDOFF BRIDGE ← from flow gate  │
              └───────────────────────────────────┘
```

## Files

| Prompt | When | What |
|---|---|---|
| `section_diagnosis_prompt.md` | Before sentence pass | Diagnoses section arc, flags structural issues, identifies priority sentences |
| `iterative_sentence_rewrite_ledger.md` | Per sentence | Generates up to 3 candidates with full scoring rubric |
| `claim_control_rewrite_prompt.md` | Per candidate | 5-check safety validation before acceptance |
| `seo_metadata_prompt.md` | After draft complete | Generates publication metadata from final text |
| `series_handoff_bridge_prompt.md` | After series flow gate | Generates bridge sentences for flagged transitions |

## Integration with Existing Code

**scoring.py** — The rewrite prompt's scoring factors map 1:1 to the `POSITIVE_LIMITS` and `PENALTY_LIMITS` already defined in `app/core/scoring.py`. When LLM integration is added, the LLM's score output should be validated against these same limits.

**rewrite_ledger.py** — The JSON output format from the rewrite prompt maps directly to `RewriteLedgerEntry` and `RewriteCandidate` dataclasses. The `meaning_drift_risk` and `claim_strength_risk` fields already exist in the ledger model.

**Series flow gate** — The handoff bridge prompt consumes the output of `03_SCORED/series-flow/run_series_flow.py`. When a handoff is flagged, the bridge prompt generates insertion candidates. After insertion, rerun the flow gate to verify the score improved.

**Audit scripts** — The section diagnosis prompt and the existing `kimi_style_measure_first.py` + `gpt_adversarial_writing_audit.py` are complementary. The audits measure; the diagnosis interprets. Run audits first, feed their findings into the diagnosis context if available.

## What Changed from v1

| v1 (original) | v2 (this) |
|---|---|
| 14-line generic instruction | Full LLM prompt with input format, output schema, scoring rubric, voice calibration, and hard boundaries |
| 3-line claim control | 5-check validation framework with term fidelity table and severity mapping |
| 3-line SEO stub | Structured metadata schema with concrete rules |
| No section-level prompt | Section diagnosis with arc typing, paragraph mapping, and priority targeting |
| No series-level prompt | Handoff bridge generator tied to the flow gate output |
