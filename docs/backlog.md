# Backlog

Ordered by build sequence.

## 1. Phase 1: prompt-only job ad extraction - to do

**What:** Paste a job ad into the terminal and get back a validated JSON object with `title`, `skills` and `seniority`. It's done when valid replies print as pretty JSON, and every failure (parse, validation, stop reason, API) is reported clearly while the loop keeps running.

**Agreed:**

- Setup: `uv add anthropic`, `uv add --dev pytest`; API key from the environment
- Input: multi-line paste ended by a line containing only `.`; `/quit`, Ctrl-C or Ctrl-D exits cleanly
- No conversation history: each ad is an independent call (system prompt + ad)
- Structured output comes from plain assistant text only: no Pydantic, no `output_config.format`, no tool use, no prefill
- No re-asking on parse or validation failure; the SDK's default network retries stay on
- Model settings: `claude-sonnet-5`, default adaptive thinking, `effort: low`, `max_tokens` around 2048
- System prompt: schema description + one example (ad in, JSON out); tells the model to reply with the JSON object only, no code fences
- Schema: `title` string as written in the ad; `skills` flat list of strings in the ad's wording; `seniority` one of `intern|junior|mid|senior|lead|principal` or `null`; all keys always present, `null`/`[]` when absent
- Non-job input is deliberately left unspecified in the prompt - whatever comes back goes through normal parse/validation
- Response handling order: check `stop_reason` first (`max_tokens` / `refusal` are failures), then join the text blocks, then strict `json.loads(text.strip())` - fenced or prose-wrapped JSON counts as a failure
- Hand-written validation: top level is an object, exactly the three keys, correct types, `seniority` in the allowed set or `null`
- Success output: the parsed dict re-serialized with `json.dumps(indent=2)` to stdout
- Tests: parse + validate only - valid object, fenced JSON (fails), missing key, wrong type, out-of-range seniority

## 2. Conversation history - backlog

**What:** Keep the per-run conversation history (in memory only) across extractions.

**Open:**

- What the history is for: refining the last result with follow-ups vs. independent ads with history only as implicit examples
- Cross-contamination risk (skills or title from earlier ads leaking into later ones) and token growth
- Whether a failed turn stays in history, gets dropped, or keeps only the user message
- Whether a `/reset` command is needed

## 3. Phase 2: schema-enforced structured output - backlog

**What:** Replace prompt-only JSON with schema tooling (Pydantic and/or the API's structured output features) and compare reliability against phase 1.

**Open:**

- Which mechanism: `messages.parse()` with Pydantic, `output_config.format`, or strict tool use
- Whether phase 1's hand-written validator is removed or kept for comparison
- Whether parse retries are introduced
