# ConstraintGraph

ConstraintGraph is a zero-LLM, stateful conversational product-retrieval agent for the TechJam 2026 Shopping Copilot challenge. It turns conversation into typed intent events, narrows the official 50,000-product catalog with exact constraint signatures, asks questions by expected information gain, and adaptively fuses BM25 with word/character TF-IDF after intent changes.

## Result

On the official 200-session public evaluator:

| Metric | Official starter | ConstraintGraph |
|---|---:|---:|
| Hit Rate@10 | 0.125 | **0.995** |
| MRR | 0.0680 | **0.7308** |
| MTTC (lower is better) | 9.81 | **2.19** |
| Efficiency | 0.119 | **0.881** |
| TechnicalScore | 0.1067 | **0.8929** |
| Runtime LLM tokens | 0 | **0** |

The fixed 40-session pseudo-hidden split scored Hit@10 0.975, MRR 0.7059, MTTC 2.45, and TechnicalScore 0.8703. It was used only after the architecture was frozen.

These are public-development results, not a guarantee of private evaluation performance.

## Why it works

The evaluator reveals requirements derived from participant-visible catalog metadata. ConstraintGraph creates a reproducible “intent signature” for every product and maps normalized phrases back to candidate products. Conversation then becomes progressive uncertainty reduction rather than open-ended text generation.

```text
customer message
  -> deterministic event parser
  -> append-only event log
  -> projected current intent
  -> Buying or Browsing route
  -> exact / broad candidate generation
  -> adaptive lexical fusion
  -> Top 10 + information-gain question
```

### Event-sourced state

Changes are explicit and replayable:

```text
ADD(color=black)
REMOVE(color=black)
ADD(color=navy)
NO_PREFERENCE(brand)
RESET(preferences)
SET_CATEGORY(shoes)
```

This prevents old requirements from leaking through intent overrides and makes state transitions straightforward to test.

### Distinct routes

- **Buying:** hard constraints, posting-list intersection, precision-first exact ranking, and lexical recovery.
- **Browsing:** broad category/profile retrieval, controlled diversity, and clarification before transitioning to Buying.

### Information-gain clarification

The agent scores every answerable attribute by expected candidate-pool reduction. It asks the question that best partitions the current candidates, excluding attributes already asked or marked as having no preference.

### Adaptive retrieval

Exact signatures remain dominant for ordinary Buying. After an intent reset, when one replacement clue may be ambiguous, ConstraintGraph activates BM25 plus word and character TF-IDF. This policy improved held-out MRR without reducing ordinary Buying precision.

## Repository structure

```text
src/constraintgraph/       core agent, state, parser, routing, retrieval
starter/agent.py           organizer-compatible Agent entry point
evaluator/                 unmodified official evaluator
tests/                     unit, state, route, retrieval, and contract tests
scripts/                   split, index, evaluation, comparison, and demo tools
config/public_splits.json  deterministic target-free 120/40/40 manifest
reports/                   ablations, error analysis, Devpost copy, demo script
data/                      official data location (large/label files ignored)
```

## Requirements

- Python 3.10+
- Approximately 2 GB free RAM is recommended during index construction
- No GPU, external model, API key, vector database, or network connection at runtime

Tested locally with Python 3.10.10 on Windows and an NVIDIA GTX 1660 Ti. The runtime is CPU-based.

## Setup

```bash
python -m venv .venv
```

Activate the environment, then install:

```bash
python -m pip install -e ".[dev]"
```

Download `catalog.jsonl.gz` from the [official participant-kit release](https://github.com/TechJam2026/techjam-conversational-search/releases/tag/participant-kit), decompress it to `data/catalog.jsonl`, and copy the official public set to `data/public_set.jsonl`.

Verify the catalog against the organizer-provided SHA256 checksum before use. The catalog and session labels are deliberately excluded from Git.

## Prepare derived indexes

```bash
python scripts/prepare_indexes.py
```

This creates `indexes/lexical.joblib`, a local ignored artifact derived only from the official catalog. A clean build takes roughly 80 seconds on the tested machine; a cached Agent startup takes roughly 39 seconds including catalog parsing and the in-memory BM25 index.

## Test

```bash
python -m pytest
```

Current suite: 26 tests.

## Evaluate

Run the unmodified official evaluator:

```bash
python -m evaluator.local_evaluator --output artifacts/results.json
```

Run only frozen development and validation splits:

```bash
python scripts/run_split_evaluation.py \
  --splits development validation \
  --output artifacts/results_devval.json
```

PowerShell accepts the same command on one line.

Runtime modes can be selected through `CONSTRAINTGRAPH_MODE`:

- `adaptive` — default and selected architecture;
- `exact` — no TF-IDF/BM25 fusion or cache dependency;
- `hybrid` — lexical fusion for every Buying state, retained for ablation.

## Demo

```bash
python scripts/demo_session.py --sample-id public_0003
```

This runs one public session through the official evaluator while printing the customer messages, structured questions, and recommendations. It does not expose the target to the Agent.

## Reproducibility and integrity

- The official evaluator is copied unchanged from the participant kit.
- Catalog files, public labels, generated indexes, raw run logs, secrets, and videos are ignored.
- The runtime never reads ground-truth labels.
- The split manifest contains only public sample IDs and aggregate strata—not targets.
- All recommendations are valid catalog `parent_asin` values.
- The Agent reports zero prompt and completion tokens.

## Limitations

- Exact signatures benefit from the published deterministic catalog-derived message policy; unconstrained human paraphrases would require stronger semantic retrieval.
- One Buying session in the 200-session public set remained a miss after the architecture freeze.
- Boundary sessions sometimes need an extra turn after the user reports no preference.
- Sparse lexical index construction increases startup time and local disk use.
- The public set is small; private-session behavior is the meaningful final test.

## Reports

- [Ablations](reports/ABLATIONS.md)
- [Error analysis](reports/ERROR_ANALYSIS.md)
- [AI-assisted development](reports/AI_ASSISTED_DEVELOPMENT.md)
- [Devpost draft](reports/DEVPOST.md)
- [Demo script](reports/DEMO_SCRIPT.md)

## Solo contribution

Designed, implemented, tested, evaluated, and documented as a solo TechJam 2026 submission with AI-assisted development. Runtime inference is deterministic and LLM-free.

## Data attribution

See [DATA_ATTRIBUTION.md](DATA_ATTRIBUTION.md). The competition data is derived from Amazon Reviews 2023 by McAuley Lab at UCSD.
