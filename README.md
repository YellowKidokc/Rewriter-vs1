# Theophysics Writing Audit Scripts

These are reconstructed working scripts based on the documented “measure before reading” pipeline.

The original raw Python files were not found in the uploaded/searchable material. What was found was the description of the method:
- word frequency
- motif distribution
- sentence rhythm
- section weight ratios
- redundancy detection
- coherence scoring
- proof-tag / burden-of-proof review

## Files

### 1. `kimi_style_measure_first.py`
Measurement-first structural audit.

Best for:
- motif counts
- section balance
- sentence rhythm
- repeated phrases
- proof-tag coverage
- basic coherence signal

Run:
```bash
python kimi_style_measure_first.py paper.md --out kimi_report.json
```

### 2. `gpt_adversarial_writing_audit.py`
Claim-control and adversarial review.

Best for:
- overclaims
- unsupported strong claims
- undefined load-bearing terms
- repeated phrases
- language that needs downgrading

Run:
```bash
python gpt_adversarial_writing_audit.py paper.md --out adversarial_report.md
```

### 3. `combined_theophysics_paper_auditor.py`
Combined pipeline: measurement first, adversarial second.

Run:
```bash
python combined_theophysics_paper_auditor.py paper.md --outdir reports
```

## Important limitation

These scripts do not prove truth. They check structural integrity, readability pressure, motif distribution, claim burden, and coherence signals.
