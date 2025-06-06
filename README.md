# DevOps Maturity Assessment

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
python -m cli.main check
```

This will prompt you to answer questions interactively and generate a badge based on your score.

## Assessment Categories & Criteria

The assessment covers the following categories and criteria:

### CI/CD Basics
- Build a specific branch (must have)
- Build upon pull request (must have)
- Docker (nice to have)

### Quality
- Automated Testing: Functional testing (must have)
- Automated Testing: Performance testing (must have)
- Code Coverage (nice to have)
- Accessibility Testing (nice to have)

### Security
- Security scan (must have)
- License scan (nice to have)

### Secure Supply Chain
- Documented Build Chain (must have)
- CICD as coded (must have)
- Artifacts are signed (nice to have)
- Artifactory download for Package Managers (nice to have)

### Reporting
- Email/Slack reporting functionality

### Analysis
- Quality Gate (nice to have)
- Code Lint (nice to have)
- Static code analysis (nice to have)
- Dynamic code analysis (nice to have)

## Badge Levels

Your score will generate one of the following badges:
- **WIP**: 0%
- **PASSING**: 1–49%
- **BRONZE**: 50–69%
- **SILVER**: 70–89%
- **GOLD**: 90–100%
