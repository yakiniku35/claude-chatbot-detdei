import streamlit as st
from groq import Groq
import PyPDF2
import docx
import io
import json
import os
from typing import TypedDict, Annotated, Literal
from datetime import datetime
import uuid

# LangChain imports
try:
    from langchain_groq import ChatGroq
    from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
    from langgraph.graph import StateGraph, END, add_messages
    from langgraph.checkpoint.memory import MemorySaver
    from langchain_tavily import TavilySearch
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

# Fallback to DuckDuckGo if Tavily not available
try:
    from duckduckgo_search import DDGS
    DDGS_AVAILABLE = True
except ImportError:
    DDGS_AVAILABLE = False

# Supabase is optional
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except Exception:
    create_client = None
    Client = None
    SUPABASE_AVAILABLE = False

# 讀取 prompts.json
@st.cache_data
def load_prompts():
    try:
        with open('config/prompts.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"executive_orders": []}


DEFAULT_ASSISTANT_MESSAGE = """👋 你好！我是 DEI 政策助手。

我可以幫你：
• 💬 回答 DEI 政策與情境問題
• 📋 判斷某段內容或情境是否可能違反 DEI 政策
• ❓ 在資訊不足時先幫你釐清重點
• 💡 提供改善建議與下一步

你可以直接貼一段對話、政策、招募條件、公告或真實情境，我會幫你判斷是否有 DEI 風險。

---

👋 Hello! I'm the DEI Policy Assistant.

I can help you:
• 💬 Answer DEI policy and scenario questions
• 📋 Assess whether content or a situation may conflict with DEI policy
• ❓ Ask clarifying questions when key facts are missing
• 💡 Suggest safer wording and practical next steps

You can paste a message, policy, hiring requirement, announcement, or workplace scenario, and I will help assess the DEI risk."""


def get_policy_reference_text(prompts_data):
    """Build a readable policy reference block from prompts.json."""
    parts = []

    executive_orders = prompts_data.get('executive_orders') or []
    if executive_orders:
        parts.append("📋 Policy References:")
        for order in executive_orders:
            title = order.get('title', '')
            description = order.get('description', '')
            purpose = order.get('purpose', '')
            actions = order.get('actions', [])

            parts.append(f"- {title}: {description}")
            if purpose:
                parts.append(f"  Purpose: {purpose}")
            if actions:
                action_text = "; ".join(actions[:3])
                if len(actions) > 3:
                    action_text += "..."
                parts.append(f"  Key actions: {action_text}")

    document = prompts_data.get('document')
    if isinstance(document, list) and document:
        document = document[0]

    if isinstance(document, dict):
        policies = document.get('policies') or document.get('policy') or {}
        if isinstance(policies, dict) and policies:
            parts.append("\n📚 Policy Summary:")
            for key, policy in policies.items():
                title = policy.get('title') or key
                summary = policy.get('summary', '')
                parts.append(f"- {title}: {summary}")

                actions = policy.get('actions', [])
                if actions:
                    action_text = "; ".join(actions[:3])
                    if len(actions) > 3:
                        action_text += "..."
                    parts.append(f"  Expected actions: {action_text}")

        administration = document.get('administration')
        if isinstance(administration, dict):
            president = administration.get('president')
            term = administration.get('term')
            focus = administration.get('policy_focus', [])

            admin_bits = []
            if president:
                admin_bits.append(f"leader={president}")
            if term:
                admin_bits.append(f"term={term}")
            if focus:
                admin_bits.append(f"focus={', '.join(focus)}")

            if admin_bits:
                parts.append("\n🏛️ Administration Context:")
                parts.append(f"- {'; '.join(admin_bits)}")

    return "\n".join(parts).strip()


def get_mode_specific_instruction(is_scenario_review):
    if is_scenario_review:
        return """# Current Response Mode
The user's latest message most likely asks for a DEI scenario review.

Use this structure:
- Scenario Summary:
- Score Breakdown:
    - Policy Signal Strength (0-40):
    - Impact Severity (0-30):
    - Pattern/Systemic Risk (0-30):
- Violation Score: [0-100]
- Initial Assessment: Likely DEI policy concern | Possible DEI concern | Low concern | Insufficient information
- Confidence: High | Medium | Low
- Relevant Policy Signals:
- Explanation:
- Recommended Next Step:
- Clarifying Questions: only include this section when the missing facts materially change the assessment

Score rubric (higher means more likely DEI policy violation):
- 0-20: Low concern
- 21-50: Possible concern
- 51-80: Likely concern
- 81-100: Severe concern and should be escalated for human review

Scoring method:
- Violation Score = Policy Signal Strength + Impact Severity + Pattern/Systemic Risk
- Do not output a total score that doesn't match the component sum.
- If key facts are missing, cap the total score at 40 unless explicit severe harm is clearly stated.
- Use ranges conservatively. Do not jump to high scores from a single weak signal.

When the facts are incomplete, do not guess. Ask up to three concise clarifying questions before making a strong conclusion."""

    return """# Current Response Mode
The user's latest message appears to be general guidance or conversation.

Answer naturally, but include a line `Violation Score: X/100` in your response.
For pure greetings or non-assessment chat, use a low score (typically 0-10) and briefly note that no concrete scenario was provided.
If the user includes a concrete scenario, policy text, hiring practice, workplace interaction, or asks whether something is acceptable, switch into the scenario review structure automatically."""


def build_system_prompt(user_text, include_tool_guidance=False):
    """Build a layered DEI system prompt inspired by sectioned prompt architecture."""
    prompts_data = load_prompts()
    policy_reference_text = get_policy_reference_text(prompts_data)
    user_language = detect_language(user_text)
    language_instruction = get_language_instruction(user_language)
    scenario_review = is_analysis_request(user_text)

    tool_guidance = ""
    if include_tool_guidance:
        tool_guidance = """
# Tool Guidance
You may use the tavily_search tool when the user asks for recent developments, statistics, case law, current events, or information that is likely to have changed over time.
Do not search the web for every DEI scenario. Prefer reasoning from the provided policy references unless current information would materially improve the answer.
Be conservative with search usage to avoid unnecessary cost and noise."""

    response_quality = """# Output Format
- Keep the answer concise and specific.
- For scenario reviews, prefer short labeled sections over long paragraphs.
- For general questions, keep the response within about 6 sentences when possible.
- Avoid copying long policy excerpts verbatim.
- Always include `Violation Score: X/100`.
- Interpret the score consistently: higher score means the situation is more likely to violate DEI policy expectations."""

    scoring_framework = """# Scoring Framework (Precision Mode)
Use the weighted scoring model below for scenario assessments:
1. Policy Signal Strength (0-40):
    - Direct discriminatory/exclusionary language, explicit unequal treatment, or denial of accommodation tied to protected attributes.
2. Impact Severity (0-30):
    - Practical harm level: hiring/promotion/pay impact, harassment pressure, access barriers, retaliation exposure.
3. Pattern/Systemic Risk (0-30):
    - Repetition, manager/organizational involvement, policy-level bias, or indications this is not an isolated event.

Calibration rules:
- Use increments of 5 for component scores unless evidence is very specific.
- Keep confidence aligned with evidence quality (Low confidence should usually avoid extreme totals).
- If evidence conflicts, explain uncertainty and reduce the total accordingly.
- Do not treat a sensitive topic mention alone as a high-risk violation signal.
"""

    return f"""You are a DEI policy assistant focused on helping the user determine whether a described situation, statement, hiring decision, workplace interaction, or document may conflict with DEI policy expectations.

{language_instruction}

# Identity
- Be professional, calm, and direct.
- Your primary job is to identify whether the user's scenario raises a DEI policy concern and explain why.
- Help the user understand the practical policy risk, not just generate a generic DEI score.

# Boundaries
- Do not present yourself as HR, a formal investigator, or legal counsel.
- Do not claim a definitive legal violation or official company finding.
- Do not invent facts, motives, or protected characteristics that the user did not provide.
- Do not ask for unnecessary personal identifiers or highly sensitive details.
- If key facts are missing, say so clearly and ask concise clarifying questions.

# Review Method
For scenarios, policies, messages, job descriptions, documents, or workplace practices:
1. Briefly summarize what happened or what was written.
2. Decide whether the information suggests a likely DEI policy concern, a possible concern, no clear concern, or insufficient information.
3. Explain which policy principles, patterns, or references are relevant.
4. Separate what is explicitly stated from what is only an assumption.
5. Offer a practical next step such as revising wording, gathering facts, or escalating to an appropriate human reviewer.

# Escalation and Care
- If the scenario suggests discrimination, harassment, exclusion, inaccessible accommodation handling, retaliation, or repeated stereotyping, say that it likely needs human review.
- If the issue is ambiguous but high-risk, prefer careful wording such as "possible concern" rather than a hard conclusion.
- If there is not enough information, ask for the facts that would change the outcome instead of pretending certainty.

# Response Quality
- Report your assessment faithfully. Do not overstate certainty.
- Keep the explanation concise but specific.
- When the answer is not a scenario review, do not force a violation label.

{response_quality}
{scoring_framework}
{get_mode_specific_instruction(scenario_review)}
{tool_guidance}

# Policy References
{policy_reference_text or 'No policy references are currently configured.'}
"""

# 設定頁面
st.set_page_config(
    page_title="DEI 聊天機器人",
    page_icon="🤖",
    layout="centered"
)

# 初始化 session state
if 'messages' not in st.session_state:
    st.session_state.messages = [{
        "role": "assistant",
        "content": DEFAULT_ASSISTANT_MESSAGE
    }]

if 'file_processed' not in st.session_state:
    st.session_state.file_processed = set()

if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if 'supabase_enabled' not in st.session_state:
    st.session_state.supabase_enabled = False

# 初始化 Groq
def init_groq():
    # Support both Streamlit secrets and environment variables
    api_key = None
    try:
        if 'groq_api_key' in st.secrets:
            api_key = st.secrets['groq_api_key']
    except:
        pass
    
    if not api_key and 'GROQ_API_KEY' in os.environ:
        api_key = os.environ.get('GROQ_API_KEY')
    
    if api_key:
        return Groq(api_key=api_key)
    return None

# 初始化 LangChain Groq (with fallback models)
def init_langchain_groq():
    if not LANGCHAIN_AVAILABLE:
        return None
    api_key = None
    try:
        if 'groq_api_key' in st.secrets:
            api_key = st.secrets['groq_api_key']
    except:
        pass
    
    if not api_key and 'GROQ_API_KEY' in os.environ:
        api_key = os.environ.get('GROQ_API_KEY')
    
    if not api_key:
        return None
    
    # 模型列表：按優先順序排列，如果達到上限會自動切換
    models = [
        "openai/gpt-oss-120b",
        "llama-3.3-70b-versatile",      # 最強大的模型
        "llama-3.1-70b-versatile",      # 備用大模型
        "llama-3.2-90b-text-preview",   # 預覽大模型
        "llama-3.1-8b-instant",         # 快速輕量模型
        "mixtral-8x7b-32768",           # Mixtral 模型
        "gemma2-9b-it",                 # Google Gemma 模型
        "llama3-70b-8192"               # 舊版 LLaMA 模型
    ]
    
    # 如果已經有失敗的模型記錄，從列表中移除
    if 'failed_models' not in st.session_state:
        st.session_state.failed_models = set()
    
    # 過濾掉已知失敗的模型
    available_models = [m for m in models if m not in st.session_state.failed_models]
    
    if not available_models:
        st.error("所有模型都已達到上限，請稍後再試或升級您的 Groq 方案")
        return None
    
    # 使用第一個可用的模型
    selected_model = available_models[0]
    st.session_state.current_model = selected_model
    
    return ChatGroq(
        model=selected_model,
        api_key=api_key,
        temperature=0.7
    )

# 當模型失敗時，切換到下一個模型
def switch_to_next_model():
    if 'current_model' in st.session_state:
        st.session_state.failed_models.add(st.session_state.current_model)
        st.warning(f"模型 {st.session_state.current_model} 達到上限，正在切換到備用模型...")
    
    # 重新初始化
    new_llm = init_langchain_groq()
    if new_llm:
        st.success(f"已切換到模型：{st.session_state.current_model}")
        st.rerun()
    return new_llm

# 初始化 Tavily
def init_tavily():
    if not LANGCHAIN_AVAILABLE:
        return None
    api_key = None
    try:
        if 'tavily_api_key' in st.secrets:
            api_key = st.secrets['tavily_api_key']
    except:
        pass
    
    if not api_key and 'TAVILY_API_KEY' in os.environ:
        api_key = os.environ.get('TAVILY_API_KEY')
    
    if api_key:
        os.environ['TAVILY_API_KEY'] = api_key
        # 使用官方 TavilySearch 工具，支援所有官方參數
        return TavilySearch(max_results=4)
    return None

# 初始化 Supabase
@st.cache_resource
def init_supabase():
    if not SUPABASE_AVAILABLE:
        return None
    try:
        has_supabase_secrets = False
        try:
            has_supabase_secrets = 'supabase_url' in st.secrets and 'supabase_key' in st.secrets
        except:
            pass
        
        if has_supabase_secrets:
            return create_client(st.secrets['supabase_url'], st.secrets['supabase_key'])
    except Exception as e:
        st.error(f"Supabase 初始化失敗: {str(e)}")
    return None

# 儲存訊息到 Supabase
def save_message_to_supabase(supabase, session_id: str, role: str, content: str):
    try:
        if not supabase:
            return False
        data = {
            "session_id": session_id,
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        }
        supabase.table("chat_history").insert(data).execute()
        return True
    except Exception as e:
        st.error(f"儲存訊息失敗: {str(e)}")
        return False

# 從 Supabase 載入聊天記錄
def load_chat_history(supabase, session_id: str):
    try:
        if not supabase:
            return None
        response = supabase.table("chat_history").select("*").eq("session_id", session_id).order("timestamp").execute()
        if response.data:
            return [{"role": msg["role"], "content": msg["content"]} for msg in response.data]
    except Exception as e:
        st.error(f"載入聊天記錄失敗: {str(e)}")
    return None

# 刪除聊天記錄
def delete_chat_history(supabase, session_id: str):
    try:
        if not supabase:
            return False
        supabase.table("chat_history").delete().eq("session_id", session_id).execute()
        return True
    except Exception as e:
        st.error(f"刪除聊天記錄失敗: {str(e)}")
        return False

# 儲存訊息的輔助函數
def add_and_save_message(role, content):
    st.session_state.messages.append({"role": role, "content": content})
    if st.session_state.supabase_enabled and supabase_client:
        save_message_to_supabase(
            supabase_client,
            st.session_state.session_id,
            role,
            content
        )

# 讀取檔案
def read_file(file):
    try:
        file_bytes = file.read()
        if file.type == "application/pdf":
            pdf = PyPDF2.PdfReader(io.BytesIO(file_bytes))
            return "\n".join([p.extract_text() for p in pdf.pages])
        elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = docx.Document(io.BytesIO(file_bytes))
            return "\n".join([p.text for p in doc.paragraphs])
        elif file.type == "text/plain":
            return file_bytes.decode("utf-8")
        else:
            raise ValueError(f"不支援的檔案類型: {file.type}")
    except Exception as e:
        st.error(f"讀取檔案失敗: {str(e)}")
        return None

# 網路搜尋 (DuckDuckGo fallback)
def search_web(query):
    if not DDGS_AVAILABLE:
        return []
    try:
        with DDGS() as ddgs:
            return list(ddgs.text(query, max_results=3))
    except Exception as e:
        st.warning(f"網路搜尋失敗: {str(e)}")
        return []

# LangGraph Agent State
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

# Agent 節點：模型決策
async def agent_model(state: AgentState, llm, tools):
    """LLM 決定是否需要使用工具"""
    llm_with_tools = llm.bind_tools(tools=tools) if tools else llm
    result = await llm_with_tools.ainvoke(state["messages"])
    return {"messages": [result]}

# Agent 節點：工具執行
async def tool_node(state: AgentState, search_tool):
    """執行搜尋工具"""
    tool_calls = state["messages"][-1].tool_calls if hasattr(state["messages"][-1], "tool_calls") else []
    tool_messages = []
    
    for tool_call in tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]
        tool_id = tool_call["id"]
        
        # LangChain TavilySearch 的工具名稱是 "tavily_search"
        if tool_name == "tavily_search":
            try:
                # 使用 ainvoke 進行異步調用，傳遞所有參數
                search_results = await search_tool.ainvoke(tool_args)
                tool_message = ToolMessage(
                    content=str(search_results),
                    tool_call_id=tool_id,
                    name=tool_name
                )
                tool_messages.append(tool_message)
            except Exception as e:
                error_msg = f"搜尋失敗: {str(e)}"
                tool_message = ToolMessage(
                    content=error_msg,
                    tool_call_id=tool_id,
                    name=tool_name
                )
                tool_messages.append(tool_message)
    
    return {"messages": tool_messages}

