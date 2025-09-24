import re
from pathlib import Path

from pfread.utils.schema import Issue, IssueIdGenerator, Span, validate_issue

LABEL_PATTERN = re.compile(r"\\label\{([^}]+)\}")
REF_PATTERN = re.compile(r"\\(ref|eqref|autoref)\{([^}]+)\}")
CITE_PATTERN = re.compile(r"\\cite\{([^}]+)\}")
CAPTION_PATTERN = re.compile(r"\\caption\{([^}]*)\}")
SECTION_PATTERN = re.compile(r"\\(section|subsection|subsubsection)\{([^}]*)\}")


STYLE_LABELS = {
    "figure": ("Fig.", "Figure"),
    "section": ("Sec.", "Section"),
    "equation": ("Eq.", "Equation"),
}


def location_from_index(text, position):
    line = text.count("\n", 0, position) + 1
    prev = text.rfind("\n", 0, position)
    if prev == -1:
        column = position
    else:
        column = position - prev - 1
    return line, column


def infer_label_type(context):
    snippet = context.lower()
    if "equation" in snippet or "\begin{equation" in snippet or "eq:" in snippet:
        return "equation"
    if "figure" in snippet or "\\includegraphics" in snippet:
        return "figure"
    if "table" in snippet or "tabular" in snippet:
        return "table"
    if "section" in snippet:
        return "section"
    return "general"


def build_label_index(files):
    index = {}
    for record in files:
        path = record["path"]
        text = record["text"]
        for match in LABEL_PATTERN.finditer(text):
            key = match.group(1)
            line, _ = location_from_index(text, match.start())
            start_context = max(0, match.start() - 200)
            context = text[start_context:match.start()]
            label_type = infer_label_type(context)
            index[key] = {"file": path, "line": line, "type": label_type}
    return index


def parse_bib_keys(bib_path):
    if not bib_path:
        return set()
    try:
        text = Path(bib_path).read_text(encoding="utf-8")
    except FileNotFoundError:
        return set()
    keys = set()
    for match in re.finditer(r"@\w+\{([^,]+),", text):
        keys.add(match.group(1).strip())
    return keys


def run_cross_pass(files, offset_index, bib_path=None, issue_id=None):
    generator = issue_id or IssueIdGenerator()
    issues = []
    label_index = build_label_index(files)
    bib_keys = parse_bib_keys(bib_path)
    used_citations = set()

    for record in files:
        path = record["path"]
        text = record["text"]
        for match in REF_PATTERN.finditer(text):
            command = match.group(1)
            key = match.group(2)
            line, column = location_from_index(text, match.start())
            span = offset_index.global_range(path, line, column, len(match.group(0)))
            if span is None:
                start = 0
                end = 0
            else:
                start, end = span
            if key not in label_index:
                issue = Issue(
                    id=generator.next_id(),
                    phase="cross",
                    type="ref_error",
                    severity="moderate",
                    span=Span(file=path, start=start, end=end, line=line),
                    excerpt=match.group(0),
                    suggestion="Add the missing label or update the reference.",
                    explanation=f"Reference '{key}' is not defined.",
                    autofix="manual",
                )
                validate_issue(issue)
                issues.append(issue)
                continue
            label_type = label_index[key]["type"]
            if command == "eqref" and label_type != "equation":
                issue = Issue(
                    id=generator.next_id(),
                    phase="cross",
                    type="ref_error",
                    severity="moderate",
                    span=Span(file=path, start=start, end=end, line=line),
                    excerpt=match.group(0),
                    suggestion="Use the correct reference command for this label.",
                    explanation="Equation reference used for non-equation label.",
                    autofix="manual",
                )
                validate_issue(issue)
                issues.append(issue)
        for match in CITE_PATTERN.finditer(text):
            keys = [item.strip() for item in match.group(1).split(",")]
            line, column = location_from_index(text, match.start())
            span = offset_index.global_range(path, line, column, len(match.group(0)))
            if span is None:
                start = 0
                end = 0
            else:
                start, end = span
            for key in keys:
                if key:
                    used_citations.add(key)
                    if bib_keys and key not in bib_keys:
                        issue = Issue(
                            id=generator.next_id(),
                            phase="cross",
                            type="citation_missing",
                            severity="moderate",
                            span=Span(file=path, start=start, end=end, line=line),
                            excerpt=match.group(0),
                            suggestion=f"Add '{key}' to the bibliography.",
                            explanation="Citation key missing from bibliography.",
                            autofix="manual",
                        )
                        validate_issue(issue)
                        issues.append(issue)
        issues.extend(check_acronyms(record, offset_index, generator))
        issues.extend(check_styles(record, offset_index, generator))
        issues.extend(check_units(record, offset_index, generator))
    for key in sorted(bib_keys - used_citations):
        issue = Issue(
            id=generator.next_id(),
            phase="cross",
            type="citation_missing",
            severity="minor",
            span=Span(file=str(bib_path), start=0, end=0, line=1),
            excerpt=key,
            suggestion="Remove unused entry or cite it.",
            explanation="Bibliography entry is unused.",
            autofix="manual",
        )
        validate_issue(issue)
        issues.append(issue)
    return issues, label_index


