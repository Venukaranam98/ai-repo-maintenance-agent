"""
orchestrator.py

The single place that wires every module together into one end-to-end run:

    clone -> analyze -> decide -> validate -> commit/push -> open PR -> log

Both the CLI entry point (main.py, used by the GitHub Actions cron job) and
the dashboard's "Scan now" button (api/routes.py) call this same function,
so there is exactly one code path for "what the agent actually does."
"""

import json
import time
import traceback

from agent.analyzer import analyze_repo
from agent.config import settings
from agent.decision import propose_change
from agent.git_ops import clone_repo, create_branch, commit_and_push, cleanup
from agent.github_pr import open_pull_request, get_default_branch, merge_pull_request
from agent.validator import apply_change, validate_change
from api.models import SessionLocal, MonitoredRepo, AgentRun


def run_agent_for_repo(full_name: str, github_token: str, monitored_repo_id: int | None = None) -> dict:
    """
    Run the full pipeline for one "owner/repo" string.

    Returns a summary dict, and (if monitored_repo_id is given) also writes
    an AgentRun row so the dashboard's history view can show it.
    """
    db = SessionLocal()
    run_row = None
    if monitored_repo_id is not None:
        run_row = AgentRun(repo_id=monitored_repo_id, status="pending")
        db.add(run_row)
        db.commit()
        db.refresh(run_row)

    repo_path = None
    try:
        # 1. Clone
        repo_path = clone_repo(full_name, github_token)

        # 2. Analyze
        report = analyze_repo(repo_path)
        if run_row:
            run_row.gap_summary = json.dumps(report.to_dict())
            db.commit()

        if not report.gaps:
            if run_row:
                run_row.status = "no_gaps"
                db.commit()
            return {"status": "no_gaps", "repo": full_name}

        # 3. Decide (LLM proposes exactly one change)
        change = propose_change(report)

        # 4. Validate (apply the change locally, run lint + tests)
        apply_change(repo_path, change)
        validation = validate_change(repo_path, change)
        if run_row:
            run_row.validation_log = validation.log
            run_row.proposed_file = change.file_path
            run_row.commit_message = change.commit_message
            db.commit()

        if not validation.passed:
            if run_row:
                run_row.status = "failed"
                db.commit()
            return {"status": "failed", "repo": full_name, "log": validation.log}

        # 5. Commit + push to a new branch
        branch_name = f"agent/maintenance-{int(time.time())}"
        create_branch(repo_path, branch_name)
        commit_and_push(repo_path, change.file_path, change.commit_message, branch_name, github_token, full_name)

        # 6. Open PR
        base_branch = get_default_branch(full_name, github_token)
        pr = open_pull_request(
            owner_repo=full_name,
            token=github_token,
            branch_name=branch_name,
            base_branch=base_branch,
            title=change.pr_title,
            body=change.pr_description,
        )

        # Optional: auto-merge if this repo has that enabled AND the change is docs-only
        monitored = db.query(MonitoredRepo).filter(MonitoredRepo.id == monitored_repo_id).first() if monitored_repo_id else None
        if monitored and monitored.auto_merge_docs_only and change.change_type == "docs":
            merge_pull_request(full_name, github_token, pr["number"])

        if run_row:
            run_row.status = "passed"
            run_row.pr_url = pr["html_url"]
            db.commit()

        return {"status": "passed", "repo": full_name, "pr_url": pr["html_url"]}

    except Exception as exc:  # noqa: BLE001 - we want to log ANY failure, not crash the cron job
        if run_row:
            run_row.status = "error"
            run_row.error_message = f"{exc}\n{traceback.format_exc()}"
            db.commit()
        return {"status": "error", "repo": full_name, "error": str(exc)}

    finally:
        if repo_path:
            cleanup(repo_path)
        db.close()


def run_agent_for_all_configured_repos() -> list[dict]:
    """Used by the GitHub Actions cron job: runs every repo in settings.target_repos
    using the single service-level GITHUB_TOKEN (not a per-user OAuth token)."""
    results = []
    for repo in settings.target_repos:
        results.append(run_agent_for_repo(repo, settings.github_token))
    return results
