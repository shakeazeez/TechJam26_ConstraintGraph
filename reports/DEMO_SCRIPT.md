# Demo Script (2–3 minutes)

## 0:00–0:20 — Problem

“A shopping query changes over time. The agent must find one hidden product among 50,000, rank it highly, and do so within ten turns. The starter searches only the latest message and reaches 0.125 Hit@10.”

Show the baseline row in the README.

## 0:20–0:45 — Architecture

Show the README flow.

“ConstraintGraph converts every message into immutable events, projects the current intent, and sends it to a distinct Buying or Browsing route. Clarification is selected by expected candidate-pool reduction.”

Briefly show `events.py`, `routing.py`, and `clarification.py`.

## 0:45–1:40 — Live intent-override session

Run:

```bash
python scripts/demo_session.py --sample-id public_0003
```

Point out:

1. the first broad/soft request;
2. the structured question selected by information gain;
3. the evaluator’s “Actually, ignore…” message;
4. the preference reset preserving category;
5. valid ranked ASINs and the conversion turn/rank.

## 1:40–2:10 — Reliability

Run:

```bash
python -m pytest
```

“The 26 tests cover event replay, session isolation, replacement/removal language, no-preference behavior, route selection, information gain, exact retrieval, lexical fusion, caching, and split integrity.”

## 2:10–2:40 — Results

Show `reports/ABLATIONS.md`.

“The final public result is 0.995 Hit@10, 0.7308 MRR, 2.19 MTTC, and 0.8929 TechnicalScore. The pseudo-hidden score remains 0.8703. Runtime token usage is zero.”

## 2:40–3:00 — Closing

“ConstraintGraph’s core insight is that a shopping conversation is a sequence of state changes and uncertainty reductions—not merely a longer search string. It is fast, explainable, reproducible, and practical beyond the prototype.”
