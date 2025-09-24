import argparse
import time
from pathlib import Path

from pfread.llm import LLMClient
from pfread.passes import run_cross_pass, run_paragraph_pass, run_review_pass, run_sentences_pass
from pfread.preprocess import flatten_sources
from pfread.utils import io
from pfread.utils.schema import IssueIdGenerator, findings_json
from pfread.utils.telemetry import Telemetry


def build_parser():
    parser = argparse.ArgumentParser(description="LaTeX-aware proofreading pipeline")
    parser.add_argument("--mode", choices=["all", "typo", "cross", "paragraph", "review"], default="all")
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--json", dest="json_path", type=Path, required=True)
    parser.add_argument("--diff", dest="diff_path", type=Path, required=False)
    parser.add_argument("--project-dir", type=Path, default=Path("."))
    parser.add_argument("--bib", type=Path, default=None)
    parser.add_argument("--model", default="gpt-5-nano")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--fake-llm", action="store_true")
    parser.add_argument("--venue", default="")
    return parser


def copy_report_assets(report_path):
    report_dir = report_path.parent
    report_dir.mkdir(parents=True, exist_ok=True)
    css_source = Path(__file__).parent / "report" / "report.css"
    js_source = Path(__file__).parent / "report" / "report.js"
    css_target = report_dir / "report.css"
    js_target = report_dir / "report.js"
    css_target.write_text(css_source.read_text(encoding="utf-8"), encoding="utf-8")
    js_target.write_text(js_source.read_text(encoding="utf-8"), encoding="utf-8")


def load_report_template():
    template_path = Path(__file__).parent / "report" / "report.html"
    return template_path.read_text(encoding="utf-8")


def run_cli(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    telemetry = Telemetry()
    generator = IssueIdGenerator()
    llm_client = LLMClient(
        model=args.model,
        temperature=args.temperature,
        fake=args.fake_llm,
        telemetry=telemetry,
    )
    tex_files = io.collect_tex_files(args.project_dir)
    if not tex_files:
        raise SystemExit("No .tex files found in project directory")
    flattened = flatten_sources(tex_files)
    text = flattened["text"]
    offset_index = flattened["index"]
    file_records = flattened["files"]
    files_meta = [{"path": item["path"], "sha": item["sha"]} for item in file_records]
    issues = []
    diff_text = ""

    if args.mode in {"all", "typo"}:
        telemetry.start_timer("typo")
        typo_issues, edits, diff_text = run_sentences_pass(text, offset_index, llm_client, generator)
        telemetry.stop_timer("typo")
        issues.extend(typo_issues)
        if args.diff_path and diff_text:
            io.write_text(args.diff_path, diff_text)
        elif args.diff_path:
            io.write_text(args.diff_path, "")

    if args.mode in {"all", "cross"}:
        telemetry.start_timer("cross")
        cross_issues, label_index = run_cross_pass(file_records, offset_index, args.bib, generator)
        telemetry.stop_timer("cross")
        issues.extend(cross_issues)
        label_path = args.report.parent / "label_index.json"
        label_payload = {key: value for key, value in label_index.items()}
        io.write_json(label_path, label_payload)

    if args.mode in {"all", "paragraph"}:
        telemetry.start_timer("paragraph")
        paragraph_issues = run_paragraph_pass(text, offset_index, llm_client, generator)
        telemetry.stop_timer("paragraph")
        issues.extend(paragraph_issues)

    review = {"summary": "", "strengths": [], "weaknesses": [], "top_fixes": [], "missing_refs": []}
    if args.mode in {"all", "review"}:
        telemetry.start_timer("review")
        review = run_review_pass(file_records, llm_client, args.venue)
        telemetry.stop_timer("review")

    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    meta = {
        "run_id": f"pfread-{int(time.time())}",
        "model": telemetry.summary().get("model", args.model),
        "tokens": telemetry.summary().get("tokens", 0),
        "cost_usd": telemetry.summary().get("cost_usd", 0.0),
        "timestamp": timestamp,
    }
    json_text = findings_json(meta, files_meta, issues, review)
    io.write_text(args.json_path, json_text)

    report_html = load_report_template()
    io.write_text(args.report, report_html)
    copy_report_assets(args.report)

    metadata_path = args.report.parent / "metadata.json"
    metadata = telemetry.summary()
    metadata["timestamp"] = timestamp
    io.write_json(metadata_path, metadata)

    if args.mode not in {"all", "typo"} and args.diff_path:
        io.write_text(args.diff_path, diff_text)

    return {
        "issues": issues,
        "review": review,
        "meta": meta,
    }
