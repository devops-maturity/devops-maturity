# DevOps Maturity Assessment

[![PyPI - Version](https://img.shields.io/pypi/v/devops-maturity)](https://pypi.org/project/devops-maturity/)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/devops-maturity)
[![CI](https://github.com/devops-maturity/devops-maturity/actions/workflows/ci.yml/badge.svg)](https://github.com/devops-maturity/devops-maturity/actions/workflows/ci.yml)
[![PASSING](https://img.shields.io/badge/DevOps%20Maturity-BRONZE-yellow.svg)](https://devops-maturity.github.io/)


## Overview

**DevOps Maturity Assessment** helps you evaluate and improve your DevOps practices.

It provides both a **web UI** and a **CLI**, built on the [DevOps Maturity Specification][Specification] — a standardized set of guidelines for DevOps best practices.

## Quick Start

### Run the CLI

Install from PyPI and start the interactive assessment:

```bash
pip install devops-maturity

# Start the assessment
devops-maturity assess

# Or use the shortcut command
dm assess
```

> [!TIP]
> `dm` is a convenient alias for `devops-maturity`, making it quicker to type.

You'll be guided through a series of questions and receive a maturity score, level, and badge. See it in action:

[![asciicast](https://asciinema.org/a/09BaFxLcu6J8xTrNCYQSlqDLz.svg)](https://asciinema.org/a/09BaFxLcu6J8xTrNCYQSlqDLz)

### Launch the Web Interface

To preview the web interface locally:

```bash
git clone https://github.com/devops-maturity/devops-maturity.git
cd devops-maturity
pip install nox
nox -s preview
```

Then visit http://127.0.0.1:8000 in your browser.

#### Web Interface Preview

Experience the full web interface workflow:

**1. Start Your Assessment**
![DevOps Maturity Assessment Home][WebHome]

**2. View Your Results**
![DevOps Maturity Assessment Results][WebResult]

**3. Track Assessment History**
![DevOps Maturity Assessment List][WebList]


## Show Your Support

If you find this tool helpful, please consider giving it a ⭐️ — your support helps others discover and adopt it.

Want to show your project aligns with the [DevOps Maturity Specification][Specification]? Add this badge to your README:

```markdown
[![DevOps Maturity](https://img.shields.io/badge/DevOps%20Maturity%20Specification-1.0.0-yellow)](https://devops-maturity.github.io/)
```

## License

This project is licensed under the [Apache License 2.0][LICENSE].

[LICENSE]: https://github.com/devops-maturity/devops-maturity/blob/main/LICENSE
[Specification]: https://devops-maturity.github.io/
[WebHome]: https://github.com/devops-maturity/devops-maturity/blob/main/docs/img/home.png?raw=true
[WebResult]: https://github.com/devops-maturity/devops-maturity/blob/main/docs/img/result.png?raw=true
[WebList]: https://github.com/devops-maturity/devops-maturity/blob/main/docs/img/list.png?raw=true
