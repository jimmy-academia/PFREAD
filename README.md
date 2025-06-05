# PFREAD

Prototype LaTeX proofreading system.

## Usage

Install dependencies:

```bash
pip install -r requirements.txt
```

Run on a LaTeX project cloned with `workon.sh` (defaults to `WorkFolder/main.tex`).
Intermediate files are written to the system's temporary directory under `pfread/`:
`flattened.tex` after consolidating `\input`/`\include` and `expanded.tex` after
macro replacement.

```bash
python main.py  # or specify a different path
```

Run tests with `pytest`:

```bash
pytest
```
