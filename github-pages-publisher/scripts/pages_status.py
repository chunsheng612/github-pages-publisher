from __future__ import annotations

import argparse
from pathlib import Path

from common import PublisherError, auth_status, ensure_tools, get_pages, load_meta


def main() -> int:
    parser = argparse.ArgumentParser(description="查詢 GitHub Pages 狀態")
    parser.add_argument("path", nargs="?", default=".")
    parser.add_argument("--repo", help="OWNER/REPO")
    args = parser.parse_args()

    ensure_tools()
    if not auth_status():
        raise PublisherError("GitHub 尚未登入。")

    full_repo = args.repo
    if not full_repo:
        meta = load_meta(Path(args.path).resolve())
        if not meta:
            raise PublisherError("找不到本機發布記錄，請使用 --repo OWNER/REPO 指定網站。")
        full_repo = f"{meta['owner']}/{meta['repository']}"

    data = get_pages(full_repo)
    print(f"網站：{full_repo}")
    print(f"狀態：{data.get('status', 'unknown')}")
    if data.get("html_url"):
        print(f"網址：{data['html_url']}")
    source = data.get("source") or {}
    if source:
        print(f"來源：{source.get('branch', '?')} {source.get('path', '?')}")
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except PublisherError as exc:
        print(f"❌ {exc}")
        raise SystemExit(2)
