"""DEI 評估助手 — Streamlit 聊天介面。

主要模組結構：
1. 設定常數        — 功能開關、模型清單、成本控制參數
2. 提示詞組裝      — prompt.md + 語言指示 + 執行期規則
3. API 呼叫層      — Groq 客戶端、模型降級、重試、串流
4. 選用功能        — 檔案讀取、網路搜尋、Supabase、LangGraph Agent
5. 介面            — 樣式、標題列、歷史訊息、輸入框
"""

from __future__ import annotations

import io
import os
import re
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, Literal, TypedDict

import streamlit as st
from groq import Groq

import PyPDF2
import docx

# LangChain / LangGraph 為選用套件，未安裝時自動關閉 Agent 模式
try:
    from langchain_groq import ChatGroq
    from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
    from langgraph.graph import StateGraph, END, add_messages
    from langgraph.checkpoint.memory import MemorySaver
    from langchain_tavily import TavilySearch
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

# DuckDuckGo 為 Tavily 的免費備援
try:
    from duckduckgo_search import DDGS
    DDGS_AVAILABLE = True
except ImportError:
    DDGS_AVAILABLE = False

# Supabase 為選用的對話保存功能
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except Exception:
    create_client = None
    Client = None
    SUPABASE_AVAILABLE = False


# ---------------------------------------------------------------------------
# 1. 設定常數
# ---------------------------------------------------------------------------

APP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = APP_DIR.parent
PROMPT_FILE = PROJECT_ROOT / "prompt.md"

# 功能開關：預設只開啟最精簡的聊天功能，降低 API 與維運成本
ENABLE_SIDEBAR = False
ENABLE_SUPABASE = False
ENABLE_FILE_UPLOAD = False
ENABLE_WEB_SEARCH = False
ENABLE_AGENT_MODE = False
ENABLE_TAVILY = False
SHOW_RESPONSE_META = False  # 開啟後會在回覆下方顯示模型名稱與耗時，方便除錯

# 模型降級順序：前面的額度用完（429）就自動換下一個，避免整個服務中斷
MODEL_CHAIN = [
    "openai/gpt-oss-120b",      # 主力模型，品質最佳
    "openai/gpt-oss-20b",       # 同系列較小模型，額度獨立計算
    "llama-3.3-70b-versatile",  # 備援大模型
    "llama-3.1-8b-instant",     # 最後防線，速度快、額度寬鬆
]

# 支援 tool calling 的模型（Agent 模式才會用到）
TOOL_CALLING_MODELS = {
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "gemma2-9b-it",
}

# 成本控制：免費額度以 token 計費，歷史訊息越長每次呼叫越貴
MAX_HISTORY_MESSAGES = 10    # 最多送出最近 10 則對話
MAX_HISTORY_CHARS = 12000    # 歷史訊息總字元上限
MAX_TOKENS = 2800            # 單次回覆的 token 上限（gpt-oss 的推理 token 也計入此額度）
TEMPERATURE = 0.4            # 合規審查場景需要穩定輸出，不宜太發散
MAX_RETRIES = 3              # 暫時性錯誤的重試次數
RETRY_BACKOFF = 1.5          # 重試間隔基數（秒），採指數退避
RATE_LIMIT_COOLDOWN = 90     # 429 後暫停使用該模型的秒數（免費層的每分鐘限制多半一分鐘內恢復）
MODEL_GONE_COOLDOWN = 86400  # 模型已下架，本次 session 內不再嘗試
FILE_TEXT_LIMIT = 10000      # 上傳檔案擷取的字元上限
SEARCH_CACHE_TTL = 3600      # 搜尋結果快取秒數

DEFAULT_ASSISTANT_MESSAGE = """👋 你好！我是DEI 評估助手。

我會依照目前設定的政策指令，協助你檢查情境、文件、公告、政策或溝通內容中的DEI風險。

你可以直接貼上具體情境、文件內容或問題，我會依內容自動用適合的審查格式回覆。

---

👋 Hello! I'm the DEI Evaluation Assistant.

I use the current policy prompt to review scenarios, documents, announcements, policies, and communications for DEI risk.

You can paste a concrete scenario, document excerpt, or question, and I will respond using the appropriate review format."""

# 首次進入時顯示的範例問題，讓使用者知道可以問什麼
EXAMPLE_PROMPTS = [
    "公司想辦女性領導力培訓營，可以嗎？",
    "徵才公告寫「歡迎多元背景者應徵」有風險嗎？",
    "我們要贊助 Pride 月活動，請幫我評估合規風險。",
]


# ---------------------------------------------------------------------------
# 2. 提示詞組裝
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def load_base_prompt(prompt_mtime: float) -> str:
    """讀取 prompt.md。參數 mtime 只用來讓檔案更新時自動失效快取。"""
    del prompt_mtime
    with PROMPT_FILE.open("r", encoding="utf-8") as f:
        return f.read().strip()


