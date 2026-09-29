"""
Smart search export: query-aware, budget-aware repository export.

PROTOTYPE — not wired into cli.py yet. Run standalone:

    python -m repo2ai.smart <path> --query "how is X done" --budget 30000

Instead of dumping the whole repository, this module ranks code CHUNKS
(Python: top-level functions/classes via ast; other files: line blocks)
against a natural-language query using BM25 over identifier sub-words,
expands the seed hits along the Python import graph (callers/callees come
along), then greedily packs the highest-scoring chunks into a hard token
budget. Everything that did not fit is still represented: a manifest table
up front and signature-level outlines at the end, so a tool-less model
knows what was omitted and can ask for it by path.

No external services, no API keys, stdlib only. Reuses scan_repository()
from core.py, so .gitignore handling, binary/size filtering and the
existing exclude flags all behave exactly like a normal export.
"""

import argparse
import ast
import math
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from .core import RepoFile, ScanResult, scan_repository

# Rough chars-per-token heuristic (GPT/Claude English+code averages ~4).
CHARS_PER_TOKEN = 4

_IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_CAMEL_RE = re.compile(r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z]+|[A-Z]+|[0-9]+")

_STOPWORDS = frozenset(
    "the a an is are was were be been being to of in on for with how what "
    "where when why which do does did done and or not this that it its "
    "from by as at we you i can could should would".split()
)


# Lock files are 31-36% of a typical export and never answer a question.
# Excluded by default in query mode; `--locks` keeps them.
LOCK_FILE_PATTERNS = (
    "poetry.lock",
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "uv.lock",
    "Cargo.lock",
    "Gemfile.lock",
    "composer.lock",
    "go.sum",
    "Pipfile.lock",
    "package-lock.yml",
)


