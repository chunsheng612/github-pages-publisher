# GitHub Pages 網頁一鍵發布 Skill

讓不熟悉 GitHub、Git、Repository、Branch、Pages 的老師或一般使用者，也可以把做好的網頁直接變成一個可分享的公開網址。

> 使用者只需要把網站交給 Codex，然後說：「幫我把這個網站上線。」

這個 Skill 會負責發布前健檢、GitHub 登入確認、Repository 建立、網站上傳、GitHub Pages 啟用，以及之後的網站更新。

---

## 這個 Skill 解決什麼問題？

很多老師已經可以用 AI 做出 HTML 教材、互動遊戲、測驗或小工具，但最後常卡在：

- 不知道什麼是 Git / GitHub
- 不知道怎麼建立 Repository
- 不會 commit / push
- 不知道 GitHub Pages 在哪裡開
- 網站在電腦上正常，上線後圖片或 CSS 卻壞掉
- Vite / React 不知道要先 build
- 不小心把 `.env`、API Key 或敏感資料一起上傳

這個 Skill 的目的不是教使用者 GitHub，而是把這些步驟盡量自動化。

---

## 使用體驗

第一次：

```text
把網站資料夾交給 Codex
        ↓
「幫我上線」
        ↓
第一次需要登入 GitHub
        ↓
自動健檢網站
        ↓
自動建立 GitHub Repository
        ↓
自動啟用 GitHub Pages
        ↓
取得網址
```

之後更新：

```text
修改網站
   ↓
「幫我更新網站」
   ↓
完成
```

一般使用者不需要手動處理：

- `git init`
- `git add`
- `git commit`
- `git push`
- Branch
- Remote
- GitHub Pages Settings
- Personal Access Token
- SSH Key

---

## 支援的網站

### 適合

- 純 HTML / CSS / JavaScript
- 教學遊戲
- 線上教材
- 互動測驗
- 班級網頁
- 作品展示
- 抽籤器、計時器、文字工具
- 已 build 完成的 `dist/` 或 `build/`
- 具有標準 `npm run build` 的 Vite / React 靜態網站

### 不適合直接用 GitHub Pages

- Express / Node.js Server
- Flask / Django
- PHP 後端
- 需要秘密 API Key 的前端程式
- 必須靠伺服器處理登入或資料庫憑證的網站
- 不適合公開的學生個資或內部資料

GitHub Pages 是靜態網站服務，而且網站內容會公開在網路上。詳細判斷請參考 [`references/supported-sites.md`](github-pages-publisher/references/supported-sites.md)。

---

## 功能

### 1. GitHub 登入檢查

自動檢查：

```bash
gh auth status
```

第一次尚未登入時，可使用瀏覽器完成 GitHub 官方登入流程：

```bash
gh auth login --web --git-protocol https
```

不需要老師建立或貼上 Personal Access Token。

### 2. 發布前網站健檢

會檢查：

- `index.html`
- HTML / CSS / JS 靜態資源
- `.env`
- API Key / Token / Private Key
- 後端伺服器需求
- GitHub Pages 絕對路徑風險
- Vite / React build
- SPA Router 重新整理 404 風險

### 3. 自動建立 Repository

使用 GitHub CLI 建立公開 Repository。

若同名 Repository 已存在，而且不是這個 Skill 先前管理的網站，工具不會直接覆寫，而會建立不衝突的名稱。

### 4. 自動發布 GitHub Pages

使用 GitHub Pages REST API 將：

```text
main / (root)
```

設定成網站來源，並讀取 GitHub 回傳的正式 `html_url`。

### 5. 一句話更新

第一次發布後，專案根目錄會產生：

```text
.github-pages-publisher.json
```

裡面只記錄：

- GitHub owner
- repository 名稱
- Pages 網址
- branch

不存 Token，也不會被發布到網站。

之後可以直接：

```text
幫我更新網站
```

---

## Skill 結構

