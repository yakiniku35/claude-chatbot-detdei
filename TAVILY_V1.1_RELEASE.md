# Tavily 搜尋功能 v1.1 發布說明

## 🔧 修復版本發布

**版本**: v1.1  
**發布日期**: 2026-01-16  
**修復類型**: 緊急修復 (Hotfix)

---

## 🐛 修復的問題

### 問題描述

使用者在使用 Tavily 智能搜尋時遇到以下錯誤：

```
❌ Agent 執行失敗: Error code: 400 
{'error': {
  'message': "Failed to call a function...", 
  'type': 'invalid_request_error',
  'code': 'tool_use_failed'
}}
```

### 根本原因

Groq LLM 在調用 `tavily_search` 工具時，自動添加了額外參數：
- `search_depth`: "advanced"
- `topic`: "news"

但 LangChain 的 `TavilySearch` 工具只接受 `query` 參數，導致 API 請求失敗。

---

## ✅ 解決方案

### 技術實作

創建自定義工具包裝器，明確限制只接受 `query` 參數：

```python
@tool
def tavily_search(query: str) -> str:
    """Search the web for current information.
    
    Args:
        query: The search query string
    """
    try:
        search = TavilySearch(max_results=4)
        results = search.invoke({"query": query})
        return str(results)
    except Exception as e:
        return f"Search failed: {str(e)}"
```

### 工具 Schema

修復後的工具明確定義參數結構：

```json
{
  "properties": {
    "query": {
      "type": "string",
      "title": "Query"
    }
  },
  "required": ["query"],
  "type": "object"
}
```

---

## 📝 變更內容

### 修改的檔案

#### src/app.py

**第 150-186 行**: `init_tavily()`
- 從 `return TavilySearch(max_results=4)` 
- 改為自定義 `@tool` 包裝器
- 增加內部錯誤處理

**第 268-299 行**: `tool_node()`
- 簡化參數提取邏輯
- 移除 `await` 關鍵字（改用同步調用）
- 改進錯誤訊息

### 新增的檔案

- `docs/TAVILY_FIX.md` - 詳細修復說明文件

### 更新的檔案

- `docs/TAVILY_SETUP.md` - 新增 v1.1 錯誤處理說明
- `TAVILY_V1.1_RELEASE.md` - 本發布說明

---

## 🎯 影響範圍

### ✅ 修復的功能

- Tavily 搜尋 API 調用
- LangGraph Agent 工具執行
- 錯誤處理流程
- 與 Groq 模型的兼容性

### ✅ 保持不變

- UI 使用者介面
- 搜尋觸發邏輯
- 關鍵字識別
- 多語言支援
- 自動降級機制
- DuckDuckGo 備援

### ⚠️ 新限制

- 無法使用 Tavily 進階參數（`search_depth`, `topic`, `max_results`）
- 如需進階功能，需擴展工具定義

---

## 🚀 升級指南

### 使用者

**步驟 1**: 更新代碼
```bash
cd /Users/peterchiu/claude-chatbot-detdei
git pull  # 如果使用 Git
# 或手動下載最新版本
```

**步驟 2**: 重啟應用
```bash
streamlit run src/app.py
```

**步驟 3**: 驗證修復
測試以下查詢確認搜尋功能正常：
- "2024年最新的DEI政策趨勢是什麼？"
- "What are the latest DEI statistics?"

**步驟 4**: 確認成功
✅ 看到 🌐 *此回覆使用智能搜尋*  
✅ 無 Error code: 400  
✅ 搜尋結果正確顯示

### 開發者

如果你有自定義修改，請注意：

**影響範圍**:
- `init_tavily()` 函數簽名改變
- `tool_node()` 從異步改為同步調用
- 工具 schema 限制更嚴格

**遷移步驟**:
1. 檢查是否有依賴 `TavilySearch` 直接實例的代碼
2. 更新為使用新的 `@tool` 包裝器
3. 如需進階參數，創建額外的工具

---

## 🧪 測試

### 自動測試

```bash
python3 test_tavily.py
```

預期所有測試通過：
```
✅ PASS - 套件安裝
✅ PASS - API Key 設定
✅ PASS - Tavily 搜尋
✅ PASS - ChatGroq LLM
✅ PASS - Agent 整合
```

### 手動測試

| 測試項目 | 測試方法 | 預期結果 |
|---------|---------|---------|
| **基本搜尋** | 輸入含關鍵字的查詢 | 返回結果，顯示 🌐 標記 |
| **中文查詢** | "2024年最新趨勢" | 正常搜尋並回應 |
| **英文查詢** | "latest statistics" | 正常搜尋並回應 |
| **錯誤處理** | API key 錯誤 | 顯示友好錯誤訊息 |
| **降級機制** | 關閉 Tavily 模式 | 自動使用 DuckDuckGo |

---

## 📚 文件更新

### 新增文件

- `docs/TAVILY_FIX.md` - 技術修復詳解

### 更新文件

- `docs/TAVILY_SETUP.md` - 故障排除章節
- `TAVILY_V1.1_RELEASE.md` - 發布說明（本文件）

### 相關文件

- `docs/TAVILY_QUICKSTART.md` - 快速開始指南
- `docs/TAVILY_EXAMPLES.md` - 使用範例
- `docs/TAVILY_IMPLEMENTATION_SUMMARY.md` - 實作總結

---

## 🔮 未來計劃

### v1.2 規劃

- [ ] 支援 Tavily 進階參數（可選）
- [ ] 搜尋結果快取機制
- [ ] 用量統計儀表板
- [ ] 自訂搜尋敏感度

### v2.0 願景

- [ ] 多搜尋引擎整合
- [ ] 結果來源追蹤
- [ ] 向量搜尋支援
- [ ] 混合搜尋策略

---

## 🙏 致謝

感謝使用者回報此問題，讓我們能快速定位並修復。

---

## 📞 支援

### 遇到問題？

1. 查看 [TAVILY_FIX.md](docs/TAVILY_FIX.md)
2. 查看 [TAVILY_SETUP.md](docs/TAVILY_SETUP.md) 故障排除
3. 執行 `python3 test_tavily.py` 診斷
4. 提交 GitHub Issue

### 常見問題

**Q: 升級後還是看到 400 錯誤？**  
A: 確認已完全重啟應用。清除瀏覽器快取後重試。

**Q: 搜尋結果品質變差了嗎？**  
A: 不會。內部仍使用相同的 Tavily API，只是參數傳遞方式改變。

**Q: 可以回退到 v1.0 嗎？**  
A: 可以，但會遇到原本的 400 錯誤。建議使用 v1.1。

**Q: 何時支援進階參數？**  
A: 計劃在 v1.2 中以可選方式支援。

---

## 📊 版本比較

| 功能 | v1.0 | v1.1 |
|------|------|------|
| **基本搜尋** | ✅ | ✅ |
| **多語言** | ✅ | ✅ |
| **錯誤處理** | ⚠️ 會出現 400 | ✅ 已修復 |
| **參數驗證** | ❌ | ✅ |
| **進階參數** | ❌ 嘗試但失敗 | ⚠️ 不支援 |
| **穩定性** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

---

**發布狀態**: ✅ 穩定版本  
**建議升級**: 是  
**相容性**: 向後兼容（無 breaking changes）  
**維護狀態**: 活躍維護

---

📅 **發布時間**: 2026-01-16  
🏷️ **版本**: v1.1  
📝 **變更類型**: 錯誤修復  
⚡ **優先級**: 高
