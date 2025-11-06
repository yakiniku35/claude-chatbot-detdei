# Supabase 整合快速上手檢查清單

## ☑️ 設定前檢查

- [ ] 已有 Supabase 帳號（沒有的話到 https://supabase.com 註冊）
- [ ] 已有 Groq API 金鑰（必須，用於 AI 對話）
- [ ] Python 3.8 或更高版本
- [ ] 已安裝 pip

## ☑️ Supabase 設定步驟

### 1. 建立 Supabase 專案
- [ ] 登入 Supabase Dashboard (https://app.supabase.com)
- [ ] 點擊 "New Project"
- [ ] 填寫專案名稱
- [ ] 設定資料庫密碼（請記住！）
- [ ] 選擇地區（建議選擇離你最近的）
- [ ] 等待專案建立完成（約 2 分鐘）

### 2. 建立資料庫表格
- [ ] 在專案中，前往左側選單的 "SQL Editor"
- [ ] 點擊右上角 "New Query"
- [ ] 開啟本專案的 `supabase_schema.sql` 檔案
- [ ] 複製所有內容並貼到 SQL Editor
- [ ] 點擊右下角 "Run" 執行
- [ ] 確認看到成功訊息（綠色勾勾）

### 3. 取得 API 憑證
- [ ] 前往 "Settings" > "API"
- [ ] 找到並複製 "Project URL"（類似 `https://xxxxx.supabase.co`）
- [ ] 找到並複製 "anon public" API key（很長的字串，以 `eyJ` 開頭）

## ☑️ 應用程式設定步驟

### 1. 安裝相依套件
```bash
cd /path/to/claude-chatbot-detdei
pip install -r requirements.txt
```
- [ ] 執行上述命令
- [ ] 確認沒有錯誤訊息
- [ ] 確認看到 `supabase` 套件已安裝

### 2. 設定機密資訊
- [ ] 在專案根目錄建立 `.streamlit` 資料夾（如果沒有的話）
  ```bash
  mkdir -p .streamlit
  ```
- [ ] 複製範本檔案
  ```bash
  cp .streamlit/secrets.toml.example .streamlit/secrets.toml
  ```
- [ ] 用文字編輯器開啟 `.streamlit/secrets.toml`
- [ ] 填入你的 Groq API 金鑰：
  ```toml
  groq_api_key = "gsk_你的金鑰"
  ```
- [ ] 填入 Supabase 憑證：
  ```toml
  supabase_url = "https://xxxxx.supabase.co"
  supabase_key = "eyJ你的金鑰"
  ```
- [ ] 儲存檔案

### 3. 啟動應用程式
```bash
streamlit run app.py
```
- [ ] 執行上述命令
- [ ] 瀏覽器應該會自動開啟 http://localhost:8501
- [ ] 確認看到應用程式介面

## ☑️ 功能測試

### 基本功能測試
- [ ] 側邊欄顯示 "✅ 系統就緒"
- [ ] 側邊欄顯示 "✅ Supabase 已連線"
- [ ] 可以看到 "💾 儲存聊天記錄到 Supabase" 開關

### Supabase 儲存測試
- [ ] 開啟 "儲存聊天記錄到 Supabase" 開關
- [ ] 展開 "📝 Session 資訊"
- [ ] 可以看到 Session ID
- [ ] 發送一則測試訊息（例如："你好"）
- [ ] 收到 AI 回應
- [ ] 沒有看到任何錯誤訊息

### 歷史記錄測試
- [ ] 發送幾則訊息建立對話
- [ ] 重新整理瀏覽器頁面（F5）
- [ ] 關閉 Supabase 開關（所有訊息會消失，這是正常的）
- [ ] 重新開啟 Supabase 開關
- [ ] 確認之前的對話記錄都載入回來了
- [ ] 應該看到 "✅ 已載入 X 則訊息" 的提示

### Supabase 資料庫驗證
- [ ] 回到 Supabase Dashboard
- [ ] 前往 "Table Editor"
- [ ] 選擇 "chat_history" 表格
- [ ] 確認可以看到你的對話記錄
- [ ] 每則訊息都有對應的 session_id, role, content

### Session 管理測試
- [ ] 記下當前的 Session ID（前 8 碼即可）
- [ ] 點擊 "🔄 建立新 Session"
- [ ] 確認 Session ID 已改變
- [ ] 確認對話記錄已清空
- [ ] 發送新訊息
- [ ] 在 Supabase Dashboard 確認有新的 session_id 記錄

### 清除功能測試
- [ ] 發送幾則訊息
- [ ] 點擊 "🗑️ 清除對話"
- [ ] 確認對話已清除
- [ ] 回到 Supabase Dashboard
- [ ] 重新整理 chat_history 表格
- [ ] 確認該 Session 的記錄已被刪除

## ☑️ 疑難排解

### 問題：側邊欄顯示 "ℹ️ Supabase 未設定"
- [ ] 檢查 `.streamlit/secrets.toml` 檔案是否存在
- [ ] 確認檔案中有 `supabase_url` 和 `supabase_key`
- [ ] 確認沒有拼字錯誤
- [ ] 重新啟動應用程式

### 問題：出現 "Supabase 初始化失敗" 錯誤
- [ ] 確認 Supabase URL 格式正確（https://xxxxx.supabase.co）
- [ ] 確認 API key 完整複製（包含開頭的 eyJ）
- [ ] 檢查 Supabase 專案狀態（在 Dashboard 確認是否正常運作）
- [ ] 確認網路連線正常

### 問題：出現 "儲存訊息失敗" 錯誤
- [ ] 確認已執行 `supabase_schema.sql` 建立表格
- [ ] 在 Supabase 前往 "Table Editor" 確認 chat_history 表格存在
- [ ] 檢查表格的 RLS 政策是否正確設定
- [ ] 前往 "Authentication" > "Policies" 確認政策已啟用

### 問題：歷史記錄無法載入
- [ ] 確認 Session ID 正確
- [ ] 在 Supabase Dashboard 查詢該 session_id 是否有記錄
- [ ] 檢查瀏覽器主控台（F12）是否有錯誤訊息
- [ ] 嘗試清除瀏覽器快取

## ☑️ 最佳實踐

### 安全性
- [ ] 絕不將 `.streamlit/secrets.toml` 提交到 Git
- [ ] 定期更換 API 金鑰
- [ ] 在 Supabase 設定適當的 RLS 政策
- [ ] 考慮設定 IP 白名單（如果是正式環境）

### 效能
- [ ] 定期清理舊的 Session 記錄
- [ ] 監控 Supabase 資料庫大小
- [ ] 考慮設定自動刪除 30 天前的記錄

### 資料管理
- [ ] 定期備份重要對話
- [ ] 為重要的 Session 做標記或筆記
- [ ] 考慮實作 Session 命名功能

## ☑️ 延伸閱讀

- [ ] 閱讀 [SUPABASE_SETUP.md](SUPABASE_SETUP.md) 了解詳細設定
- [ ] 閱讀 [SUPABASE_USAGE.md](SUPABASE_USAGE.md) 學習使用範例
- [ ] 閱讀 [ARCHITECTURE.md](ARCHITECTURE.md) 了解系統架構
- [ ] 閱讀 [UI_CHANGES.md](UI_CHANGES.md) 了解介面變更

## 📞 需要協助？

如果以上步驟都無法解決問題：

1. 檢查 [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) 的疑難排解章節
2. 查看 GitHub Issues 看看是否有類似問題
3. 在 GitHub 提交新的 Issue，附上：
   - 錯誤訊息截圖
   - 使用的 Python 版本
   - 使用的作業系統
   - 已嘗試的解決方法

---

**祝你使用愉快！** 🎉

如果一切正常，你現在應該有一個可以持久化儲存對話記錄的 DEI 聊天機器人了！
