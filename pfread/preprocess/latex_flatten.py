import hashlib
from pathlib import Path

from pfread.utils.offsets import OffsetIndex


STYLE_COMMANDS = {
    "textbf",
    "textit",
    "emph",
    "texttt",
    "textsc",
    "underline",
    "em",
    "bf",
    "it",
}


def remove_comment(line):
    result = []
    mapping = []
    escaped = False
    for index, char in enumerate(line):
        if char == "\\" and not escaped:
            escaped = True
            result.append(char)
            mapping.append(index)
            continue
        if char == "%" and not escaped:
            break
        result.append(char)
        mapping.append(index)
        if escaped:
            escaped = False
    return "".join(result), mapping


def _clean_segment(segment):
    pieces = []
    mapping = []
    index = 0
    while index < len(segment):
        char = segment[index]
        if char == "\\":
            end = index + 1
            while end < len(segment) and (segment[end].isalpha() or segment[end] in {"@"}):
                end += 1
            command = segment[index + 1:end]
            if end < len(segment) and segment[end] == "[":
                depth = 0
                pointer = end + 1
                while pointer < len(segment):
                    token = segment[pointer]
                    if token == "[":
                        depth += 1
                    elif token == "]":
                        if depth == 0:
                            break
                        depth -= 1
                    pointer += 1
                end = pointer + 1
            if end < len(segment) and segment[end] == "{":
                depth = 0
                pointer = end + 1
                while pointer < len(segment):
                    token = segment[pointer]
                    if token == "{":
                        depth += 1
                    elif token == "}":
                        if depth == 0:
                            break
                        depth -= 1
                    pointer += 1
                inner = segment[end + 1:pointer]
                inner_clean, inner_map = _clean_segment(inner)
                if command not in {"begin", "end"}:
                    pieces.append(inner_clean)
                    offset = end + 1
                    for pos in inner_map:
                        mapping.append(pos + offset)
                index = pointer + 1
                continue
            if command in STYLE_COMMANDS or command in {"begin", "end"}:
                index = end
                continue
            index = end
            continue
        pieces.append(char)
        mapping.append(index)
        index += 1
    return "".join(pieces), mapping


def clean_line(line):
    no_comment, base_map = remove_comment(line)
    cleaned, local_map = _clean_segment(no_comment)
    mapping = []
    for pos in local_map:
        mapping.append(base_map[pos])
    return cleaned, mapping


def flatten_sources(tex_files):
    index = OffsetIndex()
    combined = []
    file_records = []
    for path in tex_files:
        content = Path(path).read_text(encoding="utf-8")
        sha = hashlib.sha1(content.encode("utf-8")).hexdigest()
        file_records.append({"path": str(path), "sha": sha, "text": content})
        lines = content.splitlines()
        if content.endswith("\n"):
            lines.append("")
        for number, line in enumerate(lines, 1):
            cleaned, mapping = clean_line(line)
            combined.append(cleaned)
            index.extend_from_mapping(path, number, mapping)
            combined.append("\n")
            index.add_newline(path, number, len(line))
    text = "".join(combined)
    return {
        "text": text,
        "index": index,
        "files": file_records,
    }
