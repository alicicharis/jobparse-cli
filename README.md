# jobparse-cli

A terminal tool that turns a pasted job ad into a structured object (title,
skills, seniority) using the raw Anthropic SDK.

## Setup

Requires Python 3.13 and [uv](https://docs.astral.sh/uv/).

```
uv sync
```

Create a `.env` file in the project root with your Anthropic API key:

```
ANTHROPIC_API_KEY=your-key-here
```

The key is loaded from `.env` on startup. A key already set in your shell
environment takes precedence.

## Running

```
uv run jobparse-cli
```

Paste a job ad, then end it with a line containing only `.`. Type `/quit` to
exit.

## Tests

```
uv run pytest
```
