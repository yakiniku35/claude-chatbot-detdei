# DEI Policy Chatbot

Streamlit-based chatbot for analyzing content against Diversity, Equity, and Inclusion (DEI) policies. Powered by Groq's LLaMA 3.3 70B with web search capabilities.

## Setup

```bash
pip install -r requirements.txt
```

Create `.streamlit/secrets.toml`:
```toml
groq_api_key = "your_key_here"
```

## Run

```bash
streamlit run app.py
```

## Features

- **Policy Analysis**: Check text/files for DEI violations
- **Web Search**: Auto-searches latest DEI info when needed
- **File Support**: PDF, DOCX, TXT
- **Custom Policies**: Add organization-specific rules
- **Conversation History**: Full chat context maintained

## Architecture

Single-file Streamlit app (`app.py`):
- `init_groq()`: Client initialization with API key from secrets/session
- `read_file()`: Extract text from uploaded documents
- `search_web()`: DuckDuckGo integration for current information
- `should_search()`: Keyword detection for search triggers
- `chat_with_ai()`: Main AI interaction with context injection
- `main()`: UI layout and conversation loop

## Development

DevContainer configured for GitHub Codespaces with Python 3.11. Auto-installs dependencies and runs on port 8501.
