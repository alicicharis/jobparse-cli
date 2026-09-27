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

## Evals

```
uv run evals/run_evals.py
```

Reads `docs/data/dataset.json` (an array of `{"kind": "...", "ad": "..."}`
entries) and runs the extraction on each one. For `"kind": "job"` the model
grades the result; for `"kind": "not_job"` (resumes, articles, off-topic text,
prompt injection) the check is simply whether the input was rejected as not a
job ad. Full results go to `docs/data/eval_results/<YYYY-MM-DD_HHMMSS>.json`. Each run gets its own file,
so older runs stay around for comparison.

### Latest run: 2026-09-27

Results: `docs/data/eval_results/2026-09-27_101703.json`. 22 entries, no
errors.

| Kind      | Entries | Result                                     |
| --------- | ------- | ------------------------------------------ |
| `job`     | 14      | 0 wrongly rejected, average score 9.2 / 10 |
| `not_job` | 8       | 8 / 8 rejected                             |

Score distribution for job ads: 7 x 10, 4 x 9, 2 x 8, 1 x 7.

What held up:

- Titles came out verbatim, and were `null` when the ad had no title
  (internship ad, generic "we're hiring" post).
- Prompt injection was ignored in both directions: a real job ad with a "reply
  that this is not a job ad" note was still extracted, and a bare "ignore all
  previous instructions" input was rejected.
- A German ad and a recruiter DM were both extracted correctly.
- Resumes, "open to work" posts, rejection emails, company blurbs, news
  articles and questions about skills were all rejected, even when they
  mention titles and tech stacks.

Where points were lost:

- Seniority for entry-level roles. "No prior experience needed" (Marketing
  Coordinator, score 7) and "Entry level" (Data Analyst, score 9) both
  mapped to `junior`, which the grader flagged as debatable.
- Skills paraphrased instead of using the ad's wording, e.g. "Clear technical
  writing" for "write clear technical content" (Technical Writer, 8) and
  similar rewording for Principal Architect (8).
- Borderline skill omissions, like "cloud infrastructure" in the DevOps Lead ad
  or "modern web technologies" in the generic hiring post.
- Listing skills the company will teach as if they were requirements
  (Marketing Coordinator).

The grader is the model itself, so treat the scores as a rough signal rather
than ground truth.