def get_base_prompt() -> str:
    """取得 prompt.md 的內容；檔案不存在時直接中止並提示管理員。"""
    try:
        prompt_mtime = PROMPT_FILE.stat().st_mtime
    except FileNotFoundError:
        st.error(f"找不到 prompt 檔案：{PROMPT_FILE}")
        st.stop()
    return load_base_prompt(prompt_mtime)


def detect_language(text: str) -> str:
    """從使用者輸入判斷語言，讓模型用同一種語言回覆。"""
    # 注意：「台」不能列為簡體標記 —— 台灣、台北在繁體中文是標準寫法，
    # 誤判會讓系統指示模型用簡體回覆，直接違反 prompt.md 的絕對禁令。
    # 也不要放「開」「個」「為」這類日文常用漢字（開発、個人、為替），
    # 否則純漢字的日文句子會被誤判成中文。
    traditional_chars = ['繁', '體', '臺', '灣', '們', '這', '樣', '嗎', '麼', '與', '點']
    simplified_chars = ['简', '体', '湾', '们', '这', '样', '吗', '么', '与', '点']

    # 假名與諺文是明確且無歧義的訊號，必須最先判斷：
    # 中日韓共用漢字，先比對漢字會把「開発部門で…」這種句子判成中文。
    if any('぀' <= char <= 'ゟ' or '゠' <= char <= 'ヿ' for char in text):
        return 'ja'
    if any('가' <= char <= '힯' for char in text):
        return 'ko'

    # 用出現次數比較而非單一命中，避免一個借用字就翻轉判斷
    traditional_hits = sum(text.count(char) for char in traditional_chars)
    simplified_hits = sum(text.count(char) for char in simplified_chars)

    if simplified_hits > traditional_hits:
        return 'zh-CN'
    if traditional_hits > 0:
        return 'zh-TW'
    if any('一' <= char <= '鿿' for char in text):
        return 'zh-TW'  # 有漢字但無繁簡特徵，預設繁體
    return 'en'


def get_language_instruction(lang_code: str) -> str:
    """把語言代碼轉成要附加在系統提示後面的回覆語言指示。"""
    language_map = {
        'zh-TW': 'Please respond in Traditional Chinese (繁體中文).',
        # prompt.md 明文規定：任何形式的中文輸入都必須以繁體中文回覆。
        # 這裡若指示簡體，會與基礎提示詞產生直接牴觸的矛盾指令。
        'zh-CN': 'The user wrote in Simplified Chinese. Per the base policy prompt, '
                 'you must still respond entirely in Traditional Chinese (繁體中文).',
        'en': 'Please respond in English.',
        'ja': 'Please respond in Japanese (日本語).',
        'ko': 'Please respond in Korean (한국어).',
    }
    return language_map.get(lang_code, 'Please respond in the same language as the user.')


@st.cache_data(show_spinner=False)
def _compose_system_prompt(base_prompt: str, language_instruction: str, include_tool_guidance: bool) -> str:
    """把固定的提示詞片段組起來並快取，避免每次輸入都重新拼接長字串。"""
    prompt_parts = [
        base_prompt,
        "",
        language_instruction,
        "",
        "Additional runtime instructions:",
        "- Follow the policy definitions, scoring, and response structure in the base prompt as the primary instruction source.",
        "- If the user provides a concrete scenario, communication, proposal, or document, use the scenario compliance review format from the base prompt.",
        "- If the user asks a general question or greets you without a concrete scenario, use the general guidance mode from the base prompt.",
        "- Keep the answer concise and do not restate the full policy prompt.",
        "- Do not provide legal advice.",
        "- Keep any internal scoring hidden unless the user explicitly asks to see numeric scores.",
        "- All section headings must be in the user's language, not English.",
    ]

    if include_tool_guidance:
        prompt_parts.extend([
            "",
            "Search tool usage guidelines:",
            "- You have access to tavily_search when enabled.",
            "- Use search only when the user explicitly asks to search or find something, or asks for latest, current, recent, news, or statistics information.",
            "- Do not use search for analyzing content the user already provided or for stable prompt-defined policy wording.",
            "- Be conservative with search usage to save API credits.",
        ])

    return "\n".join(prompt_parts)


def build_system_prompt(user_text: str = "", include_tool_guidance: bool = False) -> str:
    """依使用者輸入的語言組出完整系統提示。"""
    user_language = detect_language(user_text) if user_text else "zh-TW"
    return _compose_system_prompt(
        get_base_prompt(),
        get_language_instruction(user_language),
        include_tool_guidance,
    )


# ---------------------------------------------------------------------------
# 3. API 呼叫層
# ---------------------------------------------------------------------------

def get_secret(name: str, env_name: str | None = None) -> str | None:
    """依序從 Streamlit secrets 與環境變數取得金鑰。"""
    try:
        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        pass
    return os.environ.get(env_name or name.upper())


@st.cache_resource(show_spinner=False)
def _build_groq_client(api_key: str) -> Groq:
    """以金鑰為快取鍵建立客戶端，金鑰輪替時會自動產生新的連線。"""
    return Groq(api_key=api_key, max_retries=0)  # 重試邏輯由 request_stream 自行處理