# Agent 路由：決定下一步
def tools_router(state: AgentState) -> Literal["tool_node", "__end__"]:
    """決定是否需要使用工具"""
    last_message = state["messages"][-1]
    
    if hasattr(last_message, "tool_calls") and len(last_message.tool_calls) > 0:
        return "tool_node"
    else:
        return END

# 建立 LangGraph Agent
@st.cache_resource
def create_agent_graph(_llm, _search_tool):
    """建立並編譯 agent graph"""
    memory = MemorySaver()
    graph_builder = StateGraph(AgentState)
    
    # 建立節點的 lambda 包裝器
    async def model_wrapper(state):
        return await agent_model(state, _llm, [_search_tool] if _search_tool else [])
    
    async def tool_wrapper(state):
        return await tool_node(state, _search_tool)
    
    graph_builder.add_node("model", model_wrapper)
    graph_builder.add_node("tool_node", tool_wrapper)
    graph_builder.set_entry_point("model")
    graph_builder.add_conditional_edges("model", tools_router)
    graph_builder.add_edge("tool_node", "model")
    
    return graph_builder.compile(checkpointer=memory)

def should_search(text):
    """
    判斷是否應該進行網路搜尋
    更嚴格的判斷標準，避免過度使用搜尋
    """
    # 明確的搜尋意圖關鍵字
    explicit_search_keywords = [
        # 中文
        "搜尋", "查詢", "找一下", "幫我找", "search", "find",
        # 英文
        "search for", "find me", "look up", "look for"
    ]
    
    # 時效性關鍵字（需要最新資訊）
    time_sensitive_keywords = [
        # 中文
        "最新", "近期", "現在", "當前", "目前", "今年", "本月","今天","最近"
        # 英文  
        "latest", "recent", "current", "now", "today", "this year", "2024", "2025"
    ]
    
    # 資料查詢關鍵字
    data_keywords = [
        # 中文
        "統計", "數據", "報告", "研究", "案例", "新聞","數量",
        # 英文
        "statistics", "data", "report", "research", "study", "case", "news"
    ]
    
    text_lower = text.lower()
    
    # 明確搜尋意圖
    if any(keyword in text_lower for keyword in explicit_search_keywords):
        return True
    
    # 時效性查詢 + 資料查詢
    has_time_sensitive = any(keyword in text_lower for keyword in time_sensitive_keywords)
    has_data_request = any(keyword in text_lower for keyword in data_keywords)
    
    # 兩者都有才觸發搜尋
    if has_time_sensitive and has_data_request:
        return True
    
    # 預設不搜尋
    return False

