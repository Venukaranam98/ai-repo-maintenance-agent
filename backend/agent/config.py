import os
from dataclasses import dataclass, field
from typing import List

from dotenv import load_dotenv

# Load variables from a local .env file if one exists (for local dev).
# In production (GitHub Actions / a server) these are injected as real
# environment variables / secrets instead.
load_dotenv()


@dataclass
class Settings:
    # --- Groq / LLM ---
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    groq_model: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    # --- GitHub ---
    github_token: str = os.getenv("GITHUB_TOKEN", "")  # PAT used by the agent itself
    github_client_id: str = os.getenv("GITHUB_CLIENT_ID", "")  # OAuth app (for dashboard login)
    github_client_secret: str = os.getenv("GITHUB_CLIENT_SECRET", "")
    github_oauth_redirect_uri: str = os.getenv(
        "GITHUB_OAUTH_REDIRECT_URI", "http://localhost:8000/auth/github/callback"
    )
    github_oauth_scope: str = "public_repo read:user"

    # --- App / Auth ---
    jwt_secret: str = os.getenv("JWT_SECRET", "change-me-in-production")
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = int(os.getenv("JWT_EXPIRE_MINUTES", "10080"))  # 7 days

    # --- Database ---
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./logs/run_history.db")

    # --- Agent behaviour ---
    # Repos the agent is allowed to touch when run from cron/CLI (comma separated
    # "owner/repo" list). When run via the dashboard, the user's own selected
    # repos (stored in DB) are used instead.
    target_repos: List[str] = field(
        default_factory=lambda: [
            r.strip() for r in os.getenv("TARGET_REPOS", "").split(",") if r.strip()
        ]
    )
    max_changes_per_run: int = int(os.getenv("MAX_CHANGES_PER_RUN", "1"))
    workdir: str = os.getenv("AGENT_WORKDIR", "./tmp_repos")

    # --- CORS (frontend origin) ---
    frontend_origin: str = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")


settings = Settings()
