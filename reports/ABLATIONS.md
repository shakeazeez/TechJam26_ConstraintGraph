# Ablation Study

## Selection rule

Architecture decisions were made on the frozen 120-session development and 40-session validation splits. The 40-session pseudo-hidden split was run only after the architecture was frozen. The final 200-session run was not followed by further ranking changes.

## Full-public milestones

| System | Hit@10 | MRR | MTTC | TechnicalScore |
|---|---:|---:|---:|---:|
| Official BM25 starter | 0.125 | 0.0680 | 9.81 | 0.1067 |
| Exact signatures + initial IG policy | 0.975 | 0.6332 | 2.01 | 0.8573 |
| **Final adaptive ConstraintGraph** | **0.995** | **0.7308** | **2.19** | **0.8929** |

The initial exact system had a slightly lower MTTC partly because misses receive turn 11 and its conversion distribution differed. The final system converted 199/200 sessions and substantially improved MRR.

## Development + validation route/fusion ablation

All rows below use the same 160 sessions.

| Variant | Hit@10 | MRR | MTTC | TechnicalScore | Decision |
|---|---:|---:|---:|---:|---|
| Separate routes + exact ranking | 1.000 | 0.7259 | 2.125 | 0.8953 | Strong base |
| Full BM25 + word/char TF-IDF for Buying | 1.000 | 0.7300 | 2.125 | 0.8965 | Improved override, hurt normal Buying |
| **Adaptive lexical fusion after reset** | **1.000** | **0.7370** | **2.125** | **0.8986** | Selected |

Adaptive fusion preserves exact ranking for ordinary Buying/Browsing and activates lexical fusion only after an intent generation changes.

## Selected variant by scenario: development + validation

| Scenario | Sessions | Hit@10 | MRR | MTTC |
|---|---:|---:|---:|---:|
| Buying | 64 | 1.000 | 0.7156 | 1.156 |
| Browsing | 64 | 1.000 | 0.7474 | 2.453 |
| Intent Override | 24 | 1.000 | 0.7747 | 3.625 |
| Boundary | 8 | 1.000 | 0.7118 | 2.750 |

## Frozen split generalization

| Split | Sessions | Hit@10 | MRR | MTTC | TechnicalScore |
|---|---:|---:|---:|---:|---:|
| Development | 120 | 1.000 | 0.7658 | 2.092 | 0.9079 |
| Validation | 40 | 1.000 | 0.6506 | 2.225 | 0.8707 |
| Pseudo-hidden | 40 | 0.975 | 0.7059 | 2.450 | 0.8703 |

The pseudo-hidden TechnicalScore is nearly identical to validation, supporting the decision to stop tuning.

## Semantic-model decision

We initially expected semantic models to be necessary. The ablations showed that the frozen deterministic system already achieved 0.975 pseudo-hidden Hit@10 and 0.8703 TechnicalScore. Additional semantic complexity would add a license/dependency surface, hardware variability, startup latency, and meaningful ranking-regression risk. Without measured evidence of an official-metric improvement, that complexity was not justified before submission.