# 檢測使用者語言
def detect_language(text):
    """
    檢測使用者輸入的語言
    Returns: 'zh-TW', 'zh-CN', 'en', 'ja', 等
    """
    # 檢測中文繁體
    traditional_chars = ['繁', '體', '臺', '灣', '們', '個', '這', '樣', '嗎', '麼', '為', '與']
    simplified_chars = ['简', '体', '台', '湾', '们', '个', '这', '样', '吗', '么', '为', '与']
    
    has_traditional = any(char in text for char in traditional_chars)
    has_simplified = any(char in text for char in simplified_chars)
    has_chinese = any('\u4e00' <= char <= '\u9fff' for char in text)
    has_japanese = any('\u3040' <= char <= '\u309f' or '\u30a0' <= char <= '\u30ff' for char in text)
    has_korean = any('\uac00' <= char <= '\ud7af' for char in text)
    
    # 判斷語言
    if has_traditional and not has_simplified:
        return 'zh-TW'
    elif has_simplified:
        return 'zh-CN'
    elif has_japanese:
        return 'ja'
    elif has_korean:
        return 'ko'
    elif has_chinese:
        return 'zh-TW'  # 預設繁體中文
    else:
        return 'en'

# 獲取語言對應的系統提示
def get_language_instruction(lang_code):
    """
    根據語言代碼返回相應的語言指示
    """
    language_map = {
        'zh-TW': 'Please respond in Traditional Chinese (繁體中文).',
        'zh-CN': 'Please respond in Simplified Chinese (简体中文).',
        'en': 'Please respond in English.',
        'ja': 'Please respond in Japanese (日本語).',
        'ko': 'Please respond in Korean (한국어).'
    }
    return language_map.get(lang_code, 'Please respond in the same language as the user.')

