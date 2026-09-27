import anthropic
from dotenv import load_dotenv
from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings
from rich.console import Console
from rich.text import Text

from jobparse_cli.extract import ExtractionError, extract
from jobparse_cli.reply import NotAJobAdError

out = Console()
err = Console(stderr=True)


def make_session() -> PromptSession[str]:
    bindings = KeyBindings()

    @bindings.add("enter")
    def _submit(event):
        event.current_buffer.validate_and_handle()

    # Shift+Enter arrives as Esc+Enter once the terminal is set up to send it.
    @bindings.add("escape", "enter")
    @bindings.add("c-j")
    def _newline(event):
        event.current_buffer.insert_text("\n")

    return PromptSession(multiline=True, key_bindings=bindings)


def run():
    client = anthropic.Anthropic()
    session = make_session()
    out.print(
        "Paste a job ad and press Enter. Shift+Enter or Ctrl+J adds a new line. Type /quit to exit.",
        style="dim",
    )

    while True:
        ad = session.prompt("> ")
        if ad.strip() == "/quit":
            return
        if not ad.strip():
            continue

        try:
            with out.status("Extracting..."):
                obj = extract(client, ad)
        except NotAJobAdError:
            err.print("error: not a job ad", style="red")
            continue
        except ExtractionError as e:
            err.print(Text(f"error: {e}", style="red"))
            if e.raw_text:
                err.print(e.raw_text, markup=False, highlight=False, soft_wrap=True)
            continue

        out.print_json(obj.model_dump_json())


def main():
    load_dotenv()
    try:
        run()
    except (KeyboardInterrupt, EOFError):
        pass
