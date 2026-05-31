# Section-Level Diagnosis Prompt

## Purpose

The sentence rewrite engine works one sentence at a time. This prompt works one section at a time. It diagnoses structural problems that are invisible at the sentence level: arc collapse, buried leads, misplaced evidence, redundant paragraphs, missing transitions, and section-level claim/support mismatches.

Run this BEFORE the sentence-by-sentence pass. It tells the rewriter WHERE to focus and what kind of moves to make.

## Input You Will Receive

```
ARTICLE: [filename or title]
SECTION HEADING: [heading text]
SECTION LEVEL: [h1–h6]
SECTION TEXT: [full section body]
PREVIOUS SECTION HEADING: [or "START OF ARTICLE"]
NEXT SECTION HEADING: [or "END OF ARTICLE"]
```

## What You Must Produce

### 1. Section Arc Diagnosis

In 2-4 sentences, describe what this section is trying to do and whether it succeeds. Possible arc types:

- **Claim → Evidence → Implication** (most common in Theophysics papers)
- **Narrative → Principle → Application** (common in MDA series)
- **Problem → Method → Result** (common in technical sections)
- **Context → Contrast → Resolution** (common in comparative sections)

If the section doesn't follow any recognizable arc, say so. That's a structural finding.

### 2. Paragraph-Level Map

For each paragraph in the section, state its function in ONE phrase:

```
P1: Sets up the historical context (1880s institutional data)
P2: States the central claim (moral coherence correlates with institutional alignment)
P3: Provides first evidence line (Gallup data, 1950-2020)
P4: Provides second evidence line (Pew data, cross-denominational)
P5: Repeats P2's claim in different words [REDUNDANCY FLAG]
P6: Draws implication for modern policy
```

### 3. Structural Findings

Flag any of these if present:

| Finding | Description |
|---|---|
| **BURIED_LEAD** | The strongest claim or most important data point is in paragraph 3+ instead of paragraph 1-2 |
| **REDUNDANT_PARAGRAPH** | A paragraph restates a previous paragraph without adding new information |
| **ORPHAN_EVIDENCE** | Evidence presented without connecting it to a claim |
| **ORPHAN_CLAIM** | Claim made without evidence in this section or a reference to where the evidence lives |
| **ARC_COLLAPSE** | The section starts strong but doesn't land — no conclusion, implication, or handoff |
| **REGISTER_SHIFT** | The section switches between casual and formal voice in a jarring way |
| **WALL_OF_TEXT** | A paragraph exceeds 8 sentences without a break, subheading, or structural marker |
| **MISSING_BRIDGE_IN** | This section doesn't connect to the previous section's ending |
| **MISSING_BRIDGE_OUT** | This section doesn't set up the next section's opening |

### 4. Priority Sentences

List the 3-5 sentence IDs (if available) or sentence positions that would benefit most from the rewrite engine. For each, state the specific problem and the type of move that would fix it.

```
PRIORITY 1: Sentence 3 of P1 — abstract nominalization ("the observation of decline") should be active verb ("when we observe decline")
PRIORITY 2: Sentence 1 of P5 — redundant restatement of P2's claim, should be cut or merged
PRIORITY 3: Sentence 2 of P3 — data reference without date range, needs specificity
```

### 5. Section Score

Rate the section 0-100 on these dimensions:

- **Arc completeness** (0-25): Does it set up, develop, and land?
- **Claim-evidence ratio** (0-25): Are claims supported within the section?
- **Flow** (0-25): Do paragraphs connect to each other?
- **Voice** (0-25): Does it sound like the author?

## Output Format

```json
{
  "section_heading": "...",
  "arc_type": "claim_evidence_implication | narrative_principle_application | problem_method_result | context_contrast_resolution | unrecognized",
  "arc_diagnosis": "...",
  "paragraph_map": [
    { "paragraph": 1, "function": "...", "flag": null },
    { "paragraph": 2, "function": "...", "flag": "BURIED_LEAD" }
  ],
  "structural_findings": [
    { "finding": "REDUNDANT_PARAGRAPH", "location": "P5", "detail": "..." }
  ],
  "priority_sentences": [
    { "location": "P1 S3", "problem": "...", "recommended_move": "..." }
  ],
  "scores": {
    "arc_completeness": 0,
    "claim_evidence_ratio": 0,
    "flow": 0,
    "voice": 0,
    "total": 0
  }
}
```

## Hard Boundaries

- This prompt diagnoses. It does not rewrite. It tells the rewrite engine where to aim.
- Do not propose restructuring the entire article. Stay within the section you're given.
- If the section is genuinely well-constructed, say so with a high score and an empty findings list. Not everything needs fixing.