# 判斷使用者是否要求進行 DEI 分析
def is_analysis_request(text):
    """
    判斷使用者訊息是否為 DEI 政策分析請求
    Returns: True if requesting analysis, False for casual conversation
    """
    text_lower = text.lower()

    explicit_review_keywords = [
        "檢查", "分析", "評估", "審查", "違反", "符合", "遵守", "算不算", "合不合理",
        "幫我看", "幫我確認", "這樣可以嗎", "有問題嗎", "有沒有違反", "需不需要通報",
        "check", "analyze", "analyse", "review", "assess", "evaluate", "violate",
        "violation", "comply", "compliance", "policy", "should i report", "is this okay",
        "is this allowed", "does this violate", "dei concern", "discrimination"
    ]
    scenario_signals = [
        "主管", "同事", "面試", "招募", "招聘", "升遷", "薪資", "懷孕", "身障", "殘障",
        "宗教", "性別", "年齡", "族裔", "國籍", "口音", "性傾向", "性別認同", "排除",
        "歧視", "刻板印象", "冒犯", "騷擾", "報復", "不當", "公告", "職缺", "政策",
        "manager", "coworker", "interview", "hiring", "promotion", "salary", "pregnant",
        "disability", "religion", "gender", "age", "race", "ethnicity", "accent", "harassment",
        "retaliation", "excluded", "job posting", "workplace", "accommodation"
    ]
    uploaded_or_structured_markers = [
        "📎", "請檢查以下內容", "review the following", "please review the following"
    ]

    if any(keyword in text_lower for keyword in explicit_review_keywords):
        return True

    if any(marker.lower() in text_lower for marker in uploaded_or_structured_markers):
        return True

    scenario_hits = sum(1 for keyword in scenario_signals if keyword in text_lower)
    question_like = any(token in text_lower for token in ["?", "？", "是否", "是不是", "能不能", "可不可以", "should", "can", "does"]) 

    return scenario_hits >= 2 or (scenario_hits >= 1 and question_like)

