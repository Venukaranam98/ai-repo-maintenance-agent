# Build Progress

## Done
- [x] Backend: config, analyzer, decision (Groq+LangChain structured output), validator, git_ops, github_pr
- [x] Backend: orchestrator wiring the full pipeline
- [x] Backend: SQLAlchemy models (User, MonitoredRepo, AgentRun)
- [x] Backend: GitHub OAuth login + JWT sessions
- [x] Backend: dashboard REST routes (available repos, select repos, monitored repos, history, trigger scan)
- [x] Backend: FastAPI main.py with dual CLI/server entrypoint
- [x] GitHub Actions daily cron workflow
- [x] Frontend: Vite + React + Tailwind scaffold with real Vercel DESIGN.md tokens
- [x] Frontend: Login, OAuthComplete, RepoSelect, Dashboard, RepoDetail pages
- [x] Frontend: Navbar, StatusBadge, RunHistoryTable components
- [x] README with full setup instructions

## Not yet built (nice-to-haves, phase 2)
- [ ] Celery + Redis for on-demand scans at scale (dashboard currently uses FastAPI BackgroundTasks, which is fine for single-user/demo scale)
- [ ] Slack/Discord webhook notifications on new PRs
- [ ] Auto-merge toggle exposed in the frontend UI (backend field `auto_merge_docs_only` already exists on MonitoredRepo, just needs a UI checkbox)
- [ ] Token encryption at rest for `github_access_token` column
- [ ] Docker Compose file to run backend + frontend together with one command

## How to resume if a session ends
1. Re-upload the last zip you downloaded.
2. Say "continue building from here, next add: <item from the list above>".
