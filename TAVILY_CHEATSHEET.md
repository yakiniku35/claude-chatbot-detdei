# Tavily 搜尋功能 - 快速參考

## 🚀 快速設定（3 步驟）

```bash
# 1. 獲取 API key
訪問: https://tavily.com

# 2. 配置
echo 'tavily_api_key = "tvly-your-key"' >> .streamlit/secrets.toml

# 3. 啟動
streamlit run src/app.py
```

## 🎮 如何使用

### 啟用搜尋
側邊欄 → ✅ 🌐 網路搜尋 → ✅ 🤖 智能搜尋模式

### 觸發關鍵字
中文: `最新` `近期` `現在` `查詢` `搜尋` `趨勢` `統計` `2024` `2025`
英文: `latest` `recent` `current` `search` `query` `trend` `statistics`

### 測試查詢
```
✓ "2024年最新的DEI政策趨勢是什麼？"
✓ "請搜尋最近關於職場多元性的研究"
✓ "What are the latest DEI statistics?"
```

## 📊 狀態指示

| 顯示 | 意義 |
|------|------|
| ✨ Tavily 搜尋已啟用 | 正常運作 |
| ⚠️ Tavily API 未設定 | 需配置 API key |
| 🌐 *此回覆使用智能搜尋* | 該回應使用了搜尋 |

## 🐛 快速故障排除

**問題**: 搜尋不觸發
- [ ] 開啟「網路搜尋」
- [ ] 開啟「智能搜尋模式」
- [ ] 查詢包含觸發關鍵字
- [ ] API key 已設定

**問題**: 顯示 API 未設定
```bash
# 檢查配置
cat .streamlit/secrets.toml | grep tavily

# 或使用環境變數
export TAVILY_API_KEY="tvly-xxx"
```

**問題**: 測試配置
```bash
python3 test_tavily.py
```

## 💰 配額

- 免費: 1,000 次/月
- Pro: $50/月 - 20,000 次
- 查看用量: https://tavily.com/dashboard

## 📁 相關檔案

| 檔案 | 用途 |
|------|------|
| `src/app.py` (150-167行) | Tavily 初始化 |
| `src/app.py` (311-330行) | Agent 圖建立 |
| `src/app.py` (696-708行) | UI 控制 |
| `.streamlit/secrets.toml` | API key 配置 |
| `test_tavily.py` | 測試腳本 |

## 🔗 文件連結

- [快速開始](docs/TAVILY_QUICKSTART.md)
- [完整設定](docs/TAVILY_SETUP.md)
- [使用範例](docs/TAVILY_EXAMPLES.md)
- [技術文件](docs/TAVILY_IMPLEMENTATION_SUMMARY.md)

## 📝 API Key 格式

```toml
# .streamlit/secrets.toml
groq_api_key = "gsk_..."      # 必需
tavily_api_key = "tvly-..."    # 可選
```

## 🎯 工作流程

```
使用者輸入 
  → AI 判斷需要搜尋？
    ├─ YES → Tavily 搜尋 → 整合結果 → 回應
    └─ NO → 直接回應
```

## ⚙️ 進階

### 調整搜尋數量
`src/app.py` 第 166 行：
```python
TavilySearch(max_results=4)  # 改為 2-10
```

### 自訂觸發關鍵字
`src/app.py` 第 333-340 行修改 `keywords` 列表

---

**提示**: 第一次使用？看 [TAVILY_QUICKSTART.md](docs/TAVILY_QUICKSTART.md)