def init_groq() -> Groq | None:
    """取得 Groq 客戶端；沒有金鑰時回傳 None。

    注意不要把整個函式包進 cache_resource：那樣「沒有金鑰」的 None 會被快取住，
    之後就算補上或更換金鑰，也要重啟整個程序才會生效。
    """
    api_key = get_secret("groq_api_key", "GROQ_API_KEY")
    if not api_key:
        return None
    return _build_groq_client(api_key)


def http_status(exc: Exception) -> int | None:
    """取出 HTTP 狀態碼：先用 SDK 例外自帶的，沒有才從訊息解析。

    不可以用 `"413" in message` 這種裸數字比對 —— 真實的 429 訊息本身就含有
    "Used 11413"、"try again in 2.413s" 這類數字，會被誤判成 413。
    """
    status = getattr(exc, "status_code", None)
    if isinstance(status, int):
        return status
    match = re.search(r"error code:\s*(\d{3})", str(exc).lower())
    return int(match.group(1)) if match else None


def classify_error(exc: Exception) -> str:
    """把例外歸類，決定要重試、換模型還是直接放棄。

    回傳值：
    - ``too_large``    輸入超過單次請求上限，換模型也沒用
    - ``rate_limit``   額度或頻率受限，換下一個模型
    - ``auth``         金鑰錯誤，立即中止
    - ``model_gone``   模型已下架，換下一個模型
    - ``server_error`` 供應商 5xx，重試後換下一個模型
    - ``transient``    連線或逾時，重試同一個模型
    - ``fatal``        其他
    """
    message = str(exc).lower()
    status = http_status(exc)

    # 狀態碼優先。413 與 429 在 Groq 共用 rate_limit_exceeded 錯誤碼，
    # 只有狀態碼能區分「單次請求過長」與「額度／頻率受限」。
    if status == 413:
        return "too_large"
    if status == 429:
        return "rate_limit"
    if status in (401, 403):
        return "auth"
    if status == 404:
        return "model_gone"
    if status is not None and status >= 500:
        return "server_error"

    # 沒有狀態碼時（例如連線層級的例外）才退回文字比對
    if "request too large" in message or "context_length" in message:
        return "too_large"
    if "rate limit" in message or "rate_limit" in message or "quota" in message:
        return "rate_limit"
    if "authentication" in message or "invalid api key" in message:
        return "auth"
    if "decommission" in message or "does not exist" in message or "model_not_found" in message:
        return "model_gone"
    if "overloaded" in message or "service unavailable" in message:
        return "server_error"
    # groq 的 APITimeoutError 字串是 "Request timed out."，不含 "timeout"
    if "timed out" in message or "timeout" in message or "connection" in message:
        return "transient"
    return "fatal"


def friendly_error(exc: Exception) -> str:
    """把例外轉成可以直接顯示給使用者看的中文訊息。"""
    kind = classify_error(exc)
    messages = {
        "too_large": "📄 這次輸入的內容太長，請縮短後再送出，或分段貼上。",
        "rate_limit": "⏱️ 目前呼叫太頻繁或額度已滿，請稍候片刻再試。",
        "auth": "🔑 API 驗證失敗，請聯絡管理員確認金鑰設定。",
        "model_gone": "🛠️ 目前可用的模型都無法使用，請聯絡管理員更新模型清單。",
        "server_error": "🛠️ 模型服務暫時不穩定，請稍後再試一次。",
        "transient": "🌐 連線不穩定，請稍後再試一次。",
    }
    if kind in messages:
        return messages[kind]
    # 供應商的原始錯誤訊息可能夾帶組織 ID、配額數字等內部資訊，
    # 預設只顯示例外型別；需要完整內容時開啟 SHOW_RESPONSE_META。
    if SHOW_RESPONSE_META:
        return f"❌ 發生錯誤（{type(exc).__name__}）：{exc}"
    return f"❌ 發生未預期的錯誤（{type(exc).__name__}），請稍後再試或聯絡管理員。"


def mark_model_unavailable(model: str, seconds: float):
    """讓某個模型暫時退出候選清單。

    用冷卻時間而非永久標記：Groq 免費層的每分鐘頻率限制通常幾十秒就恢復，
    永久停用會讓整個 session 都卡在最弱的備援模型上。
    """
    cooldowns = st.session_state.setdefault("model_cooldowns", {})
    cooldowns[model] = time.time() + seconds


def available_models() -> list[str]:
    """排除仍在冷卻中的模型；全部都在冷卻時回傳完整清單再試一次。"""
    cooldowns = st.session_state.get("model_cooldowns", {})
    now = time.time()
    remaining = [m for m in MODEL_CHAIN if cooldowns.get(m, 0) <= now]
    return remaining or list(MODEL_CHAIN)


