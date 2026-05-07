# 招生與宣傳組 業務管理工具

每天自動從 Gmail 和 Google Drive 簡章資料夾讀取截止事項，顯示本月待辦清單。

---

## 你需要做什麼

整個設定只需要做**一次**，大約 30–40 分鐘。之後每天早上 8:00 完全自動更新，不需要任何操作。

**前置需求**
- GitHub 帳號（已有）
- 能夠登入 ntueadmission Google 帳號的電腦
- 已安裝 Python 3.8+（驗證：開啟命令提示字元，輸入 `python --version`）

---

## 步驟一：在 GitHub 建立 Repository

1. 登入 GitHub，右上角點 **+** → **New repository**
2. Repository name 填：`ntue-tasks`（或任何你喜歡的名稱）
3. 選 **Public**（GitHub Pages 免費版需要公開）
4. 勾選 **Add a README file**
5. 點 **Create repository**

---

## 步驟二：上傳檔案

1. 在剛建立的 repository 頁面，點 **Add file** → **Upload files**
2. 上傳以下檔案（保持資料夾結構）：

```
index.html                          ← 直接上傳到根目錄
todos.json                          ← 直接上傳到根目錄
scripts/update_todos.py             ← 需先建立 scripts 資料夾
.github/workflows/update.yml        ← 需先建立 .github/workflows 資料夾
```

**建立資料夾的方法**：GitHub 網頁不能直接建資料夾，但在上傳時，在檔名前加路徑即可。例如：點 **Add file** → **Create new file**，在檔名欄位輸入 `scripts/update_todos.py`，它會自動建立 `scripts` 資料夾。

3. 點 **Commit changes** 儲存

---

## 步驟三：開啟 GitHub Pages

1. 在 repository 頁面，點上方的 **Settings**
2. 左側選單點 **Pages**
3. Source 選 **Deploy from a branch**
4. Branch 選 **main**，資料夾選 **/ (root)**
5. 點 **Save**
6. 等待約 1–2 分鐘，頁面會顯示你的網址：`https://你的帳號.github.io/ntue-tasks`

> 此時網頁已可開啟，但本月待辦區塊還沒有資料（顯示「尚未更新」），需完成後續步驟。

---

## 步驟四：取得 Google OAuth Token

這個步驟在你的**本機電腦**執行一次，取得授權 token 後貼到 GitHub Secrets。

### 4-1. 安裝必要套件
開啟命令提示字元，執行：
```
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

### 4-2. 在 Google Cloud Console 建立憑證

1. 開啟 https://console.cloud.google.com/
2. 建立新專案（名稱如：`ntue-tasks`）
3. 左側 **APIs & Services** → **Enabled APIs** → 啟用：
   - **Gmail API**
   - **Google Drive API**
4. 左側 **APIs & Services** → **OAuth consent screen**
   - User Type 選 **External**
   - App name：`NTUE Tasks`
   - 儲存並繼續（其他欄位空白即可）
   - **Test users** 頁面：加入 ntueadmission 的 Gmail 帳號
5. 左側 **APIs & Services** → **Credentials**
   - 點 **+ CREATE CREDENTIALS** → **OAuth client ID**
   - Application type：**Desktop app**
   - 下載 JSON，儲存為 `credentials.json`

### 4-3. 執行授權腳本，取得 token

在命令提示字元，切換到 `credentials.json` 所在資料夾，執行：

```python
# 把以下內容存為 get_token.py，再執行 python get_token.py

from google_auth_oauthlib.flow import InstalledAppFlow
import json

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]

flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
creds = flow.run_local_server(port=0)

print("=== 請複製以下內容，貼到 GitHub Secrets ===")
print(creds.to_json())
```

執行後：
1. 瀏覽器自動開啟，登入 ntueadmission Google 帳號
2. 允許存取 Gmail 和 Google Drive
3. 命令提示字元會顯示一長串 JSON，**全部複製**（包含前後的 `{}`）

---

## 步驟五：設定 GitHub Secrets

1. 在 GitHub repository 頁面，點 **Settings**
2. 左側 **Secrets and variables** → **Actions**
3. 點 **New repository secret**，依序建立以下三個 Secret：

| Secret 名稱 | 值 |
|-------------|-----|
| `GMAIL_TOKEN_JSON` | 步驟 4-3 複製的那串 JSON |
| `GDRIVE_TOKEN_JSON` | 同上（Gmail 和 Drive 使用同一組 token） |
| `BROCHURE_FOLDER_ID` | `1dext3fFM9TIzMjb9wo4YB0xnxADs7qZ3` |

> `BROCHURE_FOLDER_ID` 是「簡章重要時程」資料夾的 ID，已預先填入，不需修改。

---

## 步驟六：手動觸發第一次更新

1. 在 repository 頁面，點上方 **Actions**
2. 左側點「**每日自動更新本月待辦**」
3. 右側點 **Run workflow** → **Run workflow**
4. 等待約 30–60 秒，重新整理頁面
5. 若出現綠色勾勾，表示成功

現在開啟你的網址，本月待辦就會顯示資料了！

---

## 日常使用

**每天早上 8:00**，GitHub Actions 自動更新，不需要任何操作。

**有新簡章時**：把圖片或 PDF 上傳到 Google Drive 的「簡章重要時程」資料夾，等到隔天早上 8:00 自動讀取。或者手動觸發（步驟六的方法）立即更新。

**分享給同仁**：直接把網址 `https://你的帳號.github.io/ntue-tasks` 傳給大家。

---

## 常見問題

**Q: GitHub Actions 執行失敗（紅色叉叉）？**
A: 點進 Actions → 點失敗的執行 → 展開錯誤訊息。最常見原因是 Token 過期（每 6 個月需重新執行步驟 4-3 取得新 token 並更新 Secrets）或 Secret 名稱拼錯。

**Q: 本月待辦顯示空白或「尚未更新」？**
A: 表示 GitHub Actions 還沒成功執行過。請手動觸發一次（步驟六）。

**Q: 某筆待辦比對到錯誤的業務？**
A: 這是規則比對的正常誤差。可以在網頁上按「已完成」隱藏它。若某類 Email 總是比對錯誤，請告訴我，我來修改 `scripts/update_todos.py` 的關鍵字清單。

**Q: Token 多久需要更新一次？**
A: Google OAuth Refresh Token 理論上永久有效，但若長時間未使用或 Google 帳號安全設定變更，可能失效。建議每半年確認一次 Actions 是否正常執行。

**Q: repository 要設定 Public 嗎？index.html 裡有業務資料，是否有洩漏風險？**
A: index.html 中的業務清單（人名、業務名稱）是公開的。todos.json 中包含 Email 摘要片段。若不希望公開，可升級 GitHub Pro（每月 4 USD）使用 Private repository 的 GitHub Pages，或把 todos.json 中的 action 欄位改為只顯示業務名稱（請告訴我，我來修改腳本）。
