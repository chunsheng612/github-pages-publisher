from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from pathlib import Path

from common import (
    META_FILENAME,
    PublisherError,
    auth_status,
    copy_publish_tree,
    ensure_pages,
    ensure_tools,
    gh_repo_exists,
    github_login,
    init_and_push_staging,
    load_meta,
    next_available_repo,
    run,
    save_meta,
    slugify,
    wait_for_pages,
)
from preflight import scan


def build_if_needed(project_root: Path, result: dict) -> tuple[Path, dict]:
    if result["kind"] != "needs-build":
        if not result.get("publish_root"):
            raise PublisherError("找不到發布根目錄。")
        return Path(result["publish_root"]), result

    ensure_tools(require_npm=True)
    lock = project_root / "package-lock.json"
    if lock.exists():
        run(["npm", "ci"], cwd=project_root, capture=False)
    else:
        run(["npm", "install"], cwd=project_root, capture=False)
    run(["npm", "run", "build"], cwd=project_root, capture=False)

    result2 = scan(project_root)
    if not result2["ok"] or not result2.get("publish_root"):
        raise PublisherError("build 完成後仍找不到可安全發布的靜態網站。")
    return Path(result2["publish_root"]), result2


def default_repo_name(project_root: Path) -> str:
    pkg = project_root / "package.json"
    if pkg.exists():
        try:
            name = json.loads(pkg.read_text(encoding="utf-8")).get("name")
            if name:
                return slugify(str(name))
        except Exception:
            pass
    return slugify(project_root.name)


def publish(project_root: Path, requested_repo: str | None = None, update: bool = False) -> dict:
    project_root = project_root.resolve()
    ensure_tools()
    if not auth_status():
        raise PublisherError("GitHub 尚未登入。請先執行 gh auth login --web --git-protocol https")
    run(["gh", "auth", "setup-git"], check=False)

    result = scan(project_root)
    if not result["ok"]:
        raise PublisherError("發布前健檢未通過：\n- " + "\n- ".join(result["blockers"]))
    publish_root, result = build_if_needed(project_root, result)

    owner = github_login()
    meta = load_meta(project_root)

    if update:
        if not meta or not meta.get("repository") or not meta.get("owner"):
            raise PublisherError(f"找不到 {META_FILENAME}，無法安全判斷要覆寫哪一個網站。")
        full_repo = f"{meta['owner']}/{meta['repository']}"
        if not gh_repo_exists(full_repo):
            raise PublisherError(f"原本的 GitHub repository 已不存在：{full_repo}")
        repo = meta["repository"]
    else:
        requested = requested_repo or default_repo_name(project_root)
        repo = slugify(requested)
        full_repo = f"{owner}/{repo}"
        # Never overwrite an unrelated existing repository on first publish.
        if gh_repo_exists(full_repo):
            repo = next_available_repo(owner, repo)
            full_repo = f"{owner}/{repo}"
        desc = "Static website published with github-pages-publisher skill"
        proc = run(["gh", "repo", "create", full_repo, "--public", "--description", desc], check=False)
        if proc.returncode != 0:
            detail = (proc.stderr or proc.stdout or "").strip()
            raise PublisherError(f"無法建立 GitHub repository：{detail}")

    with tempfile.TemporaryDirectory(prefix="github-pages-publisher-") as td:
        staging = Path(td)
        copy_publish_tree(publish_root, staging)
        if not (staging / "index.html").exists():
            raise PublisherError("暫存發布內容沒有 index.html，已停止。")
        init_and_push_staging(staging, full_repo, force=True)

    pages = ensure_pages(full_repo)
    pages = wait_for_pages(full_repo)
    url = pages.get("html_url") or f"https://{owner}.github.io/{repo}/"

    data = {
        "owner": owner if not update else meta.get("owner", owner),
        "repository": repo,
        "url": url,
        "branch": "main",
        "publish_root": str(publish_root),
        "managed_by": "github-pages-publisher",
    }
    save_meta(project_root, data)
    return {"repo": full_repo, "url": url, "status": pages.get("status"), "warnings": result.get("warnings", [])}


def main() -> int:
    parser = argparse.ArgumentParser(description="一鍵發布靜態網站到 GitHub Pages")
    parser.add_argument("path", nargs="?", default=".")
    parser.add_argument("--repo", help="希望使用的 GitHub repository 名稱")
    parser.add_argument("--update", action="store_true", help="更新既有網站")
    args = parser.parse_args()

    output = publish(Path(args.path), args.repo, args.update)
    print("✅ 網站已發布" if not args.update else "✅ 網站已更新")
    print(f"網址：{output['url']}")
    print(f"GitHub：https://github.com/{output['repo']}")
    if output.get("status") and str(output["status"]).lower() not in {"built", "deployed"}:
        print(f"ℹ️  GitHub Pages 目前狀態：{output['status']}")
    for warning in output.get("warnings", []):
        print(f"⚠️  {warning}")
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except PublisherError as exc:
        print(f"❌ {exc}")
        raise SystemExit(2)
