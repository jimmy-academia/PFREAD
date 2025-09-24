import json
from dataclasses import dataclass, field


@dataclass
class Span:
    file: str
    start: int
    end: int
    line: int

    def to_dict(self):
        return {
            "file": self.file,
            "start": self.start,
            "end": self.end,
            "line": self.line,
        }


@dataclass
class Issue:
    id: str
    phase: str
    type: str
    severity: str
    span: Span
    excerpt: str
    suggestion: str
    explanation: str
    autofix: str
    evidence: dict = field(default_factory=dict)

    def to_dict(self):
        data = {
            "id": self.id,
            "phase": self.phase,
            "type": self.type,
            "severity": self.severity,
            "span": self.span.to_dict(),
            "excerpt": self.excerpt,
            "suggestion": self.suggestion,
            "explanation": self.explanation,
            "autofix": self.autofix,
        }
        if self.evidence:
            data["evidence"] = self.evidence
        return data


def issue_from_dict(data):
    span_data = data.get("span", {})
    span = Span(
        file=span_data.get("file", ""),
        start=span_data.get("start", 0),
        end=span_data.get("end", 0),
        line=span_data.get("line", 0),
    )
    return Issue(
        id=data.get("id", ""),
        phase=data.get("phase", ""),
        type=data.get("type", ""),
        severity=data.get("severity", "minor"),
        span=span,
        excerpt=data.get("excerpt", ""),
        suggestion=data.get("suggestion", ""),
        explanation=data.get("explanation", ""),
        autofix=data.get("autofix", "manual"),
        evidence=data.get("evidence", {}),
    )


class IssueIdGenerator:
    def __init__(self):
        self.counter = 1

    def next_id(self):
        value = self.counter
        self.counter += 1
        return "ISS-%06d" % value


def validate_issue(issue):
    required = {
        "phase": {"typo", "cross", "paragraph", "review"},
        "severity": {"minor", "moderate", "major"},
    }
    if issue.phase not in required["phase"]:
        raise ValueError("invalid phase")
    if issue.severity not in required["severity"]:
        raise ValueError("invalid severity")
    if issue.span.start < 0 or issue.span.end < issue.span.start:
        raise ValueError("invalid span")
    return True


def findings_json(meta, files, issues, review):
    payload = {
        "meta": meta,
        "files": files,
        "issues": [issue.to_dict() for issue in issues],
        "review": review,
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)
