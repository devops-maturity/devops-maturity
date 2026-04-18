# Assessment criteria

The tool evaluates 20 criteria across six categories.
Each criterion has a weight: **Required (1.0)** criteria carry full weight; **Recommended (0.5)** criteria carry half weight.

## Basics

| ID | Criterion | Weight | Description |
|---|---|---|---|
| D101 | Branch Builds | Required | Trigger an automated build on every branch push to catch issues before they reach main. |
| D102 | Pull Request Builds | Required | Run a full build and test suite on every pull request to prevent broken code from merging. |
| D103 | Clean Build Environments | Recommended | Use ephemeral, isolated environments (e.g., containers) for reproducible builds. |

## Quality

| ID | Criterion | Weight | Description |
|---|---|---|---|
| D201 | Unit Testing | Required | Automated unit tests validate individual components and catch regressions quickly. |
| D202 | Functional Testing | Required | Integration or end-to-end tests validate system behaviour from a user's perspective. |
| D203 | Performance Testing | Recommended | Automated load/stress tests prevent performance regressions from reaching production. |
| D204 | Code Coverage | Recommended | Measure coverage and enforce a minimum threshold to identify untested code paths. |
| D205 | Accessibility Testing | Recommended | Automate WCAG compliance checks in CI to ensure usability for all users. |

## Security

| ID | Criterion | Weight | Description |
|---|---|---|---|
| D301 | Vulnerability Scanning | Required | Scan code and dependencies for known vulnerabilities using SAST/SCA tools (e.g., Snyk, CodeQL). |
| D302 | License Scanning | Recommended | Ensure third-party dependency licences are compatible with your project's requirements. |

## Supply Chain Security

| ID | Criterion | Weight | Description |
|---|---|---|---|
| D401 | Documented Build Process | Required | Document how your project is built, tested, and deployed for reproducibility and onboarding. |
| D402 | CI/CD as Code | Required | Define pipelines as code (e.g., YAML, Jenkinsfile) stored in version control. |
| D403 | Artifact Signing | Recommended | Cryptographically sign build artifacts (e.g., Sigstore/Cosign) to verify integrity. |
| D404 | Dependency Pinning | Recommended | Pin all dependency versions via lock files to ensure reproducible builds. |
| D405 | SBOM Generation | Recommended | Generate a Software Bill of Materials (SBOM) for each release for transparency and compliance. |

## Analysis

| ID | Criterion | Weight | Description |
|---|---|---|---|
| D501 | Static Code Analysis | Recommended | Run SAST tools (e.g., SonarQube, Semgrep) to detect bugs and security issues without executing code. |
| D502 | Dynamic Code Analysis | Recommended | Run DAST or fuzzing tools at runtime (e.g., OWASP ZAP) to catch vulnerabilities static analysis may miss. |
| D503 | Code Linting | Recommended | Enforce code style and quality rules via linters (e.g., ESLint, Flake8, Ruff) to reduce review friction. |

## Reporting

| ID | Criterion | Weight | Description |
|---|---|---|---|
| D601 | Notifications & Alerts | Required | Send automated notifications for build failures and security alerts (e.g., Slack, email, PagerDuty). |
| D602 | Attached Reports | Recommended | Attach test results, coverage reports, and analysis outputs as CI artifacts for review. |
| D603 | Compliance Mapping & Auditability | Recommended | Map pipeline controls to frameworks (e.g., SOC 2, ISO 27001) and maintain audit trails. |
