# CLI — YAML config mode

The config mode reads answers from a `devops-maturity.yml` file instead of prompting interactively.
Store this file in your repository so that assessments are versioned, reviewable in pull requests, and repeatable in CI.

## Basic usage

```bash
# Uses devops-maturity.yml in the current directory by default
dm config
```

## Options

```bash
# Specify a custom file path
dm config --file path/to/my-baseline.yml

# Override the project name from the command line
dm config --file devops-maturity.yml --project-name "service-x"

# Override the project URL
dm config --file devops-maturity.yml --project-url "https://github.com/org/service-x"
```

## YAML file format

The file uses criterion IDs as keys and `true`/`false` as values.
See [Example: YAML config file](../examples/yaml-config.md) for a complete annotated example.

## Using in CI

Add a `dm config` step to your CI pipeline to track the maturity score over time alongside each release.

Example GitHub Actions step:

```yaml
- name: Run DevOps Maturity assessment
  run: |
    pip install devops-maturity
    dm config --file devops-maturity.yml
```

!!! tip
    Commit `devops-maturity.yml` to your repository and update it whenever you adopt a new practice. This makes maturity progress visible in your git history.

## All flags

See [CLI flags reference](../reference/cli-flags.md#dm-config) for the full list of options.