def build_api_messages(messages: list[dict], system_prompt: str) -> list[dict]:
    """組出要送給 API 的訊息，並裁掉過長的歷史以節省 token。

    裁切規則：
    1. 移除開場白（純介紹文字，對模型沒有資訊價值）
    1b. 移除錯誤提示（transient），它們不是模型說過的話
    2. 只保留最近 MAX_HISTORY_MESSAGES 則
    3. 由新到舊累加，總字元超過 MAX_HISTORY_CHARS 就停止
    4. 最新一則若自己就超過上限，截斷並加註（不能直接丟掉，那是使用者剛送出的內容）
    """
    history = [
        m for m in messages
        if m.get("content")
        and not m.get("transient")          # 錯誤提示不是模型的發言
        and m["content"] != DEFAULT_ASSISTANT_MESSAGE
    ]
    history = history[-MAX_HISTORY_MESSAGES:]

    trimmed: list[dict] = []
    used_chars = 0
    for msg in reversed(history):
        content = msg["content"]
        if not trimmed:
            # 最新一則一定要送，但仍需設上限，否則貼上長文件會直接撞 413
            if len(content) > MAX_HISTORY_CHARS:
                content = content[:MAX_HISTORY_CHARS] + "\n\n（內容過長，已截斷）"
        elif used_chars + len(content) > MAX_HISTORY_CHARS:
            break
        used_chars += len(content)
        trimmed.append({"role": msg["role"], "content": content})
    trimmed.reverse()

    return [{"role": "system", "content": system_prompt}] + trimmed


def request_stream(client: Groq, api_messages: list[dict]):
    """依序嘗試模型清單，回傳 (模型名稱, 串流物件)。

    - 輸入過長 → 立即中止（換模型也沒用）
    - 429 / 模型下架 → 加上冷卻時間，換下一個模型
    - 供應商 5xx → 退避重試，仍失敗就換下一個模型
    - 連線／逾時 → 退避重試同一個模型，仍失敗就中止（換模型也連不上）
    - 金鑰錯誤 → 立即中止，重試沒有意義
    """
    last_error: Exception | None = None

    for model in available_models():
        for attempt in range(MAX_RETRIES):
            try:
                stream = client.chat.completions.create(
                    model=model,
                    messages=api_messages,
                    temperature=TEMPERATURE,
                    max_tokens=MAX_TOKENS,
                    stream=True,
                )
                return model, stream
            except Exception as exc:  # noqa: BLE001 - 需要依錯誤類型分流
                last_error = exc
                kind = classify_error(exc)

                if kind in ("auth", "too_large"):
                    raise  # 換模型或重試都救不了
                if kind == "rate_limit":
                    mark_model_unavailable(model, RATE_LIMIT_COOLDOWN)
                    break  # 換下一個模型
                if kind == "model_gone":
                    mark_model_unavailable(model, MODEL_GONE_COOLDOWN)
                    break
                if kind in ("server_error", "transient"):
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(RETRY_BACKOFF * (2 ** attempt))
                        continue
                    if kind == "transient":
                        raise  # 連線問題與模型無關，換模型也一樣連不上
                    break  # 5xx 是該模型當下不穩，換下一個試試
                break  # 其他錯誤不重試，換下一個模型試試

    raise last_error if last_error else RuntimeError("沒有可用的模型")


def iter_stream_text(stream, notice_state: dict | None = None):
    """把 Groq 的串流物件轉成純文字產生器，給 st.write_stream 使用。

    這裡刻意不讓例外往外拋：串流到一半失敗時，若直接拋出，
    st.write_stream 已經畫在畫面上的內容會被錯誤訊息整段取代，
    使用者看得到的半段回覆也不會被寫進歷史。改成把提示接在後面。

    但提示本身不是模型的發言，不能混進存檔與下一輪的歷史。
    notice_state 會記下實際附加的提示字串，讓呼叫端把它從回覆尾端去掉。
    """
    def emit(notice: str) -> str:
        """記下附加的提示字串，並原樣回傳讓呼叫端 yield 出去。"""
        if notice_state is not None:
            notice_state["notice"] = notice
        return notice

    finish_reason = None
    try:
        for chunk in stream:
            if not chunk.choices:
                continue
            choice = chunk.choices[0]
            if choice.finish_reason:
                finish_reason = choice.finish_reason
            delta = choice.delta
            if delta and delta.content:
                yield delta.content
    except Exception as exc:  # noqa: BLE001
        yield emit(f"\n\n---\n⚠️ 回覆中斷：{friendly_error(exc)}")
        return

    if finish_reason == "length":
        # 撞到 MAX_TOKENS 而截斷。不提示的話，半截的審查報告會被當成完整結論。
        yield emit("\n\n---\n⚠️ 回覆已達長度上限而中斷，請縮小問題範圍或分次詢問。")


def build_search_context(user_text: str) -> str:
    """需要時才呼叫搜尋，並把結果整理成一段系統提示。"""
    if not should_search(user_text):
        return ""
    results = search_web(user_text[:100])
    if not results:
        return ""
    return "\n\n參考網路資訊：\n" + "\n".join(
        f"• {r.get('title', '')}: {r.get('body', '')[:100]}..."
        for r in results[:2]
    )


