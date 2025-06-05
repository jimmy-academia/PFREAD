import re
from typing import List
from pylatexenc.macrospec import MacroSpec

# Match \newcommand{\macro}[n]{definition}
NEWCOMMAND_RE = re.compile(
    r"\\(?:re)?newcommand\\*?\{\\(\w+)\}(?:\[(\d+)\])?\{",
)


def extract_macros(source: str) -> List[MacroSpec]:
    """Extract custom macro definitions and return MacroSpec list."""
    macros = []
    for name, n_args in NEWCOMMAND_RE.findall(source):
        n_args = int(n_args) if n_args else 0
        macros.append(MacroSpec(name, '{' * n_args))
    return macros
