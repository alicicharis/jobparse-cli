import json

SENIORITY_VALUES = ("intern", "junior", "mid", "senior", "lead", "principal")
REQUIRED_KEYS = ("title", "skills", "seniority")
NOT_A_JOB_AD = {"not_a_job_ad": True}


class NotAJobAdError(Exception):
    pass


def parse_reply(text: str) -> dict:
    try:
        obj = json.loads(text.strip())
    except json.JSONDecodeError as e:
        raise ValueError(f"invalid JSON: {e}") from e

    if not isinstance(obj, dict):
        raise ValueError("top level must be an object")

    if obj == NOT_A_JOB_AD:
        raise NotAJobAdError()

    for key in REQUIRED_KEYS:
        if key not in obj:
            raise ValueError(f"missing key: {key}")

    for key in obj:
        if key not in REQUIRED_KEYS:
            raise ValueError(f"unexpected key: {key}")

    title = obj["title"]
    if title is not None and not isinstance(title, str):
        raise ValueError("title must be a string or null")

    skills = obj["skills"]
    if not isinstance(skills, list) or not all(isinstance(s, str) for s in skills):
        raise ValueError("skills must be a list of strings")

    seniority = obj["seniority"]
    if seniority is not None:
        if not isinstance(seniority, str) or seniority not in SENIORITY_VALUES:
            allowed = ", ".join(SENIORITY_VALUES)
            raise ValueError(f"seniority must be one of {allowed} or null")

    return obj
