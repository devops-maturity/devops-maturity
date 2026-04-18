# DevOps Maturity Assessment

**DevOps Maturity Assessment** helps teams turn broad DevOps, DevSecOps, and software supply-chain expectations into a measurable score, a prioritised gap list, and a shareable badge.

Use it when you want a quick baseline before a platform improvement programme, an audit-ready checklist for delivery practices, or a lightweight badge that makes engineering maturity visible in a README.

It provides both a **web UI** and a **CLI**, built on the [DevOps Maturity Specification](https://devops-maturity.github.io/) — a standardised set of guidelines for DevOps best practices.

## Why teams use it

- **Fast baseline** — answer a short weighted checklist and get a maturity level in minutes.
- **Clear next steps** — see category scores and prioritised missing practices instead of a raw pass/fail list.
- **Repository-aware AI mode** — optionally let an LLM inspect repository metadata, README content, and CI configuration.
- **Shareable signal** — publish a badge that makes DevOps maturity visible to users, contributors, and stakeholders.
- **Portable scoring model** — use the same criteria from the CLI, web UI, or a YAML file in automation.

## Features

| Feature | Description |
|---|---|
| Interactive CLI | Guided question-and-answer session in your terminal |
| YAML-driven mode | Reproducible baselines stored in source control and usable in CI pipelines |
| AI auto mode | Let an LLM (OpenAI, Anthropic, Gemini, or local Ollama) inspect your repository automatically |
| Web interface | Browser-based form with history, category breakdown, and improvement recommendations |
| Weighted scoring | Criteria carry different weights; the final score is a percentage with a named level |
| Category breakdown | Per-area scores surface exactly where to improve first |
| README badge | One-line Markdown snippet makes maturity visible to contributors and stakeholders |
| Assessment history | All runs are stored locally and comparable over time |

## Quick links

- [Installation](getting-started/installation.md)
- [Quick Start](getting-started/quickstart.md)
- [Assessment criteria reference](reference/criteria.md)
- [GitHub repository](https://github.com/devops-maturity/devops-maturity)
- [PyPI package](https://pypi.org/project/devops-maturity/)
