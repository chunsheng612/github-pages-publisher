from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

META_FILENAME = ".github-pages-publisher.json"

class PublisherError(RuntimeError):
    pass


def run(cmd: list[str], cwd: Path | None = None, check: bool = True, capture: bool = True) -> subprocess.CompletedProcess:
    kwargs = {
        "cwd": str(cwd) if cwd else None,
        "text": True,
        "check": False,
    }
    if capture:
        kwargs.update(stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    proc = subprocess.run(cmd, **kwargs)
    if check and proc.returncode != 0:
        stderr = (proc.stderr or "").strip()
        stdout = (proc.stdout or "").strip()
        detail = stderr or stdout or f"exit code {proc.returncode}"
        raise PublisherError(f"指令失敗：{' '.join(cmd)}\n{detail}")
    return proc


def require_command(name: str, install_hint: str) -> None:
    if shutil.which(name) is None:
        raise PublisherError(f"找不到 {name}。{install_hint}")


def ensure_tools(require_npm: bool = False) -> None:
    require_command("git", "請先安裝 Git。")
    require_command("gh", "請先安裝 GitHub CLI：https://cli.github.com/")
    if require_npm:
        require_command("npm", "這個專案需要 build，請先安裝 Node.js / npm。")


def auth_status() -> bool:
    if shutil.which("gh") is None:
        return False
    return run(["gh", "auth", "status"], check=False).returncode == 0


def github_login() -> str:
    proc = run(["gh", "api", "user", "--jq", ".login"])
    login = (proc.stdout or "").strip()
    if not login:
        raise PublisherError("無法取得目前 GitHub 帳號。")
    return login


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9._-]+", "-", value)
    value = re.sub(r"[-_.]{2,}", "-", value).strip("-._")
    if not value:
        value = time.strftime("website-%Y%m%d-%H%M%S")
    return value[:90]


def load_meta(project_root: Path) -> dict | None:
    path = project_root / META_FILENAME
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise PublisherError(f"無法讀取 {META_FILENAME}：{exc}") from exc


def save_meta(project_root: Path, data: dict) -> None:
    path = project_root / META_FILENAME
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def gh_repo_exists(full_name: str) -> bool:
    return run(["gh", "repo", "view", full_name, "--json", "nameWithOwner"], check=False).returncode == 0


def next_available_repo(owner: str, requested: str) -> str:
    base = slugify(requested)
    candidate = base
    n = 2
    while gh_repo_exists(f"{owner}/{candidate}"):
        candidate = f"{base}-{n}"
        n += 1
    return candidate


def copy_publish_tree(source: Path, destination: Path) -> None:
    blocked_names = {
        ".git", ".github-pages-publisher.json", ".env", ".env.local", ".env.production",
        "node_modules", "__pycache__", ".DS_Store"
    }
    for item in source.iterdir():
        if item.name in blocked_names or item.name.startswith(".env."):
            continue
        target = destination / item.name
        if item.is_dir():
            shutil.copytree(item, target, ignore=shutil.ignore_patterns(".git", "node_modules", "__pycache__", ".DS_Store"))
        else:
            shutil.copy2(item, target)
    (destination / ".nojekyll").touch()


def init_and_push_staging(staging: Path, full_repo: str, force: bool = True) -> None:
    run(["git", "init"], cwd=staging)
    run(["git", "config", "user.name", "GitHub Pages Publisher"], cwd=staging)
    run(["git", "config", "user.email", "github-pages-publisher@users.noreply.github.com"], cwd=staging)
    run(["git", "add", "-A"], cwd=staging)
    run(["git", "commit", "-m", "Publish site"], cwd=staging)
    run(["git", "branch", "-M", "main"], cwd=staging)
    run(["git", "remote", "add", "origin", f"https://github.com/{full_repo}.git"], cwd=staging)
    cmd = ["git", "push", "-u", "origin", "main"]
    if force:
        cmd.append("--force")
    run(cmd, cwd=staging)


def ensure_pages(full_repo: str) -> dict:
    get_cmd = ["gh", "api", f"repos/{full_repo}/pages"]
    current = run(get_cmd, check=False)
    if current.returncode != 0:
        create = run([
            "gh", "api", "-X", "POST", f"repos/{full_repo}/pages",
            "-f", "source[branch]=main",
            "-f", "source[path]=/",
        ], check=False)
        if create.returncode != 0:
            detail = (create.stderr or create.stdout or "").strip()
            raise PublisherError(f"無法啟用 GitHub Pages：{detail}")
    else:
        # Make sure the publisher points at main/root. Ignore update errors when settings are already correct.
        run([
            "gh", "api", "-X", "PUT", f"repos/{full_repo}/pages",
            "-f", "source[branch]=main",
            "-f", "source[path]=/",
        ], check=False)
    return get_pages(full_repo)


def get_pages(full_repo: str) -> dict:
    proc = run(["gh", "api", f"repos/{full_repo}/pages"], check=False)
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip()
        raise PublisherError(f"目前查不到 GitHub Pages 狀態：{detail}")
    try:
        return json.loads(proc.stdout)
    except Exception as exc:
        raise PublisherError("GitHub Pages 回傳資料格式無法解析。") from exc


def wait_for_pages(full_repo: str, attempts: int = 12, interval: float = 5.0) -> dict:
    last = get_pages(full_repo)
    for _ in range(attempts):
        status = str(last.get("status", "")).lower()
        if status in {"built", "deployed"} and last.get("html_url"):
            return last
        time.sleep(interval)
        try:
            last = get_pages(full_repo)
        except PublisherError:
            pass
    return last