# AI 對話 (使用 LangGraph Agent)
async def chat_with_agent(graph, messages, thread_id, system_prompt):
    """使用 LangGraph agent 進行對話"""
    try:
        config = {"configurable": {"thread_id": thread_id}}
        
        # 轉換訊息格式
        langchain_messages = [SystemMessage(content=system_prompt)]
        for msg in messages:
            if msg["role"] == "system":
                continue  # 系統訊息會在節點中處理
            elif msg["role"] == "user":
                langchain_messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                langchain_messages.append(AIMessage(content=msg["content"]))

        # 執行 agent
        result = await graph.ainvoke(
            {"messages": langchain_messages},
            config=config
        )
        
        # 提取最終回應
        final_message = result["messages"][-1]
        if hasattr(final_message, "content"):
            return final_message.content
        return str(final_message)
        
    except Exception as e:
        error_msg = str(e)
        # 檢查是否為 rate limit 錯誤
        if "rate_limit" in error_msg.lower() or "429" in error_msg:
            # 切換到下一個模型
            new_llm = switch_to_next_model()
            if new_llm:
                return "模型已切換，請重新發送您的訊息"
        return f"Agent 執行失敗: {error_msg}"

# AI 對話 (原始 Groq 方法，作為備援)
def chat(client, messages, use_search=True):
    search_context = ""
    last_msg = next((m for m in reversed(messages) if m["role"] == "user"), None)
    user_text = last_msg["content"] if last_msg else ""
    
    # 檢測使用者語言
    user_language = 'zh-TW'  # 預設繁體中文
    if last_msg:
        user_language = detect_language(user_text)
    language_instruction = get_language_instruction(user_language)
    
    if use_search and last_msg and should_search(user_text):
        results = search_web(user_text[:100])
        if results:
            search_context = "\n\n參考網路資訊：\n" + "\n".join([
                f"• {r.get('title', '')}: {r.get('body', '')[:100]}..." 
                for r in results[:2]
            ])
    system = build_system_prompt(user_text, include_tool_guidance=False)
            
    try:
        msgs = [{"role": "system", "content": system}]
        if search_context:
            msgs.append({"role": "system", "content": search_context})
        msgs.extend([{"role": m["role"], "content": m["content"]} for m in messages])
        
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=msgs,
            temperature=0.7,
            max_tokens=2500
        )
        
        answer = response.choices[0].message.content
        if search_context:
            answer += "\n\n *此回覆含網路搜尋資訊*"
        
        return answer

    except Exception as e:
        error_msg = str(e)
        if "authentication" in error_msg.lower():
            return " API 驗證失敗，請聯絡管理員"
        elif "rate limit" in error_msg.lower():
            return "⏱ 使用額度已達上限，請稍後再試"
        elif "connection" in error_msg.lower():
            return " 網路連線問題，請稍後再試"
        else:
            return f"❌ 發生錯誤：{error_msg}"

