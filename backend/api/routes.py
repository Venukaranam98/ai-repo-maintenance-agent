"""
routes.py

REST endpoints the React dashboard calls. All routes (except auth) require
a valid JWT via the Authorization: Bearer <token> header.
"""

import json

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from agent.github_pr import list_user_public_repos
from api.auth import get_current_user
from api.models import User, MonitoredRepo, AgentRun, get_db
from orchestrator import run_agent_for_repo

router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/repos/available")
def available_repos(user: User = Depends(get_current_user)):
    """List the logged-in user's PUBLIC repos, for the repo-selection screen."""
    repos = list_user_public_repos(user.github_access_token)
    return [
        {"full_name": r["full_name"], "description": r.get("description"), "stargazers_count": r.get("stargazers_count", 0)}
        for r in repos
    ]


@router.post("/repos/select")
def select_repos(full_names: list[str], user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Persist which repos the user has enabled the agent on."""
    for name in full_names:
        existing = db.query(MonitoredRepo).filter(
            MonitoredRepo.user_id == user.id, MonitoredRepo.full_name == name
        ).first()
        if not existing:
            db.add(MonitoredRepo(user_id=user.id, full_name=name, enabled=True))
    db.commit()
    return {"status": "ok", "selected": full_names}


@router.get("/repos/monitored")
def monitored_repos(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    repos = db.query(MonitoredRepo).filter(MonitoredRepo.user_id == user.id).all()
    return [
        {
            "id": r.id,
            "full_name": r.full_name,
            "enabled": r.enabled,
            "auto_merge_docs_only": r.auto_merge_docs_only,
        }
        for r in repos
    ]


@router.get("/history")
def run_history(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Full audit trail across all of the user's monitored repos."""
    runs = (
        db.query(AgentRun)
        .join(MonitoredRepo)
        .filter(MonitoredRepo.user_id == user.id)
        .order_by(AgentRun.started_at.desc())
        .limit(200)
        .all()
    )
    return [
        {
            "id": run.id,
            "repo": run.repo.full_name,
            "started_at": run.started_at.isoformat(),
            "status": run.status,
            "commit_message": run.commit_message,
            "pr_url": run.pr_url,
            "gap_summary": json.loads(run.gap_summary) if run.gap_summary else None,
        }
        for run in runs
    ]


@router.post("/repos/{repo_id}/trigger")
def trigger_scan(repo_id: int, background_tasks: BackgroundTasks, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Manually trigger an on-demand scan for one repo (the dashboard's
    'Scan now' button). Runs in a FastAPI background task so the request
    returns immediately instead of blocking on the full pipeline.
    """
    repo = db.query(MonitoredRepo).filter(MonitoredRepo.id == repo_id, MonitoredRepo.user_id == user.id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repo not found")

    background_tasks.add_task(run_agent_for_repo, repo.full_name, user.github_access_token, repo.id)
    return {"status": "triggered", "repo": repo.full_name}
