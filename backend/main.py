"""
main.py

Two ways to run this file:

1. As a web server (dashboard API):
       uvicorn main:app --reload

2. As a one-off CLI run (what the GitHub Actions cron job calls):
       python main.py --cron

The CLI path re-uses the exact same orchestrator function the dashboard's
"Scan now" button calls - there is only one pipeline implementation.
"""

import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agent.config import settings
from api.auth import router as auth_router
from api.models import init_db
from api.routes import router as api_router
from orchestrator import run_agent_for_all_configured_repos

app = FastAPI(title="AI Repository Maintenance Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(api_router)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/health")
def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    if "--cron" in sys.argv:
        # Cron / GitHub Actions entry point: no web server, just run the pipeline
        # once for every repo configured in TARGET_REPOS and exit.
        init_db()
        results = run_agent_for_all_configured_repos()
        for r in results:
            print(r)
    else:
        import uvicorn
        uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
