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

# 初始化
def init_groq():
    if 'groq_api_key' in st.secrets:
        return Groq(api_key=st.secrets['groq_api_key'])
    return None

if 'messages' not in st.session_state:
    st.session_state.messages = [{
        "role": "assistant",
        "content": "👋 你好！我可以幫你檢查文字或檔案是否違反 DEI 政策，也可以回答相關問題。"
    }]

# 讀取檔案
def read_file(file):
    try:
        if file.type == "application/pdf":
            pdf = PyPDF2.PdfReader(io.BytesIO(file.read()))
            return "\n".join([p.extract_text() for p in pdf.pages])
        elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = docx.Document(io.BytesIO(file.read()))
            return "\n".join([p.text for p in doc.paragraphs])
        elif file.type == "text/plain":
            return file.read().decode("utf-8")
    except:
        return None

# 網路搜尋
def search_web(query):
    try:
        with DDGS() as ddgs:
            return list(ddgs.text(query, max_results=3))
    except:
        return []

def should_search(text):
    keywords = ["最新", "近期", "現在", "查詢", "搜尋", "2024", "2025", "案例", "趨勢"]
    return any(k in text for k in keywords)

# AI 對話
def chat(client, messages, use_search=True):
    search_context = ""
    last_msg = next((m for m in reversed(messages) if m["role"] == "user"), None)
    
    if use_search and last_msg and should_search(last_msg["content"]):
        results = search_web(last_msg["content"][:100])
        if results:
            search_context = "\n參考資訊：\n" + "\n".join([
                f"• {r.get('title', '')}: {r.get('body', '')[:100]}" 
                for r in results[:2]
            ])
    
    system = """你是 DEI 政策檢查助手。檢查文字是否有：歧視、刻板印象、排他性語言、冒犯內容。
用繁體中文簡潔回答。有網路資訊時請引用。"""
    
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
        return response.choices[0].message.content + ("\n\n🌐 *含網路搜尋*" if search_context else "")
    except Exception as e:
        return f"❌ 錯誤：{str(e)}"

# 主介面
st.title("🤖 DEI 政策助手")

# 側邊欄
with st.sidebar:
    # API 狀態
    if 'groq_api_key' not in st.secrets:
        st.error("⚠️ 請聯絡管理員")
        st.stop()
    
    st.success("✅ 系統就緒")
    
    # 檔案上傳
    st.divider()
    uploaded = st.file_uploader("📎 上傳檔案", type=['pdf', 'docx', 'txt'])
    if uploaded:
        content = read_file(uploaded)
        if content and st.button("分析", use_container_width=True):
            st.session_state.messages.append({
                "role": "user",
                "content": f"請檢查：\n\n{content[:1500]}"
            })
            st.rerun()
    
    # 設定
    st.divider()
    search_enabled = st.toggle("🌐 網路搜尋", value=True)
    st.session_state['search'] = search_enabled
    
    # 清除
    if st.button("🗑️ 清除對話", use_container_width=True):
        st.session_state.messages = [{
            "role": "assistant",
            "content": "對話已清除！"
        }]
        st.rerun()

# 聊天區
client = init_groq()
if not client:
    st.error("❌ 初始化失敗")
    st.stop()

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("輸入訊息..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        with st.spinner("💭"):
            response = chat(
                client,
                st.session_state.messages,
                st.session_state.get('search', True)
            )
            st.markdown(response)
    
    st.session_state.messages.append({"role": "assistant", "content": response})