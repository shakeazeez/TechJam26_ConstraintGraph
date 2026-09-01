# AI-Assisted Development Report

ConstraintGraph was built by a solo participant using Codex as an engineering collaborator. AI assistance was used for:

- comparing challenge feasibility against the available hardware and deadline;
- inspecting the official evaluator and API contract;
- formulating the catalog-signature hypothesis;
- generating and reviewing Python modules and tests;
- designing event-sourced state transitions and parser cases;
- implementing information-gain calculations;
- organizing evaluator ablations and fixed public splits;
- diagnosing aggregate scenario behavior;
- preparing reproducibility, error-analysis, Devpost, and demo documentation.

Every architectural change was validated by local tests and the unmodified official evaluator. The participant-visible catalog was the only retrieval/indexing source. Public target labels were never read by the runtime Agent or encoded into rules.

**Development:** AI-assisted with Codex. **Runtime:** deterministic, with zero LLM/API calls.

Runtime inference uses no external API, embedding service, or paid tokens. The system reports zero prompt and completion tokens. This separation is deliberate: AI accelerated development, while the submitted agent remains inexpensive, auditable, and reproducible.

## Development safeguards

- Local Git checkpoints after every working milestone
- `PLAN.md`, catalogs, labels, indexes, raw outputs, secrets, and media excluded from commits
- Fixed target-free 120/40/40 split manifest
- Pseudo-hidden evaluation only after architecture freeze
- Semantic model rejected when measured deterministic performance made its risk unjustified
- Official evaluator checksum compared with the untouched participant-kit copy during setup
