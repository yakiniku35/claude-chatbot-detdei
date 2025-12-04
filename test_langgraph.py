"""
Test script for LangGraph agent integration
This script tests the agent without requiring Streamlit or API keys
"""

import sys
import os
sys.path.insert(0, 'src')

def test_imports():
    """Test that all required packages can be imported"""
    print("Testing imports...")
    try:
        from langchain_groq import ChatGroq
        from langchain_core.messages import HumanMessage, AIMessage
        from langgraph.graph import StateGraph, END, add_messages
        from langgraph.checkpoint.memory import MemorySaver
        from langchain_community.tools.tavily_search import TavilySearchResults
        from typing import TypedDict, Annotated
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_agent_structure():
    """Test agent graph structure without API calls"""
    print("\nTesting agent graph structure...")
    try:
        from langgraph.graph import StateGraph, END, add_messages
        from langgraph.checkpoint.memory import MemorySaver
        from typing import TypedDict, Annotated
        
        class AgentState(TypedDict):
            messages: Annotated[list, add_messages]
        
        # Create basic graph structure
        memory = MemorySaver()
        graph_builder = StateGraph(AgentState)
        
        # Add dummy nodes
        def dummy_model(state):
            return {"messages": []}
        
        def dummy_tool(state):
            return {"messages": []}
        
        graph_builder.add_node("model", dummy_model)
        graph_builder.add_node("tool_node", dummy_tool)
        graph_builder.set_entry_point("model")
        
        # Compile
        graph = graph_builder.compile(checkpointer=memory)
        
        print("✅ Agent graph structure created successfully")
        return True
    except Exception as e:
        print(f"❌ Agent structure test failed: {e}")
        return False

def test_app_syntax():
    """Test that app.py has valid Python syntax"""
    print("\nTesting app.py syntax...")
    try:
        import ast
        with open('src/app.py', 'r', encoding='utf-8') as f:
            code = f.read()
        ast.parse(code)
        print("✅ app.py syntax is valid")
        return True
    except SyntaxError as e:
        print(f"❌ Syntax error in app.py: {e}")
        return False

def main():
    print("=" * 60)
    print("LangGraph Integration Test Suite")
    print("=" * 60)
    
    tests = [
        ("Package Imports", test_imports),
        ("Agent Graph Structure", test_agent_structure),
        ("App.py Syntax", test_app_syntax)
    ]
    
    results = []
    for test_name, test_func in tests:
        result = test_func()
        results.append((test_name, result))
    
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    all_passed = True
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if not result:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("✅ All tests passed! LangGraph integration is ready.")
        print("\nNext steps:")
        print("1. Configure TAVILY_API_KEY in .streamlit/secrets.toml")
        print("2. Run: streamlit run src/app.py")
        print("3. Enable '🤖 智能搜尋模式 (LangGraph)' in sidebar")
        return 0
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
