from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

Seniority = Literal["intern", "junior", "mid", "senior", "lead", "principal"]


class Extraction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # Part of the schema so the model can flag non-job input, but left out of
    # dumps since it is always true on a successful extraction.
    is_job_ad: bool = Field(exclude=True)
    title: str | None
    skills: list[str]
    seniority: Seniority | None


class NotAJobAdError(Exception):
    pass


def parse_reply(text: str) -> Extraction:
    try:
        extraction = Extraction.model_validate_json(text)
    except ValidationError as e:
        err = e.errors()[0]
        loc = ".".join(str(part) for part in err["loc"]) or "reply"
        raise ValueError(f"invalid reply: {loc}: {err['msg']}") from e

    if not extraction.is_job_ad:
        raise NotAJobAdError()

    return extraction