# ---------------------------------------------------------------------------
# 4. 選用功能：檔案、搜尋、Supabase、Agent
# ---------------------------------------------------------------------------

def read_file(file):
    """從 PDF / DOCX / TXT 擷取純文字。"""
    try:
        file_bytes = file.read()
        if file.type == "application/pdf":
            pdf = PyPDF2.PdfReader(io.BytesIO(file_bytes))
            return "\n".join((p.extract_text() or "") for p in pdf.pages)
        if file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = docx.Document(io.BytesIO(file_bytes))
            return "\n".join(p.text for p in doc.paragraphs)
        if file.type == "text/plain":
            return file_bytes.decode("utf-8", errors="replace")
        raise ValueError(f"不支援的檔案類型: {file.type}")
    except Exception as exc:  # noqa: BLE001
        st.error(f"讀取檔案失敗: {exc}")
        return None


@st.cache_data(ttl=SEARCH_CACHE_TTL, show_spinner=False)
def search_web(query: str) -> list[dict]:
    """DuckDuckGo 搜尋，結果快取一小時，避免重複查詢浪費配額。"""
    if not DDGS_AVAILABLE:
        return []
    try:
        with DDGS() as ddgs:
            return list(ddgs.text(query, max_results=3))
    except Exception as exc:  # noqa: BLE001
        st.warning(f"網路搜尋失敗: {exc}")
        return []


def should_search(text: str) -> bool:
    """判斷是否該搜尋。標準刻意設嚴格，避免浪費免費 API 額度。"""
    explicit_search_keywords = [
        "搜尋", "查詢", "找一下", "幫我找", "search", "find",
        "search for", "find me", "look up", "look for",
    ]
    time_sensitive_keywords = [
        "最新", "近期", "現在", "當前", "目前", "今年", "本月", "今天", "最近",
        "latest", "recent", "current", "now", "today", "this year", "2024", "2025",
    ]
    data_keywords = [
        "統計", "數據", "報告", "研究", "案例", "新聞", "數量",
        "statistics", "data", "report", "research", "study", "case", "news",
    ]

    text_lower = text.lower()
    if any(keyword in text_lower for keyword in explicit_search_keywords):
        return True
    has_time_sensitive = any(keyword in text_lower for keyword in time_sensitive_keywords)
    has_data_request = any(keyword in text_lower for keyword in data_keywords)
    return has_time_sensitive and has_data_request


@st.cache_resource(show_spinner=False)
def init_supabase():
    """建立 Supabase 客戶端；功能關閉或缺少設定時回傳 None。"""
    if not SUPABASE_AVAILABLE or not ENABLE_SUPABASE:
        return None
    url = get_secret("supabase_url", "SUPABASE_URL")
    key = get_secret("supabase_key", "SUPABASE_KEY")
    if not (url and key):
        return None
    try:
        return create_client(url, key)
    except Exception as exc:  # noqa: BLE001
        st.error(f"Supabase 初始化失敗: {exc}")
        return None


def save_message_to_supabase(supabase, session_id: str, role: str, content: str) -> bool:
    """把單則訊息寫入 chat_history 資料表，成功回傳 True。"""
    if not supabase:
        return False
    try:
        supabase.table("chat_history").insert({
            "session_id": session_id,
            "role": role,
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }).execute()
        return True
    except Exception as exc:  # noqa: BLE001
        st.error(f"儲存訊息失敗: {exc}")
        return False


def load_chat_history(supabase, session_id: str):
    """讀回這個 session 先前存下的對話；沒有資料時回傳 None。"""
    if not supabase:
        return None
    try:
        response = (
            supabase.table("chat_history")
            .select("*")
            .eq("session_id", session_id)
            .order("timestamp")
            .execute()
        )
        if response.data:
            return [{"role": m["role"], "content": m["content"]} for m in response.data]
    except Exception as exc:  # noqa: BLE001
        st.error(f"載入聊天記錄失敗: {exc}")
    return None


def delete_chat_history(supabase, session_id: str) -> bool:
    """刪除這個 session 在資料庫中的所有對話紀錄。"""
    if not supabase:
        return False
    try:
        supabase.table("chat_history").delete().eq("session_id", session_id).execute()
        return True
    except Exception as exc:  # noqa: BLE001
        st.error(f"刪除聊天記錄失敗: {exc}")
        return False


def add_and_save_message(role: str, content: str, transient: bool = False):
    """把訊息加進對話。

    transient=True 代表這是錯誤提示而非模型的真實回覆：畫面上要留著讓使用者看到，
    但不能寫進 Supabase，也不能在下一輪當成助理發言餵回模型 —— 否則模型會把
    「額度已用完」當成自己說過的話，後續回答全被帶偏。
    """
    message = {"role": role, "content": content}
    if transient:
        message["transient"] = True
    st.session_state.messages.append(message)
    if not transient and st.session_state.get("supabase_enabled") and supabase_client:
        save_message_to_supabase(supabase_client, st.session_state.session_id, role, content)


