from typing import List

from proselint.tools import lint


def check_text(text: str) -> List[str]:
    """Return a list of linting messages for the given text."""
    errors = lint(text)
    messages = []
    for err in errors:
        start = err[0]
        msg = err[3]
        messages.append(f"{msg} (at position {start})")
    return messages