def check_acronyms(record, offset_index, generator):
    path = record["path"]
    text = record["text"]
    issues = []
    definitions = {}
    positions = {}
    for match in re.finditer(r"([A-Za-z][^()]{2,}?)\s*\(([A-Z]{2,})\)", text):
        expansion = match.group(1).strip()
        acronym = match.group(2)
        line, column = location_from_index(text, match.start(2))
        span = offset_index.global_range(path, line, column, len(acronym))
        if span is None:
            start = 0
            end = 0
        else:
            start, end = span
        if acronym in definitions and definitions[acronym].lower() != expansion.lower():
            issue = Issue(
                id=generator.next_id(),
                phase="cross",
                type="acronym_inconsistent",
                severity="moderate",
                span=Span(file=path, start=start, end=end, line=line),
                excerpt=match.group(0),
                suggestion="Use a single expansion for the acronym.",
                explanation="Acronym defined with different expansions.",
                autofix="manual",
            )
            validate_issue(issue)
            issues.append(issue)
        else:
            definitions[acronym] = expansion
            positions[acronym] = match.start()
    for match in re.finditer(r"\b([A-Z]{2,})\b", text):
        acronym = match.group(1)
        if acronym in {"FIG", "SEC", "EQ"}:
            continue
        use_position = match.start()
        if acronym not in definitions or positions.get(acronym, use_position + 1) > use_position:
            line, column = location_from_index(text, use_position)
            span = offset_index.global_range(path, line, column, len(acronym))
            if span is None:
                start = 0
                end = 0
            else:
                start, end = span
            issue = Issue(
                id=generator.next_id(),
                phase="cross",
                type="acronym_inconsistent",
                severity="minor",
                span=Span(file=path, start=start, end=end, line=line),
                excerpt=acronym,
                suggestion=f"Define {acronym} at first use.",
                explanation="Acronym used before definition.",
                autofix="manual",
            )
            validate_issue(issue)
            issues.append(issue)
    return issues


def check_styles(record, offset_index, generator):
    path = record["path"]
    text = record["text"]
    issues = []
    for label_type, (short, long_form) in STYLE_LABELS.items():
        occurrences = []
        for match in re.finditer(r"\b(%s|%s)" % (re.escape(short), long_form), text):
            occurrences.append((match.group(0), match.start()))
        if not occurrences:
            continue
        count_short = sum(1 for token, _ in occurrences if token.startswith(short))
        count_long = len(occurrences) - count_short
        preferred = short if count_short >= count_long else long_form
        for token, position in occurrences:
            if token.startswith(preferred):
                continue
            line, column = location_from_index(text, position)
            span = offset_index.global_range(path, line, column, len(token))
            if span is None:
                start = 0
                end = 0
            else:
                start, end = span
            issue = Issue(
                id=generator.next_id(),
                phase="cross",
                type="style_inconsistency",
                severity="minor",
                span=Span(file=path, start=start, end=end, line=line),
                excerpt=token,
                suggestion=f"Use '{preferred}' consistently.",
                explanation="Inconsistent label style.",
                autofix="manual",
            )
            validate_issue(issue)
            issues.append(issue)
        pattern = re.compile(re.escape(short) + r"\s+[0-9]")
        for match in pattern.finditer(text):
            line, column = location_from_index(text, match.start())
            span = offset_index.global_range(path, line, column, len(match.group(0)))
            if span is None:
                start = 0
                end = 0
            else:
                start, end = span
            issue = Issue(
                id=generator.next_id(),
                phase="cross",
                type="style_inconsistency",
                severity="minor",
                span=Span(file=path, start=start, end=end, line=line),
                excerpt=match.group(0),
                suggestion="Insert '~' after the label.",
                explanation="Use non-breaking space after abbreviated label.",
                autofix="manual",
            )
            validate_issue(issue)
            issues.append(issue)
    range_pattern = re.compile(r"\b\d+-\d+\b")
    for match in range_pattern.finditer(text):
        line, column = location_from_index(text, match.start())
        span = offset_index.global_range(path, line, column, len(match.group(0)))
        if span is None:
            start = 0
            end = 0
        else:
            start, end = span
        issue = Issue(
            id=generator.next_id(),
            phase="cross",
            type="style_inconsistency",
            severity="minor",
            span=Span(file=path, start=start, end=end, line=line),
            excerpt=match.group(0),
            suggestion="Use an en-dash for ranges (e.g., 1--3).",
            explanation="Hyphen used for numeric range.",
            autofix="manual",
        )
        validate_issue(issue)
        issues.append(issue)
    return issues


def check_units(record, offset_index, generator):
    path = record["path"]
    text = record["text"]
    issues = []
    unit_pattern = re.compile(r"(\d)\s+(cm|mm|km|m|s|ms|kg|g|hz|%)", re.IGNORECASE)
    for match in unit_pattern.finditer(text):
        line, column = location_from_index(text, match.start())
        span = offset_index.global_range(path, line, column, len(match.group(0)))
        if span is None:
            start = 0
            end = 0
        else:
            start, end = span
        issue = Issue(
            id=generator.next_id(),
            phase="cross",
            type="unit_spacing",
            severity="minor",
            span=Span(file=path, start=start, end=end, line=line),
            excerpt=match.group(0),
            suggestion="Use '\\,' between value and unit.",
            explanation="Insert thin space before units.",
            autofix="manual",
        )
        validate_issue(issue)
        issues.append(issue)
    return issues
