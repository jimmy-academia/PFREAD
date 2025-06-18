import os
import re
from pathlib import Path
from typing import List, Tuple

import openai
from pylatexenc.latex2text import LatexNodes2Text

# from pfread.parser.choice_expander import expand_choices


SECTION_RE = re.compile(r"\\section\*?{([^}]*)}")


def split_sections(source: str) -> List[Tuple[str, str]]:
    """Return list of (section title, content) pairs."""
    sections: List[Tuple[str, str]] = []
    positions = [(m.start(), m.end(), m.group(1)) for m in SECTION_RE.finditer(source)]
    if not positions:
        return [("", source)]
    for idx, (start, end, title) in enumerate(positions):
        next_start = positions[idx + 1][0] if idx + 1 < len(positions) else len(source)
        content = source[end:next_start]
        sections.append((title, content))
    return sections


def split_sentences(text: str) -> List[str]:
    plain = LatexNodes2Text().latex_to_text(text)
    sentences = re.split(r"(?<=[.!?])\s+", plain)
    return [s.strip() for s in sentences if s.strip()]


def proofread_sentence(sentence: str, model: str = "gpt-3.5-turbo") -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return f"[skipped] {sentence}"
    openai.api_key = api_key
    resp = openai.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": f"Proofread the following sentence:\n{sentence}"}],
    )
    return resp.choices[0].message.content.strip()


# def proofread_document(source: str, out_dir: Path) -> None:
#     # variants = expand_choices(source)
#     out_dir.mkdir(parents=True, exist_ok=True)
#     for i, variant in enumerate(variants, start=1):
#         variant_file = out_dir / f"variant_{i}.tex"
#         variant_file.write_text(variant, encoding="utf-8")
#         for title, content in split_sections(variant):
#             for sentence in split_sentences(content):
#                 suggestion = proofread_sentence(sentence)
#                 print(f"[{variant_file.name}] ({title}) {suggestion}")
