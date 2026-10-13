#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path


TARGET_CODE = "REGEX_DELIMITER_ESCAPE"


def is_escaped(line: str, index: int) -> bool:
    count = 0
    i = index - 1
    while i >= 0 and line[i] == "\\":
        count += 1
        i -= 1
    return count % 2 == 1


def first_non_space(line: str, start: int) -> int:
    for i in range(start, len(line)):
        if not line[i].isspace():
            return i
    return -1


def candidate_for_line(line: str):
    if is_line_comment(line):
        return None
    match_index = find_match_key_outside_string_and_comment(line)
    if match_index == -1:
        return None
    colon = line.find(":", match_index)
    first = first_non_space(line, colon + 1)
    if first == -1 or line[first] != "/":
        return None
    end = find_regex_literal_end(line, first)
    if end == -1:
        return None
    internal_slashes = [i for i in range(first + 1, end) if line[i] == "/" and not is_escaped(line, i)]
    if not internal_slashes:
        return None
    return internal_slashes


def find_match_key_outside_string_and_comment(line: str) -> int:
    # 只接受真实字段位置的 match，字符串或尾随注释里的示例不能被自动修复。
    in_string = False
    for i, ch in enumerate(line):
        if ch == '"' and not is_escaped(line, i):
            in_string = not in_string
            continue
        if in_string:
            continue
        if line.startswith("//", i):
            return -1
        if line.startswith("match:", i):
            return i
    return -1


def is_line_comment(line: str) -> bool:
    first = first_non_space(line, 0)
    return first != -1 and first + 1 < len(line) and line[first:first + 2] == "//"


def find_regex_literal_end(line: str, start: int) -> int:
    result = -1
    for i in range(start + 1, len(line)):
        if line[i] == "/" and not is_escaped(line, i):
            # 只有已经找到合法结束斜杠后，后续 // 才能安全视为行注释。
            if i + 1 < len(line) and line[i + 1] == "/" and result != -1:
                break
            next_index = first_non_space(line, i + 1)
            if next_index != -1 and line[next_index] == "+":
                # 拼接表达式可能包含 var(...) 等动态片段，局部脚本无法安全确定字面量边界。
                return -1
            if can_end_regex_literal(line, i):
                result = i
    return result


def can_end_regex_literal(line: str, slash_index: int) -> bool:
    next_index = first_non_space(line, slash_index + 1)
    if next_index == -1:
        return True
    ch = line[next_index]
    if ch in ",}]":
        return True
    if "0" <= ch <= "9":
        return True
    return any(starts_with_syntax_key(line, next_index, key) for key in (
        "recordAllGroups",
        "style",
        "childrenStyle",
        "contains",
        "matchEndFirst",
        "mustMatchEnd",
        "endPriority",
        "export",
    ))


def starts_with_syntax_key(line: str, start: int, key: str) -> bool:
    if not line.startswith(key, start):
        return False
    end = start + len(key)
    return end == len(line) or line[end] == ":" or line[end].isspace()


def find_unique(lines, preferred_line):
    ranges = []
    if preferred_line:
        start = max(1, preferred_line - 1)
        end = min(len(lines), preferred_line + 1)
        ranges.append(range(start, end + 1))
    ranges.append(range(1, len(lines) + 1))
    for line_range in ranges:
        found = []
        for line_no in line_range:
            slashes = candidate_for_line(lines[line_no - 1])
            if slashes:
                found.append((line_no, slashes))
        if len(found) == 1:
            return found[0]
    return None


def repair_line(line: str, slashes) -> str:
    internal = set(slashes)
    out = []
    for i, ch in enumerate(line):
        if i in internal:
            out.append("\\/")
        else:
            out.append(ch)
    return "".join(out)


def emit(ok, changed, reason, syntax_file, output, candidate_line):
    print(json.dumps({
        "ok": ok,
        "changed": changed,
        "reason": reason,
        "syntaxFile": syntax_file,
        "output": output,
        "candidateLine": candidate_line,
    }, ensure_ascii=False))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--syntax-file", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    try:
        report = json.loads(Path(args.report).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        emit(False, False, f"cannot read report: {exc}", args.syntax_file, args.output, None)
        return 1

    error = report.get("error") or {}
    if error.get("code") != TARGET_CODE:
        emit(False, False, "report error code is not REGEX_DELIMITER_ESCAPE", args.syntax_file, args.output, None)
        return 1

    try:
        original = Path(args.syntax_file).read_text(encoding="utf-8")
    except OSError as exc:
        emit(False, False, f"cannot read syntax file: {exc}", args.syntax_file, args.output, None)
        return 1

    lines = original.splitlines(keepends=True)
    bare_lines = [line[:-1] if line.endswith("\n") else line for line in lines]
    candidate = find_unique(bare_lines, error.get("line"))
    if not candidate:
        emit(False, False, "cannot locate a unique regex literal candidate", args.syntax_file, args.output, None)
        return 1

    line_no, slashes = candidate
    line = lines[line_no - 1]
    newline = "\n" if line.endswith("\n") else ""
    repaired = repair_line(line[:-1] if newline else line, slashes) + newline
    if repaired == line:
        emit(False, False, "candidate did not require changes", args.syntax_file, args.output, line_no)
        return 1

    lines[line_no - 1] = repaired
    try:
        Path(args.output).write_text("".join(lines), encoding="utf-8")
    except OSError as exc:
        emit(False, False, f"cannot write output: {exc}", args.syntax_file, args.output, line_no)
        return 1

    emit(True, True, "escaped unescaped slash characters inside regex literal", args.syntax_file, args.output, line_no)
    return 0


if __name__ == "__main__":
    sys.exit(main())
