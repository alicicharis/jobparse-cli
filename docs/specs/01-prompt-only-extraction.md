# Prompt-only job ad extraction

## Why

**Backlog item:** Item 1: Prompt-only job ad extraction - see `docs/backlog.md`

Phase 1 of the project: get structured output (`title`, `skills`, `seniority`) from plain assistant text using prompting alone, so the reliability of that approach is visible before phase 2 adds schema tooling.

## What

`uv run main.py` starts a loop. You paste a job ad, end it with a line containing only `.`, and get back either pretty-printed JSON on stdout or a one-line failure reason plus the raw model text on stderr. The loop keeps going after every result, successful or not. `/quit`, Ctrl-C or Ctrl-D exits cleanly.

Done when: `uv run pytest` passes, a real ad prints valid JSON, and a bad reply or API error prints a reason without crashing the loop.

## Context

**Relevant files:**

- `main.py` - currently a hello-world stub; becomes the interactive loop and API call
- `pyproject.toml` - uv project, no dependencies yet, no `[build-system]` (the project is not installed, so tests need `pythonpath` set)
- `AGENTS.md` - stack and conventions (read it)

**New files:**

- `reply.py` - pure parse + validate of the model's reply text
- `prompt.py` - the system prompt constant
- `tests/test_reply.py` - pytest tests for `reply.py`

**Key decisions already made:**

- Setup: `uv add anthropic`, `uv add --dev pytest`. API key comes from the environment (`anthropic.Anthropic()` with no args)
- Input: multi-line paste ended by a line containing only `.`. `/quit`, Ctrl-C or Ctrl-D exits cleanly
- No conversation history: each ad is an independent call (system prompt + one user message holding the ad)
- Structured output comes from plain assistant text only: no Pydantic, no `output_config.format`, no tool use, no assistant prefill (prefill returns a 400 on this model)
- No re-asking on parse or validation failure. Leave the SDK's default network retries on (don't pass `max_retries`)
- Request: `model="claude-sonnet-5"`, `max_tokens=2048`, `output_config={"effort": "low"}`. Omit `thinking` entirely - Sonnet 5 runs adaptive thinking by default. Sync client, no streaming
- System prompt: describes the schema, gives one example (an ad in, the JSON out), and tells the model to reply with the JSON object only, no code fences
- Schema:
  - `title`: string as written in the ad, or `null` if absent
  - `skills`: flat list of strings in the ad's wording, `[]` if none
  - `seniority`: one of `intern|junior|mid|senior|lead|principal`, or `null`
  - All three keys are always present
- Non-job input is deliberately not addressed in the prompt. Whatever comes back goes through normal parse/validation
- Response handling order: check `stop_reason` first (`max_tokens` and `refusal` are failures), then join the text blocks, then strict `json.loads(text.strip())`. Fenced or prose-wrapped JSON is a failure
- Hand-written validation: top level is a dict, exactly the three keys (no missing, no extra), correct types, `seniority` in the allowed set or `null`
- Success output: the parsed dict re-serialized with `json.dumps(obj, indent=2)` to stdout
- Tests: parse + validate only, covering the agreed cases (see T1)
- Assumption: `title` accepts `null`. The backlog's "`null`/`[]` when absent" rule is read as applying to `title` as well as `seniority`

## Constraints

**Must:**

- Keep pure logic in `reply.py` and the loop, input reading and API call in `main.py` (AGENTS.md structure rule)
- Never crash on a bad reply or an API error: print a one-line reason to stderr, then the raw text if there is any, and keep looping
- Use `anthropic` SDK attributes as documented: `response.stop_reason`, `response.content` blocks with `.type == "text"` and `.text`. Thinking blocks also appear in `content` - skip them when joining text

**Must not:**

- Add dependencies beyond `anthropic` and dev `pytest`
- Add mocked or live API tests
- Add retries, re-prompting, fence-stripping or any other "repair" of the reply
- Use em dashes in code, comments or output

**Out of scope:**

- Schema tooling, Pydantic, structured outputs, tool use (backlog item 2)
- Handling non-job input specially
- Conversation history, streaming, config flags or CLI arguments

