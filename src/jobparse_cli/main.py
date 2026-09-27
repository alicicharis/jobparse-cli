import sys

import anthropic
from dotenv import load_dotenv

from jobparse_cli.extract import ExtractionError, extract
from jobparse_cli.reply import NotAJobAdError


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
            obj = extract(client, ad)
        except NotAJobAdError:
            print("error: not a job ad", file=sys.stderr)
            continue
        except ExtractionError as e:
            print(f"error: {e}", file=sys.stderr)
            if e.raw_text:
                print(e.raw_text, file=sys.stderr)
            continue

        print(obj.model_dump_json(indent=2))


def main():
    load_dotenv()
    try:
        run()
    except (KeyboardInterrupt, EOFError):
        pass
