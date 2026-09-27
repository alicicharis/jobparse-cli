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

Reads `evals/dataset.json` (an array of `{"kind": "...", "ad": "..."}`
entries) and runs the extraction on each one. For `"kind": "job"` the model
grades the result; for `"kind": "not_job"` (resumes, articles, off-topic text,
prompt injection) the check is simply whether the input was rejected as not a
job ad. Full results go to `evals/results/<YYYY-MM-DD_HHMMSS>.json`. Each run gets its own file,
so older runs stay around for comparison.

### Phase 1 run: prompt only (2026-09-27)

Model: Sonnet 5 (`claude-sonnet-5`).

Results: `evals/results/2026-09-27_101703.json`. 22 entries, no
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

### Phase 2 run: Pydantic (2026-09-27)

Model: Sonnet 5 (`claude-sonnet-5`).

Results: `evals/results/2026-09-27_103540.json`. 22 entries, no
errors.

What changed from phase 1: the reply shape is now a Pydantic model
(`Extraction`). Its JSON schema is sent to the API as a structured output
format, and the reply is validated with `Extraction.model_validate_json`
instead of hand-written checks. Non-job input is flagged with an `is_job_ad`
field rather than a `{"not_a_job_ad": true}` sentinel, and the prompt no longer
spells out the JSON formatting rules.

| Kind      | Entries | Result                                     |
| --------- | ------- | ------------------------------------------ |
| `job`     | 14      | 0 wrongly rejected, average score 9.3 / 10 |
| `not_job` | 8       | 8 / 8 rejected                             |

Score distribution for job ads: 7 x 10, 4 x 9, 3 x 8.

Compared with phase 1, classification is identical (22 / 22 correct) and the
average moved from 9.2 to 9.3. Only three scores changed, by one point each and
in both directions: Marketing Coordinator 7 -> 8, Principal Architect 8 -> 9,
Sales Engineer 9 -> 8. That is within what the self-grading noise could
explain, so the gain from Pydantic is a guaranteed reply shape, not better
extraction.

Where points were lost:

- Skills taken from outside the ad's skills list: "technical sales" from
  "4-6 years in a technical sales role" (Sales Engineer, 8).
- Skills paraphrased or padded: "clear technical writing" for "write clear
  technical content" (Technical Writer, 8), "strategic technology decisions"
  dropping the verb (Principal Architect, 9), "CI/CD pipeline experience"
  (DevOps Lead, 9).
- Skills the company will teach listed as requirements, and `junior` inferred
  from "no prior experience needed" (Marketing Coordinator, 8).
- Borderline calls the grader flagged but accepted: "Entry level" mapped to
  `junior` (Data Analyst, 9) and "modern web technologies" kept as a skill
  (generic hiring post, 9).

### Phase 2 follow-up: shared rules and stricter grader (2026-09-27)

Model: Sonnet 5 (`claude-sonnet-5`).

Results: `evals/results/2026-09-27_111730.json`. 22 entries, no
errors.

What changed from the previous run:

- The field rules live in one place, `FIELD_RULES` in `prompt.py`, used by
  both the app prompt and the grader, so they can't drift apart.
- The skills rule is now defined: skills the candidate is asked to have
  (required or nice to have), including ones named in experience
  requirements. Duties of the role, skills the company will teach and
  catch-all phrases are left out, and the ad's wording is trimmed of filler
  like "experience with", "strong" or "ability to".
- Seniority mapping: `intern` only for internships, entry-level roles are
  `junior`.
- The grader only takes off points for rule violations, invented items or
  missed items, gives 10 when it finds none, and may leave `weaknesses` empty.

| Kind      | Entries | Result                                     |
| --------- | ------- | ------------------------------------------ |
| `job`     | 14      | 0 wrongly rejected, average score 9.9 / 10 |
| `not_job` | 8       | 8 / 8 rejected                             |

Score distribution for job ads: 12 x 10, 2 x 9.

The average went from 9.3 to 9.9. Both prompts changed in this run, so part of
the gain comes from the grader no longer marking down choices the rules allow,
not only from better extraction. Visible changes in the output:

- Marketing Coordinator now returns `skills: []`, since every skill in the ad
  is one the company will teach (8 -> 10).
- "modern web technologies" was dropped from the generic hiring post (9 -> 10).
- Skills were trimmed: "technical writing" (Technical Writer, 8 -> 10),
  "CI/CD pipeline" (DevOps Lead, 9 -> 10), "cloud infrastructure" and
  "communication" (Sales Engineer).
- Skills named in experience requirements were included: "DevOps" and "SRE"
  from "6+ years in DevOps or SRE roles", "technical sales" from the Sales
  Engineer ad.

Remaining 9s, both style points rather than rule violations:

- Sales Engineer: "managing complex deals" instead of "manage complex deals".
- Principal Architect: "leading large engineering teams" and "strategic
  technology decisions" read like duties, though the grader itself noted they
  come from experience requirements and are allowed.

The grader is the model itself, so treat the scores as a rough signal rather
than ground truth.
