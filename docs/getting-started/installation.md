# Installation

## Prerequisites

Python 3.10 or later is required. Check your version with:

```bash
python --version
```

## Install from PyPI

The recommended way to install the CLI is via pip:

```bash
pip install devops-maturity
```

After installation, both `devops-maturity` and its short alias `dm` are available on your PATH:

```bash
dm --version
```

## Install for local web development

To run the web interface locally, clone the repository and use `nox`:

```bash
git clone https://github.com/devops-maturity/devops-maturity.git
cd devops-maturity
pip install nox
nox -s preview
```

Then open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.

## Upgrade

To upgrade to the latest release:

```bash
pip install --upgrade devops-maturity
```
