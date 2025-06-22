# DevOps Maturity Assessment

![PyPI - Version](https://img.shields.io/pypi/v/devops-maturity)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/devops-maturity)
[![CI](https://github.com/devops-maturity/devops-maturity/actions/workflows/ci.yml/badge.svg)](https://github.com/devops-maturity/devops-maturity/actions/workflows/ci.yml)

## Overview

This repository contains a DevOps Maturity Assessment tool designed to help organizations evaluate their DevOps practices and identify areas for improvement. The assessment is based on a set of questions that cover various aspects of DevOps, including culture, automation, measurement, sharing, and security.

## Usage

### Launch Web Application

To launch the web application, you can use the following command:

```bash
uvicorn src.web.main:app --reload
```

Then open [http://localhost:8000](http://localhost:8000) in your browser to access the DevOps Maturity Assessment web interface.

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
