# Supabase 聊天記錄整合指南

本指南說明如何設定 Supabase 來儲存 DEI 聊天機器人的對話記錄。

## 前置需求

- Supabase 帳號（在 [supabase.com](https://supabase.com) 註冊）
- Python 3.8+

## 設定步驟

### 1. 建立 Supabase 專案

1. 登入 [Supabase Dashboard](https://app.supabase.com)
2. 點擊 "New Project"
3. 輸入專案名稱、資料庫密碼和地區
4. 等待專案建立完成

### 2. 建立資料庫表格

1. 在 Supabase Dashboard 中，前往 "SQL Editor"
2. 點擊 "New Query"
3. 複製 `supabase_schema.sql` 的內容並貼上
4. 點擊 "Run" 執行 SQL

這將建立：
- `chat_history` 表格用於儲存聊天記錄
- 必要的索引以提升查詢效能
- Row Level Security (RLS) 政策

### 3. 取得 Supabase 憑證

1. 在 Supabase Dashboard 中，前往 "Settings" > "API"
2. 複製以下兩個值：
   - **Project URL** (例如: `https://xxxxx.supabase.co`)
   - **anon/public API key** (以 `eyJ` 開頭的長字串)

### 4. 設定應用程式

在專案根目錄建立或更新 `.streamlit/secrets.toml` 檔案：

```toml
groq_api_key = "your_groq_api_key_here"
supabase_url = "your_supabase_project_url"
supabase_key = "your_supabase_anon_key"
```

### 5. 安裝相依套件

```bash
pip install -r requirements.txt
```

## 使用方式

### 啟動應用程式

```bash
streamlit run app.py
```

### 啟用 Supabase 儲存

1. 在側邊欄中，找到 "💾 儲存聊天記錄到 Supabase" 開關
2. 開啟開關以啟用聊天記錄儲存
3. 系統會自動：
   - 載入現有的聊天記錄（如果有）
   - 儲存新的對話訊息
   - 在清除對話時刪除記錄

### Session 管理

- 每個瀏覽器 session 都有唯一的 Session ID
- 點擊 "🔄 建立新 Session" 可以開始新的對話
- 切換到不同裝置或清除瀏覽器資料會產生新的 Session ID

## 資料結構

### chat_history 表格

| 欄位 | 類型 | 說明 |
|------|------|------|
| id | BIGSERIAL | 主鍵（自動遞增） |
| session_id | UUID | Session 識別碼 |
| role | VARCHAR(20) | 訊息角色（user/assistant/system） |
| content | TEXT | 訊息內容 |
| timestamp | TIMESTAMP | 訊息時間戳記 |
| created_at | TIMESTAMP | 建立時間 |

## 功能特點

✅ **自動儲存**: 啟用後自動儲存所有對話
✅ **歷史載入**: 重新開啟應用程式時載入先前的對話
✅ **Session 隔離**: 每個 session 的對話分開儲存
✅ **安全刪除**: 清除對話時同步刪除資料庫記錄
✅ **可選功能**: 可以選擇開啟或關閉 Supabase 儲存

## 安全性考量

- 使用 Row Level Security (RLS) 保護資料
- API 金鑰儲存在 `secrets.toml` 中（不會提交到 Git）
- 支援 anonymous 和 authenticated 使用者

## 疑難排解

### 無法連線到 Supabase

1. 確認 `supabase_url` 和 `supabase_key` 正確
2. 檢查網路連線
3. 確認 Supabase 專案狀態正常

### 無法儲存訊息

1. 確認已執行 `supabase_schema.sql` 建立表格
2. 檢查 RLS 政策設定
3. 查看應用程式錯誤訊息

### Session ID 遺失

- Session ID 儲存在瀏覽器的 session state
- 清除瀏覽器快取會產生新的 Session ID
- 可以手動建立新 Session

## 進階設定

### 自訂 RLS 政策

編輯 `supabase_schema.sql` 中的 RLS 政策以符合你的安全需求：

```sql
-- 例如：只允許查看自己的 session
CREATE POLICY "Users can only see their own sessions" ON chat_history
    FOR SELECT
    USING (session_id = current_setting('app.session_id')::uuid);
```

### 資料保留政策

可以設定自動刪除舊資料：

```sql
-- 刪除 30 天前的記錄
DELETE FROM chat_history 
WHERE created_at < NOW() - INTERVAL '30 days';
```

## 支援

如有問題或建議，請在 GitHub 提交 Issue。
