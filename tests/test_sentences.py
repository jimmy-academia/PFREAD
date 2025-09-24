from pathlib import Path

from pfread.llm import LLMClient
from pfread.passes.sentences import run_sentences_pass
from pfread.preprocess import flatten_sources


def test_sentence_typo(tmp_path):
    tex_path = tmp_path / "paper.tex"
    tex_path.write_text("This is teh sentence.\n", encoding="utf-8")
    flattened = flatten_sources([tex_path])
    llm = LLMClient(fake=True)
    issues, edits, diff_text = run_sentences_pass(flattened["text"], flattened["index"], llm)
    assert len(issues) == 1
    issue = issues[0]
    assert issue.type == "spelling"
    assert issue.suggestion.strip().endswith("the sentence.")
    assert "-This is teh sentence." in diff_text
    assert "+This is the sentence." in diff_text