def reset_conversation():
    """清空對話並重置與模型相關的暫存狀態。"""
    if st.session_state.get("supabase_enabled") and supabase_client:
        delete_chat_history(supabase_client, st.session_state.session_id)
    st.session_state.messages = [{"role": "assistant", "content": DEFAULT_ASSISTANT_MESSAGE}]
    st.session_state.file_processed = set()
    st.session_state.pending_prompt = None
    st.session_state.model_cooldowns = {}  # 讓「清除」也能把降級狀態還原回主力模型


# --- LangGraph Agent（預設關閉，保留供日後啟用） ---------------------------

if LANGCHAIN_AVAILABLE:
    class AgentState(TypedDict):
        messages: Annotated[list, add_messages]


def init_langchain_groq():
    """建立 Agent 模式用的 ChatGroq，只挑選支援 tool calling 且未在冷卻中的模型。"""
    if not LANGCHAIN_AVAILABLE or not ENABLE_AGENT_MODE:
        return None
    api_key = get_secret("groq_api_key", "GROQ_API_KEY")
    if not api_key:
        return None

    usable = set(available_models())
    models = [m for m in MODEL_CHAIN if m in TOOL_CALLING_MODELS and m in usable]
    if not models:
        st.error("所有模型都已達到上限，請稍待片刻再試，或聯絡管理員")
        return None

    selected_model = models[0]
    st.session_state.current_model = selected_model
    return ChatGroq(model=selected_model, api_key=api_key, temperature=TEMPERATURE)


def init_tavily():
    """建立 Tavily 搜尋工具；未啟用或缺少金鑰時回傳 None。"""
    if not (LANGCHAIN_AVAILABLE and ENABLE_AGENT_MODE and ENABLE_TAVILY):
        return None
    api_key = get_secret("tavily_api_key", "TAVILY_API_KEY")
    if not api_key:
        return None
    os.environ["TAVILY_API_KEY"] = api_key
    return TavilySearch(max_results=4)


async def agent_model(state: AgentState, llm, tools):
    """Agent 的決策節點：讓模型決定要直接回答還是呼叫工具。"""
    llm_with_tools = llm.bind_tools(tools=tools) if tools else llm
    result = await llm_with_tools.ainvoke(state["messages"])
    return {"messages": [result]}


async def tool_node(state: AgentState, search_tool):
    """Agent 的工具節點：執行模型要求的搜尋並把結果包成 ToolMessage。"""
    last = state["messages"][-1]
    tool_calls = getattr(last, "tool_calls", []) or []
    tool_messages = []
    for tool_call in tool_calls:
        if tool_call["name"] != "tavily_search":
            continue
        try:
            search_results = await search_tool.ainvoke(tool_call["args"])
            content = str(search_results)
        except Exception as exc:  # noqa: BLE001
            content = f"搜尋失敗: {exc}"
        tool_messages.append(ToolMessage(
            content=content, tool_call_id=tool_call["id"], name=tool_call["name"],
        ))
    return {"messages": tool_messages}


def tools_router(state: AgentState) -> Literal["tool_node", "__end__"]:
    """看最後一則訊息有沒有 tool_calls，決定要走工具節點還是結束。"""
    last_message = state["messages"][-1]
    if getattr(last_message, "tool_calls", None):
        return "tool_node"
    return END


@st.cache_resource(show_spinner=False)
def create_agent_graph(_llm, _search_tool, cache_key: str):
    """建立並編譯 LangGraph agent。"""
    # cache_key 不可省略：cache_resource 會忽略底線開頭的參數，
    # 只傳 _llm 的話，模型降級換了 ChatGroq 之後仍會拿到舊的 graph。
    del cache_key
    graph_builder = StateGraph(AgentState)

    async def model_wrapper(state):
        """把節點函式綁定到這張 graph 用的 llm 與工具。"""
        return await agent_model(state, _llm, [_search_tool] if _search_tool else [])

    async def tool_wrapper(state):
        """把工具節點綁定到這張 graph 用的搜尋工具。"""
        return await tool_node(state, _search_tool)

    graph_builder.add_node("model", model_wrapper)
    graph_builder.add_node("tool_node", tool_wrapper)
    graph_builder.set_entry_point("model")
    graph_builder.add_conditional_edges("model", tools_router)
    graph_builder.add_edge("tool_node", "model")
    return graph_builder.compile(checkpointer=MemorySaver())


async def chat_with_agent(graph, messages, thread_id, system_prompt):
    """以 LangGraph agent 產生回覆，回傳最後一則訊息的文字內容。"""
    config = {"configurable": {"thread_id": thread_id}}
    langchain_messages = [SystemMessage(content=system_prompt)]
    for msg in messages[-MAX_HISTORY_MESSAGES:]:
        if msg["role"] == "user":
            langchain_messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            langchain_messages.append(AIMessage(content=msg["content"]))

    result = await graph.ainvoke({"messages": langchain_messages}, config=config)
    final_message = result["messages"][-1]
    return getattr(final_message, "content", str(final_message))


