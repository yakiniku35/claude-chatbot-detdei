# LangGraph Integration Guide

## Overview

This DEI chatbot now includes an optional **LangGraph-based intelligent search system** inspired by Perplexity 2.0. The system uses an AI agent that intelligently decides when to search the web for current information.

## Features

### 1. **Intelligent Tool Routing**
- The AI agent automatically determines whether to:
  - Answer from cached DEI policy knowledge
  - Search the web for current information
  - Combine both sources

### 2. **Tavily Search API**
- More comprehensive and reliable than DuckDuckGo
- Returns up to 4 high-quality search results
- Better context extraction from web pages

### 3. **Conversation Memory**
- Maintains context across the entire conversation
- Uses LangGraph's MemorySaver for persistent state
- Thread-based conversation tracking

### 4. **Fallback Architecture**
- Gracefully falls back to traditional Groq + DuckDuckGo if:
  - LangChain packages not installed
  - Tavily API key not configured
  - Agent initialization fails

## Architecture

```
User Input
    ↓
LangGraph Agent
    ↓
Agent Model (LLaMA 3.3 70B via Groq)
    ↓
Decision: Search or Respond?
    ↓
├─ Search → Tavily API → Process Results → Generate Response
└─ Respond → Use DEI Policy Context → Generate Response
```

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

New dependencies:
- `langchain>=0.3.0`
- `langchain-community>=0.3.0`
- `langchain-core>=0.3.0`
- `langchain-groq>=0.2.0`
- `langgraph>=0.3.0`
- `langgraph-checkpoint>=2.0.0`
- `langchain-tavily>=0.2.0`

### 2. Configure Tavily API Key

**Option 1 - Streamlit Secrets (recommended for local):**

Create or update `.streamlit/secrets.toml`:

```toml
groq_api_key = "your_groq_key_here"
tavily_api_key = "your_tavily_key_here"
```

**Option 2 - Environment Variable (recommended for deployment):**

```bash
export GROQ_API_KEY="your_groq_key_here"
export TAVILY_API_KEY="your_tavily_key_here"
```

### 3. Get a Tavily API Key

1. Visit [https://tavily.com/](https://tavily.com/)
2. Sign up for a free account
3. Generate an API key
4. Free tier includes 1,000 searches/month

## Usage

### Enabling Agent Mode

1. Start the application: `streamlit run src/app.py`
2. In the sidebar, find "🤖 智能搜尋模式 (LangGraph)"
3. Toggle it ON to enable intelligent search
4. The system will show "✨ Tavily 搜尋已啟用" if configured correctly

### How It Works

**Traditional Mode (Default Groq):**
- Uses keyword detection to trigger DuckDuckGo search
- Keywords: "最新", "latest", "2024", "2025", etc.
- Simple, fast, but less intelligent

**Agent Mode (LangGraph):**
- AI decides autonomously when to search
- More context-aware decision making
- Can combine multiple information sources
- Slower but more accurate

### Example Queries

**Queries that trigger search:**
```
User: "What are the latest DEI trends in 2025?"
Agent: [Searches web] → [Processes results] → [Generates informed response]
```

**Queries that use cached knowledge:**
```
User: "Explain the DEI policy on inclusive language"
Agent: [Uses policy context] → [Generates response]
```

**Queries that combine both:**
```
User: "How does our DEI policy compare to recent industry standards?"
Agent: [Uses policy + web search] → [Generates comprehensive response]
```

## Technical Details

### Agent State Management

```python
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
```

The agent maintains conversation state using LangGraph's checkpoint system.

### Search Tool Configuration

```python
TavilySearch(max_results=4)
```

Returns top 4 results with:
- Title
- URL
- Content snippet
- Relevance score

### Model Configuration

```python
ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=api_key,
    temperature=0.7
)
```

Using Groq's LLaMA 3.3 70B model for agent reasoning.

## Troubleshooting

### Agent mode not available

**Symptom:** Toggle doesn't appear in sidebar

**Solution:**
- Check if `langchain` packages are installed: `pip list | grep langchain`
- Verify Groq API key is configured
- Check console for initialization errors

### Tavily search not working

**Symptom:** Warning "⚠️ Tavily API 未設定，使用基礎模式"

**Solution:**
- Verify `TAVILY_API_KEY` is in secrets or environment
- Check API key is valid at [Tavily Dashboard](https://tavily.com/dashboard)
- Ensure you haven't exceeded free tier limits (1,000/month)

### Slow response times

**Symptom:** Agent takes >10 seconds to respond

**Cause:** Agent is searching the web and processing results

**Solutions:**
- This is normal behavior for web search queries
- Disable agent mode for casual conversation
- Increase Tavily result limit if needed

### "Agent 執行失敗" error

**Symptom:** Error message when using agent mode

**Solutions:**
1. Check all dependencies are installed
2. Verify API keys are valid
3. Check Streamlit console for detailed error
4. Fall back to traditional mode if persistent

## Performance Comparison

| Feature | Traditional Mode | Agent Mode |
|---------|-----------------|------------|
| Response Time | ~2-3s | ~5-10s |
| Search Quality | Basic (DuckDuckGo) | Advanced (Tavily) |
| Decision Making | Keyword-based | AI-driven |
| Context Awareness | Limited | High |
| Cost | Lower | Higher (Tavily API) |

## Best Practices

1. **Use agent mode for:**
   - Research questions
   - Current events
   - Comparative analysis
   - Complex policy inquiries

2. **Use traditional mode for:**
   - Simple questions
   - Casual conversation
   - Known policy lookups
   - File analysis

3. **API Key Management:**
   - Never commit API keys to version control
   - Use `.streamlit/secrets.toml` (gitignored)
   - Rotate keys periodically

4. **Cost Optimization:**
   - Monitor Tavily usage in dashboard
   - Disable agent mode when not needed
   - Free tier sufficient for most use cases

## Future Enhancements

Potential improvements:
- [ ] Streaming responses for agent mode
- [ ] Visual search progress indicators
- [ ] Multiple search result sources
- [ ] Search result caching
- [ ] Custom tool integration
- [ ] Advanced agent reasoning patterns

## References

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Tavily API Documentation](https://docs.tavily.com/)
- [Groq API Documentation](https://console.groq.com/docs)
- [Perplexity 2.0 Inspiration](https://github.com/harishneel1/perplexity_2.0)
