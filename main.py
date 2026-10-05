"""Start the CLI with output safe for the terminal's configured encoding."""
import sys

from cli import Repl


if __name__ == "__main__":
    # Redirected Windows output can use a legacy encoding even for UTF-8 records.
    # Escape unsupported characters for display without altering stored data.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="backslashreplace")
    Repl().run()
