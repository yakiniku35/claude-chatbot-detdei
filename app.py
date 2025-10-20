import streamlit as st
from groq import Groq
import PyPDF2
import docx
import io
import json
from duckduckgo_search import DDGS

# 設定頁面
st.set_page_config(
    page_title="DEI Policy Chatbot",
    page_icon="🤖",
    layout="wide"
)

# 初始化 Groq client
def init_groq():
    if 'groq_api_key' in st.secrets:
        return Groq(api_key=st.secrets['groq_api_key'])
    elif 'api_key' in st.session_state and st.session_state['api_key']:
        return Groq(api_key=st.session_state['api_key'])
    return None

# 初始化對話記錄
if 'messages' not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({
        "role": "assistant",
        "content": "👋 你好！我是 DEI 政策檢查助手。\n\n我可以幫你：\n- 檢查文字或檔案是否違反 DEI 政策\n- 解答 DEI 相關問題\n- 提供改進建議\n\n請直接輸入文字、上傳檔案，或問我任何問題！"
    })

# 網路搜尋功能
def search_web(query, max_results=3):
    """使用 DuckDuckGo 搜尋網路資訊"""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
            return results
    except Exception as e:
        return [{"title": "搜尋失敗", "body": str(e), "href": ""}]

# 判斷是否需要搜尋
def should_search(user_message):
    """判斷使用者的訊息是否需要網路搜尋"""
    search_keywords = [
        "最新", "近期", "現在", "目前", "今年", "2024", "2025",
        "查詢", "搜尋", "找", "search", "新聞", "案例",
        "趨勢", "統計", "研究", "報告"
    ]
    return any(keyword in user_message.lower() for keyword in search_keywords)
def read_file(uploaded_file):
    try:
        if uploaded_file.type == "application/pdf":
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.read()))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
            return text
        elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = docx.Document(io.BytesIO(uploaded_file.read()))
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text
        elif uploaded_file.type == "text/plain":
            return uploaded_file.read().decode("utf-8")
        else:
            return None
    except Exception as e:
        return f"讀取檔案錯誤: {str(e)}"

# 呼叫 AI（支援網路搜尋）
def chat_with_ai(client, messages, custom_policy="", web_search_enabled=True):
    # 檢查最後一條使用者訊息是否需要搜尋
    search_results = None
    last_user_msg = next((msg for msg in reversed(messages) if msg["role"] == "user"), None)
    
    if web_search_enabled and last_user_msg and should_search(last_user_msg["content"]):
        # 執行網路搜尋
        search_query = last_user_msg["content"][:100]  # 限制查詢長度
        search_results = search_web(search_query)
    
    system_prompt = f"""你是一個專業且友善的 DEI (Diversity, Equity, and Inclusion) 政策檢查助手。

你的職責：
1. 檢查文字內容是否違反 DEI 政策
2. 回答 DEI 相關問題
3. 提供具體且實用的改進建議
4. 保持對話自然、友善
5. 當有網路搜尋結果時，結合最新資訊回答

DEI 政策包含：
1. **歧視性語言**：針對種族、性別、年齡、宗教、性取向、殘疾等的歧視
2. **刻板印象**：強化負面或不當的群體刻板印象
3. **排他性語言**：排除或邊緣化特定群體的用語
4. **冒犯性內容**：可能冒犯特定群體的表達
5. **不當幽默**：以特定群體為笑柄的內容

{custom_policy}

回覆原則：
- 用繁體中文回覆
- 如果是檢查請求，提供結構化的分析
- 如果是一般問題，自然對話
- 永遠保持專業且有同理心
- 如果有網路搜尋結果，引用相關資訊並註明來源"""

    try:
        # 準備訊息歷史
        api_messages = [{"role": "system", "content": system_prompt}]
        
        # 如果有搜尋結果，加入上下文
        if search_results:
            search_context = "以下是相關的網路搜尋結果，請參考這些資訊回答：\n\n"
            for i, result in enumerate(search_results, 1):
                search_context += f"{i}. {result.get('title', 'No title')}\n"
                search_context += f"   內容：{result.get('body', 'No content')}\n"
                search_context += f"   來源：{result.get('href', 'No link')}\n\n"
            
            # 將搜尋結果作為系統訊息加入
            api_messages.append({"role": "system", "content": search_context})
        
        for msg in messages:
            api_messages.append({"role": msg["role"], "content": msg["content"]})
        
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=api_messages,
            temperature=0.7,
            max_tokens=2000
        )
        
        ai_response = response.choices[0].message.content
        
        # 如果使用了搜尋，在回應後加上標記
        if search_results:
            ai_response += "\n\n🌐 *此回覆包含網路搜尋資訊*"
        
        return ai_response
    except Exception as e:
        error_msg = str(e)
        if "authentication" in error_msg.lower() or "api key" in error_msg.lower():
            return "❌ API Key 驗證失敗。請聯絡管理員檢查系統設定。"
        elif "rate limit" in error_msg.lower():
            return "⏱️ API 使用額度已達上限，請稍後再試。"
        elif "connection" in error_msg.lower():
            return "🌐 網路連線問題，請稍後再試。"
        else:
            return f"❌ 發生錯誤：{error_msg}"

