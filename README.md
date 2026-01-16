# DEI Policy Chatbot
- [link](https://yakiniku35-claude-chatbot-detdei-srcapp-sesxar.streamlit.app/)
- A Streamlit-based chatbot application for analyzing content against Diversity, Equity, and Inclusion (DEI) policies.

## ✨ New: Intelligent Search with LangGraph

This chatbot now features an optional **AI-powered search agent** using LangGraph and Tavily API for smarter, more accurate responses. [Learn more →](docs/LANGGRAPH_INTEGRATION.md)

## Quick Start

```bash
pip install -r requirements.txt
streamlit run src/app.py
```

## Documentation

- [Full README](docs/README.md)
- [Architecture](docs/ARCHITECTURE.md)
- [LangGraph Integration Guide](docs/LANGGRAPH_INTEGRATION.md) 🆕
- [Security Policy](docs/security.md)
- [Improvements Summary](docs/IMPROVEMENTS_SUMMARY.md)

## Configuration

- Application config: `config/prompts.json`
- Dependencies: `requirements.txt`
- Database schema: `supabase/migrations/schema.sql`

### API Keys

Required:
- `GROQ_API_KEY` - For AI chat functionality

Optional:
- `TAVILY_API_KEY` - For intelligent web search with LangGraph (1,000 free searches/month)
- `SUPABASE_URL` + `SUPABASE_KEY` - For chat history persistence

Configure in `.streamlit/secrets.toml` or as environment variables.

### Quick Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Configure API keys (copy and edit)
cp .streamlit/secrets.toml.example .streamlit/secrets.toml

# Run the application
streamlit run src/app.py
```

### Enable Tavily Search

1. Get a free API key from [Tavily.com](https://tavily.com)
2. Add to `.streamlit/secrets.toml`:
   ```toml
   tavily_api_key = "tvly-your-key-here"
   ```
3. In the app sidebar, enable **🤖 智能搜尋模式 (LangGraph)**

See [TAVILY_QUICKSTART.md](docs/TAVILY_QUICKSTART.md) for details.

## License

See [LICENSE](docs/LICENSE)
