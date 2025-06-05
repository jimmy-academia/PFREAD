import argparse
from pathlib import Path
from pylatexenc.latex2text import LatexNodes2Text
from pfread.parser.latex_flatten import flatten_tex
from pfread.parser.macro_parser import replace_newcommands
from pfread.analysis.grammar_check import check_text
from pfread.analysis.todo_finder import find_todos


def main():
    parser = argparse.ArgumentParser(description="Proofread LaTeX paper")
    parser.add_argument("tex_file", type=Path, nargs="?", default=Path("WorkFolder") / "main.tex", help="Path to main.tex inside the downloaded project",
    )
    args = parser.parse_args()

    tmp_dir = Path('outputs') 
    tmp_dir.mkdir(exist_ok=True)

    # Step 1: flatten inputs
    flattened = flatten_tex(args.tex_file)
    flat_path = tmp_dir / "flattened.tex"
    flat_path.write_text(flattened, encoding="utf-8")
    print('created flattend inputs')

    # Step 2: expand custom macros
    replaced = replace_newcommands(flattened)
    replaced_path = tmp_dir / "expanded.tex"
    replaced_path.write_text(replaced, encoding="utf-8")
    print('replaced custom macros')

    text = LatexNodes2Text().latex_to_text(replaced).strip()

    # print("Grammar Suggestions:")
    # for msg in check_text(text):
    #     print(" -", msg)

    # print("\nTODOs:")
    # for todo in find_todos(flattened):
    #     print(" -", todo)


if __name__ == "__main__":
    main()
