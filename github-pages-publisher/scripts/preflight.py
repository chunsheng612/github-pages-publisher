from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

TEXT_EXTS = {".html", ".htm", ".css", ".js", ".jsx", ".ts", ".tsx", ".json", ".md", ".txt", ".py", ".php"}
SKIP_DIRS = {".git", "node_modules", ".next", "coverage", "vendor", "__pycache__"}
SECRET_FILENAMES = {".env", ".env.local", ".env.production", ".env.development", "credentials.json", "service-account.json"}

SECRET_PATTERNS = [
    ("OpenAI API Key", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
    ("Google API Key", re.compile(r"\bAIza[0-9A-Za-z_-]{30,}\b")),
    ("GitHub Token", re.compile(r"\b(?:ghp|github_pat)_[A-Za-z0-9_]{20,}\b")),
    ("Private Key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("疑似 Secret Assignment", re.compile(r"(?im)^\s*(?:API_KEY|SECRET|TOKEN|PRIVATE_KEY|PASSWORD)\s*[=:]\s*['\"]?(?!your-|example|demo|placeholder|changeme)([^'\"\s]{10,})")),
]

ABSOLUTE_PATH_PATTERNS = [
    re.compile(r"(?:src|href)\s*=\s*[\"']/[^/]", re.I),
    re.compile(r"url\(\s*[\"']?/[^/]", re.I),
    re.compile(r"fetch\(\s*[\"']/[^/]", re.I),
]

ROUTER_PATTERNS = [re.compile(r"\bBrowserRouter\b"), re.compile(r"\bcreateBrowserRouter\b")]


def iter_files(root: Path):
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        yield p


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def find_publish_root(root: Path) -> tuple[Path | None, str]:
    if (root / "dist" / "index.html").exists():
        return root / "dist", "built-dist"
    if (root / "build" / "index.html").exists():
        return root / "build", "built-build"
    if (root / "index.html").exists():
        return root, "static"

    pkg = root / "package.json"
    if pkg.exists():
        try:
            data = json.loads(pkg.read_text(encoding="utf-8"))
            scripts = data.get("scripts", {})
            if "build" in scripts:
                return None, "needs-build"
        except Exception:
            pass

    candidates = []
    for p in root.glob("*/index.html"):
        if p.parent.name not in SKIP_DIRS:
            candidates.append(p.parent)
    if len(candidates) == 1:
        return candidates[0], "nested-static"
    return None, "unknown"


def detect_backend(root: Path) -> list[str]:
    findings = []
    names = {p.name.lower() for p in root.iterdir() if p.is_file()}
    if any(n in names for n in {"requirements.txt", "pyproject.toml", "pipfile"}):
        for p in [root / "app.py", root / "manage.py", root / "server.py"]:
            if p.exists():
                findings.append(f"偵測到可能的 Python 後端入口：{p.name}")
    if any(p.suffix.lower() == ".php" for p in root.rglob("*.php")):
        findings.append("偵測到 PHP 檔案；GitHub Pages 不會執行 PHP。")
    for name in ["server.js", "server.ts"]:
        if (root / name).exists():
            findings.append(f"偵測到可能的 Node 後端入口：{name}")
    pkg = root / "package.json"
    if pkg.exists():
        text = read_text(pkg).lower()
        if '"express"' in text or '"fastify"' in text or '"koa"' in text:
            findings.append("package.json 含常見 Node server framework；請確認是否需要後端。")
    return findings


def scan(root: Path) -> dict:
    root = root.resolve()
    blockers = []
    warnings = []
    notes = []

    if not root.exists() or not root.is_dir():
        return {"ok": False, "root": str(root), "publish_root": None, "kind": "invalid", "blockers": ["指定路徑不是有效資料夾。"], "warnings": [], "notes": []}

    backend = detect_backend(root)
    blockers.extend(backend)

    secret_files = []
    secret_hits = []
    absolute_hits = []
    router_hits = []

    for p in iter_files(root):
        rel = p.relative_to(root)
        if p.name in SECRET_FILENAMES or p.name.startswith(".env."):
            secret_files.append(str(rel))
            continue
        if p.suffix.lower() not in TEXT_EXTS:
            continue
        text = read_text(p)
        if not text:
            continue
        for label, pat in SECRET_PATTERNS:
            if pat.search(text):
                secret_hits.append({"file": str(rel), "type": label})
        if p.suffix.lower() in {".html", ".css", ".js", ".jsx", ".ts", ".tsx"}:
            if any(pat.search(text) for pat in ABSOLUTE_PATH_PATTERNS):
                absolute_hits.append(str(rel))
            if any(pat.search(text) for pat in ROUTER_PATTERNS):
                router_hits.append(str(rel))

    if secret_files:
        blockers.append("發現敏感環境／憑證檔案：" + ", ".join(secret_files[:10]))
    if secret_hits:
        short = ", ".join(f"{x['file']} ({x['type']})" for x in secret_hits[:10])
        blockers.append("發現疑似秘密資訊：" + short)
    if absolute_hits:
        warnings.append("偵測到可能不相容 GitHub Project Pages 的根目錄絕對路徑：" + ", ".join(sorted(set(absolute_hits))[:10]))
    if router_hits:
        warnings.append("偵測到 Browser Router；直接開啟或重新整理子路由可能 404：" + ", ".join(sorted(set(router_hits))[:10]))

    publish_root, kind = find_publish_root(root)
    if kind == "needs-build":
        notes.append("偵測到 package.json build script；發布前需要執行 npm build。")
    elif publish_root is None:
        blockers.append("找不到可發布的 index.html，也沒有可辨識的標準 build 流程。")
    else:
        if not (publish_root / "index.html").exists():
            blockers.append("發布根目錄沒有 index.html。")

    return {
        "ok": not blockers,
        "root": str(root),
        "publish_root": str(publish_root) if publish_root else None,
        "kind": kind,
        "blockers": blockers,
        "warnings": warnings,
        "notes": notes,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="GitHub Pages 發布前健檢")
    parser.add_argument("path", nargs="?", default=".")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    result = scan(Path(args.path))
    if args.as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("GitHub Pages 發布前健檢")
        print(f"路徑：{result['root']}")
        print(f"類型：{result['kind']}")
        if result.get("publish_root"):
            print(f"發布根目錄：{result['publish_root']}")
        for x in result["notes"]:
            print(f"ℹ️  {x}")
        for x in result["warnings"]:
            print(f"⚠️  {x}")
        for x in result["blockers"]:
            print(f"⛔ {x}")
        print("✅ 可繼續發布" if result["ok"] else "❌ 已停止：請先處理阻擋問題")
    return 0 if result["ok"] else 2

if __name__ == "__main__":
    raise SystemExit(main())
