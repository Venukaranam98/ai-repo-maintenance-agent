# AI Repository Maintenance Agent

An autonomous agent that analyzes public GitHub repositories, detects real
maintenance gaps (missing docs, missing tests, undocumented functions, stale
README sections), asks an LLM (Groq) to propose exactly one safe fix, runs
lint/tests to validate it, then opens a Pull Request — never pushing directly
to your default branch.

## Project structure

```
ai-repo-maintenance-agent/
├── backend/            FastAPI app + the agent pipeline itself
│   ├── agent/           core pipeline modules (analyzer, decision, validator, git_ops, github_pr)
│   ├── api/              auth (GitHub OAuth) + dashboard REST routes + DB models
│   ├── orchestrator.py    wires the pipeline together (used by both CLI and dashboard)
│   └── main.py            FastAPI entrypoint AND cron CLI entrypoint
├── frontend/            React + Tailwind dashboard (Vercel-inspired design tokens)
├── .github/workflows/   daily cron GitHub Action
└── DESIGN.md            design tokens reference used to build the frontend
```

## 1. Prerequisites

- Python 3.11+
- Node.js 18+
- A [Groq API key](https://console.groq.com) (free)
- A GitHub Personal Access Token with `public_repo` scope (for the agent itself)
- A GitHub OAuth App (for dashboard login) — create one at
  https://github.com/settings/developers → "New OAuth App"
  - Homepage URL: `http://localhost:5173`
  - Authorization callback URL: `http://localhost:8000/auth/github/callback`

## 2. Backend setup

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # then fill in your real keys
python main.py                   # starts the dashboard API on :8000
```

To run the agent once manually (without the dashboard), against the repos
listed in `TARGET_REPOS` in your `.env`:

```bash
python main.py --cron
```

## 3. Frontend setup

```bash
cd frontend
npm install
npm run dev                      # starts on :5173
```

Open http://localhost:5173, click "Continue with GitHub", select repos, then
watch the Dashboard for run history and PR links.

## 4. Automating it with GitHub Actions (production mode)

1. Push this project to its own GitHub repo.
2. In that repo's Settings → Secrets and variables → Actions, add:
   - `GROQ_API_KEY`
   - `AGENT_GITHUB_TOKEN` (a PAT with `public_repo` scope)
   - `TARGET_REPOS` (comma-separated `owner/repo` list)
3. The workflow in `.github/workflows/daily_maintenance.yml` runs daily at
   03:00 UTC, or trigger it manually from the Actions tab.

## 5. Design decisions worth mentioning in an interview

- **Public repos only** — deliberately scoped to avoid the agent ever
  touching private/production code.
- **PR-based, not direct push** — the agent proposes, a human (or an
  explicit auto-merge rule for docs-only changes) approves.
- **One pipeline, two entry points** — `orchestrator.py` is called by both
  the cron job and the dashboard's "Scan now" button, so there's exactly one
  implementation of "what the agent does," not two versions to keep in sync.
- **Validation before commit** — lint + existing test suite are run against
  the proposed change before anything is pushed.

See `PROGRESS.md` for the build checklist and `DESIGN.md` for the frontend
design tokens.


## Usage
To use the AI Repository Maintenance Agent, follow these steps:
1. Install the required dependencies.
2. Configure the agent by setting the environment variables.
3. Run the agent using the `--cron` flag.