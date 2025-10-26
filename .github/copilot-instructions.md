# Copilot Instructions for DEI Policy Chatbot

## Repository Overview

This is a Streamlit-based chatbot application for analyzing content against Diversity, Equity, and Inclusion (DEI) policies. The application uses Groq's LLaMA 3.3 70B model with web search capabilities to provide policy analysis and recommendations.

## Project Structure

```
claude-chatbot-detdei/
├── app.py                 # Main Streamlit application (single-file architecture)
├── prompts.json           # Policy configuration and executive orders
├── requirements.txt       # Python dependencies
├── README.md              # Project documentation
├── security.md            # Security policy
├── .devcontainer/         # GitHub Codespaces configuration
│   └── devcontainer.json
└── .streamlit/
    └── secrets.toml       # API keys (not in version control)
```

## Core Functionality

The application is structured as a single-file Streamlit app with these key functions:

- `load_prompts()`: Loads policy definitions from `prompts.json` (cached)
- `init_groq()`: Initializes Groq API client using secrets or environment variables
- `is_analysis_request()`: Detects if user wants analysis or casual conversation
- `read_file()`: Extracts text from uploaded documents (PDF, DOCX, TXT)
- `search_web()`: DuckDuckGo integration for current information
- `should_search()`: Detects keywords that trigger web search
- `chat()`: Main AI interaction with context-aware prompts (two modes: casual vs. analysis)

## Development Setup

### Prerequisites
- Python 3.11+
- Groq API key

### Installation
```bash
pip install -r requirements.txt
```

### Configuration
Option 1 - Streamlit Secrets (recommended for local):
Create `.streamlit/secrets.toml`:
```toml
groq_api_key = "your_key_here"
```

Option 2 - Environment Variable (recommended for deployment):
```bash
export GROQ_API_KEY="your_key_here"
```

### Running the Application
```bash
streamlit run app.py
```
The app runs on port 8501.

## Coding Standards

### Language
- Primary language: Python 3.11+
- UI text: Traditional Chinese (繁體中文)
- Comments: Mixed Chinese/English acceptable

### Python Style
- Follow PEP 8 conventions
- Use type hints where appropriate
- Keep functions focused and single-purpose
- Use descriptive variable names (both Chinese and English are used)

### Streamlit Patterns
- Use `st.cache_data` for expensive operations (e.g., loading prompts)
- Store application state in `st.session_state`
- Use `st.rerun()` to refresh the UI after state changes
- Handle file uploads with unique identifiers to prevent reprocessing

### Error Handling
- Gracefully handle API errors with user-friendly messages
- Provide specific error messages for common issues:
  - Authentication failures
  - Rate limiting
  - Connection problems
- Always use try-except blocks for external API calls and file operations

## Dependencies

### Core Dependencies
- `streamlit>=1.24.0` - Web application framework
- `groq>=0.1.0` - LLM API client
- `PyPDF2>=3.0.0` - PDF text extraction
- `python-docx>=0.8.11` - Word document processing
- `duckduckgo_search>=2.5.0` - Web search functionality

### AI Model
- Model: `openai/gpt-oss-120b` (via Groq)
- Temperature: 0.7
- Max tokens: 2500

## Policy Configuration

The `prompts.json` file contains:
- `executive_orders`: List of policy references with title and description
- `document`: Policy details including:
  - Individual policies with titles, summaries, and actions
  - Administration information (president, term, focus areas)

When modifying policy configurations:
- Maintain the JSON structure
- Ensure all required fields are present
- Test policy rendering in the chat interface

## Testing Approach

Currently, there is no automated test infrastructure. Manual testing should focus on:

1. **File Upload Testing**
   - Test PDF, DOCX, and TXT files
   - Verify content extraction accuracy
   - Test file size limits (10,000 character truncation)

2. **Chat Functionality**
   - Verify policy context injection
   - Test web search triggering with keywords
   - Validate DEI compliance scoring (0-5 scale)

3. **Session Management**
   - Test conversation history preservation
   - Verify file processing deduplication
   - Test clear conversation functionality

4. **Error Handling**
   - Test with invalid API keys
   - Test network failure scenarios
   - Test unsupported file types

## DevContainer Configuration

The repository includes a DevContainer configuration for GitHub Codespaces:
- Base image: Python 3.11
- Auto-installs dependencies on container creation
- Port 8501 forwarded for Streamlit

## Security Considerations

- Never commit API keys or secrets to version control
- API keys are stored in `.streamlit/secrets.toml` (gitignored)
- File uploads are limited to specific types (PDF, DOCX, TXT)
- Content is truncated to prevent excessive token usage
- No user data is persisted between sessions

## Common Patterns

### Adding a New File Type
1. Add MIME type to `st.file_uploader` type list
2. Add extraction logic to `read_file()` function
3. Handle exceptions gracefully

### Modifying the System Prompt
- System prompt is in the `chat()` function
- Includes DEI compliance scale (0-5)
- Dynamically incorporates policies from `prompts.json`
- Search context is appended when available

### Adding New Search Triggers
- Modify the `keywords` list in `should_search()` function
- Keywords are matched case-insensitively

## Best Practices

1. **Minimal Changes**: Make surgical modifications to existing code
2. **Preserve Functionality**: Don't break existing features when adding new ones
3. **User Experience**: Maintain the friendly, professional tone in Chinese
4. **Performance**: Use caching (`@st.cache_data`) for expensive operations
5. **State Management**: Always use `st.session_state` for cross-rerun persistence
6. **Documentation**: Update README.md when adding significant features

## Known Limitations

- No automated testing framework
- Single-file architecture (intentional for simplicity)
- No database persistence (session-based only)
- Limited to Groq API (no fallback providers)
- Web search limited to top 3 results
- File content truncated to 10,000 characters

## Contributing Guidelines

When making changes:
1. Test the application locally with `streamlit run app.py`
2. Verify all existing functionality still works
3. Update documentation if adding new features
4. Follow the existing code style and patterns
5. Ensure error handling is comprehensive