def estimate_tokens(text: str) -> int:
    """Cheap token estimate: len/4, floor 1."""
    return max(1, len(text) // CHARS_PER_TOKEN)


def split_identifier(ident: str) -> List[str]:
    """Split snake_case and camelCase identifiers into lowercase sub-words."""
    parts: List[str] = []
    for piece in ident.split("_"):
        if not piece:
            continue
        parts.extend(m.lower() for m in _CAMEL_RE.findall(piece))
    return parts


def tokenize(text: str) -> List[str]:
    """Tokenize text/code into lowercase sub-word tokens for ranking."""
    tokens: List[str] = []
    for ident in _IDENT_RE.findall(text):
        lower = ident.lower()
        subs = split_identifier(ident)
        tokens.extend(subs)
        # Keep the whole identifier too so exact matches rank higher
        if len(subs) > 1:
            tokens.append(lower)
    return [t for t in tokens if len(t) > 1 and t not in _STOPWORDS]


def tokenize_query(query: str) -> List[str]:
    return tokenize(query)


@dataclass
class Chunk:
    """A rankable, packable unit of repository content."""

    rel_path: str
    start_line: int  # 1-based, inclusive
    end_line: int
    text: str
    kind: str  # "module", "def name", "class Name", "block", "file"
    symbols: List[str] = field(default_factory=list)
    tokens: int = 0
    score: float = 0.0

    def __post_init__(self) -> None:
        if not self.tokens:
            self.tokens = estimate_tokens(self.text)


def _chunk_blocks(rel_path: str, content: str, block_lines: int = 80) -> List[Chunk]:
    """Fallback chunker: fixed line blocks."""
    lines = content.splitlines()
    chunks = []
    for start in range(0, len(lines), block_lines):
        block = lines[start : start + block_lines]
        chunks.append(
            Chunk(
                rel_path=rel_path,
                start_line=start + 1,
                end_line=start + len(block),
                text="\n".join(block),
                kind="block",
            )
        )
    return chunks


def _chunk_python(rel_path: str, content: str) -> List[Chunk]:
    """Chunk a Python file into module header + top-level defs/classes."""
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return _chunk_blocks(rel_path, content)

    lines = content.splitlines()
    chunks: List[Chunk] = []
    covered: Set[int] = set()

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            start = min([node.lineno] + [d.lineno for d in node.decorator_list])
            end = node.end_lineno or node.lineno
            covered.update(range(start, end + 1))
            symbols = [node.name]
            if isinstance(node, ast.ClassDef):
                symbols.extend(
                    child.name
                    for child in node.body
                    if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
                )
                kind = f"class {node.name}"
            else:
                kind = f"def {node.name}"
            chunks.append(
                Chunk(
                    rel_path=rel_path,
                    start_line=start,
                    end_line=end,
                    text="\n".join(lines[start - 1 : end]),
                    kind=kind,
                    symbols=symbols,
                )
            )

    # Everything not covered (imports, module docstring, constants) → header chunk
    header_lines = [
        (i + 1, line)
        for i, line in enumerate(lines)
        if (i + 1) not in covered and line.strip()
    ]
    if header_lines:
        text = "\n".join(line for _, line in header_lines)
        chunks.insert(
            0,
            Chunk(
                rel_path=rel_path,
                start_line=header_lines[0][0],
                end_line=header_lines[-1][0],
                text=text,
                kind="module",
            ),
        )
    return chunks


def chunk_file(repo_file: RepoFile, repo_root: Path) -> List[Chunk]:
    rel_path = str(repo_file.path.relative_to(repo_root))
    if repo_file.language == "python":
        return _chunk_python(rel_path, repo_file.content)
    # Small non-Python files stay whole; large ones get block-split
    if len(repo_file.content.splitlines()) <= 120:
        return [
            Chunk(
                rel_path=rel_path,
                start_line=1,
                end_line=max(1, len(repo_file.content.splitlines())),
                text=repo_file.content,
                kind="file",
            )
        ]
    return _chunk_blocks(rel_path, repo_file.content)


class BM25:
    """Minimal BM25 over pre-tokenized chunk documents."""

    def __init__(self, docs: List[List[str]], k1: float = 1.2, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.doc_freqs = [Counter(d) for d in docs]
        self.doc_lens = [len(d) for d in docs]
        self.avg_len = (sum(self.doc_lens) / len(docs)) if docs else 0.0
        self.n_docs = len(docs)
        df: Counter = Counter()
        for freqs in self.doc_freqs:
            df.update(freqs.keys())
        self.idf = {
            term: math.log(1 + (self.n_docs - n + 0.5) / (n + 0.5))
            for term, n in df.items()
        }

    def score(self, query_terms: List[str], doc_idx: int) -> float:
        freqs = self.doc_freqs[doc_idx]
        dlen = self.doc_lens[doc_idx]
        if not dlen or not self.avg_len:
            return 0.0
        score = 0.0
        for term in query_terms:
            tf = freqs.get(term, 0)
            if not tf:
                continue
            idf = self.idf.get(term, 0.0)
            score += idf * (
                tf
                * (self.k1 + 1)
                / (tf + self.k1 * (1 - self.b + self.b * dlen / self.avg_len))
            )
        return score


def _path_boost(rel_path: str, query_terms: Set[str]) -> float:
    """Boost chunks whose file path contains query terms."""
    path_terms = set(tokenize(rel_path.replace("/", " ")))
    hits = len(path_terms & query_terms)
    return 1.5 * hits


def _symbol_boost(chunk: Chunk, query_terms: Set[str]) -> float:
    """Boost chunks whose symbol names match query terms."""
    boost = 0.0
    for sym in chunk.symbols:
        subs = set(split_identifier(sym)) | {sym.lower()}
        hits = len(subs & query_terms)
        if hits:
            boost += 2.0 * hits
    return boost


def _module_candidates(rel_path: str) -> List[str]:
    """Dotted-module names a repo file can be imported as (suffix forms)."""
    p = Path(rel_path)
    if p.suffix != ".py":
        return []
    parts = list(p.with_suffix("").parts)
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    if not parts:
        return []
    # 'src/repo2ai/core.py' → ['src.repo2ai.core', 'repo2ai.core', 'core']
    return [".".join(parts[i:]) for i in range(len(parts))]


def build_import_graph(files: List[RepoFile], repo_root: Path) -> Dict[str, Set[str]]:
    """Undirected import graph between repo Python files (rel-path keyed)."""
    module_to_path: Dict[str, str] = {}
    py_files: List[Tuple[str, RepoFile]] = []
    for rf in files:
        rel = str(rf.path.relative_to(repo_root))
        if rf.language != "python":
            continue
        py_files.append((rel, rf))
        for cand in _module_candidates(rel):
            module_to_path.setdefault(cand, rel)

    graph: Dict[str, Set[str]] = defaultdict(set)

    def resolve(module: str) -> Optional[str]:
        # Longest suffix match against known repo modules
        parts = module.split(".")
        for end in range(len(parts), 0, -1):
            hit = module_to_path.get(".".join(parts[:end]))
            if hit:
                return hit
        return None

    for rel, rf in py_files:
        try:
            tree = ast.parse(rf.content)
        except SyntaxError:
            continue
        pkg_parts = list(Path(rel).parent.parts)
        for node in ast.walk(tree):
            targets: List[str] = []
            if isinstance(node, ast.Import):
                targets = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                if node.level:  # relative import
                    base = pkg_parts[: len(pkg_parts) - (node.level - 1)]
                    prefix = ".".join(base)
                    mod = node.module or ""
                    stem = f"{prefix}.{mod}".strip(".") if prefix else mod
                    if stem:
                        targets = [stem]
                        targets += [f"{stem}.{a.name}" for a in node.names]
                elif node.module:
                    targets = [node.module]
                    targets += [f"{node.module}.{a.name}" for a in node.names]
            for target in targets:
                dep = resolve(target)
                if dep and dep != rel:
                    graph[rel].add(dep)
                    graph[dep].add(rel)
    return dict(graph)


_CONTRACT_NAMES = {
    "schema.yml",
    "schema.yaml",
    "sources.yml",
    "sources.yaml",
    "exposures.yml",
    "openapi.yml",
    "openapi.yaml",
    "openapi.json",
    "swagger.yml",
    "swagger.yaml",
    "swagger.json",
}
_CONTRACT_SUFFIXES = {".proto", ".avsc", ".graphql", ".thrift"}
_LOCK_NAMES = {
    "poetry.lock",
    "package-lock.json",
    "package-lock.yml",
    "yarn.lock",
    "cargo.lock",
    "uv.lock",
    "pipfile.lock",
    "pnpm-lock.yaml",
}
_DDL_RE = re.compile(
    r"\bCREATE\s+(OR\s+REPLACE\s+)?(TABLE|VIEW|EXTERNAL\s+TABLE)\b", re.I
)


def classify_role(rel_path: str, content: str = "") -> str:
    """Classify a file into a role: contract|lock|test|docs|config|source."""
    p = Path(rel_path)
    name = p.name.lower()
    if name in _LOCK_NAMES:
        return "lock"
    if (
        name in _CONTRACT_NAMES
        or p.suffix.lower() in _CONTRACT_SUFFIXES
        or (p.suffix.lower() == ".sql" and _DDL_RE.search(content or ""))
        or (p.suffix.lower() == ".json" and '"$schema"' in (content or "")[:2000])
    ):
        return "contract"
    top = rel_path.split("/", 1)[0].lower()
    if (
        top in ("tests", "test")
        or name.startswith("test_")
        or name.endswith("_test.py")
    ):
        return "test"
    if top in ("docs", "doc") or p.suffix.lower() in (".md", ".rst", ".txt", ".puml"):
        return "docs"
    if p.suffix.lower() in (".yml", ".yaml", ".toml", ".json", ".ini", ".cfg"):
        return "config"
    return "source"


def external_imports(files: List[RepoFile], repo_root: Path) -> Dict[str, List[str]]:
    """Per-file third-party top-level imports (not stdlib, not in-repo)."""
    in_repo: Set[str] = set()
    for rf in files:
        rel = str(rf.path.relative_to(repo_root))
        for cand in _module_candidates(rel):
            in_repo.add(cand.split(".")[0])
    stdlib = set(getattr(sys, "stdlib_module_names", ()))
    result: Dict[str, List[str]] = {}
    for rf in files:
        if rf.language != "python":
            continue
        try:
            tree = ast.parse(rf.content)
        except SyntaxError:
            continue
        mods: Set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                mods.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
                mods.add(node.module.split(".")[0])
        ext = sorted(m for m in mods if m not in stdlib and m not in in_repo)
        if ext:
            result[str(rf.path.relative_to(repo_root))] = ext
    return result


@dataclass
class SmartResult:
    """Everything needed to render the smart export."""

    query: str
    budget: int
    chunks: List[Chunk]  # all chunks, scored
    selected: List[Chunk]  # packed subset, in pack order
    file_status: Dict[str, str]  # rel_path -> full|partial|outline|omitted
    file_scores: Dict[str, float]
    file_roles: Dict[str, str]  # rel_path -> contract|lock|test|docs|config|source
    ext_imports: Dict[str, List[str]]  # rel_path -> third-party imports
    outline_budget: int  # token cap for the outline section
    scan: ScanResult


def _path_prior(rel_path: str) -> float:
    """Mild source-first prior: tests and docs matter, but source wins ties."""
    top = rel_path.split("/", 1)[0]
    if top in ("tests", "test", "docs", "doc", "examples"):
        return 0.7
    return 1.0


def rank_and_pack(
    scan: ScanResult,
    query: str,
    budget: int,
    hops: int = 1,
    neighbor_factor: float = 0.35,
    outline_ratio: float = 0.15,
) -> SmartResult:
    """Rank chunks against query, expand via imports, pack into budget."""
    repo_root = scan.repo_root
    chunks: List[Chunk] = []
    for rf in scan.files:
        chunks.extend(chunk_file(rf, repo_root))

    query_terms = tokenize_query(query)
    query_term_set = set(query_terms)

    docs = [tokenize(c.text) + tokenize(c.rel_path.replace("/", " ")) for c in chunks]
    bm25 = BM25(docs)
    for i, chunk in enumerate(chunks):
        chunk.score = _path_prior(chunk.rel_path) * (
            bm25.score(query_terms, i)
            + _path_boost(chunk.rel_path, query_term_set)
            + _symbol_boost(chunk, query_term_set)
        )

    # File-level scores = max chunk score per file
    file_scores: Dict[str, float] = defaultdict(float)
    for chunk in chunks:
        file_scores[chunk.rel_path] = max(file_scores[chunk.rel_path], chunk.score)

    # Import-graph expansion: neighbors of high-scoring files get a floor score
    graph = build_import_graph(scan.files, repo_root)
    current = dict(file_scores)
    for _ in range(max(0, hops)):
        floors: Dict[str, float] = {}
        for rel, score in current.items():
            if score <= 0:
                continue
            for neighbor in graph.get(rel, ()):
                floor = score * neighbor_factor
                if floor > current.get(neighbor, 0.0):
                    floors[neighbor] = max(floors.get(neighbor, 0.0), floor)
        for rel, floor in floors.items():
            current[rel] = floor
    for chunk in chunks:
        floor = current.get(chunk.rel_path, 0.0)
        if chunk.score <= 0 and floor > 0:
            # Graph-pulled chunk: inherit a fraction so it can compete
            chunk.score = floor * 0.5
    file_scores = defaultdict(float)
    for chunk in chunks:
        file_scores[chunk.rel_path] = max(file_scores[chunk.rel_path], chunk.score)

    # Contract-file rule: a contract file (schema.yml, sources.yml, .proto,
    # DDL, ...) is floored to 60% of the best score in its own directory.
    # Contracts describe the data other selected files produce or consume,
    # so they must never lose the packing race by lexical accident.
    roles = {
        str(rf.path.relative_to(repo_root)): classify_role(
            str(rf.path.relative_to(repo_root)), rf.content
        )
        for rf in scan.files
    }
    dir_best: Dict[str, float] = defaultdict(float)
    for rel, score in file_scores.items():
        dir_best[str(Path(rel).parent)] = max(dir_best[str(Path(rel).parent)], score)
    for rel, role in roles.items():
        if role != "contract":
            continue
        floor = 0.6 * dir_best.get(str(Path(rel).parent), 0.0)
        if floor > file_scores.get(rel, 0.0):
            for chunk in chunks:
                if chunk.rel_path == rel and chunk.score < floor:
                    chunk.score = floor
            file_scores[rel] = floor

    # Greedy packing, reserving space for manifest + outlines.
    # Manifest cost is estimated from the actual row contents; each packed
    # chunk adds ~25 tokens of heading/fence scaffolding around its content.
    ext_imports = external_imports(scan.files, repo_root)
    manifest_cost = (
        sum(estimate_tokens(rel) + 12 for rel in file_scores)
        + sum(
            estimate_tokens(rel) + estimate_tokens(", ".join(deps))
            for rel, deps in ext_imports.items()
        )
        + 150
    )
    chunk_overhead = 25
    content_budget = int(budget * (1 - outline_ratio)) - manifest_cost
    ranked = sorted(
        (c for c in chunks if c.score > 0),
        key=lambda c: (-c.score, c.rel_path, c.start_line),
    )
    selected: List[Chunk] = []
    used = 0
    for chunk in ranked:
        cost = chunk.tokens + chunk_overhead
        if used + cost <= content_budget:
            selected.append(chunk)
            used += cost

    selected_by_file: Dict[str, int] = Counter(c.rel_path for c in selected)
    total_by_file: Dict[str, int] = Counter(c.rel_path for c in chunks)
    file_status = {}
    for rel in total_by_file:
        n_sel = selected_by_file.get(rel, 0)
        if n_sel == total_by_file[rel]:
            file_status[rel] = "full"
        elif n_sel > 0:
            file_status[rel] = "partial"
        elif file_scores.get(rel, 0.0) > 0:
            file_status[rel] = "outline"
        else:
            file_status[rel] = "omitted"

    return SmartResult(
        query=query,
        budget=budget,
        chunks=chunks,
        selected=selected,
        file_status=file_status,
        file_scores=dict(file_scores),
        file_roles=roles,
        ext_imports=ext_imports,
        outline_budget=int(budget * outline_ratio),
        scan=scan,
    )


def _python_outline(content: str) -> List[str]:
    """Signature-level outline of a Python file: defs/classes + docstring gist."""
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return []
    lines: List[str] = []

    def sig(node: ast.AST, indent: str = "") -> None:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = ", ".join(a.arg for a in node.args.args)
            lines.append(f"{indent}def {node.name}({args})")
        elif isinstance(node, ast.ClassDef):
            lines.append(f"{indent}class {node.name}")
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    sig(child, indent + "    ")

    doc = ast.get_docstring(tree)
    if doc:
        lines.append(f"# {doc.strip().splitlines()[0]}")
    for node in tree.body:
        sig(node)
    return lines


def generate_smart_markdown(result: SmartResult) -> str:
    """Render the smart export: manifest, packed content, outlines."""
    scan = result.scan
    repo_name = scan.repo_root.name
    out: List[str] = []

    out.append(f"# {repo_name} — smart export")
    out.append("")
    out.append(f"**Query:** {result.query}")
    out.append(f"**Token budget:** {result.budget}")
    out.append("")
    out.append(
        "This is a query-focused slice of the repository, not a full dump. "
        "The manifest lists every file and whether it is included in full, "
        "partially, as a signature outline, or omitted. If you need an "
        "omitted or outlined file, ask for it by path."
    )
    out.append("")

    # Manifest
    out.append("## Manifest")
    out.append("")
    out.append("| File | Role | Status | Relevance |")
    out.append("|---|---|---|---|")
    order = sorted(
        result.file_status.items(),
        key=lambda kv: (-result.file_scores.get(kv[0], 0.0), kv[0]),
    )
    for rel, status in order:
        score = result.file_scores.get(rel, 0.0)
        role = result.file_roles.get(rel, "source")
        out.append(f"| `{rel}` | {role} | {status} | {score:.1f} |")
    out.append("")

    if result.ext_imports:
        out.append("### Third-party imports by file")
        out.append("")
        for rel in sorted(result.ext_imports):
            deps = ", ".join(result.ext_imports[rel])
            out.append(f"- `{rel}`: {deps}")
        out.append("")

    # Selected content, grouped by file, chunks in source order
    out.append("## Selected content")
    out.append("")
    by_file: Dict[str, List[Chunk]] = defaultdict(list)
    for chunk in result.selected:
        by_file[chunk.rel_path].append(chunk)
    lang_by_path = {
        str(rf.path.relative_to(scan.repo_root)): (rf.language or "")
        for rf in scan.files
    }
    for rel in sorted(by_file, key=lambda r: -max(c.score for c in by_file[r])):
        file_chunks = sorted(by_file[rel], key=lambda c: c.start_line)
        status = result.file_status[rel]
        out.append(f"### {rel} ({status})")
        out.append("")
        lang = lang_by_path.get(rel, "")
        for chunk in file_chunks:
            out.append(f"**{chunk.kind}** — lines {chunk.start_line}-{chunk.end_line}")
            out.append(f"```{lang}")
            out.append(chunk.text)
            out.append("```")
            out.append("")

    # Outlines for relevant-but-unpacked files
    outline_files = [
        rel for rel, status in order if result.file_status[rel] == "outline"
    ]
    partial_files = [
        rel for rel, status in order if result.file_status[rel] == "partial"
    ]
    if outline_files or partial_files:
        out.append("## Outlines of files not fully included")
        out.append("")
        content_by_path = {
            str(rf.path.relative_to(scan.repo_root)): rf.content for rf in scan.files
        }
        outline_used = 0
        skipped = 0
        for rel in outline_files + partial_files:
            sig_lines = _python_outline(content_by_path.get(rel, ""))
            if not sig_lines:
                continue
            text = "\n".join(sig_lines)
            cost = estimate_tokens(text) + 15
            if outline_used + cost > result.outline_budget:
                skipped += 1
                continue
            outline_used += cost
            out.append(f"### {rel}")
            out.append("```")
            out.extend(sig_lines)
            out.append("```")
            out.append("")
        if skipped:
            out.append(
                f"({skipped} more outlines omitted for budget; "
                "see manifest for the file list.)"
            )
            out.append("")

    return "\n".join(out)


def create_smart_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="repo2ai-smart",
        description="Query-aware, budget-aware repository export (prototype)",
    )
    parser.add_argument("path", nargs="?", default=".")
    parser.add_argument("--query", "-q", required=True, help="Question or topic")
    parser.add_argument(
        "--budget",
        type=int,
        default=30000,
        help="Hard token ceiling for the export (default: 30000)",
    )
    parser.add_argument(
        "--hops",
        type=int,
        default=1,
        help="Import-graph expansion hops from seed hits (default: 1)",
    )
    parser.add_argument("--output", "-o", type=Path)
    parser.add_argument("--stdout", "-s", action="store_true")
    parser.add_argument("--exclude", action="append", metavar="PATTERN")
    parser.add_argument("--no-meta", action="store_true")
    parser.add_argument("--max-file-size", type=int, default=1024 * 1024)
    parser.add_argument("-v", "--verbose", action="store_true")
    return parser


def main() -> None:
    args = create_smart_parser().parse_args()
    repo_path = Path(args.path).resolve()
    if not repo_path.is_dir():
        print(f"Error: not a directory: {repo_path}", file=sys.stderr)
        sys.exit(1)

    print("Scanning repository...", file=sys.stderr)
    scan = scan_repository(
        repo_path=repo_path,
        ignore_patterns=args.exclude or [],
        exclude_meta_files=args.no_meta,
        max_file_size=args.max_file_size,
        verbose=args.verbose,
    )

    print(f"Ranking {len(scan.files)} files against query...", file=sys.stderr)
    result = rank_and_pack(scan, query=args.query, budget=args.budget, hops=args.hops)
    markdown = generate_smart_markdown(result)

    if args.output:
        args.output.write_text(markdown, encoding="utf-8")
        print(f"Written to {args.output}", file=sys.stderr)
    else:
        print(markdown)

    est = estimate_tokens(markdown)
    n_full = sum(1 for s in result.file_status.values() if s == "full")
    n_partial = sum(1 for s in result.file_status.values() if s == "partial")
    print(
        f"✓ {len(scan.files)} files scanned → {n_full} full + {n_partial} partial "
        f"packed, ~{est} tokens (budget {args.budget}, "
        f"{len(markdown)} chars)",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
