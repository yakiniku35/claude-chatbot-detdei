import streamlit as st
from groq import Groq
import PyPDF2
import docx
import io
import json
import os
from duckduckgo_search import DDGS
# Supabase is optional. Guard the import so the app can run without the package.
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except Exception:
    create_client = None
    Client = None
    SUPABASE_AVAILABLE = False
from datetime import datetime
import uuid

# 讀取 prompts.json
@st.cache_data
def load_prompts():
    try:
        with open('config/prompts.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"executive_orders": []}

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
        "content": "👋 你好！我是 DEI 政策助手。\n\n我可以幫你：\n• 💬 聊天和回答問題\n• 📋 檢查內容是否符合 DEI 政策\n• 💡 提供改善建議\n\n有什麼我可以幫忙的嗎？😊\n\n---\n\n👋 Hello! I'm the DEI Policy Assistant.\n\nI can help you:\n• 💬 Chat and answer questions\n• 📋 Check content for DEI policy compliance\n• 💡 Provide improvement suggestions\n\nHow can I help you today? 😊"
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

# 網路搜尋
def search_web(query):
    try:
        with DDGS() as ddgs:
            return list(ddgs.text(query, max_results=3))
    except Exception as e:
        st.warning(f"網路搜尋失敗: {str(e)}")
        return []

def should_search(text):
    keywords = [
        # 中文關鍵字
        "最新", "近期", "現在", "查詢", "搜尋", "案例", "趨勢", "統計", "研究",
        # 英文關鍵字
        "latest", "recent", "current", "search", "query", "case", "trend", "statistics", "research",
        # 年份
        "2024", "2025"
    ]
    return any(k in text.lower() for k in keywords)

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
    analysis_keywords = [
        # 中文關鍵字
        "檢查", "分析", "評估", "審查", "違反", "符合", "遵守", "等級",
        "dei", "政策", "歧視", "刻板印象", "排他", "冒犯", "不當",
        "請幫我看", "幫我確認", "這樣可以嗎", "有問題嗎", "有沒有違反", "討論",
        # 英文關鍵字
        "check", "analyze", "analyse", "review", "assess", "evaluate", 
        "violate", "violation", "comply", "compliance", "policy", "discrimination",
        "stereotype", "offensive", "inappropriate", "inclusive", "diversity"
    ]
    
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in analysis_keywords)

# AI 對話
def chat(client, messages, use_search=True):
    search_context = ""
    last_msg = next((m for m in reversed(messages) if m["role"] == "user"), None)
    
    # 檢測使用者語言
    user_language = 'zh-TW'  # 預設繁體中文
    if last_msg:
        user_language = detect_language(last_msg["content"])
    language_instruction = get_language_instruction(user_language)
    
    if use_search and last_msg and should_search(last_msg["content"]):
        results = search_web(last_msg["content"][:100])
        if results:
            search_context = "\n\n參考網路資訊：\n" + "\n".join([
                f"• {r.get('title', '')}: {r.get('body', '')[:100]}..." 
                for r in results[:2]
            ])
    
    # 判斷使用者是否要求進行分析
    requesting_analysis = last_msg and is_analysis_request(last_msg["content"])
    
    # 從 prompts.json 讀取執行命令
    prompts_data = load_prompts()
    executive_orders_parts = []
    if prompts_data.get('executive_orders'):
        executive_orders_parts.append("\n\n📋 **參考政策：**")
        for order in prompts_data['executive_orders']:
            executive_orders_parts.append(f"• **{order.get('title', '')}**: {order.get('description', '')}")
    executive_orders_text = "\n".join(executive_orders_parts)
    
    # 從 prompts.json 讀取 document.policies 與 administration（如果存在）並摘要化
    policies_parts = []
    doc = prompts_data.get('document')
    # 支援 document 為物件或單元素陣列
    if doc:
        if isinstance(doc, list) and len(doc) > 0:
            doc = doc[0]
        if isinstance(doc, dict):
            policies = doc.get('policies') or doc.get('policy')
            if policies and isinstance(policies, dict):
                policies_parts.append("\n\n📚 **政策摘要：**")
                for key, p in policies.items():
                    title = p.get('title') or key
                    summary = p.get('summary', '')
                    actions = p.get('actions', [])
                    policies_parts.append(f"**{title}**: {summary}")
                    if actions:
                        action_text = "; ".join(actions[:3])
                        if len(actions) > 3:
                            action_text += "..."
                        policies_parts.append(f"  - 動作: {action_text}")
            admin = doc.get('administration')
            if admin and isinstance(admin, dict):
                policies_parts.append("\n🏛️ **管理團隊：**")
                president = admin.get('president')
                term = admin.get('term')
                if president:
                    policies_parts.append(f"- 主席/總統: {president}")
                if term:
                    policies_parts.append(f"- 任期: {term}")
    policies_text = "\n".join(policies_parts)
    
    # 準備一般系統提示（適用於非深入法規分析的對話）
    system_general = f"""
    You are a DEI (Diversity, Equity, and Inclusion) policy assistant. Please respond in a professional, friendly, and neutral tone.
    
    {language_instruction}
    
    When users request policy background or reference materials, you may cite the following summaries:
    {executive_orders_text}
    {policies_text}
    """

    # 根據使用者意圖選擇不同的系統提示
    if requesting_analysis:
        # 分析模式：專業的 DEI 政策檢查
        system = f"""You are an analyst specialized in Diversity, Equity, and Inclusion (DEI). 
For each policy, practice, or statement given, provide:

1. Whether it is relevant to DEI or should be considered (Yes/No).
2. A DEI impact score on a scale of 0-5 (0 = no impact, 5 = very strong impact).
3. If applicable, explain potential implications according to relevant laws or regulations (e.g., Title VII of the Civil Rights Act, ADA, etc.).

Format your output as:

- DEI Relevance: Yes/No
- DEI Score: [0-5]
- Legal/Regulatory Consideration: [brief explanation, if applicable]

Be concise but clear, and only include points directly related to DEI.

{language_instruction}

Refer to the following policies and executive orders for your analysis:
{executive_orders_text}{policies_text}
"""
    else:
        system = system_general
            
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
            answer += "\n\n🌐 *此回覆含網路搜尋資訊*"
        
        return answer
        
    except Exception as e:
        error_msg = str(e)
        if "authentication" in error_msg.lower():
            return "❌ API 驗證失敗，請聯絡管理員"
        elif "rate limit" in error_msg.lower():
            return "⏱️ 使用額度已達上限，請稍後再試"
        elif "connection" in error_msg.lower():
            return "🌐 網路連線問題，請稍後再試"
        else:
            return f"❌ 發生錯誤：{error_msg}"

