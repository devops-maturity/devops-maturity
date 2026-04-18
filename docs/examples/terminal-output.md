# Example: terminal output

Below is an example of what the CLI prints after a completed assessment.

```
Your score: 72.5%
Your maturity level: SILVER
Badge URL: https://img.shields.io/badge/DevOps%20Maturity-SILVER-silver.svg

Category Breakdown:
  Basics                 [████████████████░░░░] 80%
  Quality                [████████████░░░░░░░░] 60%
  Security               [████████████████░░░░] 80%
  Supply Chain Security  [████████████░░░░░░░░] 60%
  Analysis               [████████░░░░░░░░░░░░] 40%
  Reporting              [████████████████░░░░] 80%

Improvement Recommendations:

  Quality:
    [D203] Performance Testing (🟡)
         Include automated performance, load, or stress tests in your CI/CD pipeline.
    [D205] Accessibility Testing (🟡)
         Automate accessibility checks (e.g., WCAG compliance) in CI.

  Analysis:
    [D501] Static Code Analysis (🟡)
         Run static analysis tools (SAST) to detect bugs, code smells, and security issues.
    [D502] Dynamic Code Analysis (🟡)
         Run dynamic analysis or fuzzing tools that test the application at runtime.

Next steps:
  1. Commit a devops-maturity.yml baseline for repeatable reviews.
  2. Add the Markdown badge to your README to make progress visible.
  3. Re-run the assessment after improving the missing practices.

Assessment saved to database.
```