# 主介面
def main():
    st.title("🤖 DEI 政策檢查聊天機器人")
    st.caption("⚡ Powered by Groq AI - 即時對話與政策檢查")
    
    # 側邊欄
    with st.sidebar:
        st.header("⚙️ 設定")
        
        # API Key 檢查
        if 'groq_api_key' in st.secrets:
            st.success("✅ 系統已就緒")
            st.session_state['api_key'] = st.secrets['groq_api_key']
            
            # API 測試
            if st.button("🔌 測試連線"):
                test_client = Groq(api_key=st.secrets['groq_api_key'])
                try:
                    test_response = test_client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "user", "content": "Hi"}],
                        max_tokens=10
                    )
                    st.success("✅ 連線成功！")
                except Exception as e:
                    st.error(f"❌ 連線失敗: {str(e)}")
        else:
            st.error("⚠️ 請聯絡管理員設定 API Key")
            st.stop()
        
        st.markdown("---")
        
        # 網路搜尋開關
        st.header("🌐 網路搜尋")
        web_search = st.checkbox(
            "啟用網路搜尋",
            value=True,
            help="AI 會在需要時自動搜尋最新資訊"
        )
        st.session_state['web_search_enabled'] = web_search
        
        if web_search:
            st.info("🔍 AI 會自動偵測並搜尋：\n- 最新資訊\n- 案例研究\n- 統計數據")
        
        st.markdown("---")
        
        # 自訂政策
        st.header("📝 自訂政策")
        custom_policy = st.text_area(
            "額外的 DEI 政策規範",
            placeholder="例如：公司特別規定...",
            height=100,
            key="custom_policy"
        )
        
        st.markdown("---")
        
        # 檔案上傳
        st.header("📎 上傳檔案")
        uploaded_file = st.file_uploader(
            "支援 PDF, DOCX, TXT",
            type=['pdf', 'docx', 'txt'],
            help="上傳檔案後會自動分析內容"
        )
        
        if uploaded_file:
            file_content = read_file(uploaded_file)
            if file_content and not file_content.startswith("讀取檔案錯誤"):
                st.success(f"✅ 已讀取：{uploaded_file.name}")
                if st.button("🔍 分析檔案"):
                    # 將檔案內容加入對話
                    user_message = f"請檢查以下檔案內容是否違反 DEI 政策：\n\n{file_content[:2000]}"
                    if len(file_content) > 2000:
                        user_message += f"\n\n（檔案過長，已截取前 2000 字元）"
                    
                    st.session_state.messages.append({
                        "role": "user",
                        "content": f"📄 上傳檔案：{uploaded_file.name}"
                    })
                    
                    # 重新執行以顯示訊息
                    st.rerun()
            else:
                st.error(file_content)
        
        st.markdown("---")
        
        # 使用說明
        st.header("💡 使用說明")
        st.markdown("""
        **檢查文字：**
        - 直接輸入或貼上文字
        
        **檢查檔案：**
        - 上傳 PDF/Word/TXT
        - 點擊「分析檔案」
        
        **詢問問題：**
        - 什麼是 DEI？
        - 如何改進這段文字？
        - 為什麼這樣說不妥？
        
        **搜尋最新資訊：**
        - "最新的 DEI 趨勢是什麼？"
        - "2025 年有哪些 DEI 案例？"
        - "查詢台灣的性別平等政策"
        """)
        
        # 清除對話
        if st.button("🗑️ 清除對話", use_container_width=True):
            st.session_state.messages = []
            st.session_state.messages.append({
                "role": "assistant",
                "content": "對話已清除！有什麼我可以幫你的嗎？"
            })
            st.rerun()
    
    # 主要聊天區域
    client = init_groq()
    
    if not client:
        st.error("❌ 系統初始化失敗")
        st.stop()
    
    # 顯示對話歷史
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # 使用者輸入
    if prompt := st.chat_input("輸入訊息或要檢查的文字..."):
        # 顯示使用者訊息
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # 獲取 AI 回應
        with st.chat_message("assistant"):
            with st.spinner("思考中..."):
                custom_policy = st.session_state.get('custom_policy', '')
                web_search_enabled = st.session_state.get('web_search_enabled', True)
                
                # 如果啟用搜尋且需要搜尋，顯示搜尋狀態
                if web_search_enabled and should_search(prompt):
                    st.info("🔍 正在搜尋網路資訊...")
                
                response = chat_with_ai(
                    client, 
                    st.session_state.messages,
                    custom_policy,
                    web_search_enabled
                )
                st.markdown(response)
        
        # 儲存 AI 回應
        st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()