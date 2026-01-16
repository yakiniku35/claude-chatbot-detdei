# Tavily 搜尋功能設定指南

## 概述

本應用已整合 **Tavily Search API**，透過 LangGraph 提供智能網路搜尋功能。Tavily 是專為 AI 應用設計的搜尋引擎，可提供更準確、結構化的搜尋結果。

## 功能特色

- ✨ **智能搜尋決策**：AI 自動判斷何時需要搜尋
- 🎯 **結構化結果**：專為 LLM 優化的搜尋結果格式
- 🚀 **更快更準確**：比傳統搜尋引擎更適合 AI 應用
- 🔄 **自動降級**：如未設定，自動使用 DuckDuckGo 備援

## 快速設定

### 1. 獲取 API Key

訪問 [Tavily.com](https://tavily.com) 註冊並獲取 API key。

免費方案提供：
- 每月 1,000 次搜尋
- 無需信用卡

### 2. 配置 API Key

#### 方法 A：使用 Streamlit Secrets（推薦本地開發）

編輯 `.streamlit/secrets.toml`：

```toml
# Groq API Key (必需)
groq_api_key = "gsk_your_groq_api_key_here"

# Tavily API Key (可選 - 智能搜尋功能)
tavily_api_key = "tvly-your_tavily_api_key_here"
```

#### 方法 B：使用環境變數（推薦部署）

```bash
export GROQ_API_KEY="your_groq_key"
export TAVILY_API_KEY="tvly-your_tavily_key"
```

### 3. 啟用智能搜尋模式

在應用側邊欄：
1. 開啟 **🌐 網路搜尋**
2. 開啟 **🤖 智能搜尋模式 (LangGraph)**
3. 看到 **✨ Tavily 搜尋已啟用** 表示成功

## 使用方式

### 自動觸發搜尋

AI 會自動判斷以下情況需要搜尋：
- 使用者詢問「最新」、「近期」等時間相關問題
- 查詢特定統計數據、案例或研究
- 涉及當前事件或趨勢

#### 範例問題（會觸發搜尋）：

```
📌 "2024年最新的DEI政策趨勢是什麼？"
📌 "請幫我找最近關於職場多元性的研究"
📌 "目前美國有哪些新的反歧視法規？"
```

### 回應標記

使用 Tavily 搜尋的回應會標記：
```
🌐 *此回覆使用智能搜尋*
```

## 技術架構

### LangGraph Agent Flow

```
使用者輸入
    ↓
[LLM 決策] ← 系統提示 + 政策上下文
    ↓
需要搜尋？
    ├─ YES → [Tavily Search] → 搜尋結果 → [LLM 整合] → 回應
    └─ NO → [直接回應]
```

### 關鍵組件

- **LangGraph**: 狀態圖管理 agent 工作流程
- **ChatGroq**: LLM 推理引擎（支援多模型降級）
- **TavilySearch**: 搜尋工具（最多 4 個結果）
- **MemorySaver**: 維護對話上下文

## 與 DuckDuckGo 的比較

| 功能 | Tavily | DuckDuckGo |
|------|--------|------------|
| **智能決策** | ✅ AI 自動判斷 | ❌ 關鍵字觸發 |
| **結果品質** | ✅ 為 LLM 優化 | ⚠️ 需手動解析 |
| **搜尋速度** | ✅ 快速 | ⚠️ 較慢 |
| **免費額度** | 1,000/月 | 無限制 |
| **配置要求** | 需 API key | 無需配置 |

## 故障排除

### ⚠️ Tavily API 未設定

**現象**：側邊欄顯示「⚠️ Tavily API 未設定，使用基礎模式」

**解決方案**：
1. 檢查 `.streamlit/secrets.toml` 是否包含 `tavily_api_key`
2. 或設定環境變數 `TAVILY_API_KEY`
3. 重啟應用

### ❌ Agent 執行失敗

**現象**：回應顯示「Agent 執行失敗」

**可能原因**：
- Groq API 達到速率限制（會自動切換模型）
- Tavily API key 無效或配額用盡
- 網路連線問題

**解決方案**：
1. 檢查 API key 是否正確
2. 查看 Tavily 儀表板確認配額
3. 暫時關閉智能搜尋模式使用備援

### 🔄 降級到 DuckDuckGo

如果 Tavily 不可用，系統會自動降級：
- 關閉「智能搜尋模式」
- 保留「網路搜尋」開啟
- 將使用 DuckDuckGo 進行關鍵字搜尋

## 進階配置

### 調整搜尋結果數量

編輯 `src/app.py` 第 166 行：

```python
return TavilySearch(max_results=4)  # 改為 2-10
```

### 自訂搜尋觸發邏輯

修改系統提示（第 789-802 行）以調整 AI 何時使用搜尋工具。

### 模型降級策略

支援 7 個 Groq 模型自動降級（第 106-114 行）：
1. `llama-3.3-70b-versatile` （主要）
2. `llama-3.1-70b-versatile` （備援）
3. `llama-3.2-90b-text-preview`
4. `llama-3.1-8b-instant`
5. `mixtral-8x7b-32768`
6. `gemma2-9b-it`
7. `llama3-70b-8192`

## 成本估算

### Tavily 免費方案
- **1,000 次搜尋/月**
- 適用於中小型應用
- 約每天 33 次搜尋

### 升級建議
如果每月搜尋超過 1,000 次：
- **Pro Plan**: $50/月 - 20,000 次搜尋
- **Enterprise**: 聯絡銷售

## 相關文件

- [LangGraph 整合指南](LANGGRAPH_INTEGRATION.md)
- [架構文件](ARCHITECTURE.md)
- [完整 README](README.md)

## 支援

遇到問題？
1. 查看 [Tavily 官方文件](https://docs.tavily.com)
2. 檢查 [LangChain 文件](https://python.langchain.com/docs/integrations/tools/tavily_search)
3. 提交 GitHub Issue
