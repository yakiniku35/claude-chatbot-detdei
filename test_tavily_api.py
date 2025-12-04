"""
Test Tavily API connectivity and functionality
"""

import os

def test_tavily_connection():
    """Test that Tavily API is working"""
    print("Testing Tavily API connection...")
    
    try:
        # Load API key from secrets
        api_key = None
        try:
            from pathlib import Path
            secrets_path = Path(".streamlit/secrets.toml")
            if secrets_path.exists():
                with open(secrets_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if 'tavily_api_key' in line:
                            api_key = line.split('=')[1].strip().strip('"').strip("'")
                            break
        except Exception as e:
            print(f"Could not load from secrets.toml: {e}")
        
        if not api_key:
            api_key = os.environ.get('TAVILY_API_KEY')
        
        if not api_key:
            print("❌ No Tavily API key found")
            return False
        
        print(f"✅ Found API key: {api_key[:10]}...")
        
        # Test with TavilySearchResults
        from langchain_community.tools.tavily_search import TavilySearchResults
        
        os.environ['TAVILY_API_KEY'] = api_key
        search = TavilySearchResults(max_results=2)
        
        print("\nTesting search query: 'DEI policy trends 2024'...")
        results = search.invoke("DEI policy trends 2024")
        
        print(f"\n✅ Search successful! Got {len(results)} results")
        
        # Display results
        for i, result in enumerate(results, 1):
            print(f"\nResult {i}:")
            print(f"  URL: {result.get('url', 'N/A')}")
            print(f"  Content: {result.get('content', 'N/A')[:150]}...")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Tavily API test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=" * 70)
    print("Tavily API Connectivity Test")
    print("=" * 70)
    
    success = test_tavily_connection()
    
    print("\n" + "=" * 70)
    if success:
        print("✅ Tavily API is working correctly!")
        print("\nThe integration is ready to use in the chatbot.")
    else:
        print("❌ Tavily API test failed.")
        print("\nPlease check:")
        print("1. API key is valid at https://tavily.com/dashboard")
        print("2. You have remaining quota")
        print("3. Internet connection is working")
    print("=" * 70)
    
    return 0 if success else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
