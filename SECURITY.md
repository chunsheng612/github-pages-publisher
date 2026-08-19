# 安全說明

這個 Skill 會操作 GitHub Repository 與 GitHub Pages，因此安全原則優先於「一定要發布成功」。

## 不要提交秘密資訊

請勿把以下內容放進要發布的網站：

- `.env`
- API Key / Access Token
- Private Key
- Service Account 憑證
- 資料庫密碼
- 學生或個人的敏感資料

發布前的 `preflight.py` 會攔截部分常見秘密格式，但掃描器不能保證找出所有秘密。使用者仍應自行確認網站內容適合公開。

## 如果秘密曾經上傳

不要只刪除檔案。請立即到對應服務撤銷／輪替金鑰，因為秘密可能仍存在 Git 歷史或快取中。

## 回報安全問題

不要在公開 Issue 貼出真實 Token、密碼、Private Key 或學生個資。回報時請先遮罩敏感值，只描述檔案位置、問題類型與重現步驟。
