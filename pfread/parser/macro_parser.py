import re
from typing import Dict, List, Tuple
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

def _parse_macro_definitions(source: str) -> Tuple[str, Dict[str, Tuple[int, str]]]:
    """Remove \newcommand definitions and return remaining source and macros."""
    macros: Dict[str, Tuple[int, str]] = {}
    pattern = re.compile(r"\\(?:re)?newcommand\\*?\{\\(\w+)\}(?:\[(\d+)\])?{", re.DOTALL)
    pos = 0
    result = ""
    while True:
        m = pattern.search(source, pos)
        if not m:
            result += source[pos:]
            break
        result += source[pos:m.start()]
        name = m.group(1)
        nargs = int(m.group(2) or 0)
        start = m.end()
        depth = 1
        i = start
        while i < len(source) and depth > 0:
            if source[i] == '{':
                depth += 1
            elif source[i] == '}':
                depth -= 1
            i += 1
        body = source[start:i-1]
        macros[name] = (nargs, body)
        pos = i
    return result, macros


def _expand_macros(text: str, macros: Dict[str, Tuple[int, str]]) -> str:
    for name, (nargs, body) in macros.items():
        arg_pattern = ''.join(r'\{([^{}]*)\}' for _ in range(nargs))
        pattern = re.compile(rf'\\{re.escape(name)}{arg_pattern}')

        def repl(match: re.Match) -> str:
            expansion = body
            for i in range(nargs):
                expansion = expansion.replace(f'#{i+1}', match.group(i+1))
            return expansion

        text = pattern.sub(repl, text)
    return text


def replace_newcommands(source: str) -> str:
    """Expand custom macros defined via \newcommand and remove the definitions."""
    without_defs, macros = _parse_macro_definitions(source)
    return _expand_macros(without_defs, macros)