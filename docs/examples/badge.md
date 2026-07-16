# Example: adding a badge to your README

After every assessment the CLI prints a badge URL and a ready-to-paste Markdown snippet.
Add it to your project README to make the maturity level visible to contributors and stakeholders.

## Maturity badge

```markdown
[![DevOps Maturity](https://img.shields.io/badge/DevOps%20Maturity-SILVER-silver.svg)](https://devops-maturity.github.io/)
```

The badge level updates each time you re-run the assessment and update the URL in your README.

## Specification badge

Add this badge to indicate your project follows the DevOps Maturity Specification:

```markdown
[![DevOps Maturity](https://img.shields.io/badge/DevOps%20Maturity%20Specification-1.0.0-yellow)](https://devops-maturity.github.io/)
```

## Available levels

| Badge label | Score range |
|---|---|
| `WIP` | 0 – 39 % |
| `PASSING` | 40 – 59 % |
| `BRONZE` | 60 – 74 % |
| `SILVER` | 75 – 89 % |
| `GOLD` | 90 – 100 % |

See [Maturity levels](../reference/maturity-levels.md) for a full description of each level.
