# GitHub Pages 發布排錯

## 1. `gh` 不存在

症狀：

```text
找不到 gh
```

處理：安裝 GitHub CLI，再執行：

```bash
gh auth login --web --git-protocol https
```

官方：
https://cli.github.com/

## 2. GitHub 登入失效

檢查：

```bash
gh auth status
```

重新登入：

```bash
gh auth login --web --git-protocol https
```

## 3. Repository 建立失敗

檢查：

- Repository 名稱是否衝突
- 帳號是否有建立 repository 權限
- GitHub CLI 是否登入正確帳號

不要在新網站第一次發布時直接 force push 一個未知的既有 repository。

## 4. Pages API 404

新 repository 可能尚未建立 Pages site。使用：

```bash
gh api -X POST repos/OWNER/REPO/pages \
  -f 'source[branch]=main' \
  -f 'source[path]=/'
```

官方：
https://docs.github.com/en/rest/pages/pages

## 5. 首頁 404

確認發布根目錄的頂層有：

```text
index.html
```

注意大小寫。

## 6. CSS / 圖片 / JS 壞掉

檢查：

```text
src="/
href="/
url(/
fetch("/
```

Project Pages 通常多一層 repository pathname。

## 7. React 子頁重新整理 404

若使用 BrowserRouter，可評估改成 Hash Router，或改用適合 SPA fallback 的託管服務。

## 8. Vite 網站白畫面

常見原因是 `base` 路徑與 GitHub Pages repository 路徑不相容。第一版 Skill 會提出警告，但不應在不了解專案的情況下自動大改 `vite.config.*`。

## 9. 偵測到秘密金鑰

停止發布。先移除秘密值、撤銷可能已外洩的金鑰，並改用後端代理、Edge Function、Serverless Function 或適合的安全架構。

如果秘密曾經 commit 到 Git，即使之後刪除檔案，也應視為可能已外洩並進行金鑰輪替。

## 10. Pages 一直在 building

可查：

```bash
gh api repos/OWNER/REPO/pages
```

GitHub Pages 部署可能需要短暫處理時間。若持續失敗，再檢查 Repository 的 Pages 設定、branch、入口檔與 GitHub 服務狀態。
