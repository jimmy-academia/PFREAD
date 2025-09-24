from pathlib import Path

from pfread.passes.cross import run_cross_pass
from pfread.preprocess import flatten_sources
from pfread.utils.schema import IssueIdGenerator


def test_cross_checks_detects_missing_reference_and_style(tmp_path):
    tex_path = tmp_path / "paper.tex"
    tex_path.write_text(
        """\\section{Intro}\nFigure 1 illustrates the system while Fig. 2 summarises it.\nSee \\ref{fig:missing} for more.\n\\begin{figure}\n\\caption{System overview}\n\\label{fig:system}\n\\end{figure}\n""",
        encoding="utf-8",
    )
    flattened = flatten_sources([tex_path])
    generator = IssueIdGenerator()
    issues, label_index = run_cross_pass(flattened["files"], flattened["index"], None, generator)
    issue_types = {issue.type for issue in issues}
    assert "ref_error" in issue_types
    assert "style_inconsistency" in issue_types
    assert "fig:system" in label_index
