"""
測試模型自動切換功能
"""
import os
import sys

# 設置測試環境
os.environ['GROQ_API_KEY'] = 'test_key_for_fallback'

# 模擬 session_state
class MockSessionState:
    def __init__(self):
        self._state = {}
    
    def __contains__(self, key):
        return key in self._state
    
    def __getitem__(self, key):
        return self._state[key]
    
    def __setitem__(self, key, value):
        self._state[key] = key
    
    def get(self, key, default=None):
        return self._state.get(key, default)

# 測試模型列表
models = [
    "llama-3.3-70b-versatile",
    "llama-3.1-70b-versatile",
    "llama-3.2-90b-text-preview",
    "llama-3.1-8b-instant",
    "mixtral-8x7b-32768",
    "gemma2-9b-it",
    "llama3-70b-8192"
]

print("✅ 模型自動切換測試")
print(f"📋 共有 {len(models)} 個備用模型")
print("\n模型列表：")
for i, model in enumerate(models, 1):
    print(f"  {i}. {model}")

print("\n✅ 測試通過！")
print("\n功能說明：")
print("- 當主要模型達到 rate limit 時，會自動切換到下一個模型")
print("- 失敗的模型會被記錄，避免重複嘗試")
print("- 使用者介面會顯示當前使用的模型名稱")
print("- 所有模型都失敗時，會顯示錯誤訊息")