# 主介面
st.title("DEI 政策助手")

# 顯示當前使用的模型
if 'current_model' in st.session_state:
    st.info(f"當前使用模型：**{st.session_state.current_model}**")

# 初始化所有組件（在側邊欄之前）
client = init_groq()
if not client:
    st.error("系統初始化失敗")
    st.stop()

# 初始化 LangChain 組件
langchain_llm = init_langchain_groq()
tavily_search = init_tavily()

# 嘗試建立 agent graph
agent_graph = None
if LANGCHAIN_AVAILABLE and langchain_llm:
    try:
        agent_graph = create_agent_graph(langchain_llm, tavily_search)
        if 'agent_mode' not in st.session_state:
            st.session_state.agent_mode = True
    except Exception as e:
        st.warning(f"Agent 初始化失敗，使用傳統模式: {str(e)}")
        st.session_state.agent_mode = False

# 初始化 Supabase
supabase_client = init_supabase()

# 側邊欄
with st.sidebar:
    # API 狀態
    try:
        has_secret = 'groq_api_key' in st.secrets
    except:
        has_secret = False
    
    if not has_secret and 'GROQ_API_KEY' not in os.environ:
        st.error("系統未設定，請聯絡管理員，可點選右上角github連結提出issue")
        st.stop()
    
    st.success("系統就緒")
    
    # Supabase 設定
    st.divider()
    supabase_client = init_supabase()
    if supabase_client:
        st.success("Supabase 已連線")
        
        # Supabase 開關
        supabase_enabled = st.toggle(
            "儲存聊天記錄到 Supabase", 
            value=st.session_state.supabase_enabled,
            help="開啟後會將聊天記錄儲存到 Supabase"
        )
        
        # 如果開關狀態改變
        if supabase_enabled != st.session_state.supabase_enabled:
            st.session_state.supabase_enabled = supabase_enabled
            
            # 如果是開啟，嘗試載入歷史記錄
            if supabase_enabled:
                loaded_history = load_chat_history(supabase_client, st.session_state.session_id)
                if loaded_history:
                    st.session_state.messages = loaded_history
                    st.success(f"已載入 {len(loaded_history)} 則訊息")
                    st.rerun()
        
        # 顯示當前 Session ID
        if st.session_state.supabase_enabled:
            with st.expander("Session 資訊"):
                st.text(f"Session ID: {st.session_state.session_id[:8]}...")
                if st.button("建立新 Session", use_container_width=True):
                    st.session_state.session_id = str(uuid.uuid4())
                    st.session_state.messages = [{
                        "role": "assistant",
                        "content": DEFAULT_ASSISTANT_MESSAGE
                    }]
                    st.session_state.file_processed = set()
                    st.rerun()
    else:
        st.info("Supabase 未設定")
    
    # 檔案上傳
    st.divider()
    uploaded = st.file_uploader(
        "上傳檔案",
        type=['pdf', 'docx', 'txt'],
        help="支援 PDF、Word、TXT 格式"
    )
    
    if uploaded:
        # 使用檔案 ID 防止重複處理
        file_id = f"{uploaded.name}_{uploaded.size}"
        
        if st.button("分析檔案", use_container_width=True):
            if file_id not in st.session_state.file_processed:
                st.session_state.file_processed.add(file_id)
                
                content = read_file(uploaded)
                if content:
                    user_message = f"**{uploaded.name}**\n\n請檢查以下內容：\n\n{content[:10000]}"
                    if len(content) > 10000:
                        user_message += "\n\n*（檔案較長，已截取前 10000 字元）*"

                    add_and_save_message("user", user_message)
                    st.rerun()
    
    # 設定
    st.divider()
    search_enabled = st.toggle("網路搜尋", value=True, help="AI 會自動搜尋最新資訊")
    st.session_state['search'] = search_enabled
    
    # Agent 模式切換
    if LANGCHAIN_AVAILABLE and agent_graph:
        agent_enabled = st.toggle(
            "智能搜尋模式 (LangGraph)", 
            value=st.session_state.get('agent_mode', True),
            help="使用 LangGraph + Tavily 進行智能搜尋決策"
        )
        st.session_state['agent_mode'] = agent_enabled
        
        if agent_enabled and tavily_search:
            st.success("Tavily 搜尋已啟用")
        elif agent_enabled:
            st.warning("Tavily API 未設定，使用基礎模式")
    
    # 清除
    st.divider()
    if st.button("清除對話", use_container_width=True):
        # 如果啟用 Supabase，從資料庫刪除
        if st.session_state.supabase_enabled and supabase_client:
            delete_chat_history(supabase_client, st.session_state.session_id)
        
        st.session_state.messages = [{
            "role": "assistant",
            "content": DEFAULT_ASSISTANT_MESSAGE
        }]
        st.session_state.file_processed = set()
        st.rerun()

