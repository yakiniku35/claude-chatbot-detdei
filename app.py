import streamlit as st
from groq import Groq
import PyPDF2
import docx
import io
from duckduckgo_search import DDGS

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
        "content": "👋 你好！我可以幫你檢查文字或檔案是否違反 DEI 政策，也可以回答相關問題。"
    }]

if 'file_processed' not in st.session_state:
    st.session_state.file_processed = set()

# 初始化 Groq
def init_groq():
    if 'groq_api_key' in st.secrets:
        return Groq(api_key=st.secrets['groq_api_key'])
    return None

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
    
    system = """You are a **Smart Content & DEI Policy Assistant**.

💡 **Core Idea**
Your main job is to help review content **only when it’s relevant to DEI, identity, or merit-based policy issues**.  
For all other conversations (chatting, homework, programming, general discussion), just respond naturally without activating DEI checks.

---

### 1. Context Awareness
Before performing any DEI analysis:
1. Check if the content involves:
   - Diversity, equity, inclusion, or DEI/DEIA frameworks  
   - Identity-based preferences or quotas  
   - Gender/biological sex discussions related to policy
2. If **YES**, proceed with full DEI review.  
3. If **NO**, respond naturally in context, ignoring DEI rules.

---

### 2. DEI Content Review (Only if Relevant)
Check for:
- Group-based preferences overriding individual merit  
- Promotion of DEI/DEIA programs or trainings  
- Statements denying biological sex or extreme gender ideology  

---

### 3. Policy Guidance
Explain clearly how content relates to **current U.S. federal law (January 2025 onward)**, focusing on:
- Anti-discrimination laws  
- Merit-based opportunity  
- Legal recognition of biological sex  

Cite official **executive orders or DOJ guidelines** when necessary.

---

### 4. Recommendations
If content violates policy, provide **specific, actionable, and respectful advice** emphasizing:
- Individual merit and effort  
- Equal opportunity  
- Compliance with federal anti-discrimination laws  

---

⚖️ **Compliance Levels (If DEI-Relevant)**

| Level | Description |
|-------|--------------|
| Level 0 | Fully compliant; aligns with merit-based fairness and anti-discrimination laws. |
| Level 1 | Minor divergence; small edits suggested. |
| Level 2 | Moderate divergence; too much focus on identity or quotas. |
| Level 3 | Major violation; promotes DEI or identity-based programs. |
| Level 4 | Critical violation; hate speech, denial of biological sex, or extreme gender ideology. |

---

💬 **Response Guidelines**
- Respond **in Traditional Chinese** when performing DEI review.  
- Keep tone **professional, clear, and respectful**.  
- Focus on **legal accuracy** and **constructive improvement**.  
- Reference **January 2025 U.S. executive orders** or DOJ guidance when relevant.  

---

📋 **Example (DEI-Relevant)**

**【Review Result】**  
Level: Level 3 (Major Violation)  
Explanation: Promotes DEI as a required organizational principle, conflicting with federal merit-based directives.  

**【Reason】**  
January 2025 executive orders prohibit agencies and contractors from promoting DEI or evaluating based on group identity.  

**【Recommendation】**  
Revise to:  
> “Our organization values individual merit and effort and complies fully with all federal anti-discrimination laws.”

---

📋 **Example (Not DEI-Relevant)**

**Response:**  
> “This content doesn’t involve DEI, identity, or policy issues, so no compliance review is needed.”

"""
    
    try:
        msgs = [{"role": "system", "content": system}]
        if search_context:
            msgs.append({"role": "system", "content": search_context})
        msgs.extend([{"role": m["role"], "content": m["content"]} for m in messages])
        
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=msgs,
            temperature=0.7,
            max_tokens=1500
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
    if 'groq_api_key' not in st.secrets:
        st.error("⚠️ 系統未設定，請聯絡管理員")
        st.stop()
    
    st.success("✅ 系統就緒")
    
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
                    user_message = f"📎 **{uploaded.name}**\n\n請檢查以下內容：\n\n{content[:1500]}"
                    if len(content) > 1500:
                        user_message += "\n\n*（檔案較長，已截取前 1500 字元）*"
                    
                    st.session_state.messages.append({
                        "role": "user",
                        "content": user_message
                    })
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
        st.session_state.messages = [{
            "role": "assistant",
            "content": "對話已清除！有什麼我可以幫你的嗎？"
        }]
        st.session_state.file_processed = set()
        st.rerun()

# 聊天區
client = init_groq()
if not client:
    st.error("❌ 系統初始化失敗")
    st.stop()

# 顯示對話歷史
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 文字輸入
if prompt := st.chat_input("輸入訊息..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
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
    st.rerun()