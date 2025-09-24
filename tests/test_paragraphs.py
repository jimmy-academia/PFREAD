from pfread.llm import LLMClient
from pfread.passes.paragraphs import run_paragraph_pass
from pfread.preprocess import flatten_sources


def test_paragraph_pass_detects_multiple_issues(tmp_path):
    tex_path = tmp_path / "paper.tex"
    tex_path.write_text(
        """This paragraph maybe includes a very very long explanation that keeps going without stopping so that it easily exceeds the normal expectations for concise academic prose.\n\nSecond paragraph.""",
        encoding="utf-8",
    )
    flattened = flatten_sources([tex_path])
    llm = LLMClient(fake=True)
    issues = run_paragraph_pass(flattened["text"], flattened["index"], llm)
    kinds = {issue.type for issue in issues}
    assert "hedging" in kinds
    assert "long_sentence" in kinds