# 顯示對話歷史
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 文字輸入
if prompt := st.chat_input("輸入訊息..."):
    add_and_save_message("user", prompt)
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        # 決定使用 agent 還是傳統方法
        use_agent = (
            st.session_state.get('agent_mode', False) and 
            agent_graph is not None and 
            st.session_state.get('search', True)
        )
        
        if use_agent:
            with st.spinner("🔍 智能搜尋中..."):
                system_prompt = build_system_prompt(prompt, include_tool_guidance=True)
                
                # 使用 async 執行
                import asyncio
                try:
                    response = asyncio.run(chat_with_agent(
                        agent_graph,
                        st.session_state.messages,
                        st.session_state.session_id,
                        system_prompt
                    ))
                    # 檢查是否使用了搜尋
                    if "tavily" in str(response).lower() or any(keyword in prompt.lower() for keyword in ["最新", "latest", "2024", "2025"]):
                        response += "\n\n*此回覆使用智能搜尋*"
                except Exception as e:
                    st.error(f"Agent 執行錯誤: {str(e)}")
                    response = "抱歉，發生錯誤。請稍後再試。"
        else:
            with st.spinner("思考中..."):
                response = chat(
                    client,
                    st.session_state.messages,
                    st.session_state.get('search', True)
                )
        
        st.markdown(response)
    
    add_and_save_message("assistant", response)
    st.rerun()