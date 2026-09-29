"""Tests for query-aware export (smart mode)."""

from pathlib import Path

from repo2ai.core import scan_repository
from repo2ai.smart import (
    LOCK_FILE_PATTERNS,
    BM25,
    classify_role,
    estimate_tokens,
    format_query_diagnostics,
    generate_smart_markdown,
    rank_and_pack,
    split_identifier,
    stem,
    tokenize_query,
)


def _write(repo: Path, rel: str, content: str) -> None:
    target = repo / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def _fixture_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _write(
        repo,
        "app/loader.py",
        "import json\n\n\n"
        "def load_gitignore(path):\n"
        '    """Parse ignore patterns from a file."""\n'
        "    return path.read_text().splitlines()\n",
    )
    _write(
        repo,
        "app/unrelated.py",
        "def compute_totals(rows):\n    return sum(rows)\n",
    )
    _write(repo, "schema.yml", "models:\n  - name: orders\n")
    _write(repo, "poetry.lock", "# lock content\n" * 50)
    return repo


def test_split_identifier_splits_snake_and_camel():
    assert "load" in split_identifier("load_gitignore")
    assert "gitignore" in split_identifier("load_gitignore")
    assert "parse" in split_identifier("parseGitignoreFile")


def test_tokenize_query_drops_stopwords():
    terms = tokenize_query("How does the gitignore parsing work")
    assert stem("gitignore") in terms
    assert "the" not in terms
    assert "how" not in terms


def test_stem_matches_query_wording_to_code_wording():
    # The pairs that keyword-only matching used to miss.
    assert stem("parsing") == stem("parse")
    assert stem("prices") == stem("price")
    assert stem("rounded") == stem("round") == stem("rounding")
    assert stem("queries") == stem("query")
    assert stem("settings") == stem("setting")


def test_stem_leaves_non_plural_s_endings_alone():
    for word in ("class", "status", "basis", "process", "pass"):
        assert stem(word) == word


def test_stem_never_strips_a_token_away():
    # stem() is applied exactly once per token (in tokenize), so it need not be
    # idempotent -- stem("pars") is "par". It must never return an empty or
    # one-character token, which would match almost everything.
    for word in (
        "parsing",
        "prices",
        "classes",
        "settings",
        "gitignore",
        "ies",
        "sses",
        "eed",
    ):
        assert len(stem(word)) >= 2


def test_query_diagnostics_report_terms_and_ranked_files(tmp_path):
    _write(
        tmp_path, "pricing.py", "def round_price(value):\n    return round(value, 2)\n"
    )
    _write(tmp_path, "other.py", "def unrelated():\n    return 1\n")
    scan = scan_repository(repo_path=tmp_path)
    result = rank_and_pack(scan, "where are prices rounded?", budget=5000)
    report = format_query_diagnostics(result)

    assert stem("prices") in report
    assert "pricing.py" in report
    # The stopwords never become search terms.
    assert "where" not in report.replace(result.query, "")


def test_query_diagnostics_name_terms_that_match_nothing(tmp_path):
    _write(
        tmp_path, "pricing.py", "def round_price(value):\n    return round(value, 2)\n"
    )
    scan = scan_repository(repo_path=tmp_path)
    result = rank_and_pack(scan, "kubernetes ingress", budget=5000)
    report = format_query_diagnostics(result)

    assert "No match in this repo" in report
    assert stem("kubernetes") in report


def test_estimate_tokens_is_never_zero():
    assert estimate_tokens("") == 1
    assert estimate_tokens("a" * 400) == 100


def test_bm25_ranks_matching_document_higher():
    bm25 = BM25([["gitignore", "parse"], ["totals", "sum"]])
    matching = bm25.score(["gitignore"], 0)
    other = bm25.score(["gitignore"], 1)
    assert matching > other


def test_classify_role_detects_contract_files():
    assert classify_role("schema.yml", "models:\n") == "contract"
    assert classify_role("app/loader.py", "def f():\n    pass\n") == "source"


def test_rank_and_pack_respects_budget(tmp_path):
    repo = _fixture_repo(tmp_path)
    scan = scan_repository(repo_path=repo)
    result = rank_and_pack(scan, "gitignore parsing", budget=2000)
    markdown = generate_smart_markdown(result)
    assert estimate_tokens(markdown) <= 2000


def test_rank_and_pack_manifest_lists_every_scanned_file(tmp_path):
    repo = _fixture_repo(tmp_path)
    scan = scan_repository(repo_path=repo)
    result = rank_and_pack(scan, "gitignore parsing", budget=4000)
    markdown = generate_smart_markdown(result)
    for repo_file in scan.files:
        rel = repo_file.path.relative_to(scan.repo_root).as_posix()
        assert rel in markdown


def test_lock_file_patterns_cover_common_ecosystems():
    for name in ("poetry.lock", "package-lock.json", "uv.lock", "Cargo.lock"):
        assert name in LOCK_FILE_PATTERNS
