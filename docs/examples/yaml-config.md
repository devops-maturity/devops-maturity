# Example: YAML config file

Create a `devops-maturity.yml` file in your repository root and commit it.
Each key is a criterion ID; set it to `true` if the practice is in place or `false` if it is not.

```yaml
project_name: my-api
project_url: https://github.com/org/my-api

# Basics
D101: true   # Branch Builds
D102: true   # Pull Request Builds
D103: false  # Clean Build Environments

# Quality
D201: true   # Unit Testing
D202: true   # Functional Testing
D203: false  # Performance Testing
D204: true   # Code Coverage
D205: false  # Accessibility Testing

# Security
D301: true   # Vulnerability Scanning
D302: false  # License Scanning

# Supply Chain Security
D401: true   # Documented Build Process
D402: true   # CI/CD as Code
D403: false  # Artifact Signing
D404: true   # Dependency Pinning
D405: false  # SBOM Generation

# Analysis
D501: false  # Static Code Analysis
D502: false  # Dynamic Code Analysis
D503: true   # Code Linting

# Reporting
D601: true   # Notifications & Alerts
D602: false  # Attached Reports
D603: false  # Compliance Mapping & Auditability
```

Run the assessment against this file:

```bash
dm config --file devops-maturity.yml
```

!!! tip
    Omitted criterion IDs default to `false`. You only need to list the criteria you want to explicitly set.
