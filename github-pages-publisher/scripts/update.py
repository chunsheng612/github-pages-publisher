from __future__ import annotations

import argparse
from pathlib import Path

from common import PublisherError
from publish import publish


def main() -> int:
    parser = argparse.ArgumentParser(description="更新先前發布的 GitHub Pages 網站")
    parser.add_argument("path", nargs="?", default=".")
    args = parser.parse_args()
    output = publish(Path(args.path), update=True)
    print("✅ 網站已更新")
    print(f"網址：{output['url']}")
    for warning in output.get("warnings", []):
        print(f"⚠️  {warning}")
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except PublisherError as exc:
        print(f"❌ {exc}")
        raise SystemExit(2)
