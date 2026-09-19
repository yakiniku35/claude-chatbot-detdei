# DEI Policy Chatbot

Streamlit 聊天機器人，依據 `prompt.md` 的政策指令，協助檢查情境、公告、政策與溝通內容中的 DEI 合規風險。
目前使用 Groq API（免費層）作為模型供應商。

## 安裝

```bash
pip install -r requirements.txt
```

### API 金鑰設定

**方式一：Streamlit Secrets（本機開發建議）**

建立 `.streamlit/secrets.toml`（可複製 `.streamlit/secrets.toml.example`）：

```toml
groq_api_key = "your_key_here"
```

**方式二：環境變數（部署建議）**

```bash
export GROQ_API_KEY="your_key_here"
```

金鑰只在伺服器端使用，不會傳到前端。

## 執行

```bash
streamlit run src/app.py
```

## 功能

- **合規審查**：依 `prompt.md` 的格式輸出違反條款、政策來源、明確禁止事項、風險評估與建議行動
- **自動語言偵測**：使用者用什麼語言提問就用什麼語言回覆（中文一律繁體）
- **串流回覆**：逐字顯示，不必等整段生成完
- **模型自動降級**：主力模型額度用完時自動改用備援模型
- **範例問題**：首次進入時提供三個起手式

以下功能已實作但預設關閉，改 `src/app.py` 頂端的開關即可啟用：
`ENABLE_SIDEBAR`、`ENABLE_FILE_UPLOAD`（PDF/DOCX/TXT）、`ENABLE_WEB_SEARCH`、
`ENABLE_SUPABASE`（對話保存）、`ENABLE_AGENT_MODE` + `ENABLE_TAVILY`（LangGraph 智能搜尋）。

## 架構

單檔 Streamlit App（`src/app.py`），分成五個區塊：

| 區塊 | 內容 |
|---|---|
| 1. 設定常數 | 功能開關、`MODEL_CHAIN` 降級清單、token 與重試等成本控制參數 |
| 2. 提示詞組裝 | `get_base_prompt()` 讀取 `prompt.md`、`detect_language()`、`build_system_prompt()` |
| 3. API 呼叫層 | `init_groq()`、`build_api_messages()` 裁切歷史、`request_stream()` 降級與重試、`classify_error()` |
| 4. 選用功能 | `read_file()`、`search_web()`、Supabase、LangGraph Agent |
| 5. 介面 | 自訂 CSS、標題列、對話歷史、範例問題、`st.chat_input` |

主要成本控制參數（都在檔案頂端）：

```python
MAX_HISTORY_MESSAGES = 10    # 最多送出最近 10 則對話
MAX_HISTORY_CHARS = 12000    # 歷史訊息總字元上限
MAX_TOKENS = 1600            # 單次回覆上限，最直接的省錢開關
```

## 文件

- [`docs/api-strategy.md`](docs/api-strategy.md) — **免費 API 之後的升級路線、成本試算與方案比較**
- [`prompt.md`](prompt.md) — 政策審查的系統提示詞
- [`security.md`](security.md) — 安全性說明
- [`config/prompts.json`](config/prompts.json) — 行政命令與政策條文資料

## 開發環境

DevContainer 已設定給 GitHub Codespaces（Python 3.11+），會自動安裝相依套件並開放 8501 埠。
