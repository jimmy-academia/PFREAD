import re
from pathlib import Path


def _read_file(path: Path) -> str:
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def flatten_tex(path: Path) -> str:
    """Recursively expand \input and \include commands."""
    source = _read_file(path)
    dir_path = path.parent

    pattern = re.compile(r"\\(?:input|include){([^}]+)}")

    def replacer(match):
        rel = match.group(1)
        included = dir_path / rel
        if not included.suffix:
            included = included.with_suffix('.tex')
        try:
            return flatten_tex(included)
        except FileNotFoundError:
            return match.group(0)

    return pattern.sub(replacer, source)

def clean_tex(latex_str: str) -> str:
    # Remove LaTeX inline and full-line comments (ignores escaped %)
    no_line_comments = re.sub(r'(?<!\\)%.*', '', latex_str)

    # Remove \begin{comment} ... \end{comment} blocks (multiline)
    no_comment_env = re.sub(
        r'\\begin\{comment\}.*?\\end\{comment\}',
        '',
        no_line_comments,
        flags=re.DOTALL
    )

    # Remove consecutive empty lines (collapse to one)
    no_extra_newlines = re.sub(r'\n\s*\n+', '\n\n', no_comment_env)

    # Strip leading/trailing whitespace
    cleaned = no_extra_newlines.strip()

    return cleaned
