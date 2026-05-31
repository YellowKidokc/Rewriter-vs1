# Series Handoff Bridge Prompt

## Purpose

The series flow gate has identified transitions between articles where the semantic handoff score is below threshold. This prompt generates bridge sentences — the 1-3 sentences at the end of Article A and/or the beginning of Article B that connect them.

This is NOT a rewrite of either article. It is a surgical insertion of connective tissue at the seam between two articles.

## Input You Will Receive

```
ARTICLE A: [filename]
ARTICLE A TITLE: [title]
ARTICLE A SECTION: [which folder/section it belongs to]
ARTICLE A FINAL PARAGRAPH: [last paragraph of Article A]

ARTICLE B: [filename]
ARTICLE B TITLE: [title]
ARTICLE B SECTION: [which folder/section it belongs to]
ARTICLE B OPENING PARAGRAPH: [first paragraph of Article B]

HANDOFF SCORE: [0.00-1.00 from the series flow gate]
TRANSITION TYPE: [within_section | cross_section]
SERIES CONTEXT: [1-2 sentences about where these articles sit in the overall series arc]
```

## What You Must Produce

### 1. Diagnosis

In 1-2 sentences, explain WHY the handoff is broken. Common causes:

- **Topic jump:** A ends on topic X, B opens on topic Y, with no bridge
- **Register shift:** A ends in narrative mode, B opens in technical mode (or vice versa)
- **Missing "so what":** A presents evidence but doesn't draw the implication that B picks up
- **Missing callback:** B assumes the reader remembers something from A that A didn't emphasize at the end
- **Section boundary:** A and B are in different logical sections (e.g., chronology → mechanism) — the handoff should acknowledge the mode shift

### 2. Bridge Options

Provide 2-3 bridge options. For each, specify WHERE it goes:

```
OPTION 1:
Placement: END of Article A (append to final paragraph)
Text: "[1-3 sentences that close A and point toward B's territory]"

OPTION 2:
Placement: START of Article B (prepend to opening paragraph)
Text: "[1-3 sentences that acknowledge A's conclusion and set up B's opening]"

OPTION 3:
Placement: BOTH (close A + open B)
End-of-A text: "[1-2 sentences]"
Start-of-B text: "[1-2 sentences]"
```

### 3. Projected Score

Estimate what the handoff score would become with each option applied. This is an educated guess, not a measurement — the series flow gate can verify after insertion.

## Rules

1. **Bridge sentences must be in the author's voice.** Not generic academic transitions. Not "In the next article, we will examine..." That's textbook writing. The author's style would be more like: "But if the data is this clear, why didn't anyone act? That's the question the next decade answers."

2. **Do not summarize either article.** The bridge connects; it does not recap. The reader has just finished A. They don't need a summary of what they just read.

3. **Cross-section bridges should name the mode shift.** If you're moving from chronological evidence to mechanism analysis, say so: "The timeline tells you *what* happened. The next question is *why* — and that requires a different kind of tool."

4. **Within-section bridges should carry a thread.** If both articles are in the same logical section, there should be a concept, data thread, or question that A's ending poses and B's opening answers. Find it or flag that it doesn't exist.

5. **Never invent evidence or claims.** The bridge is connective tissue, not content. It may reference what was established in A or preview what B covers, but it does not introduce new arguments.

6. **Maximum bridge length: 3 sentences per insertion point.** If you need more than that, the problem isn't the handoff — it's the article endings or openings themselves, and that's a section diagnosis problem, not a bridge problem.

## Output Format

```json
{
  "article_a": "MDA-018",
  "article_b": "MDA-019",
  "current_handoff_score": 0.03,
  "diagnosis": "...",
  "options": [
    {
      "placement": "end_of_a | start_of_b | both",
      "end_text": "...",
      "start_text": "...",
      "projected_score": 0.45,
      "rationale": "..."
    }
  ],
  "recommended_option": 1
}
```
