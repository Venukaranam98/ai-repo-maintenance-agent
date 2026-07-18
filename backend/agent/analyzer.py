import ast
import os
from dataclasses import dataclass, field
from typing import List


@dataclass
class Gap:
    """A single detected improvement opportunity."""
    category: str          # e.g. "missing_docstring", "stale_readme", "todo_comment"
    file_path: str
    detail: str
    priority: int           # 1 (low) - 5 (high)


@dataclass
class HealthReport:
    repo_path: str
    gaps: List[Gap] = field(default_factory=list)

    def top_gap(self) -> Gap | None:
        """Return the single highest-priority gap, or None if repo is healthy."""
        if not self.gaps:
            return None
        return sorted(self.gaps, key=lambda g: g.priority, reverse=True)[0]

    def to_dict(self) -> dict:
        return {
            "repo_path": self.repo_path,
            "gap_count": len(self.gaps),
            "gaps": [g.__dict__ for g in self.gaps],
        }


# Files/dirs we never want to touch or scan.
IGNORE_DIRS = {".git", "node_modules", "venv", ".venv", "__pycache__", "dist", "build"}


def _iter_python_files(repo_path: str):
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for f in files:
            if f.endswith(".py"):
                yield os.path.join(root, f)


def _check_missing_docstrings(repo_path: str) -> List[Gap]:
    """Find top-level functions/classes with no docstring."""
    gaps = []
    for path in _iter_python_files(repo_path):
        try:
            with open(path, "r", encoding="utf-8") as fh:
                source = fh.read()
            tree = ast.parse(source)
        except (SyntaxError, UnicodeDecodeError):
            continue  # skip files we can't safely parse

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if ast.get_docstring(node) is None and not node.name.startswith("_"):
                    rel = os.path.relpath(path, repo_path)
                    gaps.append(
                        Gap(
                            category="missing_docstring",
                            file_path=rel,
                            detail=f"'{node.name}' (line {node.lineno}) has no docstring",
                            priority=2,
                        )
                    )
    return gaps


def _check_todo_comments(repo_path: str) -> List[Gap]:
    """Find TODO/FIXME comments left in the code."""
    gaps = []
    for path in _iter_python_files(repo_path):
        try:
            with open(path, "r", encoding="utf-8") as fh:
                lines = fh.readlines()
        except UnicodeDecodeError:
            continue
        for i, line in enumerate(lines, start=1):
            if "TODO" in line or "FIXME" in line:
                rel = os.path.relpath(path, repo_path)
                gaps.append(
                    Gap(
                        category="todo_comment",
                        file_path=rel,
                        detail=f"Line {i}: {line.strip()[:120]}",
                        priority=1,
                    )
                )
    return gaps


def _check_readme(repo_path: str) -> List[Gap]:
    """Check whether README exists and has key sections."""
    gaps = []
    candidates = ["README.md", "Readme.md", "readme.md"]
    readme_path = next((c for c in candidates if os.path.exists(os.path.join(repo_path, c))), None)

    if readme_path is None:
        gaps.append(
            Gap(
                category="missing_readme",
                file_path="README.md",
                detail="Repository has no README.md file",
                priority=5,
            )
        )
        return gaps

    with open(os.path.join(repo_path, readme_path), "r", encoding="utf-8", errors="ignore") as fh:
        content = fh.read().lower()

    expected_sections = ["install", "usage", "license"]
    for section in expected_sections:
        if section not in content:
            gaps.append(
                Gap(
                    category="stale_readme",
                    file_path=readme_path,
                    detail=f"README is missing a '{section.title()}' section",
                    priority=3,
                )
            )
    return gaps


def _check_missing_tests(repo_path: str) -> List[Gap]:
    """Very simple heuristic: any top-level module with no matching test file."""
    gaps = []
    has_tests_dir = os.path.exists(os.path.join(repo_path, "tests"))
    if not has_tests_dir:
        gaps.append(
            Gap(
                category="missing_tests",
                file_path="tests/",
                detail="No tests/ directory found in the repository",
                priority=4,
            )
        )
    return gaps


def analyze_repo(repo_path: str) -> HealthReport:
    """
    Run all checks against a local repo clone and return a HealthReport.
    This is the entry point main.py / api routes call.
    """
    gaps: List[Gap] = []
    gaps += _check_readme(repo_path)
    gaps += _check_missing_tests(repo_path)
    gaps += _check_missing_docstrings(repo_path)
    gaps += _check_todo_comments(repo_path)

    return HealthReport(repo_path=repo_path, gaps=gaps)
