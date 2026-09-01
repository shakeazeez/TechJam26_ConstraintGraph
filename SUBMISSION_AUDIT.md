# ConstraintGraph Submission Audit

Audit date: 2026-09-01. Organizer-controlled files were compared against the adjacent participant-kit originals before implementation. The evaluator, contract, configuration, competition specification, submission rules, and final-evaluation FAQ are byte-for-byte unchanged.

Status vocabulary: **PASS**, **NEEDS UPDATE**, **MISSING**, **NOT APPLICABLE**.

| Requirement | Source | Status | Evidence / File | Action |
|---|---|---|---|---|
| One Python entry file exports `Agent` | `docs/submission_rules.md` | PASS | `starter/agent.py` | None |
| Local helper modules included | `docs/submission_rules.md` | PASS | `src/constraintgraph/` | None |
| `reset(session_id, user_profile)` signature | `docs/submission_rules.md`; `docs/agent_api_contract.json` | PASS | `constraintgraph.agent.Agent`; contract test | None |
| `respond(session_id, user_message, turn, top_k)` signature | `docs/submission_rules.md`; `docs/agent_api_contract.json` | PASS | `constraintgraph.agent.Agent`; contract test | None |
| `message` is always a string | `docs/submission_rules.md`; API contract | PASS | `agent.py`; diagnostics/contract tests | None |
| `ask_attribute` is allowed or null | `docs/submission_rules.md`; API contract | PASS | `QUESTION_TEXT`; contract tests | None |
| Recommendations are ordered | `docs/submission_rules.md` | PASS | retrievers return deterministic ranked tuples | None |
| Recommendations use valid frozen-catalog `parent_asin` values | `docs/final_evaluation_faq.md` section 4 | PASS | `CatalogIndex`; `submission_check` | None |
| No duplicate recommendations | `docs/final_evaluation_faq.md` section 5 | PASS | ranked candidate IDs are unique; `submission_check` | None |
| Agent honors requested Top K | API contract; `docs/evaluation_config.json` | PASS | `agent.py`; `submission_check` | None |
| Usage values are non-negative | `docs/submission_rules.md`; API contract | PASS | zero integer counts in `agent.py` | None |
| Setup instructions | `docs/submission_rules.md` | PASS | `README.md` Setup | Expanded |
| Dependency installation instructions | `docs/submission_rules.md` | PASS | `pyproject.toml`, `requirements.txt`, README | None |
| Python requirement and measured version | `docs/submission_rules.md`; FAQ section 3 | PASS | `pyproject.toml`; README; `benchmark_results.json` | Clarified |
| Official harness command | `docs/submission_rules.md`; FAQ section 7 | PASS | README Evaluate / Final Evaluation Procedure | Clarified |
| Required environment-variable names | `docs/submission_rules.md`; FAQ section 2 | PASS | README Requirements | Explicitly states none required; lists two optional variables |
| Method description | `docs/submission_rules.md` | PASS | README Why it works; `reports/DEVPOST.md` | None |
| Model choice disclosure | `docs/submission_rules.md`; FAQ section 2 | PASS | README Runtime and Cost; Devpost | Clarified deterministic non-LLM choice |
| Limitations disclosure | `docs/submission_rules.md` | PASS | README and Devpost Limitations | Expanded |
| Latency disclosure | `docs/submission_rules.md`; FAQ section 3 | PASS | `benchmark_results.json`; README | Added reproducible benchmark |
| Token usage disclosure | `docs/submission_rules.md`; FAQ section 7 | PASS | README; Devpost; Agent usage | None |
| Estimated model/API cost | `docs/submission_rules.md`; FAQ section 3 | PASS | README Runtime and Cost; Devpost | Added explicit `$0` |
| Hardware disclosure | FAQ section 3 | PASS | `benchmark_results.json`; README | Added CPU/RAM context |
| Network/external service disclosure | FAQ sections 2-3 | PASS | README; Devpost | Explicitly zero runtime calls |
| External fallback disclosure | FAQ section 2 | NOT APPLICABLE | No external runtime dependency | Stated |
| Frozen 50,000-product catalog is retrieval/scoring space | FAQ section 4; competition specification | PASS | `catalog.py`; data README; submission check | Verified 50,000 rows |
| Catalog-derived artifacts use permitted visible fields | FAQ section 4 | PASS | `catalog.py`, `lexical.py`, `scripts/prepare_indexes.py` | None |
| External/public preprocessing data disclosed | FAQ section 4 | NOT APPLICABLE | `DATA_ATTRIBUTION.md`; Devpost | No external preprocessing data used |
| No fabricated or replacement ASINs | FAQ section 4 | PASS | all IDs resolve through loaded catalog | Checked |
| Per-session state isolation | FAQ section 5 | PASS | keyed `sessions`; existing and new tests | Strengthened tests |
| Shared indexes do not contain conversational state | FAQ section 5 | PASS | catalog/retriever/index objects shared; state stored in `SessionState` | Checked |
| Demonstration shows a complete multi-turn session | FAQ section 7; competition specification Final Deliverables | PASS | `constraintgraph.demo`; `reports/DEMO_SCRIPT.md` | Added real three-turn scenario |
| UI does not replace runnable Agent | FAQ section 7 | PASS | demo is separate; `starter/agent.py` remains entry point | None |
| Demo video duration specified | Organizer files inspected | NOT APPLICABLE | No duration found locally | Confirm on Devpost form manually |
| Demo hosting/public/unlisted/narration/URL rules specified | Organizer files inspected | NOT APPLICABLE | No such rules found locally | Confirm on Devpost form manually |
| Official evaluator unmodified | `docs/submission_rules.md`; FAQ sections 1 and 5 | PASS | SHA256 matches participant kit | Reverified |
| Official API contract/config/rules unmodified | Submission rules and participant kit | PASS | SHA256 matches participant kit | Reverified |
| Evaluator stdout remains free of demo diagnostics | Output integrity requirement | PASS | diagnostics disabled by default; silence test | Added test |
| Final commit frozen at Devpost deadline | FAQ section 1; submission rules | NEEDS UPDATE | README Final Evaluation Procedure | Procedure documented; participant must execute |
| Final evaluator run uses released unmodified package | FAQ section 1 | NEEDS UPDATE | README Final Evaluation Procedure | Final package not yet available |
| Preserve final `results.json` with per-session data | FAQ section 1 | NEEDS UPDATE | README Final Evaluation Procedure | Participant must execute after final release |
| Preserve commit/environment/execution evidence | FAQ sections 1 and 3 | PASS | `capture_environment`; README | Added helper/procedure |
| Do not adapt after final sessions release | FAQ section 1 | PASS | README procedure; AI safeguards | Explicitly documented |
| No unreleased labels or organizer-only files in submission | `docs/submission_rules.md` | PASS | tracked-file audit; `.gitignore` | None |
| No API keys or secrets | `docs/submission_rules.md` | PASS | `.gitignore`; tracked secret scan; `audit_submission.py` | None |
| No privileged-host dependency | `docs/submission_rules.md` | PASS | local Python/SQLite/scikit-learn stack | None |
| No undeclared external service | `docs/submission_rules.md` | PASS | none used | None |
| Large generated assets documented rather than committed | FAQ section 4 | PASS | index ignored; preparation command documented | None |
| AI-assisted development disclosed | Devpost deliverable/team transparency | PASS | `reports/AI_ASSISTED_DEVELOPMENT.md`; README; Devpost | Preserved and clarified |
| Architecture, libraries, data, results, future work, team | Competition specification Final Deliverables | PASS | README; `reports/DEVPOST.md` | Expanded |

