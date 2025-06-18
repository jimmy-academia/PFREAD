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

def xspace_decision(next_chars: str) -> str:
    """Simplified \\xspace logic: skip '}' and look ahead for the first meaningful char."""
    for c in next_chars[:5]:
        if c == '}':
            continue
        if c.isspace() or c in '.,;:!?)]\'"':
            return ''
        return ' '
    return ' '  # Default if nothing found


def _expand_macros(text: str, macros: Dict[str, Tuple[int, str]], debug: bool = False) -> str:
    if debug:
        print(f"[DEBUG] Starting macro expansion. {len(macros)} macros found.\n")

    for name, (nargs, body) in macros.items():
        if debug:
            print(f"[DEBUG] Expanding macro: \\{name} with {nargs} argument(s)")
            print(f"        Macro body: {body!r}")

        pattern = re.compile(rf'\\{re.escape(name)}\s*', re.DOTALL)

        def parse_args(s, start):
            args = []
            i = start
            for _ in range(nargs):
                while i < len(s) and s[i].isspace():
                    i += 1
                if i >= len(s) or s[i] != '{':
                    return None, start
                depth = 1
                i += 1
                arg_start = i
                while i < len(s) and depth > 0:
                    if s[i] == '{':
                        depth += 1
                    elif s[i] == '}':
                        depth -= 1
                    i += 1
                if depth != 0:
                    return None, start
                args.append(s[arg_start:i-1])
            return args, i

        result = []
        pos = 0
        while True:
            m = pattern.search(text, pos)
            if not m:
                result.append(text[pos:])
                break
            result.append(text[pos:m.start()])
            args, next_pos = parse_args(text, m.end())
            if args is None:
                result.append(text[m.start():next_pos])
                pos = next_pos
                continue
            expansion = body
            for i in range(nargs):
                expansion = expansion.replace(f'#{i+1}', args[i])
            
            next_chunk = text[next_pos:next_pos + 5]
            expansion = expansion.replace(r'\xspace', xspace_decision(next_chunk))
            result.append(expansion)
            pos = next_pos

        text = ''.join(result)

    if debug:
        print(f"[DEBUG] Macro expansion complete.\n")

    return text


def replace_newcommands(source: str) -> str:
    """Expand custom macros defined via \newcommand and remove the definitions."""
    without_defs, macros = _parse_macro_definitions(source)
    return _expand_macros(without_defs, macros)


####################################
####### for \usepackage{opt} #######
####################################

from typing import Optional, Tuple

def extract_active_opt_key(latex: str) -> Optional[str]:
    match = re.search(r'\\usepackage\[(\w+)\]\{optional\}', latex)
    return match.group(1) if match else None

def resolve_optional_macros(latex: str, active_option: Optional[str] = None) -> Tuple[str, bool]:
    if active_option is None:
        active_option = extract_active_opt_key(latex)
        if not active_option:
            return latex, False

    result = []
    i = 0
    while i < len(latex):
        if latex.startswith(r'\opt{', i):
            key_start = i + 5
            key_end = latex.find('}', key_start)
            if key_end == -1:
                result.append(latex[i])
                i += 1
                continue
            key = latex[key_start:key_end]
            if key not in ('short', 'long', 'bin'):
                result.append(latex[i])
                i += 1
                continue

            # Now look for the content block
            if key_end + 1 >= len(latex) or latex[key_end + 1] != '{':
                result.append(latex[i])
                i += 1
                continue

            # Parse the argument block { ... } with nesting
            content_start = key_end + 2
            depth = 1
            j = content_start
            while j < len(latex) and depth > 0:
                if latex[j] == '{':
                    depth += 1
                elif latex[j] == '}':
                    depth -= 1
                j += 1
            content = latex[content_start:j-1]

            if key == active_option:
                result.append(content)
            # else skip it

            i = j  # move past entire \opt{key}{...}
        else:
            result.append(latex[i])
            i += 1

    return ''.join(result), True


def remove_text_formatting_commands(latex: str) -> str:
    """
    Removes LaTeX formatting commands like \textit{...}, \textsf{...}, emph{...}, etc.,
    and keeps only their inner content.
    """
    pattern = re.compile(r'\\(?:textsf|textit|textsc|text|textbf|emph)\{((?:[^{}]*|{[^{}]*})*)\}')
    
    while True:
        new_latex = pattern.sub(r'\1', latex)
        if new_latex == latex:
            break  # no more replacements
        latex = new_latex
    
    return latex
