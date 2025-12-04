# LangGraph Integration - Quick Reference

## 🚀 What's New?

Your DEI chatbot now has **intelligent search** powered by LangGraph and Tavily API!

## 📋 Quick Setup

### 1. Install Dependencies (Already Done ✅)
```bash
pip install -r requirements.txt
```

### 2. Get Tavily API Key (Optional but Recommended)

1. Visit: https://tavily.com/
2. Sign up (Free tier: 1,000 searches/month)
3. Copy your API key

### 3. Configure API Key

Create/Edit `.streamlit/secrets.toml`:
```toml
groq_api_key = "your_existing_groq_key"
tavily_api_key = "your_new_tavily_key"  # Add this line
```

### 4. Start the App
```bash
streamlit run src/app.py
```

### 5. Enable Agent Mode

In the sidebar, toggle **"🤖 智能搜尋模式 (LangGraph)"** to ON.

## 🎯 When to Use Each Mode?

### Traditional Mode (Default)
✅ Use for:
- Simple questions
- Casual chat
- Known policy lookups
- File analysis
- **Faster responses** (2-3 seconds)

### Agent Mode (LangGraph)
✅ Use for:
- "What are the **latest** DEI trends?"
- "Recent case studies in 2025"
- Research questions
- Comparative analysis
- **More accurate** but slower (5-10 seconds)

## 🔍 How It Works

### Traditional Flow
```
Question → Keyword Match → DuckDuckGo → Response
```

### Agent Flow
```
Question → AI Decides → Maybe Search Tavily → Smarter Response
```

The agent **intelligently decides** when to search, not just based on keywords!

## 💡 Example Queries

### Triggers Intelligent Search
```
❓ "What are the latest DEI regulations in 2025?"
❓ "Recent diversity hiring trends"
❓ "Current best practices for inclusive workplace"
```

### Uses Cached Policy Knowledge
```
❓ "Explain our DEI policy on language"
❓ "What does our policy say about accessibility?"
❓ "How do we define diversity?"
```

## 🛠️ Troubleshooting

### Agent toggle not showing?
- LangChain packages not installed
- Run: `pip install -r requirements.txt`

### "Tavily API 未設定" warning?
- Tavily API key not configured
- Agent still works, but less effective
- Add key to `.streamlit/secrets.toml`

### Slow responses?
- Normal for agent mode with search (5-10s)
- Switch to traditional mode for faster responses
- Or disable "🌐 網路搜尋" entirely

### Error messages?
- Check Streamlit console for details
- Verify API keys are correct
- Run test: `python test_langgraph.py`

## 📊 Features Comparison

| Feature | Traditional | Agent Mode |
|---------|-------------|------------|
| Speed | ⚡⚡⚡ Fast | ⚡⚡ Moderate |
| Search | Keyword-based | AI-driven |
| Accuracy | Good | Better |
| Context | Limited | High |
| Cost | Lower | Higher |

## 🧪 Testing

Verify everything works:
```bash
python test_langgraph.py
```

Should see:
```
✅ PASS - Package Imports
✅ PASS - Agent Graph Structure
✅ PASS - App.py Syntax
✅ All tests passed!
```

## 📚 Documentation

- **Setup Guide**: `docs/LANGGRAPH_INTEGRATION.md`
- **Implementation Details**: `docs/LANGGRAPH_IMPLEMENTATION.md`
- **Architecture Diagrams**: `docs/ARCHITECTURE_DIAGRAMS.md`

## 🎓 Tips

1. **Start Simple**: Try traditional mode first
2. **Test Agent**: Ask about "latest 2025 DEI trends"
3. **Monitor Cost**: Free tier = 1,000 Tavily searches/month
4. **Toggle Modes**: Switch based on query complexity
5. **Check Indicators**: Look for "🌐 *此回覆使用智能搜尋*"

## 🔑 API Keys Summary

### Required
- ✅ `GROQ_API_KEY` - For all AI chat (already have)

### Optional
- 🆕 `TAVILY_API_KEY` - For intelligent search (NEW!)
- 📦 `SUPABASE_URL/KEY` - For chat history (existing)

## 🚨 Important Notes

- ✅ **Backward Compatible**: Works without Tavily
- ✅ **Graceful Fallback**: Auto-switches if agent fails
- ✅ **No Breaking Changes**: All existing features work
- ✅ **Optional Feature**: Can disable anytime

## 📞 Quick Help

### App won't start?
```bash
pip install -r requirements.txt
python test_langgraph.py
streamlit run src/app.py
```

### Need API keys?
- Groq: https://console.groq.com/
- Tavily: https://tavily.com/

### Want to verify installation?
```bash
python -c "import langgraph; print('✅ LangGraph ready!')"
```

## 🎉 You're Ready!

The LangGraph integration is fully installed and tested. 

**Next Steps:**
1. ✅ Dependencies installed
2. ⏭️ Get Tavily API key (optional)
3. ⏭️ Configure in secrets.toml
4. ⏭️ Run `streamlit run src/app.py`
5. ⏭️ Toggle agent mode ON
6. ⏭️ Ask: "What are the latest DEI trends in 2025?"

---

**Happy chatting! 🤖✨**
