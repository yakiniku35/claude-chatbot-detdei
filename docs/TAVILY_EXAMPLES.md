# Tavily 搜尋功能範例

## 簡介

這裡展示如何在 DEI 政策助手中使用 Tavily 智能搜尋功能。

## 使用範例

### 範例 1：查詢最新趨勢

**使用者輸入：**
```
請告訴我2024年最新的DEI政策趨勢
```

**系統行為：**
1. 🤖 AI 偵測到「最新」、「2024」關鍵字
2. 🔍 自動觸發 Tavily 搜尋
3. 📊 獲取最新資訊
4. 💬 整合搜尋結果回應

**預期回應：**
```
根據最新研究，2024年的DEI政策趨勢包括：

1. **AI與演算法偏見治理**
   許多組織開始關注AI系統中的隱性偏見...

2. **混合辦公環境的包容性**
   遠端工作常態化後，企業著重於...

3. **心理健康納入DEI範疇**
   心理健康議題逐漸被視為DEI的一部分...

[來源: 從 Tavily 搜尋結果整合]

🌐 *此回覆使用智能搜尋*
```

---

### 範例 2：尋找統計數據

**使用者輸入：**
```
美國職場多元性的最新統計數據是什麼？
```

**系統行為：**
1. 偵測「統計」、「最新」
2. 執行 Tavily 搜尋
3. 提取相關數據

**預期回應：**
```
根據最近的研究報告：

• 2024年財富500強企業中，女性CEO佔比為10.4%
• 科技業中非白人員工比例達到38%（較2020年增長5%）
• 68%的企業設有專職DEI主管
• 員工資源群組（ERG）參與率提升至45%

資料來源：[從搜尋結果提取]

🌐 *此回覆使用智能搜尋*
```

---

### 範例 3：查詢特定案例

**使用者輸入：**
```
Search for recent DEI lawsuit cases in 2024
```

**系統行為：**
1. 偵測「recent」、「2024」
2. 英文查詢，自動以英文搜尋
3. 以英文回應

**預期回應：**
```
Here are some notable DEI-related cases from 2024:

1. **Tech Industry Discrimination Case**
   A major tech company faced a class-action lawsuit...

2. **Pay Equity Settlement**
   A financial institution settled for $50M...

3. **Hiring Practices Dispute**
   Federal investigation into algorithmic bias...

[Sources: Recent search results]

🌐 *This response uses intelligent search*
```

---

### 範例 4：不觸發搜尋的對話

**使用者輸入：**
```
什麼是DEI？
```

**系統行為：**
1. 基本概念問題，無需搜尋
2. 使用訓練數據直接回答

**預期回應：**
```
DEI 是 Diversity（多元）、Equity（平等）和 Inclusion（包容）的縮寫。

🌈 **Diversity（多元）**
指重視和尊重人與人之間的差異，包括種族、性別、年齡...

⚖️ **Equity（平等）**
確保每個人都能獲得公平的機會和資源...

🤝 **Inclusion（包容）**
創造一個讓所有人都感到被重視和尊重的環境...

（無搜尋標記，因為是基本知識回答）
```

---

### 範例 5：檔案分析（不使用搜尋）

**使用者操作：**
1. 上傳招聘公告 PDF
2. 點擊「分析檔案」

**系統行為：**
1. 提取檔案內容
2. 根據 DEI 政策分析
3. 不需要網路搜尋（已有完整上下文）

**預期回應：**
```
📋 **DEI 合規性分析**

**檔案**: 招聘公告.pdf

**DEI 相關性**: Yes
**DEI 評分**: 3/5

**分析結果**:

✅ **優點**:
• 使用包容性語言
• 明確歡迎多元背景申請者

⚠️ **需要改進**:
• 「年輕有活力」可能暗示年齡偏好
• 缺少平等機會雇主聲明
• 未提及合理調整措施

**建議修改**:
1. 將「年輕有活力」改為「充滿熱情」
2. 添加："我們是平等機會雇主，歡迎..."

（無搜尋標記，因為是檔案內容分析）
```

