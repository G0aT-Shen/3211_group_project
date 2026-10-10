"""Start the CLI with console IO safe for the terminal's configured encoding."""
import sys

from cli import Repl


if __name__ == "__main__":
    # Redirected Windows output can use a legacy encoding even for UTF-8 records.
    # Escape unsupported characters for display without altering stored data.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="backslashreplace")
    # Bytes invalid in the input encoding would otherwise end the session and lose
    # unsaved records. Keep them as surrogates, which the model rejects as text.
    if hasattr(sys.stdin, "reconfigure"):
        sys.stdin.reconfigure(errors="surrogateescape")
    Repl().run()