```text
github-pages-publisher/
├── SKILL.md
├── README.md
├── VERSION
├── scripts/
│   ├── common.py
│   ├── preflight.py
│   ├── github_auth.py
│   ├── publish.py
│   ├── update.py
│   └── pages_status.py
├── references/
│   ├── supported-sites.md
│   └── troubleshooting.md
└── tests/
    └── test_preflight.py
```

OpenAI 的 Skill 格式以 `SKILL.md` 為必要檔案，並可搭配 `scripts/`、`references/` 等資源。Codex 會依 Skill 的 `name` 與 `description` 判斷是否啟用，再讀取完整指示。

官方說明：

- https://learn.chatgpt.com/docs/build-skills

---

## 安裝需求

### 必要

1. **Git**
2. **GitHub CLI (`gh`)**
3. **Python 3.10+**
4. GitHub 帳號

### Vite / React 額外需要

- Node.js
- npm

---

## 安裝方式

### 方法 A：直接從 GitHub 安裝（推薦）

最簡單的方式，是把下面這句貼給 Codex：

```text
請使用 $skill-installer，從 https://github.com/chunsheng612/github-pages-publisher/tree/main/github-pages-publisher 安裝這個 Skill。
```

OpenAI 官方文件指出，Codex 的 Skill Installer 可以從其他 repository 下載 Skill。

### 方法 B：手動安裝

把整個 `github-pages-publisher` 資料夾放到：

```text
$HOME/.agents/skills/
```

最後結構應為：

```text
$HOME/.agents/skills/github-pages-publisher/SKILL.md
```

如果 Codex 沒有立刻看到 Skill，可重新啟動 Codex。

---

## 第一次使用

### 1. 檢查 GitHub CLI

```bash
gh --version
```

### 2. 登入 GitHub

```bash
gh auth login --web --git-protocol https
```

或讓 Skill 自動處理：

```bash
python scripts/github_auth.py --login-if-needed
```

GitHub CLI 官方預設支援瀏覽器登入，完成後認證資訊會交由系統的 credential store 儲存（若系統沒有可用的 credential store，GitHub CLI 可能退回本機檔案儲存機制）。

GitHub CLI 官方文件：

- https://cli.github.com/manual/gh_auth_login

---

## 使用方式

### 最簡單

把網站或專案交給 Codex，然後說：

```text
幫我把這個網站上線。
```

也可以說：

```text
幫我發布這個網頁。
```

```text
把這個放到 GitHub Pages。
```

```text
給我一個可以分享給學生的網址。
```

### 更新

修改完網站後：

```text
幫我更新網站。
```

### 查詢網址

```text
這個網站的網址是什麼？
```

---

## 手動測試腳本

通常不需要老師自己執行，但開發者可以使用。

### 健檢

```bash
python scripts/preflight.py ./my-site
```

JSON 輸出：

```bash
python scripts/preflight.py ./my-site --json
```

### 登入檢查

```bash
python scripts/github_auth.py
```

需要時自動開啟登入：

```bash
python scripts/github_auth.py --login-if-needed
```

### 新網站發布

```bash
python scripts/publish.py ./my-site --repo my-teaching-game
```

### 更新

```bash
python scripts/update.py ./my-site
```

### 查詢 Pages

```bash
python scripts/pages_status.py ./my-site
```

或：

```bash
python scripts/pages_status.py --repo OWNER/REPO
```

---

## 為什麼發布時使用「暫存 Repository」？

這是本 Skill 一個重要的安全設計。

它不會直接在老師原本的專案裡：

- 重設 Git
- 改 remote
- force push 原本 repository

而是：

```text
原始專案
   ↓
健檢 / build
   ↓
只挑出真正網站檔案
   ↓
暫存 staging directory
   ↓
建立獨立 Git repository
   ↓
推到 GitHub Pages repository
```

這樣即使原本的專案已經有自己的 Git 歷史，也比較不容易被部署工具破壞。

---

## GitHub Pages 路徑問題

Project Pages 通常是：

```text
https://USERNAME.github.io/REPOSITORY/
```

因此這種寫法可能出問題：

```html
<script src="/assets/app.js"></script>
```