## Tasks

### T1: Reply parser and validator with tests

**Do:**

- `uv add --dev pytest`
- Add to `pyproject.toml` so tests can import root-level modules:
  ```toml
  [tool.pytest.ini_options]
  pythonpath = ["."]
  ```
- Create `reply.py` with one public function `parse_reply(text: str) -> dict`:
  - `json.loads(text.strip())`. On `json.JSONDecodeError`, raise `ValueError(f"invalid JSON: {e}")` from it
  - Validate as described under "Hand-written validation" above. Every failure raises `ValueError` with a short one-line reason naming the problem (e.g. `"missing key: skills"`, `"unexpected key: location"`, `"skills must be a list of strings"`, `"seniority must be one of intern, junior, mid, senior, lead, principal or null"`)
  - Hold the allowed seniority values in a tuple and check `isinstance(value, str)` before membership, so a list or dict value produces a `ValueError`, not a `TypeError`
  - Return the parsed dict unchanged on success
- Create `tests/test_reply.py` with one test per agreed case:
  - valid object returns the dict
  - JSON wrapped in a ` ```json ` fence raises `ValueError`
  - missing key raises `ValueError`
  - wrong type (e.g. `skills` as a string) raises `ValueError`
  - out-of-range seniority (e.g. `"staff"`) raises `ValueError`

**Files:** `pyproject.toml`, `uv.lock`, `reply.py`, `tests/test_reply.py`

**Verify:** `uv run pytest` - 5 tests pass

### T2: System prompt and interactive loop

**Do:**

- `uv add anthropic`
- Create `prompt.py` with a `SYSTEM_PROMPT` string constant containing:
  - the task (extract fields from a job ad)
  - the schema with the rules from "Schema" above, including `null`/`[]` for absent values and the exact seniority values
  - one short example ad followed by its exact expected JSON output
  - the instruction to reply with the JSON object only: no code fences, no text before or after
- Replace `main.py`:
  - Create one `anthropic.Anthropic()` client at startup
  - Print a one-line usage hint once at startup (paste an ad, end with `.`, `/quit` to exit)
  - Read lines with `input()` until a line that is exactly `.`. A line that is exactly `/quit` exits. If the collected ad is empty or whitespace-only, skip it and read again
  - Call `client.messages.create(...)` with the request settings under "Key decisions" and `system=SYSTEM_PROMPT`, `messages=[{"role": "user", "content": ad}]`
  - On `anthropic.APIError`: print `error: API error: <ExceptionClassName>: <message>` to stderr and continue
  - Join the text of all `type == "text"` blocks into `text`
  - If `stop_reason` is `"max_tokens"` or `"refusal"`: print `error: stop_reason <value>` to stderr, then `text` if non-empty, and continue
  - Call `reply.parse_reply(text)`. On `ValueError`: print `error: <reason>` to stderr, then the raw `text`, and continue
  - On success: `print(json.dumps(obj, indent=2))`
  - Wrap the loop so `KeyboardInterrupt` and `EOFError` (at the input prompt or during the API call) end the program with exit code 0 and no traceback

**Files:** `pyproject.toml`, `uv.lock`, `prompt.py`, `main.py`

**Verify:**

- `uv run pytest` still passes
- Manual (needs `ANTHROPIC_API_KEY`): `uv run main.py`, paste a real job ad, end with `.`, see pretty JSON with all three keys
- Manual: paste `hello` then `.`. Whatever comes back is either valid JSON or an `error:` line plus raw text, and the loop prompts again
- Manual: `ANTHROPIC_API_KEY=bad uv run main.py`, paste an ad, see `error: API error: AuthenticationError: ...` and the loop continues
- Manual: `/quit`, Ctrl-C and Ctrl-D each exit with no traceback

## Done

- [ ] `uv run pytest` passes
- [ ] Manual: a real ad prints valid pretty JSON matching the schema
- [ ] Manual: a failing reply and an API error each print one `error:` line to stderr and the loop continues
- [ ] Manual: `/quit`, Ctrl-C and Ctrl-D exit cleanly
- [ ] No files touched outside those listed in T1 and T2