# 主介面
st.title("🤖 DEI 政策助手")

# 側邊欄
with st.sidebar:
    # API 狀態
    try:
        has_secret = 'groq_api_key' in st.secrets
    except:
        has_secret = False
    
    if not has_secret and 'GROQ_API_KEY' not in os.environ:
        st.error("⚠️ 系統未設定，請聯絡管理員")
        st.stop()
    
    st.success("✅ 系統就緒")
    
    # Supabase 設定
    st.divider()
    supabase_client = init_supabase()
    if supabase_client:
        st.success("✅ Supabase 已連線")
        
        # Supabase 開關
        supabase_enabled = st.toggle(
            "💾 儲存聊天記錄到 Supabase", 
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
            with st.expander("📝 Session 資訊"):
                st.text(f"Session ID: {st.session_state.session_id[:8]}...")
                if st.button("🔄 建立新 Session", use_container_width=True):
                    st.session_state.session_id = str(uuid.uuid4())
                    st.session_state.messages = [{
                        "role": "assistant",
                        "content": "👋 你好！我是 DEI 政策助手。\n\n我可以幫你：\n• 💬 聊天和回答問題\n• 📋 檢查內容是否符合 DEI 政策\n• 💡 提供改善建議\n\n有什麼我可以幫忙的嗎？😊"
                    }]
                    st.session_state.file_processed = set()
                    st.rerun()
    else:
        st.info("ℹ️ Supabase 未設定")
    
    # 檔案上傳
    st.divider()
    uploaded = st.file_uploader(
        "📎 上傳檔案",
        type=['pdf', 'docx', 'txt'],
        help="支援 PDF、Word、TXT 格式"
    )
    
    if uploaded:
        # 使用檔案 ID 防止重複處理
        file_id = f"{uploaded.name}_{uploaded.size}"
        
        if st.button("📤 分析檔案", use_container_width=True):
            if file_id not in st.session_state.file_processed:
                st.session_state.file_processed.add(file_id)
                
                content = read_file(uploaded)
                if content:
                    user_message = f"📎 **{uploaded.name}**\n\n請檢查以下內容：\n\n{content[:10000]}"
                    if len(content) > 10000:
                        user_message += "\n\n*（檔案較長，已截取前 10000 字元）*"

                    add_and_save_message("user", user_message)
                    st.rerun()
    
    # 設定
    st.divider()
    search_enabled = st.toggle("🌐 網路搜尋", value=True, help="AI 會自動搜尋最新資訊")
    st.session_state['search'] = search_enabled
    
    # 清除
    st.divider()
    if st.button("🗑️ 清除對話", use_container_width=True):
        # 如果啟用 Supabase，從資料庫刪除
        if st.session_state.supabase_enabled and supabase_client:
            delete_chat_history(supabase_client, st.session_state.session_id)
        
        st.session_state.messages = [{
            "role": "assistant",
            "content": "對話已清除！😊 有什麼我可以幫你的嗎？"
        }]
        st.session_state.file_processed = set()
        st.rerun()

# 聊天區
client = init_groq()
if not client:
    st.error("❌ 系統初始化失敗")
    st.stop()

# 初始化 Supabase (在這裡也初始化以供聊天使用)
supabase_client = init_supabase()

# 顯示對話歷史
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

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

# 文字輸入
if prompt := st.chat_input("輸入訊息..."):
    add_and_save_message("user", prompt)
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        with st.spinner("思考中..."):
            response = chat(
                client,
                st.session_state.messages,
                st.session_state.get('search', True)
            )
            st.markdown(response)
    
    add_and_save_message("assistant", response)
    st.rerun()