# ---------------------------------------------------------------------------
# 5. 介面
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="DEI 評估助手",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# 自訂樣式：使用 Streamlit 的佈景變數，深色/淺色主題都能正常顯示
st.markdown(
    """
    <style>
      /* 收窄上方留白，讓對話區域更早開始 */
      .block-container { padding-top: 2.5rem; padding-bottom: 6rem; max-width: 820px; }

      /* 隱藏 Streamlit 預設的頁尾與選單，介面更像獨立產品 */
      footer { visibility: hidden; }
      #MainMenu { visibility: hidden; }

      /* 對話泡泡：加上邊框與圓角，長篇審查結果比較好閱讀。
         背景用半透明灰而非 Streamlit 佈景變數 —— 那些變數並不存在於
         Streamlit 的樣式表中，寫了不會有任何效果。半透明灰會疊在頁面
         底色上，淺色與深色主題都能得到合適的對比。 */
      [data-testid="stChatMessage"] {
        border: 1px solid rgba(128, 128, 128, 0.18);
        border-radius: 14px;
        padding: 0.9rem 1.1rem;
        margin-bottom: 0.65rem;
        background-color: rgba(128, 128, 128, 0.06);
      }
      [data-testid="stChatMessage"] p { line-height: 1.75; }
      [data-testid="stChatMessage"] h1,
      [data-testid="stChatMessage"] h2,
      [data-testid="stChatMessage"] h3 { margin-top: 0.8rem; font-size: 1.05rem; }

      /* 輸入框固定在底部並加上陰影，與內容區分開 */
      [data-testid="stChatInput"] { border-radius: 12px; }

      /* 範例問題按鈕：低調的次要樣式 */
      div[data-testid="stButton"] > button {
        border-radius: 10px;
        font-size: 0.86rem;
        line-height: 1.4;
        white-space: normal;
        height: auto;
        min-height: 2.6rem;
      }

      /* 手機版再收窄左右留白 */
      @media (max-width: 640px) {
        .block-container { padding-left: 1rem; padding-right: 1rem; }
      }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- session state 初始化 ---
st.session_state.setdefault("messages", [{"role": "assistant", "content": DEFAULT_ASSISTANT_MESSAGE}])
st.session_state.setdefault("file_processed", set())
st.session_state.setdefault("session_id", str(uuid.uuid4()))
st.session_state.setdefault("model_cooldowns", {})
st.session_state.setdefault("pending_prompt", None)
st.session_state.supabase_enabled = ENABLE_SUPABASE
st.session_state.search = ENABLE_WEB_SEARCH
# 用 setdefault：agent 失敗時會把它設成 False，每次 rerun 重新指派會讓那個
# 自動降級失效，導致每則訊息都再撞一次同樣的錯誤。
st.session_state.setdefault("agent_mode", ENABLE_AGENT_MODE and ENABLE_TAVILY)

# --- 初始化各項服務 ---
client = init_groq()
if not client:
    st.error("系統未設定 API 金鑰，請聯絡管理員，可點選右上角 GitHub 連結提出 issue")
    st.stop()

supabase_client = init_supabase()

# 開啟 Supabase 時把先前的對話載回來。原本只有側邊欄的開關會呼叫
# load_chat_history()，側邊欄關閉後就變成「只寫不讀」，紀錄等於白存。
if st.session_state.supabase_enabled and supabase_client and not st.session_state.get("history_loaded"):
    st.session_state.history_loaded = True
    saved = load_chat_history(supabase_client, st.session_state.session_id)
    if saved:
        st.session_state.messages = saved

agent_graph = None
if ENABLE_AGENT_MODE and LANGCHAIN_AVAILABLE:
    langchain_llm = init_langchain_groq()
    tavily_search = init_tavily()
    if langchain_llm:
        try:
            agent_graph = create_agent_graph(
                langchain_llm,
                tavily_search,
                cache_key=st.session_state.get("current_model", ""),
            )
        except Exception as exc:  # noqa: BLE001
            st.warning(f"Agent 初始化失敗，使用一般模式: {exc}")
            st.session_state.agent_mode = False

# --- 標題列 ---
header_left, header_right = st.columns([5, 1], vertical_alignment="center")
with header_left:
    st.title("DEI 評估助手")
    st.caption(
        "貼上情境、公告或政策內容，即可取得合規風險評估。"
        "本工具僅供內部參考，不構成法律意見；**請勿輸入個資或未公開的機密文件**。"
    )
with header_right:
    if st.button("🗑️ 清除", help="清除目前的對話紀錄", use_container_width=True):
        reset_conversation()
        st.rerun()

st.divider()

# --- 側邊欄（預設關閉） ---
if ENABLE_SIDEBAR:
    with st.sidebar:
        st.success("系統就緒")

        if ENABLE_SUPABASE and supabase_client:
            st.divider()
            st.success("Supabase 已連線")
            with st.expander("Session 資訊"):
                st.text(f"Session ID: {st.session_state.session_id[:8]}...")
                if st.button("建立新 Session", use_container_width=True):
                    st.session_state.session_id = str(uuid.uuid4())
                    reset_conversation()
                    st.rerun()

        if ENABLE_FILE_UPLOAD:
            st.divider()
            uploaded = st.file_uploader("上傳檔案", type=["pdf", "docx", "txt"], help="支援 PDF、Word、TXT 格式")
            if uploaded and st.button("分析檔案", use_container_width=True):
                file_id = f"{uploaded.name}_{uploaded.size}"
                if file_id not in st.session_state.file_processed:
                    st.session_state.file_processed.add(file_id)
                    content = read_file(uploaded)
                    if content:
                        user_message = f"**{uploaded.name}**\n\n請檢查以下內容：\n\n{content[:FILE_TEXT_LIMIT]}"
                        if len(content) > FILE_TEXT_LIMIT:
                            user_message += f"\n\n*（檔案較長，已截取前 {FILE_TEXT_LIMIT} 字元）*"
                        # 必須走 pending_prompt：回答流程是由 prompt 觸發的，
                        # 只把訊息塞進 messages 的話，檔案會顯示出來卻永遠不被分析。
                        st.session_state.pending_prompt = user_message
                        st.rerun()

        st.divider()
        if st.button("清除對話", use_container_width=True):
            reset_conversation()
            st.rerun()

# --- 接收輸入：聊天框或範例按鈕 ---
# st.chat_input 無論在程式的哪個位置呼叫，都會固定顯示在畫面最下方，
# 所以可以提前取值，讓後面的區塊知道這一輪有沒有待處理的輸入。
prompt = st.chat_input("輸入要評估的情境或問題…")
if not prompt and st.session_state.pending_prompt:
    prompt = st.session_state.pending_prompt
    st.session_state.pending_prompt = None

# --- 顯示對話歷史 ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="🤖" if msg["role"] == "assistant" else "🙋"):
        st.markdown(msg["content"])

# --- 範例問題（只在對話尚未開始、且這次沒有待處理輸入時顯示） ---
# 必須先取得 prompt 再決定畫不畫：否則送出第一個問題的那一輪，按鈕會被畫在
# 開場白與第一組問答中間，要等到下一次互動才消失。
if not prompt and len(st.session_state.messages) <= 1:
    st.caption("💡 你可以從這些問題開始：")
    for column, example in zip(st.columns(len(EXAMPLE_PROMPTS)), EXAMPLE_PROMPTS):
        with column:
            if st.button(example, key=f"example_{example}", use_container_width=True):
                st.session_state.pending_prompt = example
                st.rerun()

if prompt:
    add_and_save_message("user", prompt)
    with st.chat_message("user", avatar="🙋"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="🤖"):
        use_agent = bool(st.session_state.agent_mode and agent_graph)
        started_at = time.perf_counter()
        used_model = None
        response = ""
        is_error = False  # 錯誤提示不寫進送給模型的歷史

        if use_agent:
            import asyncio
            with st.spinner("智能搜尋中…"):
                try:
                    response = asyncio.run(chat_with_agent(
                        agent_graph,
                        st.session_state.messages,
                        st.session_state.session_id,
                        build_system_prompt(prompt, include_tool_guidance=True),
                    ))
                    used_model = st.session_state.get("current_model")
                except Exception:  # noqa: BLE001
                    st.session_state.agent_mode = False
                    st.info("智能搜尋暫時無法使用，已改用一般回答模式。")
                    use_agent = False

        if not use_agent:
            system_prompt = build_system_prompt(prompt)
            search_context = build_search_context(prompt) if st.session_state.search else ""
            if search_context:
                system_prompt = f"{system_prompt}\n{search_context}"

            api_messages = build_api_messages(st.session_state.messages, system_prompt)

            notice_state: dict = {}
            try:
                with st.spinner("分析中…"):
                    used_model, stream = request_stream(client, api_messages)
                # 串流輸出：使用者不必等整段生成完才看到內容
                response = st.write_stream(iter_stream_text(stream, notice_state))

                # 中斷／截斷提示要留在畫面上，但不能存檔也不能回送模型 ——
                # 否則模型下一輪會把「回覆中斷」當成自己說過的話。
                notice = notice_state.get("notice")
                if notice and isinstance(response, str):
                    trimmed = response.removesuffix(notice)
                    if trimmed.strip():
                        response = trimmed
                    else:
                        is_error = True  # 完全沒產生內容，整則都只是提示
            except Exception as exc:  # noqa: BLE001
                response = friendly_error(exc)
                is_error = True
                st.markdown(response)

            # 只有真的產生回覆才標註搜尋，錯誤訊息加上這句會造成誤導
            if response and not is_error and search_context:
                response += "\n\n*此回覆含網路搜尋資訊*"
                st.caption("此回覆含網路搜尋資訊")

        if use_agent and response:
            st.markdown(response)

        if SHOW_RESPONSE_META and used_model:
            st.caption(f"模型：{used_model} ・ 耗時 {time.perf_counter() - started_at:.1f}s")

    if not response:
        response, is_error = "（沒有取得回覆，請再試一次）", True
    add_and_save_message("assistant", response, transient=is_error)
