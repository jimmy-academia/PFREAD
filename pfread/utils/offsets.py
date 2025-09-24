from dataclasses import dataclass


@dataclass
class OffsetEntry:
    file: str
    line: int
    column: int


class OffsetIndex:
    def __init__(self):
        self.entries = []

    def __len__(self):
        return len(self.entries)

    def add(self, file_path, line, column):
        self.entries.append(OffsetEntry(str(file_path), line, column))

    def extend_from_mapping(self, file_path, line, mapping):
        for column in mapping:
            self.add(file_path, line, column)

    def add_newline(self, file_path, line, column):
        self.add(file_path, line, column)

    def global_range(self, file_path, line, column, length):
        start = self._find_position(file_path, line, column)
        if start is None:
            return None
        end_column = column + max(length, 0)
        end = self._find_position(file_path, line, end_column)
        if end is None:
            end = start + length
        return (start, max(end, start + length))

    def _find_position(self, file_path, line, column):
        for idx, entry in enumerate(self.entries):
            if entry.file == str(file_path) and entry.line == line and entry.column >= column:
                return idx
        return None

    def global_from_local(self, file_path, line, column):
        for idx, entry in enumerate(self.entries):
            if entry.file == str(file_path) and entry.line == line and entry.column == column:
                return idx
        return None

    def span_for(self, start, end):
        if not self.entries:
            return None
        length = len(self.entries)
        left = min(max(start, 0), length - 1)
        right_index = min(max(end - 1, 0), length - 1)
        start_entry = self.entries[left]
        end_entry = self.entries[right_index]
        return {
            "file": start_entry.file,
            "start": start,
            "end": end,
            "line": start_entry.line,
            "end_line": end_entry.line,
        }

    def line_at(self, position):
        if position < 0 or position >= len(self.entries):
            return 0
        return self.entries[position].line

    def file_at(self, position):
        if position < 0 or position >= len(self.entries):
            return ""
        return self.entries[position].file
