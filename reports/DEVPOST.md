# Devpost Draft

## Project name

ConstraintGraph

## Tagline

An adaptive shopping agent that turns evolving conversations into structured intent and asks the question that reduces uncertainty fastest.

## Inspiration

Shopping conversations are not static queries. Requirements accumulate, disappear, and sometimes reverse completely. Most assistants hide that evolution inside a prompt. ConstraintGraph instead treats intent as inspectable state and product search as progressive uncertainty reduction. It is the intelligent orchestration layer between the conversation and retrieval—not simply a graph search.

## What it does

ConstraintGraph searches the official 50,000-product Amazon-derived catalog and recommends up to ten valid products on every turn. Its core innovations are:

- routes hard-constraint Buying and exploratory Browsing through distinct pipelines;
- stores conversation changes in event-sourced state using `ADD`, `REMOVE`, `NO_PREFERENCE`, and `RESET`;
- derives product intent signatures from visible catalog metadata;
- intersects exact constraints for high-precision Buying;
- retrieves broad, profile-aware and diverse candidates for Browsing;
- chooses clarification questions by expected information gain;
- adaptively activates BM25 plus word/character TF-IDF after an intent reset;
- handles intent overrides without leaking stale constraints.

The result runs locally with zero LLM/API calls, which improves efficiency, auditability, and reproducibility.

## How it was built

The Python agent uses:

- an append-only event log and deterministic reducer for session state;
- normalized reverse postings over features, details, material, color, price, and category;
- SQLite FTS5 BM25;
- scikit-learn sparse word and character TF-IDF;
- route-specific ranking and controlled diversity;
- the official deterministic evaluator and API contract;
- pytest for parser, state, information-gain, routing, retrieval, cache, split, and contract tests.

No target ASIN is hard-coded. The catalog is read-only, the evaluator is unmodified, and generated indexes are reproducible from visible fields.

## Results

On the official 200-session public evaluator:

- Hit Rate@10: **0.995**
- MRR: **0.7308**
- MTTC: **2.19**
- Efficiency: **0.881**
- TechnicalScore: **0.8929**
- Runtime tokens: **0**

The official starter scored Hit Rate@10 0.125, MRR 0.0680, MTTC 9.81, and TechnicalScore 0.1067.

A fixed 40-session pseudo-hidden split scored Hit Rate@10 0.975 and TechnicalScore 0.8703. No changes were made from inspecting individual pseudo-hidden sessions.

## Challenges

The hardest state problem was intent override. A full reset incorrectly loses a still-valid category, while a partial update can leave stale constraints behind. ConstraintGraph solves this with explicit intent generations and a preference-scoped reset that clears constraints/questions while retaining a compatible category.

We initially expected semantic models to be necessary. Our ablations showed otherwise: the frozen deterministic architecture achieved 0.975 pseudo-hidden Hit@10. Additional semantic complexity would add dependency, latency, hardware, and ranking-regression risk without measured evidence of an official-metric gain, so it was not justified before submission. Full lexical fusion also slightly hurt normal Buying, so the final system activates BM25 + TF-IDF only after an intent reset, improving held-out MRR while protecting exact precision.

## Accomplishments

- Improved public TechnicalScore from 0.1067 to 0.8929
- Converted 199 of 200 public sessions
- Ranked 127 targets first
- Achieved perfect public Hit@10 on Browsing, Intent Override, and Boundary scenarios
- Created a replayable event-state architecture with focused override tests
- Delivered deterministic local inference with no paid model dependency

## What was learned

An effective shopping agent needs intelligent orchestration, not complexity for its own sake. Explicit state, route-aware retrieval, information theory, and measured ablations produced a system that is reliable, inexpensive, and easy to audit.

## What is next

- Test against genuinely free-form human paraphrases
- Calibrate question answerability on a larger conversation corpus
- Add a separately validated lightweight semantic retriever for broad Browsing
- Learn fusion weights without using competition target exceptions
- Persist the catalog/BM25 index in a portable reproducible artifact

## Tools and technologies

Python 3.10, SQLite FTS5, NumPy, SciPy, scikit-learn, pytest, Git, VS Code/Codex, Amazon Reviews 2023-derived official competition data.

### APIs, models, and data

- Runtime APIs: none
- Runtime model/LLM: none; deterministic non-LLM agent
- Embedding API or service: none
- Required credentials or environment variables: none
- Optional local configuration: `CONSTRAINTGRAPH_MODE` and `CONSTRAINTGRAPH_INDEX_PATH`
- Retrieval/scoring source: only the frozen 50,000-product participant-visible competition catalog derived from Amazon Reviews 2023
- External preprocessing data: none

## Runtime, cost, and reproducibility

On the measured Windows/Python 3.10.10 setup with a prebuilt catalog-derived lexical cache, Agent initialization took 36.059 seconds. Across 40 isolated representative turns after four warm-ups, `respond()` latency was 387.504 ms median, 751.905 ms p95, and 766.808 ms p99. Each timed turn used a freshly reset session and `time.perf_counter()`; initialization and `reset()` were excluded from warm-turn timing.

Runtime uses the local CPU, makes zero external API calls, reports zero prompt and completion tokens, and has an estimated runtime model/API cost of $0. Hardware and full dependency versions are recorded in `benchmark_results.json`.

## Limitations

- Exact signatures benefit from the organizer's deterministic catalog-derived message policy and are less robust to unrestricted human paraphrases.
- Character TF-IDF handles lexical surface variation; it is not semantic understanding.
- One of 200 public Buying sessions remained a miss after architecture freeze.
- The cached startup still rebuilds the in-memory SQLite FTS5 table and is materially slower than an individual warm turn.
- Public and pseudo-hidden results do not guarantee performance on the final 800 sessions.

## Demonstration

The presentation runs the real Agent end to end. A built-in user-message-only override scenario displays actual intent events, current projected state, route, real candidate counts, production information-gain values, the selected question, and catalog-backed recommendations. No target or expected recommendation is embedded in the demo.

## Team

Solo participant. **Development:** AI-assisted with Codex. **Runtime:** deterministic, with zero LLM/API calls.
