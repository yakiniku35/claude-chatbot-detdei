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
            text = "\n".join([p.extract_text() for p in pdf.pages])
            return text if text.strip() else None
        elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = docx.Document(io.BytesIO(file_bytes))
            text = "\n".join([p.text for p in doc.paragraphs])
            return text if text.strip() else None
        elif file.type == "text/plain":
            return file_bytes.decode("utf-8")
        return None
    except Exception as e:
        return f"讀取錯誤：{str(e)}"

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
    
    # 判斷是否需要搜尋
    if use_search and last_msg and should_search(last_msg["content"]):
        results = search_web(last_msg["content"][:100])
        if results:
            search_context = "\n\n參考網路資訊：\n"
            for r in results[:2]:
                search_context += f"• {r.get('title', '')}: {r.get('body', '')[:100]}...\n"
    
    system_prompt = """你是 DEI (Diversity, Equity, and Inclusion) 政策檢查助手。

你的任務：
1. 檢查內容是否違反 DEI 政策（歧視、刻板印象、排他性語言、冒犯內容、不當幽默）
2. 回答 DEI 相關問題
3. 提供具體改進建議

回覆要求：
- 使用繁體中文
- 簡潔明瞭
- 有搜尋結果時引用來源
- 保持專業且友善"""
    
    try:
        api_messages = [{"role": "system", "content": system_prompt}]
        
        if search_context:
            api_messages.append({"role": "system", "content": search_context})
        
        for m in messages:
            api_messages.append({"role": m["role"], "content": m["content"]})
        
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=api_messages,
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

# ========== 主介面 ==========

st.title("🤖 DEI 政策助手")

# 側邊欄
with st.sidebar:
    # API 狀態檢查
    if 'groq_api_key' not in st.secrets:
        st.error("⚠️ 系統未設定，請聯絡管理員")
        st.stop()
    
    st.success("✅ 系統就緒")
    st.divider()
    
    # 網路搜尋開關
    search_enabled = st.toggle("🌐 網路搜尋", value=True, help="AI 會自動搜尋最新資訊")
    st.session_state['search'] = search_enabled
    
    st.divider()
    
    # 清除對話
    if st.button("🗑️ 清除對話", use_container_width=True):
        st.session_state.messages = [{
            "role": "assistant",
            "content": "對話已清除！有什麼我可以幫你的嗎？"
        }]
        st.session_state.file_processed = set()
        st.rerun()

# 初始化 client
client = init_groq()
if not client:
    st.error("❌ 系統初始化失敗")
    st.stop()

# 顯示對話歷史
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ========== 輸入區域（文字 + 檔案） ==========

# 使用 columns 讓檔案上傳按鈕在輸入框旁邊
col1, col2 = st.columns([9, 1])

with col2:
    # 檔案上傳器（右側小按鈕）
    uploaded_file = st.file_uploader(
        "上傳",
        type=['pdf', 'docx', 'txt'],
        label_visibility="collapsed",
        key=f"file_{len(st.session_state.messages)}"
    )

with col1:
    # 文字輸入（左側大輸入框）
    user_input = st.chat_input("輸入訊息...")

# 處理檔案上傳（立即自動處理）
if uploaded_file is not None:
    # 使用檔案名稱和大小作為唯一識別
    file_id = f"{uploaded_file.name}_{uploaded_file.size}"
    
    if file_id not in st.session_state.file_processed:
        # 標記已處理
        st.session_state.file_processed.add(file_id)
        
        # 讀取檔案
        content = read_file(uploaded_file)
        
        if content and not content.startswith("讀取錯誤"):
            # 建立使用者訊息（顯示檔案）
            user_message = f"📎 **{uploaded_file.name}**\n\n請檢查以下內容：\n\n{content[:1500]}"
            
            if len(content) > 1500:
                user_message += "\n\n*（檔案較長，已截取前 1500 字元）*"
            
            # 加入對話
            st.session_state.messages.append({"role": "user", "content": user_message})
            
            # 顯示使用者訊息
            with st.chat_message("user"):
                st.markdown(user_message)
            
            # 獲取 AI 回應
            with st.chat_message("assistant"):
                with st.spinner("分析中..."):
                    response = chat(
                        client,
                        st.session_state.messages,
                        st.session_state.get('search', True)
                    )
                    st.markdown(response)
            
            # 儲存 AI 回應
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()
        else:
            st.error(f"無法讀取檔案：{content if content else '檔案可能是空的'}")

# 處理文字輸入
if user_input:
    # 加入使用者訊息
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # 顯示使用者訊息
    with st.chat_message("user"):
        st.markdown(user_input)
    
    # 獲取 AI 回應
    with st.chat_message("assistant"):
        with st.spinner("思考中..."):
            response = chat(
                client,
                st.session_state.messages,
                st.session_state.get('search', True)
            )
            st.markdown(response)
    
    # 儲存 AI 回應
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.rerun()