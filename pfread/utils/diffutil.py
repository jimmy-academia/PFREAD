import difflib


def sentence_diff(edits):
    hunks = []
    for edit in edits:
        original = edit.get("original", "").splitlines()
        suggestion = edit.get("suggestion", "").splitlines()
        diff = difflib.unified_diff(
            original,
            suggestion,
            fromfile="original",
            tofile="suggestion",
            lineterm="",
        )
        hunks.extend(list(diff))
    return "\n".join(hunks) + ("\n" if hunks else "")
