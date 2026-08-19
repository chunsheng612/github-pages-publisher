from __future__ import annotations

import argparse
import shutil

from common import PublisherError, auth_status, github_login, require_command, run


def main() -> int:
    parser = argparse.ArgumentParser(description="檢查 GitHub CLI 登入狀態")
    parser.add_argument("--login-if-needed", action="store_true")
    args = parser.parse_args()

    require_command("gh", "請先安裝 GitHub CLI：https://cli.github.com/")

    if not auth_status():
        if not args.login_if_needed:
            print("尚未登入 GitHub。請執行：gh auth login --web --git-protocol https")
            return 2
        print("第一次發布需要連結 GitHub。即將使用瀏覽器登入。")
        run(["gh", "auth", "login", "--web", "--git-protocol", "https"], capture=False)

    run(["gh", "auth", "setup-git"], check=False)
    login = github_login()
    print(f"✅ GitHub 已連結：{login}")
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except PublisherError as exc:
        print(f"❌ {exc}")
        raise SystemExit(2)
