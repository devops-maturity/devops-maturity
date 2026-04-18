# CLI — Interactive mode

Interactive mode walks you through every criterion with a yes/no prompt.
It is the fastest way to get a baseline for any project, with no configuration files needed.

## Basic usage

```bash
dm assess
```

You will be prompted for a project name, then asked a yes/no question for each of the 20 criteria.

## Options

```bash
# Provide the project name upfront to skip the prompt
dm assess --project-name "my-api"

# Also attach a project URL to the saved record
dm assess --project-name "my-api" --project-url "https://github.com/org/my-api"
```

## What happens after the assessment

At the end of the session, results are printed to the terminal and saved to the local SQLite database for history tracking.

See [Example: terminal output](../examples/terminal-output.md) for a full sample of the output.

!!! tip
    `dm` is a convenient alias for `devops-maturity`, making it quicker to type.

## All flags

See [CLI flags reference](../reference/cli-flags.md#dm-assess) for the full list of options.
