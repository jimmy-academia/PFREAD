from pfread.utils.schema import Issue, Span, issue_from_dict


def test_issue_round_trip():
    span = Span(file="paper.tex", start=5, end=15, line=2)
    issue = Issue(
        id="ISS-000123",
        phase="typo",
        type="spelling",
        severity="minor",
        span=span,
        excerpt="The orig text",
        suggestion="The original text",
        explanation="Fix spelling.",
        autofix="safe",
    )
    data = issue.to_dict()
    clone = issue_from_dict(data)
    assert clone == issue
