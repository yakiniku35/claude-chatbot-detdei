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
- [Testing & Quality Assurance](docs/TESTING.md) 🆕
- [Security Policy](docs/security.md)
- [Improvements Summary](docs/IMPROVEMENTS_SUMMARY.md)

## Configuration

- Application config: `config/prompts.json`
- Dependencies: `requirements.txt`
- Database schema: `supabase/migrations/schema.sql`

### API Keys

Required:
- `GROQ_API_KEY` - For AI chat functionality

Optional (for enhanced search):
- `TAVILY_API_KEY` - For intelligent web search with LangGraph

Configure in `.streamlit/secrets.toml` or as environment variables.

## License

See [LICENSE](docs/LICENSE)
