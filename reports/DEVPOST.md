# Devpost Draft

## Project name

ConstraintGraph

## Tagline

A zero-LLM shopping copilot that turns conversation into replayable intent events and asks the question that shrinks uncertainty fastest.

## Inspiration

Shopping conversations are not static queries. Requirements accumulate, disappear, and sometimes reverse completely. Most assistants hide that evolution inside a prompt. ConstraintGraph instead treats intent as inspectable state and product search as progressive uncertainty reduction.

## What it does

ConstraintGraph searches the official 50,000-product Amazon-derived catalog and recommends up to ten valid products on every turn. It:

- routes hard-constraint Buying and exploratory Browsing through distinct pipelines;
- stores conversation changes as typed events such as `ADD`, `REMOVE`, `NO_PREFERENCE`, and `RESET`;
- derives product intent signatures from visible catalog metadata;
- intersects exact constraints for high-precision Buying;
- retrieves broad, profile-aware and diverse candidates for Browsing;
- chooses clarification questions by expected information gain;
- activates BM25 plus word/character TF-IDF after an intent reset;
- runs locally with zero LLM/API tokens.

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

The main ranking challenge was deciding whether semantic complexity was warranted. Full lexical fusion slightly hurt normal Buying, so the final system activates it only after an intent reset. This improved held-out MRR while protecting exact precision.

## Accomplishments

- Improved public TechnicalScore from 0.1067 to 0.8929
- Converted 199 of 200 public sessions
- Ranked 127 targets first
- Achieved perfect public Hit@10 on Browsing, Intent Override, and Boundary scenarios
- Created a replayable event-state architecture with focused override tests
- Delivered deterministic local inference with no paid model dependency

## What was learned

The best “AI agent” architecture does not always require an LLM at runtime. Careful benchmark understanding, explicit state, information theory, and a layered retrieval system can be more reliable, cheaper, and easier to audit.

## What is next

- Test against genuinely free-form human paraphrases
- Calibrate question answerability on a larger conversation corpus
- Add a separately validated lightweight semantic retriever for broad Browsing
- Learn fusion weights without using competition target exceptions
- Persist the catalog/BM25 index in a portable reproducible artifact

## Tools and technologies

Python 3.10, SQLite FTS5, NumPy, SciPy, scikit-learn, pytest, Git, VS Code/Codex, Amazon Reviews 2023-derived official competition data.

## Team

Solo participant. AI-assisted development is documented transparently; runtime inference is LLM-free.
