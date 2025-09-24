import json
import subprocess
import sys
from pathlib import Path


def test_cli_end_to_end(tmp_path):
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    tex_path = project_dir / "main.tex"
    tex_path.write_text(
        """\\section{Intro}\nThis is teh intro sentence.\n\nAn acronym ABC appears without definition.\n""",
        encoding="utf-8",
    )
    bib_path = project_dir / "refs.bib"
    bib_path.write_text("@article{smith2020,}\n", encoding="utf-8")

    repo_root = Path(__file__).resolve().parents[1]
    report_path = tmp_path / "outputs" / "report.html"
    json_path = tmp_path / "outputs" / "findings.json"
    diff_path = tmp_path / "outputs" / "sentences.diff"

    command = [
        sys.executable,
        "main.py",
        "--mode",
        "all",
        "--report",
        str(report_path),
        "--json",
        str(json_path),
        "--diff",
        str(diff_path),
        "--project-dir",
        str(project_dir),
        "--bib",
        str(bib_path),
        "--fake-llm",
    ]
    subprocess.run(command, cwd=repo_root, check=True)

    assert report_path.exists()
    assert json_path.exists()

    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert "meta" in data and "issues" in data and "review" in data
    assert any(issue["phase"] == "typo" for issue in data["issues"])
    assert "PFREAD" in report_path.read_text(encoding="utf-8")
