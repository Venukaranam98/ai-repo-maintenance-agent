import os
import shutil
import time

import git  # GitPython

from agent.config import settings


def clone_repo(owner_repo: str, token: str) -> str:
    """
    Clone `owner/repo` into a fresh temp folder using the given token for
    auth, and return the local path. Uses an authenticated HTTPS URL so we
    can push branches back without SSH key setup.
    """
    owner, name = owner_repo.split("/")
    dest = os.path.join(settings.workdir, f"{owner}__{name}_{int(time.time())}")
    os.makedirs(settings.workdir, exist_ok=True)

    if os.path.exists(dest):
        shutil.rmtree(dest)

    auth_url = f"https://{token}@github.com/{owner}/{name}.git"
    git.Repo.clone_from(auth_url, dest, depth=50)  # shallow clone, we don't need full history
    return dest


def create_branch(repo_path: str, branch_name: str) -> None:
    """Create and check out a new branch off the current HEAD."""
    repo = git.Repo(repo_path)
    new_branch = repo.create_head(branch_name)
    new_branch.checkout()


def commit_and_push(repo_path: str, file_path: str, commit_message: str, branch_name: str, token: str, owner_repo: str) -> None:
    """
    Stage the single changed file, commit it, and push the branch to the
    remote. We push explicitly with the auth URL again rather than relying
    on the 'origin' remote credentials caching.
    """
    repo = git.Repo(repo_path)
    repo.index.add([file_path])
    repo.index.commit(commit_message)

    owner, name = owner_repo.split("/")
    auth_url = f"https://{token}@github.com/{owner}/{name}.git"
    remote = repo.remote(name="origin")
    remote.set_url(auth_url)
    remote.push(refspec=f"{branch_name}:{branch_name}")


def cleanup(repo_path: str) -> None:
    """Remove the temporary local clone once we're done with it."""
    if os.path.exists(repo_path):
        shutil.rmtree(repo_path, ignore_errors=True)
