# jobparse-cli

## Vision

A terminal tool that turns a pasted job ad into a structured object (title, skills, seniority) using the raw Anthropic SDK. It's a learning project, built in phases. Phase 1 gets structured output from plain assistant text through prompting alone, so you can see how reliable that is before phase 2 brings in schema tooling.

## Stack

- Language / runtime: Python 3.13, managed with uv (`uv add`, `uv run`)
- LLM: raw `anthropic` SDK, sync client, no streaming
- Model: `claude-sonnet-5` - assistant prefill returns a 400 on this model, so don't use it
- Tests: pytest (dev dependency)

## Conventions

- Error handling: the CLI never crashes on a bad model reply or API error - it prints a one-line reason plus the raw text to stderr and keeps looping
- Testing: pytest covers pure functions only; no live or mocked API tests
- Structure: pure logic (parsing, validation) lives in small importable modules; the interactive loop stays in `main.py`
