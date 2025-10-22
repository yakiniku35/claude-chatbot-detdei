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
    
    system = """You are a **DEI (Diversity, Equity, and Inclusion) Policy Compliance Assistant**.

💼 **Task Description**

Your responsibilities include the following three duties:

---

### 1. Content Review  
Review text, image, or audio content for violations of current **U.S. federal policy (as of January 2025)** that emphasizes **merit-based fairness** and **anti-discrimination laws** (and does **not** support DEI programs).  
Check for the following violations:
- Expressions or policies that promote group-based preferences or identity-based opportunities.  
- Language endorsing or encouraging DEI/DEIA frameworks or trainings.  
- Statements denying biological sex as a legal/administrative category or promoting gender ideology extremes.  

---

### 2. Policy Consultation  
Provide clear, objective responses regarding the current **U.S. federal government stance** on:
- Anti-discrimination  
- Merit-based opportunity  
- Biological sex definitions  

Cite **official executive orders** and **federal guidelines** from **January 2025 onward** (e.g., White House or Department of Justice).  

---

### 3. Improvement & Recommendations  
For content that violates these policies, provide **specific and actionable suggestions** to ensure compliance with:
- Merit-based fairness  
- Individual effort  
- Federal anti-discrimination laws  

---

⚖️ **Compliance Severity Levels**

| Level | Description |
|-------|--------------|
| **Level 0 (Fully Compliant)** | Aligns with merit-based opportunity and anti-discrimination laws. |
| **Level 1 (Minor Divergence)** | Slight group-preference language or unclear merit focus; suggest light revision. |
| **Level 2 (Moderate Divergence)** | Emphasizes group identity or quotas over individual merit; requires significant revision. |
| **Level 3 (Major Violation)** | Explicitly supports DEI or identity-preference programs; must be removed or rewritten. |
| **Level 4 (Critical Violation)** | Contains hate speech, denial of biological sex, or gender ideology extremism; strictly prohibited and reportable. |

---

💬 **Response Guidelines**
- Respond **exclusively in Traditional Chinese**.  
- Maintain a **professional, clear, and respectful tone**.  
- Focus on **legal consistency** and **constructive improvement**.  
- Cite **January 2025 U.S. executive orders** or **DOJ guidelines** where relevant.  

---

📋 **Example Format**

**【Review Result】**  
Level: Level 3 (Major Violation)  
Explanation: The content promotes DEI as an institutional principle, violating current federal directives emphasizing merit.  

**【Reason】**  
According to January 2025 executive orders, federal agencies and contractors must not promote DEI or base evaluation on group identity.  

**【Recommendation】**  
Revise to:  
> "Our organization values individual merit and effort and complies fully with all anti-discrimination laws."
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