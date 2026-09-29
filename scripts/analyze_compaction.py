"""
Compaction analysis for repo2ai exports (companion to smart.py prototype).

Breaks a repository's export down by content class (code, docstrings,
comments, markdown docs, config, lock files, scaffolding) and quantifies
what LOSSLESS structural compaction vs LOSSY prose compaction (caveman-
style, ~70% char reduction on prose) could save.

Usage:
    python scripts/analyze_compaction.py <repo_path>
"""

import io
import re
import sys
import tokenize as tok
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from repo2ai.core import scan_repository, generate_markdown  # noqa: E402

LOCK_FILES = {"poetry.lock", "package-lock.json", "package-lock.yml", "yarn.lock", "Cargo.lock", "uv.lock", "Pipfile.lock", "pnpm-lock.yaml"}
DOC_EXT = {".md", ".rst", ".txt", ".puml"}
CONFIG_EXT = {".yml", ".yaml", ".toml", ".json", ".ini", ".cfg", ".flake8"}

# Caveman-style prose compression, measured on a real example: 408 -> 112 chars
CAVEMAN_CHAR_RATIO = 0.72


def split_python(content: str):
    """Split Python source chars into (code, docstrings, comments)."""
    import ast

    docstring_chars = 0
    comment_chars = 0
    try:
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant) and isinstance(node.body[0].value.value, str):
                    seg = ast.get_source_segment(content, node.body[0])
                    if seg:
                        docstring_chars += len(seg)
    except SyntaxError:
        pass
    try:
        for t in tok.generate_tokens(io.StringIO(content).readline):
            if t.type == tok.COMMENT:
                comment_chars += len(t.string)
    except (tok.TokenizeError, IndentationError, SyntaxError):
        pass
    code_chars = len(content) - docstring_chars - comment_chars
    return code_chars, docstring_chars, comment_chars


def sql_comments(content: str) -> int:
    chars = 0
    for m in re.finditer(r"--[^\n]*|/\*.*?\*/", content, re.S):
        chars += len(m.group())
    return chars


def blank_line_savings(text: str) -> int:
    """Bytes saved by collapsing runs of 2+ blank lines to one."""
    collapsed = re.sub(r"\n{3,}", "\n\n", text)
    return len(text) - len(collapsed)


def main() -> None:
    repo = Path(sys.argv[1]).resolve()
    scan = scan_repository(repo)
    export = generate_markdown(scan)
    export_bytes = len(export.encode("utf-8"))

    classes = {
        "python code": 0,
        "python docstrings": 0,
        "python comments": 0,
        "sql code": 0,
        "sql comments": 0,
        "markdown/docs": 0,
        "config (yaml/toml/json/ini)": 0,
        "lock files": 0,
        "other source": 0,
    }
    content_total = 0
    lock_bytes = 0
    py_outline_candidates = 0

    for rf in scan.files:
        n = len(rf.content.encode("utf-8"))
        content_total += n
        name = rf.path.name
        suffix = rf.path.suffix.lower()
        if name in LOCK_FILES:
            classes["lock files"] += n
            lock_bytes += n
        elif rf.language == "python":
            code, doc, com = split_python(rf.content)
            classes["python code"] += code
            classes["python docstrings"] += doc
            classes["python comments"] += com
            py_outline_candidates += n
        elif suffix == ".sql":
            com = sql_comments(rf.content)
            classes["sql code"] += n - com
            classes["sql comments"] += com
        elif suffix in DOC_EXT or name.upper().startswith(("README", "LICENSE", "CHANGELOG", "CLAUDE")):
            classes["markdown/docs"] += n
        elif suffix in CONFIG_EXT:
            classes["config (yaml/toml/json/ini)"] += n
        else:
            classes["other source"] += n

    scaffolding = export_bytes - content_total

    print(f"repo: {repo.name}")
    print(f"full export: {export_bytes:,} bytes (~{export_bytes // 4:,} tokens est.)")
    print(f"scaffolding/headers (export minus file contents): {scaffolding:,} bytes ({100 * scaffolding / export_bytes:.1f}%)")
    print()
    print("content classes (of export):")
    for k, v in sorted(classes.items(), key=lambda kv: -kv[1]):
        print(f"  {k:32s} {v:>10,} bytes  {100 * v / export_bytes:5.1f}%")

    prose = classes["python docstrings"] + classes["python comments"] + classes["markdown/docs"] + classes["sql comments"]
    print()
    print(f"total prose-like (docstrings+comments+docs): {prose:,} bytes ({100 * prose / export_bytes:.1f}%)")

    print()
    print("LOSSLESS structural compaction:")
    bl = blank_line_savings(export)
    print(f"  drop lock files:           {lock_bytes:>10,} bytes ({100 * lock_bytes / export_bytes:5.1f}%)")
    print(f"  collapse 2+ blank lines:   {bl:>10,} bytes ({100 * bl / export_bytes:5.1f}%)")
    tw = sum(len(line) - len(line.rstrip()) for line in export.splitlines())
    print(f"  strip trailing whitespace: {tw:>10,} bytes ({100 * tw / export_bytes:5.1f}%)")

    print()
    print("LOSSY prose compaction (caveman-style, model call required):")
    lossy = int(prose * CAVEMAN_CHAR_RATIO)
    print(f"  ~{CAVEMAN_CHAR_RATIO:.0%} of prose chars removed:  {lossy:>10,} bytes ({100 * lossy / export_bytes:5.1f}%)")


if __name__ == "__main__":
    main()
