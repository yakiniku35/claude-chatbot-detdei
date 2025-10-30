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
        with open('prompts.json', 'r', encoding='utf-8') as f:
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
        "content": "👋 你好！我是 DEI 政策助手。\n\n我可以幫你：\n• 💬 聊天和回答問題\n• 📋 檢查內容是否符合 DEI 政策\n• 💡 提供改善建議\n\n有什麼我可以幫忙的嗎？😊"
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
    if 'groq_api_key' in st.secrets:
        api_key = st.secrets['groq_api_key']
    elif 'GROQ_API_KEY' in os.environ:
        api_key = os.environ.get('GROQ_API_KEY')
    
    if api_key:
        return Groq(api_key=api_key)
    return None

# 初始化 Supabase
def init_supabase():
    if not SUPABASE_AVAILABLE:
        # Supabase client not installed in environment
        return None
    try:
        if 'supabase_url' in st.secrets and 'supabase_key' in st.secrets:
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
    except Exception as e:
        return None

# 網路搜尋
def search_web(query):
    try:
        with DDGS() as ddgs:
            return list(ddgs.text(query, max_results=3))
    except:
        return []

def should_search(text):
    keywords = ["最新", "近期", "現在", "查詢", "搜尋", "2024", "2025", "案例", "趨勢", "統計", "研究"]
    return any(k in text.lower() for k in keywords)

# 判斷使用者是否要求進行 DEI 分析
def is_analysis_request(text):
    """
    判斷使用者訊息是否為 DEI 政策分析請求
    Returns: True if requesting analysis, False for casual conversation
    """
    analysis_keywords = [
        "檢查", "分析", "評估", "審查", "違反", "符合", "遵守", "等級",
        "dei", "政策", "歧視", "刻板印象", "排他", "冒犯", "不當",
        "請幫我看", "幫我確認", "這樣可以嗎", "有問題嗎", "有沒有違反",
        "check", "analyze", "review", "violate", "comply", "policy"
    ]
    
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in analysis_keywords)

