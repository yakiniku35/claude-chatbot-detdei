import streamlit as st
from groq import Groq
import PyPDF2
import docx
import io
import json

# 設定頁面
st.set_page_config(
    page_title="DEI Policy Checker",
    page_icon="🛡️",
    layout="wide"
)

# 初始化 Groq client
def init_groq():
    # 優先從 Streamlit Secrets 讀取（部署時使用）
    if 'groq_api_key' in st.secrets:
        return Groq(api_key=st.secrets['groq_api_key'])
    # 其次從 session state 讀取（使用者輸入）
    elif 'api_key' in st.session_state and st.session_state['api_key']:
        return Groq(api_key=st.session_state['api_key'])
    return None

# 讀取不同檔案格式
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
        st.error(f"讀取檔案時發生錯誤: {str(e)}")
        return None

# DEI 檢查函數
def check_dei_violation(client, text, custom_policy=""):
    system_prompt = f"""你是一個專業的 DEI (Diversity, Equity, and Inclusion) 政策檢查助手。
你的任務是分析文字內容，偵測是否違反 DEI 政策。

DEI 政策包含但不限於：
1. **歧視性語言**：針對種族、性別、年齡、宗教、性取向、殘疾等的歧視
2. **刻板印象**：強化負面或不當的群體刻板印象
3. **排他性語言**：排除或邊緣化特定群體的用語
4. **冒犯性內容**：可能冒犯特定群體的表達
5. **不當幽默**：以特定群體為笑柄的內容

{custom_policy}

請以以下 JSON 格式回覆（必須是有效的 JSON）：
{{
    "violation_detected": true,
    "severity": "high",
    "violations": [
        {{
            "type": "違規類型",
            "content": "具體違規內容",
            "explanation": "為什麼這違反 DEI 政策",
            "suggestion": "改進建議"
        }}
    ],
    "overall_assessment": "整體評估說明"
}}"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",  # Groq 的高效能模型
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"請檢查以下內容是否違反 DEI 政策：\n\n{text}"}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        return response.choices[0].message.content
    except Exception as e:
        error_msg = str(e)
        st.error(f"❌ API 呼叫失敗")
        
        # 詳細錯誤訊息
        if "authentication" in error_msg.lower() or "api key" in error_msg.lower():
            st.warning("🔑 API Key 驗證失敗，請檢查：")
            st.markdown("""
            1. Secrets 中的 API Key 是否正確
            2. API Key 格式：`groq_api_key = "gsk_..."`
            3. 到 https://console.groq.com/keys 確認 Key 有效
            """)
        elif "rate limit" in error_msg.lower():
            st.warning("⏱️ API 使用額度已達上限，請稍後再試")
        elif "connection" in error_msg.lower():
            st.warning("🌐 網路連線問題，請檢查：")
            st.markdown("""
            1. Groq API 服務是否正常（https://status.groq.com）
            2. 稍後再試一次
            """)
        else:
            st.error(f"詳細錯誤：{error_msg}")
        
        return None

# 主介面
def main():
    st.title("🛡️ DEI 政策違規偵測器")
    st.markdown("**檢測文字或檔案內容是否違反多元、公平、共融政策**")
    st.caption("⚡ Powered by Groq (超高速 AI)")
    
    # 側邊欄 - 設定
    with st.sidebar:
        st.header("⚙️ 設定")
        
        # 檢查是否已設定 Secrets（完全隱藏 API Key）
        if 'groq_api_key' in st.secrets:
            st.success("✅ 系統已就緒")
            st.session_state['api_key'] = st.secrets['groq_api_key']
            
            # API 測試按鈕
            if st.button("🔌 測試 API 連線"):
                test_client = Groq(api_key=st.secrets['groq_api_key'])
                try:
                    test_response = test_client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "user", "content": "Hi"}],
                        max_tokens=10
                    )
                    st.success("✅ API 連線成功！")
                except Exception as e:
                    st.error(f"❌ API 連線失敗: {str(e)}")
        else:
            st.error("⚠️ 系統設定錯誤，請聯絡管理員")
            st.stop()
        
        st.markdown("---")
        st.header("📝 自訂政策")
        custom_policy = st.text_area(
            "額外的 DEI 政策規範",
            placeholder="例如：公司特別規定不得使用...",
            height=150
        )
        
        st.markdown("---")
        st.markdown("### 💡 使用說明")
        st.markdown("""
        1. 上傳檔案或輸入文字
        2. 點擊「開始檢查」
        3. 查看詳細分析結果
        
        **🛡️ 支援檢測：**
        - 歧視性語言
        - 刻板印象
        - 排他性用語
        - 冒犯性內容
        - 不當幽默
        """)
    
    # 主要內容區
    client = init_groq()
    
    if not client:
        st.error("❌ 系統初始化失敗，請聯絡管理員")
        st.stop()
    
    # 輸入方式選擇
    input_method = st.radio(
        "選擇輸入方式：",
        ["📄 上傳檔案", "✍️ 直接輸入文字"],
        horizontal=True
    )
    
    text_to_check = ""
    
    if input_method == "📄 上傳檔案":
        uploaded_file = st.file_uploader(
            "上傳檔案 (支援 PDF, DOCX, TXT)",
            type=['pdf', 'docx', 'txt']
        )
        
        if uploaded_file:
            text_to_check = read_file(uploaded_file)
            if text_to_check:
                with st.expander("📖 查看擷取的文字內容"):
                    st.text_area("檔案內容", text_to_check, height=200, disabled=True)
            else:
                st.error("無法讀取檔案或不支援的檔案格式")
    
    else:
        text_to_check = st.text_area(
            "輸入要檢查的文字：",
            height=200,
            placeholder="在此輸入或貼上要檢查的內容..."
        )
    
    # 檢查按鈕
    if st.button("🔍 開始檢查", type="primary", use_container_width=True):
        if not text_to_check or not text_to_check.strip():
            st.warning("請先輸入文字或上傳檔案")
            return
        
        with st.spinner("🤖 AI 正在高速分析中..."):
            result = check_dei_violation(client, text_to_check, custom_policy)
        
        if result:
            try:
                data = json.loads(result)
                
                # 顯示結果
                st.markdown("---")
                st.header("📊 檢測結果")
                
                # 違規狀態
                col1, col2 = st.columns(2)
                with col1:
                    if data.get('violation_detected', False):
                        st.error("❌ 偵測到 DEI 政策違規")
                    else:
                        st.success("✅ 未偵測到 DEI 政策違規")
                
                with col2:
                    severity_colors = {
                        "high": "🔴 高",
                        "medium": "🟡 中",
                        "low": "🟢 低",
                        "none": "⚪ 無"
                    }
                    severity = data.get('severity', 'none')
                    st.metric("嚴重程度", severity_colors.get(severity, severity))
                
                # 違規詳情
                violations = data.get('violations', [])
                if violations:
                    st.subheader("⚠️ 違規項目")
                    for i, violation in enumerate(violations, 1):
                        with st.expander(f"違規 {i}: {violation.get('type', '未知')}", expanded=True):
                            st.markdown(f"**具體內容：** {violation.get('content', 'N/A')}")
                            st.markdown(f"**說明：** {violation.get('explanation', 'N/A')}")
                            st.markdown(f"**建議：** {violation.get('suggestion', 'N/A')}")
                
                # 整體評估
                if 'overall_assessment' in data:
                    st.subheader("📝 整體評估")
                    st.info(data['overall_assessment'])
                
            except json.JSONDecodeError as e:
                st.error(f"解析結果時發生錯誤: {str(e)}")
                with st.expander("查看原始回應"):
                    st.code(result)

if __name__ == "__main__":
    main()