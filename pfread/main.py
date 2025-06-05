import argparse
from pathlib import Path
import tempfile

from pylatexenc.latexwalker import LatexWalker

from pfread.parser.latex_flatten import flatten_tex
from pfread.parser.macro_parser import extract_macros, replace_newcommands
from pfread.analysis.grammar_check import check_text
from pfread.analysis.todo_finder import find_todos


def main():
    parser = argparse.ArgumentParser(description="Proofread LaTeX paper")
    parser.add_argument(
        "tex_file",
        type=Path,
        nargs="?",
        default=Path("WorkFolder") / "main.tex",
        help="Path to main.tex inside the downloaded project",
    )
    args = parser.parse_args()

    tmp_dir = Path(tempfile.gettempdir()) / "pfread"
    tmp_dir.mkdir(exist_ok=True)

    # Step 1: flatten inputs
    flattened = flatten_tex(args.tex_file)
    flat_path = tmp_dir / "flattened.tex"
    flat_path.write_text(flattened, encoding="utf-8")

    # Step 2: expand custom macros
    replaced = replace_newcommands(flattened)
    replaced_path = tmp_dir / "expanded.tex"
    replaced_path.write_text(replaced, encoding="utf-8")

    macros = extract_macros(replaced)
    lw = LatexWalker(replaced, macro_dict={m.macroname: m for m in macros})
    _, _, _ = lw.get_latex_nodes()
    text = lw.get_tex().strip()

    print("Grammar Suggestions:")
    for msg in check_text(text):
        print(" -", msg)

    print("\nTODOs:")
    for todo in find_todos(replaced):
        print(" -", todo)


if __name__ == "__main__":
    main()
