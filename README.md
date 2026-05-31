# Rewrite Ledger Workbench

`rewrite-ledger-workbench` is a manual-first PySide6 desktop workbench for controlled sentence-by-sentence rewriting. It is designed as a separate tool around the existing writing-audit scripts, not as a one-shot rewriting pipeline.

The central rule is:

> Each accepted rewrite becomes part of the working draft before the next sentence is judged.

That rule keeps the workflow focused on sentence decisions, a progressive ledger, and a reconstructed draft that changes only when a user accepts a rewrite.

## First milestone status

This prototype can:

1. Open `.md`, `.txt`, `.html`, and `.htm` files.
2. Split documents into Markdown-style sections and sentences.
3. Display sections and sentences in a PySide6 GUI.
4. Let a user manually enter rewrite candidates A/B/C.
5. Accept a candidate, reject the current candidates, leave a sentence unchanged, or mark it as needing David review.
6. Update the reconstructed draft preview after accepted rewrites.
7. Export the rewrite ledger, reconstructed draft, rejected alternatives, and audit report.

LLM rewrite generation is intentionally not connected yet. The ledger and draft-state loop should remain stable before any model integration is added.

## Repository structure

```text
app/
  main.py
  gui/
    main_window.py
    file_panel.py
    audit_panel.py
    rewrite_panel.py
    preview_panel.py
    export_panel.py
  core/
    document_loader.py
    sentence_splitter.py
    rewrite_ledger.py
    scoring.py
    draft_state.py
    html_cleaner.py
    export_manager.py
  audits/
    combined_theophysics_paper_auditor.py
    gpt_adversarial_writing_audit.py
    kimi_style_measure_first.py
    event_coupling_scanner.py
  prompts/
    iterative_sentence_rewrite_ledger.md
    claim_control_rewrite_prompt.md
    seo_metadata_prompt.md
outputs/
examples/
```

The audit scripts in `app/audits/` preserve their standalone CLI behavior while also being importable by the GUI.

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run the GUI

```bash
python -m app.main
```

or, after installing the package:

```bash
rewrite-ledger-workbench
```

## Manual rewrite workflow

1. Click **Open file** and choose a Markdown, text, or HTML document.
2. Select a sentence from the left panel.
3. Enter manual candidates A/B/C in the center panel.
4. Add a 0–100 score and reason for each candidate as needed.
5. Click **Accept A/B/C**, **Reject candidates**, **Leave unchanged**, or **Needs David Review**.
6. The right-panel preview updates immediately when a rewrite is accepted.
7. Click **Export ledger + draft** to write outputs.

## Exports

Exports are written to `outputs/`:

- `rewrite_decisions.json`
- `rewrite_decisions.md`
- `paper_reconstructed.md`
- `paper_rejected_options.md`
- `audit_report.md`

## Audit integration

The right panel includes buttons for:

- measurement audit via `kimi_style_measure_first.py`
- adversarial claim audit via `gpt_adversarial_writing_audit.py`

The copied scripts can still be run directly, for example:

```bash
python app/audits/kimi_style_measure_first.py examples/sample_paper.md --out outputs/kimi_report.json
python app/audits/gpt_adversarial_writing_audit.py examples/sample_paper.md --out outputs/adversarial_report.md
python app/audits/combined_theophysics_paper_auditor.py examples/sample_paper.md --outdir outputs/combined
```

## Hard boundaries

- Do not invent evidence.
- Do not strengthen claims unless the source text already supports them.
- Do not flatten the author's style into generic academic prose.
- Do not silently change theology, math, data, names, dates, citations, or key terms.
- Do not rewrite the whole paper at once.
- Do not overwrite the original file.
- Flag risky changes instead of hiding them.
