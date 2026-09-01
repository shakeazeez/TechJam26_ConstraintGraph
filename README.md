# ConstraintGraph

ConstraintGraph is an adaptive shopping agent for the TechJam 2026 Shopping Copilot challenge. It turns evolving conversations into structured intent, routes Buying and Browsing differently, and asks the question that reduces uncertainty fastest. It is the intelligent orchestration layer between conversation state and product retrieval—not simply a graph search.

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

The simulated customer progressively reveals shopping requirements generated from participant-visible catalog metadata. ConstraintGraph maps these requirements to product intent signatures and progressively reduces the candidate space. Conversation becomes structured uncertainty reduction rather than a longer search string.

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

### Core innovations

- **Event-sourced conversational state:** every addition, removal, reset, and no-preference statement is replayable.
- **Buying vs Browsing routing:** hard-constraint purchase intent and exploratory discovery remain genuinely different pipelines.
- **Information-gain clarification:** the next question is the one expected to reduce the candidate pool most.
- **Exact constraint retrieval:** normalized product intent signatures make explicit requirements dominant.
- **Adaptive BM25 + TF-IDF:** lexical fusion activates where ambiguity warrants it instead of weakening every result.
- **Intent-override handling:** preference resets and category changes cannot silently leak stale requirements.

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

### Evidence-based model choice

We initially expected semantic models to be necessary. The frozen deterministic architecture already achieved 0.975 Hit@10 on the pseudo-hidden split. Adding semantic complexity would introduce dependency, latency, hardware, and ranking-regression risk without measured evidence that it improved the official metrics, so it was not justified before submission. Zero runtime LLM/API calls are therefore an efficiency and reproducibility result—not the project's main claim.

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

Tested locally with Python 3.10.10 on Windows. The measured runtime is CPU-based; the machine has an NVIDIA GTX 1660 Ti, but ConstraintGraph does not use it.

No environment variable is required. Two optional variables are supported:

- `CONSTRAINTGRAPH_MODE`: `adaptive` (default), `exact`, or `hybrid`;
- `CONSTRAINTGRAPH_INDEX_PATH`: path to the reproducible catalog-derived lexical cache.

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

This creates `indexes/lexical.joblib`, a local ignored artifact derived only from the official catalog. Build time varies by machine. The reproducible benchmark below separately reports cached Agent startup, including catalog parsing and the in-memory BM25 index.

## Test

```bash
python -m pytest
```

