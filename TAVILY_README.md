# 🔍 Tavily 搜尋功能

## 狀態：✅ 已完全實作

Tavily 智能搜尋功能已整合到 DEI 政策助手中！

## 📖 快速導覽

### 新使用者
👉 從這裡開始：[快速開始指南](docs/TAVILY_QUICKSTART.md)

### 開發人員
👉 詳細設定：[完整設定指南](docs/TAVILY_SETUP.md)

### 想看範例
👉 使用案例：[實際範例](docs/TAVILY_EXAMPLES.md)

### 技術細節
👉 實作總結：[技術文件](docs/TAVILY_IMPLEMENTATION_SUMMARY.md)

## ⚡ 3 分鐘快速設定

```bash
# 1. 獲取 Tavily API key (免費)
# 訪問 https://tavily.com

# 2. 配置 API key
echo 'tavily_api_key = "tvly-your-key"' >> .streamlit/secrets.toml

# 3. 啟動應用
streamlit run src/app.py

# 4. 在側邊欄啟用「智能搜尋模式」
```

## ✨ 主要功能

- 🤖 **智能決策** - AI 自動判斷何時需要搜尋
- 🌐 **多語言** - 支援繁中、簡中、英文
- ⚡ **快速準確** - 專為 LLM 優化的搜尋結果
- 🔄 **自動降級** - 無 Tavily 時使用 DuckDuckGo
- 💰 **免費額度** - 每月 1,000 次免費搜尋

## 📝 測試查詢

試試這些問題來體驗智能搜尋：

```
📌 "2024年最新的DEI政策趨勢是什麼？"
📌 "請搜尋最近關於職場多元性的研究"
📌 "What are the latest DEI statistics?"
```

成功的回應會標示：🌐 *此回覆使用智能搜尋*

## 🆘 需要幫助？

- ❓ [常見問題](docs/TAVILY_SETUP.md#故障排除)
- 🧪 [測試腳本](test_tavily.py)
- 📚 [Tavily 官方文件](https://docs.tavily.com)

---

**更新日期**: 2026-01-16  
**版本**: 1.0  
**狀態**: 生產就緒
