# SEO & Publication Metadata Prompt

## Purpose

After the rewrite ledger is complete and the reconstructed draft is final, generate metadata for publication. All metadata must be derived from the actual content of the final draft. Do not add claims, topics, keywords, or descriptions that are absent from the text.

## Input You Will Receive

```
ARTICLE TITLE: [title]
SERIES: [e.g., Moral Decline of America, Genesis to Quantum, Convergence]
ARTICLE NUMBER: [e.g., MDA-003, GTQ-07]
RECONSTRUCTED DRAFT: [full final text]
```

## What You Must Produce

```json
{
  "title": "...",
  "slug": "mda-003-measuring-moral-health",
  "meta_description": "...(max 155 characters, no clickbait, must reflect actual content)...",
  "og_title": "...(max 60 characters)...",
  "og_description": "...(max 200 characters)...",
  "keywords": ["...", "...", "..."],
  "categories": ["..."],
  "tags": ["..."],
  "series": "...",
  "series_position": 3,
  "estimated_read_time_minutes": 0,
  "primary_claim": "One sentence: the single strongest claim this article makes.",
  "evidence_type": "formal_proof | experimental_data | historical_analysis | mathematical_derivation | comparative_study | theoretical_framework",
  "audience_level": "general | informed | technical | academic",
  "framework_terms_used": ["coherence", "entropy", "..."],
  "cross_references": ["MDA-002", "GTQ-04", "..."]
}
```

## Rules

1. **meta_description** must be a real summary, not a teaser. "This article explores..." is weak. "Decade-by-decade data shows moral coherence declined 47% after institutional prayer removal" is concrete.
2. **keywords** — max 10. Pull from the actual text. Include framework terms (coherence, entropy, grace, etc.) only if the article actually uses them substantively, not just in passing.
3. **primary_claim** — the single thing this article argues. If you can't state it in one sentence, the article may have a structural problem. Flag that.
4. **cross_references** — other articles in the series that this article explicitly references or whose arguments it depends on. Only include confirmed references, not guesses.
5. **estimated_read_time** — calculate from word count at 238 wpm (average adult reading speed for technical nonfiction).
6. Do not optimize for search engine tricks. Optimize for accurate discovery — someone searching for what this article actually covers should find it.
