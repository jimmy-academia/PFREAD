import argparse
from pathlib import Path

from pylatexenc.latexwalker import LatexWalker

from pfread.parser.latex_flatten import flatten_tex
from pfread.parser.macro_parser import extract_macros
from pfread.analysis.grammar_check import check_text
from pfread.analysis.todo_finder import find_todos


def main():
    parser = argparse.ArgumentParser(description="Proofread LaTeX paper")
    parser.add_argument("tex_file", type=Path)
    args = parser.parse_args()

    source = flatten_tex(args.tex_file)
    macros = extract_macros(source)

    lw = LatexWalker(source, macro_dict={m.macroname: m for m in macros})
    nodes, _, _ = lw.get_latex_nodes()

    text = lw.get_tex().strip()

    print("Grammar Suggestions:")
    for msg in check_text(text):
        print(" -", msg)

    print("\nTODOs:")
    for todo in find_todos(source):
        print(" -", todo)


if __name__ == "__main__":
    main()
