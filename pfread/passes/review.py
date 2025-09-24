import json
import re

from pfread.preprocess.latex_flatten import clean_line

SYSTEM_PROMPT = "You provide structured peer reviews from provided skeletons."
SECTION_PATTERN = re.compile(r"\\(section|subsection|subsubsection)\{([^}]*)\}")
CAPTION_PATTERN = re.compile(r"\\caption\{([^}]*)\}")


def extract_clean_text(block):
    lines = []
    for raw in block.splitlines():
        cleaned, _ = clean_line(raw)
        lines.append(cleaned)
    joined = "\n".join(lines)
    paragraphs = [item.strip() for item in joined.split("\n\n") if item.strip()]
    return paragraphs


def build_skeleton(files):
    parts = []
    parts.append("Table of contents:")
    for record in files:
        text = record["text"]
        matches = list(SECTION_PATTERN.finditer(text))
        for index, match in enumerate(matches):
            title = match.group(2).strip()
            section_start = match.end()
            section_end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            block = text[section_start:section_end]
            paragraphs = extract_clean_text(block)
            parts.append(f"Section: {title}")
            if paragraphs:
                parts.append(f"First: {paragraphs[0][:200]}")
                parts.append(f"Last: {paragraphs[-1][:200]}")
    for record in files:
        text = record["text"]
        for match in CAPTION_PATTERN.finditer(text):
            caption, _ = clean_line(match.group(0))
            caption_text = caption.replace("caption", "", 1).strip()
            parts.append(f"Caption: {caption_text[:200]}")
    return "\n".join(parts)


def run_review_pass(files, llm_client, venue_hint=""):
    skeleton = build_skeleton(files)
    payload = {
        "task": "paper_review",
        "venue_hint": venue_hint,
        "skeleton": skeleton,
        "output": {
            "summary": "...",
            "strengths": ["..."],
            "weaknesses": ["..."],
            "top_fixes": [{"section": "...", "action": "...", "impact": "high"}],
            "missing_refs": ["..."],
        },
    }
    response = llm_client.complete_json(
        SYSTEM_PROMPT,
        json.dumps(payload, ensure_ascii=False),
        temperature=0.2,
        max_tokens=512,
    )
    review = {
        "summary": response.get("summary", ""),
        "strengths": response.get("strengths", []),
        "weaknesses": response.get("weaknesses", []),
        "top_fixes": response.get("top_fixes", []),
        "missing_refs": response.get("missing_refs", []),
    }
    return review