因為瀏覽器可能會去找：

```text
https://USERNAME.github.io/assets/app.js
```

而不是：

```text
https://USERNAME.github.io/REPOSITORY/assets/app.js
```

所以健檢會特別警告：

```text
src="/
href="/
url(/
fetch("/
```

目前第一版採取「偵測與警告」，不會對所有檔案進行危險的全域自動取代。

---

## React Router / SPA

如果使用：

```text
BrowserRouter
createBrowserRouter
```

GitHub Pages 在直接開啟或重新整理子路由時可能 404。

對單純教材或遊戲，可考慮 Hash Router：

```text
/#/about
```

第一版會警告，不會在無法確認行為的情況下自動重構整個 Router。

---

## 安全機制

若找到疑似：

```text
.env
API_KEY
SECRET
TOKEN
PRIVATE_KEY
PASSWORD
```

或常見金鑰格式，發布會停止。

例如：

```text
⚠️ 暫停發布

我發現網站中可能包含 API 金鑰或敏感資訊。
GitHub Pages 是公開網站，因此沒有上傳這些內容。
```

工具不應在訊息中完整輸出疑似秘密值。

---

## GitHub Pages 的限制

依 GitHub 官方文件，目前 GitHub Pages 包含一些使用限制，例如：

- 發布網站大小上限 1 GB
- 每月 100 GB 軟性頻寬限制
- 從 branch 發布時，每小時 10 次 build 的軟性限制

一般教學小工具通常不會碰到這些限制，但大量影片、音檔或超大型素材不適合直接塞進 Pages。

官方文件：

- https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits

---

## GitHub Pages 官方機制

GitHub Pages 可以從 Repository 的指定 branch 與資料夾發布；可使用 `/` 或 `/docs` 作為來源。GitHub REST API 也提供建立、查詢與更新 Pages site 的 endpoint。

本 Skill 使用：

```text
branch: main
path: /
```

官方文件：

- https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site
- https://docs.github.com/en/rest/pages/pages

建立 Repository 使用 GitHub CLI：

- https://cli.github.com/manual/gh_repo_create

---

## 常見問題

### Q：老師需要懂 GitHub 嗎？

不需要。第一次只需要完成 GitHub 帳號登入。

### Q：每次都要登入嗎？

通常不用。Skill 會先檢查 `gh auth status`，只有認證失效才需要重新登入。

### Q：一定要付費嗎？

一般 public repository 可使用 GitHub Pages。若涉及 private repository，請依自己的 GitHub 方案確認 Pages 支援情況。

### Q：學生需要 GitHub 帳號嗎？

不需要。GitHub Pages 產生的是一般公開網址。

### Q：可以放學生個資嗎？

不建議。Pages 是公開網站，請不要放姓名、帳號密碼、私人紀錄或其他不適合公開的資料。

### Q：Firebase 可以嗎？

Firebase 的前端 SDK 本身有些情境可以在靜態頁面運作，但這不代表所有 Firebase 設定都安全或適合直接公開。第一版遇到 Firebase 或其他外部服務時，應額外檢查是否含伺服器端憑證、Private Key 或不該公開的秘密值。

### Q：可以部署 Next.js 嗎？

要看專案是否能輸出純靜態網站。需要 Server-Side Rendering、Server Actions 或 Node server 的 Next.js 專案不屬於第一版支援範圍。

---

## 開發狀態

目前版本：`0.1.0`

定位為 MVP：

- 靜態 HTML / CSS / JS：主要支援
- Vite / React 靜態 build：主要支援
- GitHub Pages branch publishing：支援
- 敏感資訊掃描：支援
- SPA / 路徑風險：偵測與警告
- 後端網站：阻擋並說明
- 自訂網域：尚未納入
- GitHub Actions 自訂部署：尚未納入
- Next.js / Nuxt SSR：尚未納入

---

## 設計理念

這個 Skill 的重點不是：

> 「讓老師學會 GitHub。」

而是：

> **「讓老師把做好的網頁，變成一個真的網址。」**
