#!/usr/bin/env python3
"""
Tavily Search 功能測試腳本

用途：
1. 測試 Tavily API 連線
2. 驗證搜尋功能
3. 檢查 LangGraph agent 整合

使用方式：
    export TAVILY_API_KEY="tvly-your-key"
    python3 test_tavily.py
"""

import os
import sys
from datetime import datetime

def test_imports():
    """測試必要套件是否已安裝"""
    print("=" * 60)
    print("🔍 測試 1: 檢查套件安裝")
    print("=" * 60)
    
    try:
        from langchain_tavily import TavilySearch
        print("✅ langchain_tavily - 已安裝")
    except ImportError as e:
        print(f"❌ langchain_tavily - 未安裝: {e}")
        return False
    
    try:
        from langgraph.graph import StateGraph
        print("✅ langgraph - 已安裝")
    except ImportError as e:
        print(f"❌ langgraph - 未安裝: {e}")
        return False
    
    try:
        from langchain_groq import ChatGroq
        print("✅ langchain_groq - 已安裝")
    except ImportError as e:
        print(f"❌ langchain_groq - 未安裝: {e}")
        return False
    
    print()
    return True

def test_api_key():
    """檢查 API key 設定"""
    print("=" * 60)
    print("🔑 測試 2: 檢查 API Key 設定")
    print("=" * 60)
    
    tavily_key = os.environ.get('TAVILY_API_KEY')
    groq_key = os.environ.get('GROQ_API_KEY')
    
    if tavily_key:
        print(f"✅ TAVILY_API_KEY - 已設定 ({tavily_key[:10]}...)")
    else:
        print("⚠️  TAVILY_API_KEY - 未設定（搜尋功能將無法使用）")
    
    if groq_key:
        print(f"✅ GROQ_API_KEY - 已設定 ({groq_key[:10]}...)")
    else:
        print("❌ GROQ_API_KEY - 未設定（必需）")
        return False
    
    print()
    return bool(tavily_key)

def test_tavily_search():
    """測試 Tavily 搜尋功能"""
    print("=" * 60)
    print("🔎 測試 3: Tavily 搜尋功能")
    print("=" * 60)
    
    try:
        from langchain_tavily import TavilySearch
        
        if not os.environ.get('TAVILY_API_KEY'):
            print("⚠️  跳過：TAVILY_API_KEY 未設定")
            return False
        
        search = TavilySearch(max_results=2)
        query = "DEI policy trends 2024"
        
        print(f"查詢: {query}")
        print("執行搜尋...")
        
        results = search.invoke({"query": query})
        
        if results:
            print(f"✅ 搜尋成功！找到 {len(str(results))} 字元的結果")
            print(f"結果預覽: {str(results)[:200]}...")
        else:
            print("⚠️  搜尋返回空結果")
        
        print()
        return True
        
    except Exception as e:
        print(f"❌ 搜尋失敗: {str(e)}")
        print()
        return False

def test_langchain_groq():
    """測試 ChatGroq 初始化"""
    print("=" * 60)
    print("🤖 測試 4: ChatGroq LLM 初始化")
    print("=" * 60)
    
    try:
        from langchain_groq import ChatGroq
        
        if not os.environ.get('GROQ_API_KEY'):
            print("❌ GROQ_API_KEY 未設定")
            return False
        
        llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0.7
        )
        
        print(f"✅ LLM 初始化成功")
        print(f"   模型: {llm.model_name}")
        print(f"   溫度: {llm.temperature}")
        print()
        return True
        
    except Exception as e:
        print(f"❌ LLM 初始化失敗: {str(e)}")
        print()
        return False

def test_agent_integration():
    """測試完整的 LangGraph Agent"""
    print("=" * 60)
    print("🎯 測試 5: LangGraph Agent 整合")
    print("=" * 60)
    
    try:
        from langchain_tavily import TavilySearch
        from langchain_groq import ChatGroq
        from langgraph.graph import StateGraph, END, add_messages
        from langgraph.checkpoint.memory import MemorySaver
        from typing import TypedDict, Annotated
        from langchain_core.messages import HumanMessage
        
        # 檢查必要的 API keys
        if not os.environ.get('GROQ_API_KEY'):
            print("❌ 跳過：GROQ_API_KEY 未設定")
            return False
        
        if not os.environ.get('TAVILY_API_KEY'):
            print("⚠️  跳過：TAVILY_API_KEY 未設定（將使用無搜尋模式）")
            search_tool = None
        else:
            search_tool = TavilySearch(max_results=2)
        
        # 初始化 LLM
        llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.7)
        
        # 定義狀態
        class AgentState(TypedDict):
            messages: Annotated[list, add_messages]
        
        # 建立簡單的 graph
        graph_builder = StateGraph(AgentState)
        
        def model_node(state):
            if search_tool:
                llm_with_tools = llm.bind_tools(tools=[search_tool])
                result = llm_with_tools.invoke(state["messages"])
            else:
                result = llm.invoke(state["messages"])
            return {"messages": [result]}
        
        graph_builder.add_node("model", model_node)
        graph_builder.set_entry_point("model")
        graph_builder.add_edge("model", END)
        
        memory = MemorySaver()
        graph = graph_builder.compile(checkpointer=memory)
        
        print("✅ Agent graph 編譯成功")
        
        # 測試簡單對話
        print("測試簡單查詢...")
        config = {"configurable": {"thread_id": "test_001"}}
        result = graph.invoke(
            {"messages": [HumanMessage(content="Hello, what is DEI?")]},
            config=config
        )
        
        if result and "messages" in result:
            print(f"✅ Agent 回應成功")
            last_message = result["messages"][-1]
            print(f"   回應預覽: {str(last_message.content)[:100]}...")
        else:
            print("⚠️  Agent 回應格式異常")
        
        print()
        return True
        
    except Exception as e:
        print(f"❌ Agent 整合測試失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        print()
        return False

def main():
    """執行所有測試"""
    print()
    print("🧪 Tavily Search 功能測試")
    print(f"⏰ 測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    results = []
    
    # 測試 1: 套件安裝
    results.append(("套件安裝", test_imports()))
    
    # 測試 2: API Key
    results.append(("API Key 設定", test_api_key()))
    
    # 測試 3: Tavily 搜尋
    if os.environ.get('TAVILY_API_KEY'):
        results.append(("Tavily 搜尋", test_tavily_search()))
    
    # 測試 4: ChatGroq
    results.append(("ChatGroq LLM", test_langchain_groq()))
    
    # 測試 5: Agent 整合
    results.append(("Agent 整合", test_agent_integration()))
    
    # 總結
    print("=" * 60)
    print("📊 測試總結")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print()
    print(f"總計: {passed}/{total} 測試通過")
    
    if passed == total:
        print()
        print("🎉 所有測試通過！Tavily 搜尋功能已就緒。")
        print()
        print("下一步：")
        print("1. 在 .streamlit/secrets.toml 設定 tavily_api_key")
        print("2. 執行 streamlit run src/app.py")
        print("3. 在側邊欄啟用「智能搜尋模式」")
        return 0
    else:
        print()
        print("⚠️  部分測試失敗。請檢查錯誤訊息並修正。")
        return 1

if __name__ == "__main__":
    sys.exit(main())
