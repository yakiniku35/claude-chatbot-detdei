# DEI Policy Chatbot

Streamlit-based chatbot for analyzing content against Diversity, Equity, and Inclusion (DEI) policies. Powered by Groq's LLaMA 3.3 70B with web search capabilities.

## Setup

```bash
pip install -r requirements.txt
```

### API Key Configuration

The bot requires a Groq API key. You can provide it in two ways:

**Option 1: Streamlit Secrets (Recommended for local development)**
Create `.streamlit/secrets.toml`:
```toml
groq_api_key = "your_key_here"
```

**Option 2: Environment Variable (Recommended for deployment)**
```bash
export GROQ_API_KEY="your_key_here"
streamlit run app.py
```

**Security Note**: The API key is never exposed to end users. It's used server-side only to make API calls to Groq.

## Run

```bash
streamlit run app.py
```

## Features

- **Intelligent Conversation**: Bot distinguishes between casual chat and analysis requests
- **Policy Analysis**: Check text/files for DEI violations with 0-5 rating scale
- **Web Search**: Auto-searches latest DEI info when needed
- **File Support**: PDF, DOCX, TXT
- **Custom Policies**: Add organization-specific rules via `prompts.json`
- **Conversation History**: Full chat context maintained
- **Supabase Integration**: Optional persistent chat history storage (see [SUPABASE_SETUP.md](SUPABASE_SETUP.md))

### Two Interaction Modes

The bot automatically adapts its behavior:
- **Casual Mode**: Friendly conversations, answers questions, no automatic DEI rating
- **Analysis Mode**: Professional DEI policy checking when you use keywords like "檢查", "分析", "check", "analyze"

## Architecture

Single-file Streamlit app (`app.py`):
- `init_groq()`: Client initialization with API key from secrets or environment
- `is_analysis_request()`: Intent detection to distinguish conversation from analysis
- `read_file()`: Extract text from uploaded documents
- `search_web()`: DuckDuckGo integration for current information
- `should_search()`: Keyword detection for search triggers
- `chat()`: Main AI interaction with context-aware prompts
- Main section: UI layout and conversation loop

## Development

DevContainer configured for GitHub Codespaces with Python 3.11+. Auto-installs dependencies and runs on port 8501.
