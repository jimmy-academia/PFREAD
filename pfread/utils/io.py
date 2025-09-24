import json
from pathlib import Path


def collect_tex_files(project_dir):
    root = Path(project_dir)
    return sorted(path for path in root.rglob("*.tex") if path.is_file())


def read_file(path):
    return Path(path).read_text(encoding="utf-8")


def write_text(path, content):
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(content, encoding="utf-8")


def write_json(path, payload):
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
