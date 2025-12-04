# LangGraph Integration Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     DEI Chatbot Application                      │
│                        (Streamlit UI)                            │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │   Mode Selection     │
              │  (Sidebar Toggle)    │
              └──────────┬───────────┘
                         │
          ┌──────────────┴──────────────┐
          ▼                             ▼
┌─────────────────────┐       ┌─────────────────────┐
│  Traditional Mode   │       │    Agent Mode       │
│   (Groq Direct)     │       │   (LangGraph)       │
└─────────┬───────────┘       └─────────┬───────────┘
          │                             │
          ▼                             ▼
┌─────────────────────┐       ┌─────────────────────┐
│ Keyword Detection   │       │  LangGraph Agent    │
│  (Rule-based)       │       │  (AI Decision)      │
└─────────┬───────────┘       └─────────┬───────────┘
          │                             │
          ▼                             ▼
┌─────────────────────┐       ┌─────────────────────┐
│  DuckDuckGo Search  │       │  Tavily Search API  │
│  (max_results=3)    │       │  (max_results=4)    │
└─────────┬───────────┘       └─────────┬───────────┘
          │                             │
          └──────────────┬──────────────┘
                         ▼
              ┌──────────────────────┐
              │    Groq LLM API      │
              │  (LLaMA 3.3 70B)     │
              └──────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │   Final Response     │
              │  (Markdown + Badge)  │
              └──────────────────────┘
```

## Agent Decision Flow

```
User Message
     │
     ▼
┌──────────────────────┐
│  LangGraph Agent     │
│  (State: messages)   │
└─────────┬────────────┘
          │
          ▼
┌──────────────────────────────────────────┐
│         Agent Model Node                 │
│  ┌────────────────────────────────────┐  │
│  │ LLM with Tools (Groq LLaMA 3.3)   │  │
│  │ - Analyzes user query             │  │
│  │ - Decides: search or answer?      │  │
│  │ - Generates tool_calls if needed  │  │
│  └────────────────────────────────────┘  │
└─────────┬────────────────────────────────┘
          │
          ▼
┌──────────────────────┐
│  Tools Router        │
│  (Conditional Edge)  │
└─────────┬────────────┘
          │
     Has tool_calls?
          │
    ┌─────┴─────┐
    │           │
   Yes         No
    │           │
    ▼           ▼
┌─────────┐  ┌─────┐
│  Tools  │  │ END │
│  Node   │  └─────┘
└────┬────┘
     │
     ▼
┌──────────────────────┐
│  Execute Tavily      │
│  Search Tool         │
│  - Send query        │
│  - Get 4 results     │
│  - Format as         │
│    ToolMessage       │
└─────────┬────────────┘
          │
          ▼
┌──────────────────────┐
│  Back to Model Node  │
│  - Process results   │
│  - Generate answer   │
└─────────┬────────────┘
          │
          ▼
        ┌─────┐
        │ END │
        └─────┘
```

## State Management

```
┌─────────────────────────────────────────┐
│         AgentState (TypedDict)          │
├─────────────────────────────────────────┤
│  messages: Annotated[list, add_messages]│
│                                         │
│  Contains:                              │
│  - HumanMessage                         │
│  - AIMessage                            │
│  - ToolMessage                          │
│  - System prompts                       │
└─────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│         MemorySaver Checkpoint          │
├─────────────────────────────────────────┤
│  Thread ID: session_id (UUID)           │
│  Stores: Full conversation history      │
│  Enables: Context across messages       │
└─────────────────────────────────────────┘
```

## Message Flow

```
Streamlit Message Format:
{
  "role": "user" | "assistant" | "system",
  "content": "message text"
}
        │
        ▼ (Conversion)
LangChain Message Format:
HumanMessage(content="message text")
AIMessage(content="response text")
ToolMessage(content="tool result", tool_call_id="...")
        │
        ▼ (Agent Processing)
Agent Output:
{
  "messages": [
    AIMessage(content="final response")
  ]
}
        │
        ▼ (Extraction)
Final Response String → Streamlit Display
```

## Component Dependencies

```
┌─────────────────────────────────────────────────────────┐
│                    src/app.py                            │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Required:                                               │
│  ├─ streamlit         (UI framework)                     │
│  ├─ groq              (Direct API client)                │
│  ├─ PyPDF2            (File processing)                  │
│  └─ python-docx       (File processing)                  │
│                                                          │
│  Optional (Agent Mode):                                  │
│  ├─ langchain         (Core framework)                   │
│  ├─ langchain-groq    (Groq integration)                 │
│  ├─ langgraph         (Agent orchestration)              │
│  ├─ langgraph-checkpoint (State management)              │
│  └─ langchain-tavily  (Search API)                       │
│                                                          │
│  Optional (Fallback):                                    │
│  └─ duckduckgo_search (Traditional search)               │
│                                                          │
│  Optional (Storage):                                     │
│  └─ supabase          (Chat history)                     │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## API Key Flow

