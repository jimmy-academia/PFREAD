import json

from pfread.utils.diffutil import sentence_diff
from pfread.utils.schema import Issue, IssueIdGenerator, Span, validate_issue

SYSTEM_PROMPT = (
    "You are a precise proofreader. Preserve meaning. Prefer minimal edits. Fix grammar, spelling, punctuation, "
    "agreement, capitalization. No rewrites unless necessary for correctness. Return STRICT JSON."
)


def trim_segment(segment):
    left = 0
    right = len(segment)
    while left < right and segment[left].isspace():
        left += 1
    while right > left and segment[right - 1].isspace():
        right -= 1
    return segment[left:right], left, right


def split_sentences(text):
    sentences = []
    start = 0
    braces = 0
    brackets = 0
    inline_math = False
    display_math = 0
    index = 0
    length = len(text)
    while index < length:
        char = text[index]
        if text.startswith("\\(", index):
            inline_math = True
            index += 2
            continue
        if text.startswith("\\)", index):
            inline_math = False
            index += 2
            continue
        if text.startswith("\\[", index):
            display_math += 1
            index += 2
            continue
        if text.startswith("\\]", index):
            if display_math > 0:
                display_math -= 1
            index += 2
            continue
        if char == "$":
            inline_math = not inline_math
            index += 1
            continue
        if char == "{":
            braces += 1
        elif char == "}":
            if braces > 0:
                braces -= 1
        elif char == "[":
            brackets += 1
        elif char == "]":
            if brackets > 0:
                brackets -= 1
        boundary = False
        if char in {".", "!", "?"} and not braces and not brackets and not inline_math and display_math == 0:
            peek = index + 1
            while peek < length and text[peek] in {'"', "'", ")", "]"}:
                peek += 1
            if peek >= length or text[peek].isspace():
                boundary = True
        if boundary:
            segment = text[start:index + 1]
            cleaned, offset_left, offset_right = trim_segment(segment)
            if cleaned:
                sentences.append(
                    {
                        "text": cleaned,
                        "start": start + offset_left,
                        "end": start + offset_right,
                    }
                )
            start = index + 1
        index += 1
    if start < length:
        segment = text[start:length]
        cleaned, offset_left, offset_right = trim_segment(segment)
        if cleaned:
            sentences.append(
                {
                    "text": cleaned,
                    "start": start + offset_left,
                    "end": start + offset_right,
                }
            )
    return sentences


def run_sentences_pass(text, offset_index, llm_client, issue_id=None):
    generator = issue_id or IssueIdGenerator()
    issues = []
    edits = []
    sentences = split_sentences(text)
    for sentence in sentences:
        payload = {
            "task": "proofread_sentence",
            "schema": {
                "ok": {"status": "ok"},
                "edit": {
                    "status": "edit",
                    "original": "...",
                    "suggestion": "...",
                    "types": ["spelling"],
                    "explanation": "...",
                },
            },
            "sentence": sentence["text"],
        }
        response = llm_client.complete_json(
            SYSTEM_PROMPT,
            json.dumps(payload, ensure_ascii=False),
            temperature=0.0,
            max_tokens=64,
        )
        status = response.get("status")
        if status == "ok":
            continue
        if status == "edit":
            suggestion = response.get("suggestion", "")
            original = response.get("original", sentence["text"])
            types = response.get("types", ["grammar"])
            issue_type = types[0] if types else "grammar"
            start = sentence["start"]
            end = sentence["end"]
            if len(offset_index) > 0:
                mapped_start = min(start, len(offset_index) - 1)
                mapped_end = min(max(end, mapped_start + 1), len(offset_index))
            else:
                mapped_start = 0
                mapped_end = 0
            file_path = offset_index.file_at(mapped_start) if len(offset_index) > 0 else ""
            if not file_path and len(offset_index) > 0:
                file_path = offset_index.entries[0].file
            line = offset_index.line_at(mapped_start)
            issue = Issue(
                id=generator.next_id(),
                phase="typo",
                type=issue_type,
                severity="minor",
                span=Span(file=file_path, start=mapped_start, end=mapped_end, line=line),
                excerpt=original,
                suggestion=suggestion,
                explanation=response.get("explanation", ""),
                autofix="safe",
            )
            validate_issue(issue)
            issues.append(issue)
            edits.append({"original": original, "suggestion": suggestion})
    diff_text = sentence_diff(edits)
    return issues, edits, diff_text
