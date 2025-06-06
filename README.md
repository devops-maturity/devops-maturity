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