# Error Analysis

## Final public distribution

- 200 sessions evaluated
- 199 hits and 1 miss
- 127 targets ranked first
- 17 ranked second
- 9 ranked third
- 46 ranked from fourth through tenth
- 89 sessions converted on turn 1
- 17 converted on turn 2
- 69 converted on turn 3
- 24 converted on turns 4–5

No post-freeze change was made from inspecting the remaining miss.

## Scenario findings

### Buying

Buying was the fastest route: Hit@10 0.9875, MRR 0.7111, and MTTC 1.30. Exact hard-constraint postings often identify a small candidate set immediately. The one final miss was in Buying, demonstrating that a common first constraint plus category can still leave a target outside the popularity/lexical Top 10.

Potential future improvement: train or calibrate a reranker on a separate, legally usable product-search corpus—not on public target exceptions.

### Browsing

Browsing reached Hit@10 1.0, MRR 0.7401, and MTTC 2.425. Broad category retrieval often produced an early hit, while information-gain questions supplied exact evidence when the pool was large.

Failure pressure: diversity can trade rank precision for coverage. ConstraintGraph protects the strongest six candidates before diversifying the tail.

### Intent Override

Intent Override reached Hit@10 1.0 and the highest scenario MRR at 0.7753, but MTTC was 3.667 because the evaluator does not allow conversion before the new intent is revealed.

The critical fix was distinguishing `RESET(preferences)` from `RESET(intent)`. A preference reset clears constraints and prior questions while preserving a compatible category. Adaptive lexical fusion then resolves ambiguity from the replacement clue.

### Boundary

Boundary reached Hit@10 1.0, MRR 0.6794, and MTTC 3.0. Four boundary sessions converted at turn 4 or later. A no-preference reply correctly produces `NO_PREFERENCE(attribute)` and prevents that attribute from being asked again, but it necessarily spends a turn without narrowing the candidate set.

Potential future improvement: incorporate answerability probability more explicitly into information gain so attributes likely to produce “no preference” receive a larger penalty.

## Parser risks covered by tests

- “Actually, make it blue.” → remove prior color, add blue
- “Forget the leather requirement.” → remove leather
- “I don't care about brand.” → no brand preference
- “Actually I'm looking for shoes instead.” → reset incompatible intent, set category
- official multi-constraint, boundary, and override templates
- low-information rejection → safe no-op

## Generalization risks

1. Free-form paraphrases can weaken exact constraint matching.
2. Product metadata may contain repeated generic features shared by many products.
3. The public evaluator uses deterministic templates and only 200 sessions.
4. Profile tags are intentionally weak soft evidence and may not materially personalize every session.
5. Character TF-IDF is robust to surface variation, not deep semantic equivalence.

These risks are disclosed rather than addressed with unvalidated complexity.
