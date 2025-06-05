import sys, os
sys.path.insert(0, os.path.abspath("."))
from pathlib import Path

from pfread.parser.latex_flatten import flatten_tex
from pfread.parser.macro_parser import extract_macros, replace_newcommands
from pfread.analysis.todo_finder import find_todos


def test_flatten_and_macros(tmp_path):
    tex = Path('tests/sample.tex')
    source = flatten_tex(tex)
    macros = extract_macros(source)
    assert any(m.macroname == 'todo' for m in macros)
    todos = find_todos(source)
    assert 'fix this' in todos


def test_replace_newcommands():
    tex = Path('tests/sample.tex')
    source = flatten_tex(tex)
    replaced = replace_newcommands(source)
    assert '\\todo' not in replaced
    assert '\\textcolor{red}{fix this}' in replaced