# AI 對話
def chat(client, messages, use_search=True):
    search_context = ""
    last_msg = next((m for m in reversed(messages) if m["role"] == "user"), None)
    
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
    executive_orders_text = ""
    if prompts_data.get('executive_orders'):
        executive_orders_text = "\n\n📋 **參考政策：**\n"
        for order in prompts_data['executive_orders']:
            executive_orders_text += f"• **{order.get('title', '')}**: {order.get('description', '')}\n"
    # 從 prompts.json 讀取 document.policies 與 administration（如果存在）並摘要化
    policies_text = ""
    doc = prompts_data.get('document')
    # 支援 document 為物件或單元素陣列
    if doc:
        if isinstance(doc, list) and len(doc) > 0:
            doc = doc[0]
        if isinstance(doc, dict):
            policies = doc.get('policies') or doc.get('policy')
            if policies and isinstance(policies, dict):
                policies_text = "\n\n📚 **政策摘要：**\n"
                for key, p in policies.items():
                    title = p.get('title') or key
                    summary = p.get('summary', '')
                    actions = p.get('actions', [])
                    policies_text += f"**{title}**: {summary}\n"
                    if actions:
                        policies_text += "  - 動作: " + "; ".join(actions[:3]) + ("...\n" if len(actions) > 3 else "\n")
            admin = doc.get('administration')
            if admin and isinstance(admin, dict):
                policies_text += "\n🏛️ **管理團隊：**\n"
                president = admin.get('president')
                term = admin.get('term')
                if president:
                    policies_text += f"- 主席/總統: {president}\n"
                if term:
                    policies_text += f"- 任期: {term}\n"
    
    # 根據使用者意圖選擇不同的系統提示
    if requesting_analysis:
        # 分析模式：專業的 DEI 政策檢查
        system = f"""你是一位專業的政治與公共政策分析助理，請根據以下資料撰寫或分析相關內容。以下是背景說明：

美國總統唐納．川普於 2025年1月20日至21日 期間簽署了一系列行政命令，核心目標是 逆轉拜登政府時期的多元化（DEI）、性別政策與能源政策，全面恢復以「個人能力（merit-based）」與「自由市場原則」為核心的政策方向。

以下為三項主要行政命令摘要：

1️⃣ Ending Radical And Wasteful Government DEI Programs and Preferencing

（終止政府內激進且浪費資源的DEI計劃和優待政策）

廢除拜登政府在聯邦部門推行的 DEI / DEIA 職位與計劃。

要求審查所有政府資助與承包商是否實施身份優待。

恢復以「公平競爭、個人能力與績效」為原則的招聘制度。

強調終止因性別、種族而設置的優待制度。

2️⃣ Ending Illegal Discrimination And Restoring Merit-Based Opportunity

（終止非法歧視與恢復擇優就業機會）

廢除部分前任總統簽署的平權行動（Affirmative Action）行政命令。

禁止聯邦及私營部門推行違法的 DEI 政策。

要求司法部在 120 天內提出強化執法的計畫。

要求教育機構遵守 2023 年最高法院「Students for Fair Admissions v. Harvard」判決，禁止以種族為招生依據。

保留退伍軍人等依法受保護群體的合法優待。

3️⃣ Defending Women From Gender Ideology Extremism And Restoring Biological Truth to the Federal Government

（捍衛女性免受性別意識形態激進影響並恢復生物學真實）

聯邦政府僅承認「男性」與「女性」兩種生物性別。

禁止以「性別認同」取代「生物性別」作為法律或政策依據。

禁止男性進入女性專用空間（如庇護所、監獄等）。

要求撤銷與該命令相抵觸的舊有政策與文件。

要求司法部糾正《Bostock v. Clayton County》判決的錯誤延伸。

4️⃣ Unleashing American Energy

（釋放美國能源）

放寬對石油、天然氣、煤炭、核能等開採的限制。

終止拜登時期的氣候變遷政策與「American Climate Corps」。

取消電動車強制規定與能源補貼，強調市場自由。

支持關鍵礦產生產與能源供應鏈安全。

🎯 總結方向：

這些命令構成川普政府 2025 年的三大政策轉向：

反 DEI、恢復擇優制度（Merit-Based）

強調生物性別二元與傳統性別政策

推動能源自由與去氣候化政策（Anti-Green Agenda）
"""
    else:
        # 對話模式：輕鬆、友善的聊天
        system = f"""你是一位友善、親切的 DEI（Diversity, Equity, and Inclusion）政策助手。

你的個性：
- 輕鬆但專業，不會太過嚴肅
- 樂於與使用者聊天和互動
- 能理解使用者的情境和需求
- 善於用簡單的方式解釋複雜的概念

你的能力：
- 回答關於 DEI 政策的問題
- 提供政策相關的資訊和建議
- 與使用者進行友善的對話
- 當使用者需要時，可以分析內容是否符合 DEI 政策

互動原則：
- 如果使用者只是在聊天或問問題，就自然地回應，**不需要評分或進行正式分析**
- 如果使用者明確要求分析、檢查或評估內容，再進行專業的 DEI 評估並給予等級
- 保持友善、樂於助人的態度
- 使用繁體中文或與使用者語言一致

記住：不是每個對話都需要 DEI 等級評分，大多數時候你只需要像朋友一樣聊天和提供資訊！
{executive_orders_text if not requesting_analysis else ''}{policies_text if not requesting_analysis else ''}
"""
            
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
    if 'groq_api_key' not in st.secrets and 'GROQ_API_KEY' not in os.environ:
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
                    
                    st.session_state.messages.append({
                        "role": "user",
                        "content": user_message
                    })
                    
                    # 儲存到 Supabase
                    if st.session_state.supabase_enabled and supabase_client:
                        save_message_to_supabase(
                            supabase_client,
                            st.session_state.session_id,
                            "user",
                            user_message
                        )
                    
                    st.rerun()
                else:
                    st.error("無法讀取檔案")
    
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

# 文字輸入
if prompt := st.chat_input("輸入訊息..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # 儲存用戶訊息到 Supabase
    if st.session_state.supabase_enabled and supabase_client:
        save_message_to_supabase(
            supabase_client,
            st.session_state.session_id,
            "user",
            prompt
        )
    
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
    
    st.session_state.messages.append({"role": "assistant", "content": response})
    
    # 儲存助手回應到 Supabase
    if st.session_state.supabase_enabled and supabase_client:
        save_message_to_supabase(
            supabase_client,
            st.session_state.session_id,
            "assistant",
            response
        )
    
    st.rerun()