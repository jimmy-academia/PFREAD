import re
from typing import List

TODO_RE = re.compile(r"\\(?:todo|fix|note)\{([^}]*)\}")


def find_todos(source: str) -> List[str]:
    """Return a list of todo/fix/note messages."""
    return TODO_RE.findall(source)
