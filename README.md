# PFREAD

PFREAD is a LaTeX-aware proofreading pipeline that combines lightweight heuristics with structured LLM calls. It flattens multiple `.tex` sources, performs four quality passes, and emits both human-friendly and machine-readable reports.

## Installation

The project targets Python 3.10+. Create a virtual environment and install the package in editable mode:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

No external dependencies are required beyond the standard library.

## Command-line interface

Run the tool from the repository root:

```bash
python main.py \
  --mode all \
  --report outputs/report.html \
  --json outputs/findings.json \
  --diff outputs/sentences.diff \
  --project-dir path/to/project \
  --bib path/to/references.bib \
  --model gpt-5-nano \
  --temperature 0.0 \
  --fake-llm
```

### Modes

Passes can be selected by name or by number (1=typo, 2=cross, 3=paragraph, 4=review). Comma-separated numbers run multiple passes, e.g. `--mode 1,3`.

* `all` – run every pass (sentence typos, cross-distance checks, paragraph diagnostics, whole-paper review).
* `typo` – sentence-level proofreading only.
* `cross` – reference, citation, acronym, and style validation.
* `paragraph` – paragraph clarity diagnostics.
* `review` – whole-paper structured review.

### Outputs

* `findings.json` – structured results containing metadata, per-file hashes, issues, and the final review summary.
* `report.html` – interactive dashboard loading `findings.json` alongside `report.js` and `report.css`.
* `sentences.diff` – unified diff of sentence-level safe edits (Pass 1), only populated when that pass runs.
* `label_index.json` – inferred mapping of LaTeX labels to their source files and types.
* `metadata.json` – telemetry summary covering timing, tokens, and cost estimates.

Open `report.html` directly in a browser; it fetches `findings.json` from the same directory, so keep the JSON alongside the HTML and assets.

## Cost control

Telemetry records approximate token usage and applies a simple pricing table (defaulting to `gpt-5-nano`). Adjust `--temperature` or omit optional passes to reduce calls. The fake LLM mode keeps telemetry consistent without external requests.

## Fake LLM mode

Use `--fake-llm` during tests or offline runs. It returns deterministic JSON, exercises the full pipeline, and avoids network access.

## Limitations and future work

* The LaTeX parser is heuristic and may miss complex macro expansions.
* Real LLM access is not bundled; integrate your provider inside `pfread/llm.py`.
* Caching of LLM calls is not yet implemented; a persistent cache is planned for future releases.
