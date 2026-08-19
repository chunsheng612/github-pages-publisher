# 支援網站判斷

## 可以直接發布

### 純靜態網站

常見結構：

```text
index.html
style.css
script.js
images/
assets/
```

只要首頁與資源路徑正確，最適合 GitHub Pages。

### 已 build 的網站

```text
dist/index.html
```

或：

```text
build/index.html
```

優先發布 build output，而不是 `src/`。

## 可以在 build 後發布

若 `package.json` 有：

```json
{
  "scripts": {
    "build": "vite build"
  }
}
```

可執行標準 npm build，之後找 `dist/` 或 `build/`。

## 需要警告但不一定阻擋

### 根目錄絕對路徑

GitHub Project Pages 常見網址：

```text
https://USERNAME.github.io/REPOSITORY/
```

因此：

```html
<img src="/images/a.png">
```

可能指到錯誤位置。第一版以偵測、警告為主，不盲目全域改寫。

### Browser Router

`BrowserRouter` / `createBrowserRouter` 的子路由在 GitHub Pages 直接開啟或重新整理時可能 404。可視專案情況改用 Hash Router 或其他 SPA fallback 策略。

## 必須停止

### 後端伺服器

例如：

- Express / Fastify / Koa
- Flask / Django
- PHP
- WebSocket server
- 需要 Node/Python 常駐處理請求

GitHub Pages 不會執行這些 server-side code。

### 秘密資訊

例如：

- `.env`
- OpenAI API Key
- GitHub Token
- Google API Key（若為真正需要保密的 Key）
- Private Key
- Service Account JSON
- 資料庫密碼

不能因為「前端可以執行」就把秘密放進瀏覽器。所有送到前端的內容都應視為可被使用者查看。

## Firebase 補充

Firebase Web App 的部分設定本來就是前端可見設定，但 Service Account Private Key、Admin SDK 憑證等絕對不能放到 Pages。若偵測到 Firebase，應判斷使用的是一般 Web SDK 設定或伺服器端憑證，不可一概視為安全或危險。

## Next.js / Nuxt

只有能輸出純靜態成果的模式才適合。若使用 SSR、Server Actions、API Routes、Middleware 或 Node runtime，第一版不應直接部署到 GitHub Pages。
