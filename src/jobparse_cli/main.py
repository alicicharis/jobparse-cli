import json
import sys

import anthropic
from dotenv import load_dotenv

from jobparse_cli.prompt import SYSTEM_PROMPT
from jobparse_cli.reply import parse_reply


def read_ad() -> str | None:
    lines = []
    while True:
        line = input()
        if line == "/quit":
            return None
        if line == ".":
            break
        lines.append(line)
    return "\n".join(lines)


def run():
    client = anthropic.Anthropic()
    print("Paste a job ad, end with a line containing only '.'. Type /quit to exit.")

    while True:
        ad = read_ad()
        if ad is None:
            return
        if not ad.strip():
            continue

        try:
            response = client.messages.create(
                model="claude-sonnet-5",
                max_tokens=2048,
                output_config={"effort": "low"},
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": ad}],
            )
        except anthropic.APIError as e:
            print(f"error: API error: {type(e).__name__}: {e}", file=sys.stderr)
            continue

        text = "".join(
            block.text for block in response.content if block.type == "text"
        )

        if response.stop_reason in ("max_tokens", "refusal"):
            print(f"error: stop_reason {response.stop_reason}", file=sys.stderr)
            if text:
                print(text, file=sys.stderr)
            continue

        try:
            obj = parse_reply(text)
        except ValueError as e:
            print(f"error: {e}", file=sys.stderr)
            print(text, file=sys.stderr)
            continue

        print(json.dumps(obj, indent=2))


def main():
    load_dotenv()
    try:
        run()
    except (KeyboardInterrupt, EOFError):
        pass
