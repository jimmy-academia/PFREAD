import argparse
from pathlib import Path
from pfread.latex_flatten import flatten_tex, clean_tex
from pfread.macro_parser import replace_newcommands, resolve_optional_macros, remove_text_formatting_commands
from pfread.splitter import split_latex_structure, show_sentences_interactively

# from pfread.analysis.grammar_check import check_text
# from pfread.analysis.todo_finder import find_todos
# from pfread.analysis.proofreader import proofread_document

def main():
    parser = argparse.ArgumentParser(description="Proofread LaTeX paper")
    parser.add_argument("tex_file", type=Path, nargs="?", default=Path("WorkFolder") / "main.tex", help="Path to main.tex inside the downloaded project",
    )
    args = parser.parse_args()

    tmp_dir = Path('outputs') 
    tmp_dir.mkdir(exist_ok=True)

    # Step 1: flatten inputs
    flattened = flatten_tex(args.tex_file)
    flattened = clean_tex(flattened)
    
    flat_path = tmp_dir / "flattened.tex"
    flat_path.write_text(flattened, encoding="utf-8")
    print('Created flattend and cleaned inputs')
    print('==> ', tmp_dir / "flattened.tex")

    # Step 2: expand custom macros
    replaced = replace_newcommands(flattened)
    replaced, resolve_option = resolve_optional_macros(replaced)
    replaced = remove_text_formatting_commands(replaced)
    replaced = clean_tex(replaced)

    replaced_path = tmp_dir / "replaced.tex"
    replaced_path.write_text(replaced, encoding="utf-8")
    print('Replaced custom macros.')
    if resolve_option:
        print(f'    ...and dealt with opt package for option: {resolve_option}')
    print('==> ', tmp_dir / "replaced.tex")

    structured_data, float_map = split_latex_structure(replaced)
    show_sentences_interactively(structured_data, float_map)


if __name__ == "__main__":
    main()
