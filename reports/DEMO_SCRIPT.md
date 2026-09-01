# Demo Script (2-3 minutes)

## 0:00-0:20 - Problem

"A shopping query changes over time. The agent must find one hidden product among 50,000, rank it highly, and do so within ten turns. The starter searches only the latest message and reaches 0.125 Hit@10."

Show the baseline row in the README.

## 0:20-0:45 - Architecture

Show the README flow.

"ConstraintGraph converts every message into immutable events, projects the current intent, and sends it to a distinct Buying or Browsing route. Clarification is selected by expected candidate-pool reduction."

"It is the intelligent orchestration layer between conversation and retrieval, not simply a graph search. Its six pieces are event-sourced state, distinct Buying and Browsing routes, information-gain clarification, exact constraint retrieval, adaptive BM25 plus TF-IDF, and safe intent-override handling."

Briefly show `events.py`, `routing.py`, and `clarification.py`.

## 0:45-1:40 - Live intent-override session

Run in a 110-column terminal:

```bash
python -m constraintgraph.demo --scenario override
```

Point out:

1. `I'm looking for handbags. A key requirement is: leather.` produces real category/material events, Buying route, 595 candidates, and a production information-gain question.
2. `Black.` adds the real color constraint and reduces the ranking/question pool to one catalog product.
3. `Actually, make it blue.` emits the real attribute-wide `REMOVE(color)` and `ADD(color=blue)` events.
4. Generation remains zero because this replacement is not a `RESET`.
5. The projected state contains blue and no black, and catalog-backed recommendations rerank against the updated intent.

The scenario contains only these user messages. It does not contain a target, expected events, products, or scores.

## 1:40-2:10 - Reliability

Run:

```bash
python -m pytest
```

"The 35 tests cover event replay, session isolation, replacement/removal language, no-preference behavior, route selection, information gain, exact retrieval, lexical fusion, caching, split integrity, diagnostics invariance, and contract tests."

## 2:10-2:40 - Results

Show `reports/ABLATIONS.md`.

"We initially expected semantic models to be necessary. Our ablations showed otherwise. The deterministic architecture reached 0.975 pseudo-hidden Hit@10, so extra dependency, latency, and regression risk were not justified before submission."

Point to the ablation table and show the improvement: **0.1067 to 0.8929 TechnicalScore**.

"The final public result is 0.995 Hit@10, 0.7308 MRR, 2.19 MTTC, and 0.8929 TechnicalScore. The pseudo-hidden score remains 0.8703. As an efficiency and reproducibility benefit, runtime uses zero LLM/API calls."

## 2:40-3:00 - Closing

"ConstraintGraph's core insight is that a shopping conversation is a sequence of state changes and uncertainty reductions, not merely a longer search string. It is explainable, reproducible, and practical beyond the prototype."
