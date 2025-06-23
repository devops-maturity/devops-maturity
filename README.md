# DevOps Maturity Assessment

[![PyPI - Version](https://img.shields.io/pypi/v/devops-maturity)](https://pypi.org/project/devops-maturity/)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/devops-maturity)
[![CI](https://github.com/devops-maturity/devops-maturity/actions/workflows/ci.yml/badge.svg)](https://github.com/devops-maturity/devops-maturity/actions/workflows/ci.yml)

## Overview

The DevOps Maturity Assessment is a tool designed to help you evaluate your DevOps practices and maturity level. It provides a structured questionnaire that covers various aspects of DevOps, allowing you to identify strengths and areas for improvement.

## Usage

### Launch Web Application

To launch the web application, you can use the following command:

```bash
git clone https://github.com/devops-maturity/devops-maturity.git
cd devops-maturity
pip install nox
nox -s preview
```

Then open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser to access the DevOps Maturity Assessment web interface.

### Use the CLI

To run the assessment in your terminal, use:

```bash
pip install devops-maturity
devops-maturity assess
```

This will prompt you to answer questions interactively and generate a badge based on your score.

## DevOps Maturity Specification

The assessment is based on the [DevOps Maturity Specification](https://devops-maturity.github.io/).

## License

This project is licensed under the [MIT License](LICENSE).
