# Documentation

Guides for running, configuring, and extending Expert Choice.

| Guide | What it covers |
| --- | --- |
| [Getting started](getting-started.md) | Install, API keys, first run |
| [Method](method.md) | What the five stages do and why |
| [Configuration](configuration.md) | YAML, CLI flags, ablations |
| [Architecture](architecture.md) | Package layout and data flow |
| [Extending](extending.md) | Add stages, schemas, backends, tasks, policies |
| [Evaluation](evaluation.md) | Metrics, traces, paper-compatible scoring |
| [Novelty and plausibility](novelty-and-plausibility.md) | Related work, what is new, whether it should work |
| [Troubleshooting](troubleshooting.md) | Common setup and run failures |

The paper’s teamwork harness lives in `third_party/teamwork`. We reuse its scenarios and L1 scoring. We never call its discussion `execute()` loop.
