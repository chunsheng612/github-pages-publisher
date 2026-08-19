---
name: github-pages-publisher
description: 幫不熟悉 GitHub 的使用者把已完成的 HTML/CSS/JavaScript、Vite 或 React 靜態網站發布成 GitHub Pages 公開網址，也能更新既有網站、檢查發布狀態與排除常見 404／路徑問題。當使用者說「幫我上線」、「發布這個網站」、「放到 GitHub Pages」、「給我網站網址」、「更新網站」時使用。不要用於需要伺服器端 Node/Python/PHP、秘密 API Key、資料庫後端或不能公開的網站。
---

# GitHub Pages 網頁一鍵發布

你的任務不是教使用者 Git/GitHub，而是把完成的靜態網站安全地變成可分享的 GitHub Pages 網址。

## 核心原則

1. 優先使用一般使用者能理解的語言，例如「網站」、「網址」、「發布」、「更新」。
2. 不要要求一般使用者理解 commit、branch、remote、repository、GitHub Actions、PAT 或 SSH Key。
3. 不要要求使用者手動建立 Personal Access Token 或把 Token 貼進對話。
4. 每次發布前都先執行安全與相容性檢查。
5. 發現疑似秘密金鑰、後端伺服器需求或無法安全判斷時，停止發布；不要為了「成功上線」而忽略風險。
6. 不直接改寫或重設使用者原本 Git repository。發布腳本會使用暫存 staging repository，避免破壞原始專案。
7. 只有在確認 GitHub Pages 已建立並取得正式網址後，才回覆「網站已發布」。

## 支援範圍

優先支援：

- 純 HTML / CSS / JavaScript 網站
- 已有 `dist/` 或 `build/` 的靜態輸出
- Vite / React 等具有標準 `npm run build` 的前端專案
- 教學遊戲、教材、測驗、班級網頁、作品展示、抽籤器、計時器等純前端工具

不應直接部署：

- Express、Flask、Django、PHP 或其他需要常駐伺服器的網站
- 必須把秘密 API Key 放在瀏覽器中的網站
- 需要私密資料庫憑證的網站
- 含學生個資、密碼、內部文件或其他不適合公開資料的網站

更完整判斷請讀 `references/supported-sites.md`。

## 自然語言意圖

將以下意思視為「新網站發布」：

- 幫我上線
- 幫我發布這個網站
- 把這個網頁放到 GitHub Pages
- 給我一個可以分享的網址

將以下意思視為「更新既有網站」：

- 幫我更新網站
- 重新發布
- 我改好了，再上傳一次

將以下意思視為「查詢狀態」：

- 網址在哪裡
- 網站好了嗎
- 幫我檢查 Pages

## 執行流程

### A. 第一次連結 GitHub

先執行：

```bash
gh --version
gh auth status
```

若 `gh` 不存在，不要假裝可以繼續。告訴使用者需要安裝 GitHub CLI。

若尚未登入，說明：

> 第一次發布需要先連結 GitHub 帳號。瀏覽器會開啟 GitHub 登入頁面；完成登入後即可繼續，之後通常不需重新設定。

再執行：

```bash
gh auth login --web --git-protocol https
gh auth setup-git
```

不要要求使用者自行建立 Token 或 SSH Key。

可使用：

```bash
python scripts/github_auth.py --login-if-needed
```

完成後確認目前使用者：

```bash
gh api user --jq .login
```

### B. 發布前健檢

永遠先執行：

```bash
python scripts/preflight.py <網站或專案路徑>
```

若要讓其他腳本讀取結果：

```bash
python scripts/preflight.py <路徑> --json
```

必須檢查：

- 是否找到 `index.html`
- 是否為可靜態發布網站
- `.env`、秘密金鑰、Token、Private Key 等敏感資訊
- Node/Python/PHP server 等後端需求
- GitHub Project Pages 常見絕對路徑問題
- Vite / React 是否需要 build
- SPA router 是否可能在重新整理時 404

若 `preflight.py` 回傳阻擋錯誤，停止發布。

### C. 新網站發布

在使用者沒有指定網站名稱時，根據資料夾、`package.json` 或 `<title>` 推測簡短名稱。必要時可將中文名稱轉成簡短英文 slug；若無法安全推測，使用 `website-YYYYMMDD-HHMMSS`。

執行：

```bash
python scripts/publish.py <網站或專案路徑> --repo <repository-name>
```

腳本會：

1. 檢查 Git、GitHub CLI 與登入狀態。
2. 執行健檢。
3. 若需要，執行標準 npm build。
4. 只複製實際發布內容到暫存資料夾。
5. 排除 `.env`、`.git`、本機發布記錄等不應公開檔案。
6. 建立 `.nojekyll`。
7. 建立新的 public GitHub repository；若同名 repository 已存在且不是本工具先前管理的網站，不覆寫它，改用不衝突名稱。
8. 將 staging 內容推送到 `main`。
9. 透過 GitHub API 啟用 Pages，發布來源為 `main` 的 `/`。
10. 查詢 Pages 正式 `html_url`。
11. 在原始專案根目錄建立 `.github-pages-publisher.json`，供之後更新使用；這個檔案不會被發布。

### D. 更新既有網站

先找 `<專案根目錄>/.github-pages-publisher.json`。

如果存在，執行：

```bash
python scripts/update.py <網站或專案路徑>
```

更新流程仍需重新健檢與 build。

如果記錄不存在，不要猜測某個既有 repository 可以覆寫。改走新網站發布流程，或在必要時詢問使用者要更新哪一個網站。

### E. 查詢網站狀態

若專案已有本機記錄：

```bash
python scripts/pages_status.py <網站或專案路徑>
```

也可直接指定：

```bash
python scripts/pages_status.py --repo OWNER/REPO
```

## 成功回覆

對一般使用者只需要回覆：

```text
✅ 網站已發布

網站：成語挑戰王
網址：https://USERNAME.github.io/REPOSITORY/

這個網址可以直接分享。
之後修改完成，只要告訴我「幫我更新網站」即可。
```

不要主動顯示 commit SHA、remote、deployment ID 等技術資訊。

## 錯誤翻譯原則

不要把完整終端機錯誤直接丟給一般使用者。先翻成可理解的說法。

- `Authentication failed` →「GitHub 登入已失效，需要重新連結帳號。」
- `404` →「網站檔案已上傳，但首頁或發布設定目前無法正確開啟。」
- `Repository already exists` →「GitHub 已經有同名網站，我不會直接覆寫，正在改用不衝突的名稱。」
- 偵測到秘密資訊 →「我發現可能包含 API 金鑰或敏感資訊，因此已停止發布，避免公開外洩。」

需要進一步排錯時讀 `references/troubleshooting.md`。

## 安全底線

如果掃描到疑似真實秘密資訊：

- 不 commit
- 不 push
- 不在回覆中完整顯示秘密值
- 清楚指出檔案與風險類型，但敏感值只顯示遮罩

若網站涉及學生或個人資料，提醒 GitHub Pages 是公開網站；沒有明確確認適合公開前，不應部署。

## Definition of Done

只有在以下條件都成立時，才能宣告完成：

- 已找到或產生正確的靜態入口檔
- 健檢沒有 blocking issue
- GitHub 登入正常
- Repository 已建立或確認為本工具管理的既有網站
- 最新內容已 push
- GitHub Pages 已啟用
- 已取得 Pages 正式網址

最終目標：讓使用者只需要說「幫我上線」，就能得到一個可分享網址，而不需要先學 GitHub。