```
Configuration Sources (Priority Order):
1. .streamlit/secrets.toml
2. Environment Variables
3. None (fallback/disable)

┌──────────────────────┐
│  GROQ_API_KEY        │ ──┐
│  (Required)          │   │
└──────────────────────┘   │
                           ▼
┌──────────────────────┐ ┌─────────────────────┐
│  TAVILY_API_KEY      │ │  Application Init   │
│  (Optional)          │→│  - init_groq()      │
└──────────────────────┘ │  - init_langchain() │
                         │  - init_tavily()    │
┌──────────────────────┐ └─────────────────────┘
│  SUPABASE_URL/KEY    │   │
│  (Optional)          │ ──┘
└──────────────────────┘
```

## Error Handling

```
User Request
     │
     ▼
Try: LangGraph Agent
     │
     ├─ Success → Return Response
     │
     └─ Exception
           │
           ├─ LangChain Not Installed
           │    └─> Hide Agent Toggle
           │
           ├─ Tavily Key Missing
           │    └─> Show Warning, Continue
           │
           ├─ Agent Execution Error
           │    └─> Show Error, Fallback
           │
           └─ Network/API Error
                └─> User-Friendly Message
                    "抱歉，發生錯誤"
```

## Performance Considerations

```
Traditional Mode:
├─ API Calls: 1 (Groq)
├─ Latency: 2-3 seconds
└─ Cost: Low (Groq only)

Agent Mode:
├─ API Calls: 1-2 (Groq + maybe Tavily)
├─ Latency: 5-10 seconds
├─ Cost: Medium (Groq + Tavily)
└─ Quality: Higher (intelligent decisions)

Optimization Strategies:
├─ Cache agent graph (@st.cache_resource)
├─ Reuse conversation threads (thread_id)
├─ Fallback to traditional for simple queries
└─ Future: Cache search results
```

## Data Flow Example

```
Example: "What are the latest DEI trends in 2025?"

1. User Input
   │
   ▼
2. Streamlit Session State
   messages.append({"role": "user", "content": "..."})
   │
   ▼
3. Agent Mode Detection
   use_agent = True (enabled + available)
   │
   ▼
4. System Prompt Generation
   language = "zh-TW"
   analysis = False (not requesting analysis)
   prompts = load_prompts() [CACHED]
   │
   ▼
5. LangGraph Agent Execution
   config = {"thread_id": session_id}
   │
   ├─> Model Node
   │    LLM: "This query needs current data"
   │    tool_calls: [{"name": "tavily_search", "args": {...}}]
   │
   ├─> Router: "tool_node"
   │
   ├─> Tool Node
   │    Tavily API: Search "DEI trends 2025"
   │    Results: [4 recent articles]
   │
   ├─> Model Node (again)
   │    LLM: Process results + DEI policies
   │    Output: Comprehensive answer
   │
   └─> END
   │
   ▼
6. Response Enhancement
   response += "\n\n🌐 *此回覆使用智能搜尋*"
   │
   ▼
7. Save to Session State
   messages.append({"role": "assistant", "content": response})
   │
   ▼
8. Optional: Save to Supabase
   if supabase_enabled: save_message_to_supabase(...)
   │
   ▼
9. Display in Streamlit
   st.markdown(response)
   st.rerun()
```

## Testing Architecture

```
test_langgraph.py
├─ Test 1: Package Imports
│  └─ Verify all LangChain packages available
│
├─ Test 2: Agent Graph Structure
│  ├─ Create StateGraph
│  ├─ Add nodes (model, tool_node)
│  ├─ Add edges (conditional routing)
│  └─ Compile with MemorySaver
│
└─ Test 3: App.py Syntax
   └─ Parse with ast.parse()

All tests pass without requiring:
- API keys
- Network access
- Streamlit runtime
```

## Deployment Checklist

```
□ Install dependencies
  pip install -r requirements.txt

□ Configure API keys
  .streamlit/secrets.toml or environment variables

□ Run tests
  python test_langgraph.py

□ Start application
  streamlit run src/app.py

□ Verify UI elements
  - ✅ 系統就緒
  - 🤖 智能搜尋模式 (if LangChain available)
  - ✨ Tavily 搜尋已啟用 (if Tavily configured)

□ Test both modes
  - Traditional: Ask simple question, verify response
  - Agent: Ask about "latest 2025 DEI trends", verify search

□ Monitor performance
  - Traditional: ~2-3s
  - Agent: ~5-10s
```
