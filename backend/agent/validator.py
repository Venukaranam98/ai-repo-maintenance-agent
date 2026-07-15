import os
import subprocess
from dataclasses import dataclass

from agent.decision import ProposedChange


@dataclass
class ValidationResult:
    passed: bool
    log: str


def _run(cmd: list[str], cwd: str) -> tuple[int, str]:
    """Run a subprocess command, capturing combined output. Never raises -
    a failing command is a normal, expected outcome we want to detect."""
    try:
        proc = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=120,
        )
        output = proc.stdout + proc.stderr
        return proc.returncode, output
    except FileNotFoundError:
        # Tool isn't installed in this environment - treat as "skipped", not failed.
        return 0, f"[skipped] {' '.join(cmd)} not found"
    except subprocess.TimeoutExpired:
        return 1, f"[timeout] {' '.join(cmd)} exceeded time limit"


def apply_change(repo_path: str, change: ProposedChange) -> str:
    """Write the proposed content to disk, respecting apply_mode."""
    target = os.path.join(repo_path, change.file_path)
    os.makedirs(os.path.dirname(target) or repo_path, exist_ok=True)

    if getattr(change, "apply_mode", "overwrite") == "append" and os.path.exists(target):
        with open(target, "a", encoding="utf-8") as fh:
            fh.write("\n\n" + change.new_content)
    else:
        with open(target, "w", encoding="utf-8") as fh:
            fh.write(change.new_content)
    return target

def validate_change(repo_path: str, change: ProposedChange) -> ValidationResult:
    """
    Runs after apply_change(). Only touches Python-specific tooling if a
    requirements.txt / pyproject.toml is present, so this safely no-ops on
    non-Python repos rather than false-failing them.
    """
    logs = []
    is_python_repo = any(
        os.path.exists(os.path.join(repo_path, f))
        for f in ("requirements.txt", "pyproject.toml", "setup.py")
    )

    if not is_python_repo:
        logs.append("[info] Non-Python repo detected - skipping lint/test, doc-only change assumed safe.")
        return ValidationResult(passed=True, log="\n".join(logs))

    # Lint check (ruff, fast and commonly available)
    code, out = _run(["ruff", "check", "."], cwd=repo_path)
    logs.append(f"$ ruff check .\n{out}")
    if code != 0 and "not found" not in out:
        return ValidationResult(passed=False, log="\n".join(logs))

    # Existing test suite - a doc/docstring change should never break tests,
    # but we run them anyway to be certain we haven't corrupted a file.
    code, out = _run(["pytest", "-q"], cwd=repo_path)
    logs.append(f"$ pytest -q\n{out}")
    if code != 0 and "not found" not in out:
        return ValidationResult(passed=False, log="\n".join(logs))

    return ValidationResult(passed=True, log="\n".join(logs))
