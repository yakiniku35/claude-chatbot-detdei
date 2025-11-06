# Supabase 聊天記錄功能使用範例

## 基本配置

在 `.streamlit/secrets.toml` 中新增 Supabase 憑證：

```toml
# Groq API
groq_api_key = "gsk_xxxxxxxxxxxxxxxxxxxx"

# Supabase 配置
supabase_url = "https://xxxxx.supabase.co"
supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xxxxxxxxxxxx"
```

## 使用流程

### 1. 啟動應用程式

```bash
streamlit run app.py
```

### 2. 啟用 Supabase 儲存

1. 在應用程式側邊欄中，會看到以下選項：
   - ✅ Supabase 已連線（如果設定正確）
   - 💾 儲存聊天記錄到 Supabase（切換開關）

2. 開啟「儲存聊天記錄到 Supabase」開關

### 3. 開始對話

開啟 Supabase 儲存後：
- 所有新的對話都會自動儲存到資料庫
- 系統會載入該 Session 的歷史對話（如果有）
- 可以在「Session 資訊」展開區看到當前 Session ID

### 4. Session 管理

在「Session 資訊」展開區中：
- 查看當前 Session ID
- 點擊「🔄 建立新 Session」開始全新對話
- 每個 Session 的對話記錄分開儲存

### 5. 清除對話

點擊「🗑️ 清除對話」按鈕：
- 如果啟用 Supabase：會從資料庫刪除該 Session 的所有記錄
- 如果未啟用 Supabase：只清除當前 session state

## 功能展示

### 情境 1：持續對話

```
使用者: 什麼是 DEI？
助手: DEI 代表 Diversity（多元）、Equity（公平）和 Inclusion（包容）...

[關閉瀏覽器]
[重新開啟應用程式]
[開啟 Supabase 儲存]

✅ 歷史對話自動載入！
```

### 情境 2：多個 Session

```
Session A (工作相關)
- 討論公司 DEI 政策
- 分析內部文件

[建立新 Session]

Session B (學習相關)
- DEI 基本概念
- 最佳實踐案例

每個 Session 的對話分開儲存和載入
```

### 情境 3：跨裝置訪問

```
裝置 A: Session ID abc123
- 對話內容儲存在 Supabase

裝置 B: 需要手動輸入或分享 Session ID 才能訪問相同對話
（預設每個新訪問會產生新的 Session ID）
```

## 資料查詢

可以在 Supabase Dashboard 中查詢聊天記錄：

```sql
-- 查看所有 session
SELECT DISTINCT session_id, MIN(timestamp) as first_message
FROM chat_history
GROUP BY session_id
ORDER BY first_message DESC;

-- 查看特定 session 的對話
SELECT role, content, timestamp
FROM chat_history
WHERE session_id = 'your-session-id'
ORDER BY timestamp;

-- 統計訊息數量
SELECT session_id, COUNT(*) as message_count
FROM chat_history
GROUP BY session_id;
```

## 注意事項

⚠️ **Session ID 管理**
- Session ID 儲存在瀏覽器的 session state
- 清除瀏覽器資料會遺失 Session ID
- 建議記錄重要 Session 的 ID

⚠️ **資料隱私**
- 聊天記錄會儲存在 Supabase 雲端資料庫
- 確保敏感資訊不被記錄
- 定期清除不需要的對話

⚠️ **網路連線**
- 需要穩定的網路連線
- 儲存失敗時會顯示錯誤訊息
- 對話仍會保留在 session state 中

## 疑難排解

### 問題：開關顯示但無法儲存

**解決方案：**
1. 檢查 Supabase 連線狀態
2. 確認已建立 `chat_history` 表格
3. 查看瀏覽器主控台的錯誤訊息

### 問題：無法載入歷史記錄

**解決方案：**
1. 確認 Session ID 正確
2. 檢查資料庫中是否有該 Session 的記錄
3. 確認 RLS 政策設定正確

### 問題：Supabase 未連線

**解決方案：**
1. 確認 `.streamlit/secrets.toml` 設定正確
2. 檢查 Supabase 專案狀態
3. 確認 API 金鑰有效

## 最佳實踐

✅ **定期備份**: 雖然 Supabase 有自動備份，建議定期匯出重要對話

✅ **Session 命名**: 考慮在應用程式中加入 Session 命名功能

✅ **資料保留**: 設定自動刪除舊資料的政策

✅ **效能優化**: 對於長對話，考慮分頁載入歷史記錄

## 進階功能建議

### 1. Session 搜尋功能

可以擴充功能以支援：
- 搜尋特定內容的對話
- 按日期篩選 Session
- 標記重要 Session

### 2. 匯出功能

新增匯出對話為檔案：
- PDF 格式
- JSON 格式
- Markdown 格式

### 3. 分享功能

實作 Session 分享：
- 產生分享連結
- 設定權限控制
- 限時存取

## 相關資源

- [Supabase 官方文件](https://supabase.com/docs)
- [Streamlit Session State](https://docs.streamlit.io/library/api-reference/session-state)
- [SUPABASE_SETUP.md](SUPABASE_SETUP.md) - 完整設定指南