## Organizer-controlled integrity hashes

| File | SHA256 | Matches participant kit |
|---|---|---|
| `evaluator/local_evaluator.py` | `84EA899707452DE249CA62ABEE77C4B40AB7A3139B5CC798AC30C9F521F91B30` | Yes |
| `docs/submission_rules.md` | `3AAB3A4FB21F17B33CEE404FD123AF8E4D016DD202A538A95A9F5E704DCFAE65` | Yes |
| `docs/final_evaluation_faq.md` | `93C089D6A1A425727A497E23B1C034261771657C7AFA53B061A588F026774D06` | Yes |
| `docs/competition_specification.md` | `06ECBCC6445102C7823091D33645C2B9C3F7FFC74D376FD9D4DA0FD28249D391` | Yes |
| `docs/agent_api_contract.json` | `347AC1361DEE2B48C0554F4E43D1E2D131EC32A9219574B114C980B9D2F7C9A7` | Yes |
| `docs/evaluation_config.json` | `BBF22EF47C4837C268031D0B0A7DACB0BCAB2C157F3CE01EEE37612A7511097D` | Yes |

## Demo-video rules actually found

The local organizer files require at least one complete multi-turn session and state that a UI is optional and does not replace the runnable Agent. No local organizer document specifies a duration, hosting platform, public/unlisted status, narration requirement, URL format, or extra prohibited content. Check the live Devpost form before final submission because it may contain platform-specific fields not mirrored in the participant kit.

## Evidence caveats and manual items

- `results.json` at the repository root is an ignored stale weak-starter run; `results_exact.json` is an ignored intermediate exact run. Neither is final evidence. The reproduced final public run is `artifacts/baseline_public_results.json` and matches `reports/metrics.json`.
- The 800-session final package is unreleased in the inspected workspace. Final-package execution and preservation cannot be completed before release.
- The worktree contains pre-existing user documentation edits plus the changes from this audit. Review, commit, push, and submit the resulting commit hash manually.

## Overall status

**READY WITH WARNINGS**: code, contract, tests, evaluator integrity, runtime disclosure, and documented deliverables pass. Manual work remains to confirm any Devpost-form-only video fields, create the final clean commit, and later run/preserve the unreleased final evaluator from that frozen commit.
