import anthropic

from jobparse_cli.prompt import SYSTEM_PROMPT
from jobparse_cli.reply import parse_reply

MODEL = "claude-sonnet-5"


class ExtractionError(Exception):
    def __init__(self, reason: str, raw_text: str = ""):
        super().__init__(reason)
        self.raw_text = raw_text


def extract(client: anthropic.Anthropic, ad: str) -> dict:
    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=2048,
            output_config={"effort": "low"},
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": ad}],
        )
    except anthropic.APIError as e:
        raise ExtractionError(f"API error: {type(e).__name__}: {e}") from e

    text = "".join(block.text for block in response.content if block.type == "text")

    if response.stop_reason in ("max_tokens", "refusal"):
        raise ExtractionError(f"stop_reason {response.stop_reason}", text)

    try:
        return parse_reply(text)
    except ValueError as e:
        raise ExtractionError(str(e), text) from e