Current suite: 35 tests. A clean checkout without the deliberately excluded official
`data/public_set.jsonl` runs 33 tests and skips the two split-validation tests in
`tests/test_splits.py`. Installing the official public set enables all 35 tests.

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
python -m constraintgraph.demo --interactive
python -m constraintgraph.demo --scenario override
python -m constraintgraph.demo --scenario browsing
python -m constraintgraph.demo --scenario adaptive-reset
python -m constraintgraph.demo --scenario override --record-json artifacts/demo_override.json
```

Demo mode visualizes the production parser events, projected intent, route and route reason, active retrieval components, real candidate collections, production information-gain utilities, selected clarification, and catalog-backed Top recommendations. Use `--show-all-results` for all returned products and `--debug-ranking` for available production score components.

The built-in override scenario contains user messages only. It does not contain a target, expected events, expected products, or expected scores. **Demo diagnostics expose existing internal decisions and do not alter ranking behavior.** The demo is isolated from the official evaluator and emits nothing from the default Agent path.

## Latency benchmark

```bash
python -m constraintgraph.benchmark
```

The checked-in [benchmark result](benchmark_results.json) was measured on Windows with Python 3.10.10, an Intel64 Family 6 Model 158 CPU, 17,012,723,712 bytes of RAM, and a prebuilt lexical cache:

| Measurement | Result |
|---|---:|
| Cached cold Agent initialization | 36.059 s |
| Warm `respond()` median | 387.504 ms |
| Warm `respond()` p95 | 751.905 ms |
| Warm `respond()` p99 | 766.808 ms |
| Measured turns | 40 |

The benchmark uses `time.perf_counter()`. It times Agent construction separately, performs four warm-up turns, then rotates four representative Buying, Browsing, direct-constraint, and reset/override messages. Every timed turn uses a freshly reset session; `reset()` is outside the timed region. No network operation occurs. These figures describe this machine and are not a universal latency guarantee.

## Runtime and Cost

- Runtime: local CPU; no GPU execution
- Cold startup/index load: 36.059 s on the measured cached setup
- Warm per-turn latency: 387.504 ms median, 751.905 ms p95 across the methodology above
- External runtime API calls: 0
- Runtime LLM prompt tokens: 0
- Runtime LLM completion tokens: 0
- Estimated runtime model/API cost: $0
- Model choice: deterministic non-LLM retrieval and ranking

## Submission check

```bash
python -m constraintgraph.submission_check
python scripts/audit_submission.py
```

The first command performs read-only Agent contract, catalog-validity, uniqueness, session-isolation, catalog-mutation, documentation, and obvious secret-filename checks. It forces exact mode for its smoke test so it never creates a cache. The second scans tracked files for banned artifacts, oversized files, and common secret patterns.

Capture non-secret final-run evidence with:

```bash
python -m constraintgraph.capture_environment --output artifacts/environment_capture.json
```

## Reproducibility and integrity

- The official evaluator is copied unchanged from the participant kit.
- Catalog files, public labels, generated indexes, raw run logs, secrets, and videos are ignored.
- The runtime never reads ground-truth labels.
- The split manifest contains only public sample IDs and aggregate strata—not targets.
- All recommendations are valid catalog `parent_asin` values.
- The Agent reports zero prompt and completion tokens.

## Final Evaluation Procedure

1. Check out the Git commit submitted by the Devpost deadline.
2. Record the frozen commit with `git rev-parse HEAD` and confirm the worktree state.
3. Install dependencies exactly as documented above and record Python, dependency, OS, CPU, RAM, and environment details.
4. Prepare the catalog-derived index without using any final-session labels.
5. Run the unmodified official final evaluator against the frozen commit.
6. Preserve the generated `results.json`, including per-session results.
7. Preserve the commit hash, Python/dependency versions, hardware, environment, exact execution command, benchmark/runtime disclosure, token usage, and estimated cost.
8. Do not modify the Agent, parser, indexes, model configuration, ranking, prompts, or any other solution component after final sessions are released.

The final release may use its own dataset argument or package command. Follow that released unmodified evaluator exactly; for the current public harness, the command is:

```bash
python -m evaluator.local_evaluator --output artifacts/results.json
```

## Submission Reproducibility Checklist

- [x] Agent entry point documented
- [x] Python requirement and measured version documented
- [x] Dependencies and installation documented
- [x] Official evaluator command documented
- [x] Required environment variables documented (none; optional variables listed)
- [x] Valid catalog-only `parent_asin` values tested
- [x] Session isolation tested
- [x] Runtime/API/token usage and estimated cost disclosed
- [x] Reproducible latency benchmark documented
- [x] Limitations and future work documented
- [x] AI-assisted development disclosed
- [x] Official evaluator verified unmodified against the participant kit

## Public submission scope

Submit the tracked Python source, `starter/`, dependency manifests, config manifest, tests, documentation, reports, data attribution, `benchmark_results.json`, and `SUBMISSION_AUDIT.md`. The official rules permit lightweight required assets; this repository instead documents how to reproduce its generated index.

Do not publish or submit local `.env` files, credentials, private keys, unreleased/final evaluation labels, raw public labels unless the organizer explicitly requests them, the 60 MB catalog, the 172 MB generated lexical cache, raw evaluator result logs, local `artifacts/`, planning notes, editor state, caches, videos, or the outer project ZIP. These are excluded by `.gitignore`; ambiguous files should be reviewed manually rather than deleted automatically.

## Limitations

- Exact signatures benefit from the published deterministic catalog-derived message policy; unconstrained human paraphrases would require stronger semantic retrieval.
- One Buying session in the 200-session public set remained a miss after the architecture freeze.
- Boundary sessions sometimes need an extra turn after the user reports no preference.
- Sparse lexical index construction increases startup time and local disk use.
- The public set is small; private-session behavior is the meaningful final test.

## Future work

- Validate against genuinely free-form human shopping paraphrases.
- Calibrate clarification answerability on a separate conversation corpus.
- Evaluate a lightweight semantic retriever only on a separately frozen, target-free protocol.
- Persist more of the catalog/BM25 startup work in a portable reproducible artifact.

## Reports

- [Ablations](reports/ABLATIONS.md)
- [Error analysis](reports/ERROR_ANALYSIS.md)
- [AI-assisted development](reports/AI_ASSISTED_DEVELOPMENT.md)
- [Devpost draft](reports/DEVPOST.md)
- [Demo script](reports/DEMO_SCRIPT.md)

## Solo contribution

Designed, implemented, tested, evaluated, and documented as a solo TechJam 2026 submission. **Development:** AI-assisted with Codex. **Runtime:** deterministic, with zero LLM/API calls.

## Data attribution

See [DATA_ATTRIBUTION.md](DATA_ATTRIBUTION.md). The competition data is derived from Amazon Reviews 2023 by McAuley Lab at UCSD.
