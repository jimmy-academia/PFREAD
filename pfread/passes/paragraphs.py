import json

from pfread.utils.schema import Issue, IssueIdGenerator, Span, validate_issue

SYSTEM_PROMPT = (
    "You assess LaTeX paragraphs for clarity. Report diagnostics only, keep suggestions under fifteen words."
)


def split_paragraphs(text):
    paragraphs = []
    length = len(text)
    index = 0
    while index < length:
        while index < length and text[index].isspace():
            index += 1
        if index >= length:
            break
        end = text.find("\n\n", index)
        if end == -1:
            end = length
        block = text[index:end]
        paragraphs.append({"text": block, "start": index, "end": end})
        index = end + 2
    return paragraphs


def run_paragraph_pass(text, offset_index, llm_client, issue_id=None):
    generator = issue_id or IssueIdGenerator()
    issues = []
    for paragraph in split_paragraphs(text):
        if not paragraph["text"].strip():
            continue
        payload = {
            "task": "paragraph_diagnose",
            "style": {"tone": "neutral", "limit": "diagnostics_only"},
            "paragraph": paragraph["text"],
            "schema": [
                {
                    "type": "topic_drift",
                    "severity": "minor",
                    "span": {"start": 0, "end": 0},
                    "suggestion": "...",
                    "explanation": "...",
                }
            ],
        }
        response = llm_client.complete_json(
            SYSTEM_PROMPT,
            json.dumps(payload, ensure_ascii=False),
            temperature=0.2,
            max_tokens=320,
        )
        if not isinstance(response, list):
            continue
        for entry in response:
            span_data = entry.get("span", {})
            local_start = int(span_data.get("start", 0))
            local_end = int(span_data.get("end", local_start))
            if local_end < local_start:
                continue
            start = paragraph["start"] + local_start
            end = paragraph["start"] + local_end
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
                phase="paragraph",
                type=entry.get("type", "other"),
                severity=entry.get("severity", "minor"),
                span=Span(file=file_path, start=mapped_start, end=mapped_end, line=line),
                excerpt=paragraph["text"][local_start:local_end],
                suggestion=entry.get("suggestion", ""),
                explanation=entry.get("explanation", ""),
                autofix="manual",
            )
            validate_issue(issue)
            issues.append(issue)
    return issues
