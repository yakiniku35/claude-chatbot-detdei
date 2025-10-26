# DEI Chatbot Flow Diagram

## User Interaction Flow

```
┌─────────────────────────────────────────────┐
│           User sends message                │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│     is_analysis_request() function          │
│     Checks for analysis keywords            │
└────────────┬──────────────┬─────────────────┘
             │              │
    Keywords │              │ No keywords
    detected │              │ found
             │              │
             ▼              ▼
┌───────────────────┐  ┌──────────────────────┐
│  ANALYSIS MODE    │  │  CASUAL MODE         │
│                   │  │                      │
│  System Prompt:   │  │  System Prompt:      │
│  - Professional   │  │  - Friendly          │
│  - Structured     │  │  - Conversational    │
│  - DEI focused    │  │  - Helpful           │
│                   │  │                      │
│  Response:        │  │  Response:           │
│  ✓ DEI Rating     │  │  ✗ No rating         │
│  ✓ Analysis       │  │  ✓ Natural chat      │
│  ✓ Suggestions    │  │  ✓ Info sharing      │
└─────────┬─────────┘  └──────────┬───────────┘
          │                       │
          └───────────┬───────────┘
                      │
                      ▼
          ┌───────────────────────┐
          │  Bot responds to user │
          └───────────────────────┘
```

## API Key Resolution Flow

```
┌─────────────────────────────────────────┐
│        Application Starts               │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│         init_groq() called              │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│   Check st.secrets['groq_api_key']      │
└──────┬──────────────────────┬───────────┘
       │ Found                │ Not found
       │                      │
       ▼                      ▼
┌─────────────┐    ┌────────────────────────┐
│  Use from   │    │ Check env variable     │
│  secrets    │    │ GROQ_API_KEY           │
└──────┬──────┘    └───────┬────────────────┘
       │                   │ Found  │ Not found
       │                   │        │
       │                   ▼        ▼
       │           ┌──────────┐  ┌──────────┐
       │           │ Use from │  │  Return  │
       │           │   env    │  │   None   │
       │           └────┬─────┘  └────┬─────┘
       │                │             │
       └────────┬───────┘             │
                │                     │
                ▼                     ▼
     ┌────────────────────┐  ┌──────────────┐
     │ Initialize Groq    │  │ Show error   │
     │ Client ✓           │  │ message ✗    │
     └────────────────────┘  └──────────────┘
```

## Conversation Mode Decision Tree

```
User message: "請檢查這段文字"
                │
                ▼
        Contains "檢查"?
                │
            YES │
                ▼
        Analysis Mode
                │
                ▼
Response: "DEI 遵守等級: 1
這段文字有輕微偏差..."


User message: "你好，DEI 是什麼？"
                │
                ▼
        Contains analysis keywords?
                │
            NO  │ (only "dei" in question)
                ▼
         Casual Mode
                │
                ▼
Response: "你好！😊 DEI 代表
Diversity（多元性）、
Equity（公平性）、
Inclusion（包容性）..."
```

## File Upload Flow

```
┌────────────────────────────┐
│   User uploads file        │
│   (PDF/DOCX/TXT)          │
└──────────┬─────────────────┘
           │
           ▼
┌────────────────────────────┐
│   read_file() extracts     │
│   text content             │
└──────────┬─────────────────┘
           │
           ▼
┌────────────────────────────┐
│   Add to messages with     │
│   "請檢查以下內容："       │
└──────────┬─────────────────┘
           │
           ▼
┌────────────────────────────┐
│   Triggers Analysis Mode   │
│   (contains "檢查")        │
└──────────┬─────────────────┘
           │
           ▼
┌────────────────────────────┐
│   Bot analyzes content     │
│   with DEI rating          │
└────────────────────────────┘
```

## System Architecture

```
┌──────────────────────────────────────────────────┐
│              Frontend (Streamlit)                │
│  ┌────────────────────────────────────────────┐ │
│  │  Chat Interface                            │ │
│  │  - Message display                         │ │
│  │  - Input box                               │ │
│  │  - File uploader                           │ │
│  └────────────────────────────────────────────┘ │
└───────────────────┬──────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────┐
│              Backend (app.py)                    │
│  ┌────────────────────────────────────────────┐ │
│  │  Intent Detection                          │ │
│  │  - is_analysis_request()                   │ │
│  │  - Keyword matching                        │ │
│  └────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────┐ │
│  │  Prompt Generation                         │ │
│  │  - Casual mode prompt                      │ │
│  │  - Analysis mode prompt                    │ │
│  │  - Policy context injection                │ │
│  └────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────┐ │
│  │  API Integration                           │ │
│  │  - Groq client (LLaMA 3.3 70B)            │ │
│  │  - DuckDuckGo search                       │ │
│  │  - Supabase (optional)                     │ │
│  └────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────┘
```

## Data Flow

```
┌─────────┐     ┌──────────┐     ┌─────────────┐     ┌──────────┐
│  User   │────▶│ Streamlit│────▶│ Intent      │────▶│ Prompt   │
│  Input  │     │ Frontend │     │ Detection   │     │ Builder  │
└─────────┘     └──────────┘     └─────────────┘     └────┬─────┘
                                                           │
                                                           ▼
┌─────────┐     ┌──────────┐     ┌─────────────┐     ┌──────────┐
│   Bot   │◀────│ Response │◀────│ Groq API    │◀────│  API     │
│ Display │     │ Format   │     │ (LLaMA)     │     │  Call    │
└─────────┘     └──────────┘     └─────────────┘     └──────────┘
```

## Configuration Sources Priority

```
API Key Resolution:
1. st.secrets['groq_api_key'] ────┐
                                   ├──▶ First match wins
2. os.environ['GROQ_API_KEY']  ────┘

Recommended Usage:
- Development: Use st.secrets
- Production: Use environment variable
- Docker: Set ENV variable
- Cloud: Use platform secrets manager
```
