"""
auth.py

GitHub-only OAuth login, scoped to public_repo access, plus our own JWT
issuance for dashboard session management.

Flow:
1. Frontend redirects the browser to /auth/github/login
2. We redirect to GitHub's authorize URL
3. GitHub redirects back to /auth/github/callback?code=...
4. We exchange the code for a GitHub access token (server-to-server call)
5. We fetch the user's GitHub profile, upsert a User row, store their token
6. We issue our OWN short-lived JWT and send it back to the frontend
   (the GitHub token itself never goes to the browser)
"""

import datetime

import requests
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from agent.config import settings
from api.models import User, get_db

router = APIRouter(prefix="/auth", tags=["auth"])
bearer_scheme = HTTPBearer()

GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_URL = "https://api.github.com/user"


def create_jwt(user_id: int) -> str:
    expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """FastAPI dependency: validates the JWT and returns the current User row."""
    try:
        payload = jwt.decode(credentials.credentials, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        user_id = int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


@router.get("/github/login")
def github_login():
    """Step 1: redirect the browser to GitHub's OAuth consent screen."""
    params = (
        f"client_id={settings.github_client_id}"
        f"&redirect_uri={settings.github_oauth_redirect_uri}"
        f"&scope={settings.github_oauth_scope.replace(' ', '%20')}"
    )
    return RedirectResponse(f"{GITHUB_AUTHORIZE_URL}?{params}")


@router.get("/github/callback")
def github_callback(code: str, db: Session = Depends(get_db)):
    """Step 2: exchange the temporary code for an access token, upsert the user, issue our JWT."""
    token_resp = requests.post(
        GITHUB_TOKEN_URL,
        headers={"Accept": "application/json"},
        data={
            "client_id": settings.github_client_id,
            "client_secret": settings.github_client_secret,
            "code": code,
            "redirect_uri": settings.github_oauth_redirect_uri,
        },
        timeout=30,
    )
    token_resp.raise_for_status()
    access_token = token_resp.json().get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="GitHub did not return an access token")

    profile_resp = requests.get(
        GITHUB_USER_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=30,
    )
    profile_resp.raise_for_status()
    profile = profile_resp.json()

    user = db.query(User).filter(User.github_id == profile["id"]).first()
    if user is None:
        user = User(
            github_id=profile["id"],
            github_username=profile["login"],
            avatar_url=profile.get("avatar_url"),
            github_access_token=access_token,
        )
        db.add(user)
    else:
        user.github_access_token = access_token
        user.github_username = profile["login"]
        user.avatar_url = profile.get("avatar_url")
    db.commit()
    db.refresh(user)

    session_token = create_jwt(user.id)
    # Redirect back to the frontend with the JWT as a query param;
    # the frontend stores it (e.g. in memory) and uses it for API calls.
    return RedirectResponse(f"{settings.frontend_origin}/oauth/complete?token={session_token}")
