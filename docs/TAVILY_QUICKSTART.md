# Tavily 搜尋功能 - 快速開始指南

## ✅ 實作狀態

Tavily 搜尋功能**已完全實作**並整合到應用中！

### 已實作功能

- ✅ **TavilySearch 整合** - 使用 `langchain-tavily` 套件
- ✅ **LangGraph Agent** - 智能決策搜尋需求
- ✅ **多模型降級** - 7 個 Groq 模型自動切換
- ✅ **DuckDuckGo 備援** - Tavily 不可用時自動降級
- ✅ **上下文保持** - 使用 MemorySaver 維護對話歷史
- ✅ **UI 整合** - 側邊欄開關控制

## 🚀 立即使用

### 步驟 1：設定 API Keys

編輯 `.streamlit/secrets.toml`：

```toml
# 必需
groq_api_key = "gsk_your_groq_key"

# 可選 - 啟用智能搜尋
tavily_api_key = "tvly-your_tavily_key"
```

**獲取 API Keys：**
- Groq: https://console.groq.com/keys
- Tavily: https://tavily.com (免費 1000 次/月)

### 步驟 2：啟動應用

```bash
streamlit run src/app.py
```

### 步驟 3：啟用智能搜尋

在應用側邊欄：
1. ✅ 開啟 **🌐 網路搜尋**
2. ✅ 開啟 **🤖 智能搜尋模式 (LangGraph)**
3. 看到 ✨ **Tavily 搜尋已啟用** 即成功

## 💬 測試查詢

試試這些問題來觸發智能搜尋：

```
📌 2024年最新的DEI政策趨勢是什麼？
📌 請搜尋最近關於職場平等的研究
📌 目前美國有哪些反歧視法規？
📌 What are the latest DEI statistics?
```

成功使用搜尋的回應會顯示：
```
🌐 *此回覆使用智能搜尋*
```

## 🔧 技術架構

### Agent 工作流程

```mermaid
graph LR
    A[使用者輸入] --> B{LLM 決策}
    B -->|需要搜尋| C[Tavily Search]
    B -->|不需搜尋| E[直接回應]
    C --> D[整合搜尋結果]
    D --> E
    E --> F[回應使用者]
```

### 核心組件

| 組件 | 用途 | 狀態 |
|------|------|------|
| **TavilySearch** | 執行網路搜尋 | ✅ 已實作 |
| **ChatGroq** | LLM 推理引擎 | ✅ 已實作 |
| **LangGraph** | Agent 狀態管理 | ✅ 已實作 |
| **MemorySaver** | 對話記憶 | ✅ 已實作 |

### 關鍵代碼位置

- **Tavily 初始化**: `src/app.py` 第 151-167 行
- **Agent 建立**: 第 311-330 行
- **搜尋決策**: 第 261-308 行
- **主對話邏輯**: 第 750-829 行

## 📊 功能對比

### Tavily vs DuckDuckGo

| 特性 | Tavily 模式 | DuckDuckGo 模式 |
|------|------------|----------------|
| **搜尋決策** | 🤖 AI 智能判斷 | 🔤 關鍵字觸發 |
| **結果品質** | ⭐⭐⭐⭐⭐ LLM 優化 | ⭐⭐⭐ 需解析 |
| **回應速度** | ⚡ 快速 | ⏱️ 中等 |
| **配置** | 需 API key | 無需配置 |
| **成本** | 1000 次/月免費 | 完全免費 |

## 🐛 故障排除

### 問題 1：看不到「智能搜尋模式」選項

**原因**: LangGraph 未正確初始化

**解決**:
```bash
pip install -U langchain-tavily langgraph langchain-groq
```

### 問題 2：顯示「Tavily API 未設定」

**原因**: API key 未配置

**解決**:
1. 檢查 `.streamlit/secrets.toml`
2. 或設定環境變數: `export TAVILY_API_KEY="tvly-xxx"`

### 問題 3：搜尋不觸發

**原因**: 查詢未包含觸發關鍵字

**解決**: 明確使用時間相關詞彙（最新、2024、recent 等）

### 問題 4：Agent 執行失敗

**檢查**:
1. Groq API 配額（會自動切換模型）
2. Tavily 配額（查看 https://tavily.com/dashboard）
3. 網路連線

## 📈 進階配置

### 調整搜尋結果數量

編輯 `src/app.py` 第 166 行：

```python
return TavilySearch(max_results=4)  # 改為 2-10
```

### 調整自動搜尋敏感度

修改 `should_search()` 函數（第 332-341 行）的關鍵字列表。

### 自訂系統提示

在第 786-802 行調整 agent 的系統提示，影響：
- 何時觸發搜尋
- 如何整合結果
- 回應風格

## 📚 相關文件

- **完整設定指南**: [TAVILY_SETUP.md](TAVILY_SETUP.md)
- **LangGraph 整合**: [LANGGRAPH_INTEGRATION.md](LANGGRAPH_INTEGRATION.md)
- **架構文件**: [ARCHITECTURE.md](ARCHITECTURE.md)

## 🧪 測試

執行測試腳本驗證安裝：

```bash
export GROQ_API_KEY="your_key"
export TAVILY_API_KEY="your_key"
python3 test_tavily.py
```

預期輸出：
```
✅ PASS - 套件安裝
✅ PASS - API Key 設定
✅ PASS - Tavily 搜尋
✅ PASS - ChatGroq LLM
✅ PASS - Agent 整合

總計: 5/5 測試通過
🎉 所有測試通過！
```

## 💡 最佳實踐

1. **開發環境**: 使用 `.streamlit/secrets.toml`
2. **生產環境**: 使用環境變數
3. **配額管理**: 監控 Tavily 用量（免費 1000 次/月）
4. **錯誤處理**: 系統會自動降級到 DuckDuckGo
5. **用戶提示**: 明確告知使用者何時使用了搜尋

## 🎯 使用建議

### 適合使用 Tavily 的場景
- ✅ 查詢最新政策/法規
- ✅ 獲取當前統計數據
- ✅ 尋找真實案例
- ✅ 驗證事實資訊

### 不需要搜尋的場景
- ⭕ 一般 DEI 概念解釋
- ⭕ 政策檔案分析（已有上下文）
- ⭕ 閒聊對話

## 🌟 效果展示

**無搜尋模式**：
```
Q: 什麼是DEI？
A: DEI 代表多元、平等與包容...
   （基於訓練數據回答）
```

**智能搜尋模式**：
```
Q: 2024年最新的DEI趨勢？
A: 根據最新研究...（引用 Tavily 搜尋結果）
   • [來源1] ...
   • [來源2] ...
   
🌐 *此回覆使用智能搜尋*
```

---

**狀態**: ✅ 生產就緒  
**版本**: 1.0  
**更新**: 2026-01-16
