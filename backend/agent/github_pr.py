"""
github_pr.py

Thin wrapper around the GitHub REST API for the one thing we need beyond
raw git push: opening a Pull Request, and (optionally) auto-merging
doc-only changes once they've passed validation.
"""

import requests

GITHUB_API = "https://api.github.com"


def _headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def open_pull_request(
    owner_repo: str,
    token: str,
    branch_name: str,
    base_branch: str,
    title: str,
    body: str,
) -> dict:
    """Create a PR from branch_name -> base_branch. Returns the PR JSON (includes html_url, number)."""
    url = f"{GITHUB_API}/repos/{owner_repo}/pulls"
    payload = {
        "title": title,
        "head": branch_name,
        "base": base_branch,
        "body": body,
    }
    resp = requests.post(url, headers=_headers(token), json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()


def get_default_branch(owner_repo: str, token: str) -> str:
    """Fetch the repo's default branch name (e.g. 'main' or 'master')."""
    url = f"{GITHUB_API}/repos/{owner_repo}"
    resp = requests.get(url, headers=_headers(token), timeout=30)
    resp.raise_for_status()
    return resp.json()["default_branch"]


def merge_pull_request(owner_repo: str, token: str, pr_number: int) -> dict:
    """Auto-merge a PR. Only call this for low-risk (doc-only) changes."""
    url = f"{GITHUB_API}/repos/{owner_repo}/pulls/{pr_number}/merge"
    resp = requests.put(url, headers=_headers(token), json={"merge_method": "squash"}, timeout=30)
    resp.raise_for_status()
    return resp.json()


def list_user_public_repos(token: str) -> list[dict]:
    """
    Used by the dashboard's repo-selection screen: fetch the logged-in
    user's repos and filter to public ones only, matching our
    "public repos only" safety scope.
    """
    repos = []
    page = 1
    while True:
        url = f"{GITHUB_API}/user/repos?per_page=100&page={page}&affiliation=owner"
        resp = requests.get(url, headers=_headers(token), timeout=30)
        resp.raise_for_status()
        batch = resp.json()
        if not batch:
            break
        repos.extend(batch)
        page += 1
    return [r for r in repos if not r.get("private", True)]