---

## 搜尋觸發關鍵字

### 中文關鍵字
- 時間: 最新、近期、現在、2024、2025
- 動作: 查詢、搜尋、找
- 內容: 案例、趨勢、統計、研究

### 英文關鍵字
- Time: latest, recent, current, 2024, 2025
- Action: search, query, find
- Content: case, trend, statistics, research

## 開啟/關閉搜尋

### 側邊欄控制

```
側邊欄選項：
☑️ 🌐 網路搜尋          ← 基礎開關
☑️ 🤖 智能搜尋模式      ← Tavily 開關

狀態顯示：
✨ Tavily 搜尋已啟用     ← 成功
⚠️ Tavily API 未設定     ← 未配置
```

### 模式對比

| 模式 | 網路搜尋 | 智能搜尋 | 效果 |
|------|---------|---------|------|
| **模式 1** | ❌ | ❌ | 純 AI 回答 |
| **模式 2** | ✅ | ❌ | DuckDuckGo 關鍵字搜尋 |
| **模式 3** | ✅ | ✅ | Tavily 智能搜尋 |

## 配額管理

### Tavily 免費方案
- **1,000 次搜尋/月**
- 每次搜尋 = 1 次 API 呼叫
- 建議保留給重要查詢

### 監控用量
訪問 [Tavily Dashboard](https://tavily.com/dashboard) 查看：
- 當月使用量
- 剩餘配額
- 使用歷史

### 節省配額技巧
1. 一般知識問題關閉搜尋
2. 檔案分析不需搜尋
3. 只在需要最新資訊時使用

## 技術細節

### 搜尋流程

```python
# 1. 使用者輸入
user_input = "2024年最新趨勢"

# 2. AI 判斷是否需要搜尋
if contains_keywords(user_input):
    # 3. 呼叫 Tavily
    results = tavily_search.invoke({
        "query": user_input
    })
    
    # 4. 整合結果
    response = llm.invoke({
        "context": results,
        "question": user_input
    })
```

### 結果處理

Tavily 返回結構化資料：
```json
{
  "results": [
    {
      "title": "文章標題",
      "url": "來源網址",
      "content": "相關內容摘要",
      "score": 0.95
    }
  ]
}
```

AI 會：
1. 提取關鍵資訊
2. 整合到回答中
3. 保持一致語言風格
4. 添加搜尋標記

## 故障排除

### 問題：搜尋不觸發

**檢查清單**：
- [ ] 「網路搜尋」已開啟
- [ ] 「智能搜尋模式」已開啟
- [ ] 查詢包含觸發關鍵字
- [ ] Tavily API key 已設定

### 問題：搜尋結果不相關

**可能原因**：
- 查詢過於模糊
- 語言混用（中英混雜）

**改善方法**：
- 使用更具體的關鍵字
- 統一使用單一語言
- 包含時間範圍

## 最佳實踐

### ✅ 推薦做法
```
✓ "請搜尋2024年職場多元性的最新研究"
✓ "What are the latest DEI trends in 2024?"
✓ "幫我找最近的歧視訴訟案例"
```

### ❌ 不推薦做法
```
✗ "DEI是什麼"（基本知識，不需搜尋）
✗ "幫我分析這份檔案"（已有內容）
✗ "你好"（閒聊）
```

---

## 更多資源

- **完整文件**: [TAVILY_SETUP.md](TAVILY_SETUP.md)
- **快速開始**: [TAVILY_QUICKSTART.md](TAVILY_QUICKSTART.md)
- **API 文件**: https://docs.tavily.com

## 支援

遇到問題？
1. 查看 [故障排除指南](TAVILY_SETUP.md#故障排除)
2. 執行 `python3 test_tavily.py` 診斷
3. 提交 GitHub Issue
