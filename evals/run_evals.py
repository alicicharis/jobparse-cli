import json
from datetime import datetime
from pathlib import Path
from typing import Literal

import anthropic
from dotenv import load_dotenv
from pydantic import BaseModel

from jobparse_cli.extract import MODEL, ExtractionError, extract
from jobparse_cli.prompt import FIELD_RULES
from jobparse_cli.reply import NotAJobAdError

DATA_DIR = Path(__file__).parent.parent / "docs" / "data"
DATASET_PATH = DATA_DIR / "dataset.json"
RESULTS_DIR = DATA_DIR / "eval_results"


def build_eval_prompt(ad: str, output: dict) -> str:
    return f"""
You are an expert technical recruiter. Your task is to evaluate how well an AI
extracted structured data from a job ad.

The extraction had to follow these rules:
{FIELD_RULES}

Original job ad:
<job_ad>
{ad}
</job_ad>

Extraction to evaluate:
<extraction>
{json.dumps(output, indent=2)}
</extraction>

Judge accuracy (nothing invented, seniority fits the ad), completeness (no
title or skills missed) and adherence to the rules above. The rules are the
only standard: a choice they allow is not a weakness.

Fill in the evaluation fields:
- "strengths": 1-3 key strengths
- "weaknesses": up to 3 specific rule violations, invented items or missed
  items, or [] if there are none
- "reasoning": a concise explanation of your overall assessment
- "score": a whole number from 1 to 10. Give 10 when "weaknesses" is empty.
  Otherwise take off points only for the listed weaknesses, in proportion to
  how much each one matters.

Keep your response concise and direct.
"""


class Grade(BaseModel):
    strengths: list[str]
    weaknesses: list[str]
    reasoning: str
    score: Literal[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]


GRADE_FORMAT = {"type": "json_schema", "schema": anthropic.transform_schema(Grade)}


def grade(client: anthropic.Anthropic, ad: str, output: dict) -> Grade:
    response = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        output_config={"format": GRADE_FORMAT},
        messages=[{"role": "user", "content": build_eval_prompt(ad, output)}],
    )
    text = "".join(block.text for block in response.content if block.type == "text")

    # The schema guarantees valid JSON only when the reply ran to completion.
    if response.stop_reason in ("max_tokens", "refusal"):
        raise ValueError(f"grader stop_reason {response.stop_reason}\n{text}")
    return Grade.model_validate_json(text)


def main():
    load_dotenv()
    client = anthropic.Anthropic()
    dataset = json.loads(DATASET_PATH.read_text())

    results = []
    for i, entry in enumerate(dataset, start=1):
        prefix = f"[{i}/{len(dataset)}]"
        result = {"entry": entry, "output": None, "rejected": False, "grade": None, "error": None}
        results.append(result)

        try:
            result["output"] = extract(client, entry["ad"]).model_dump()
        except NotAJobAdError:
            result["rejected"] = True
        except ExtractionError as e:
            result["error"] = f"extraction failed: {e}"
            if e.raw_text:
                result["raw_text"] = e.raw_text
            print(f"{prefix} {result['error']}")
            continue

        # Non-job inputs have one right answer, so they are checked in code.
        if entry["kind"] == "not_job":
            if result["rejected"]:
                print(f"{prefix} pass - rejected as not a job ad")
            else:
                result["error"] = "extracted a non-job input instead of rejecting it"
                print(f"{prefix} fail - {result['error']}")
            continue

        if result["rejected"]:
            result["error"] = "wrongly rejected as not a job ad"
            print(f"{prefix} fail - {result['error']}")
            continue

        try:
            result["grade"] = grade(client, entry["ad"], result["output"]).model_dump()
        except (anthropic.APIError, ValueError) as e:
            result["error"] = f"grading failed: {e}"
            print(f"{prefix} {result['error']}")
            continue

        print(f"{prefix} score {result['grade']['score']} - {result['grade'].get('reasoning')}")

    RESULTS_DIR.mkdir(exist_ok=True)
    results_path = RESULTS_DIR / f"{datetime.now():%Y-%m-%d_%H%M%S}.json"
    results_path.write_text(json.dumps(results, indent=2, ensure_ascii=False))

    jobs = [r for r in results if r["entry"]["kind"] == "job"]
    not_jobs = [r for r in results if r["entry"]["kind"] == "not_job"]

    scores = [r["grade"]["score"] for r in jobs if r["grade"]]
    wrongly_rejected = sum(r["rejected"] for r in jobs)
    job_extraction_failures = sum(1 for r in jobs if r["output"] is None and not r["rejected"])
    grading_failures = len(jobs) - len(scores) - wrongly_rejected - job_extraction_failures

    correctly_rejected = sum(r["rejected"] for r in not_jobs)
    extracted_anyway = sum(1 for r in not_jobs if r["output"] is not None)
    not_job_extraction_failures = len(not_jobs) - correctly_rejected - extracted_anyway

    print()
    print(f"Job ads ({len(jobs)})")
    if scores:
        print(f"  Average score: {sum(scores) / len(scores):.2f} ({len(scores)} graded)")
    print(f"  Wrongly rejected: {wrongly_rejected}")
    print(f"  Extraction failures: {job_extraction_failures}")
    print(f"  Grading failures: {grading_failures}")
    print(f"Non-job inputs ({len(not_jobs)})")
    print(f"  Correctly rejected: {correctly_rejected} of {len(not_jobs)}")
    print(f"  Extracted anyway: {extracted_anyway}")
    print(f"  Extraction failures: {not_job_extraction_failures}")
    print(f"Full results: {results_path}")


if __name__ == "__main__":
    main()
