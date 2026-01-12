"""
Unit tests for the DEI Policy Chatbot
"""

import pytest
from app import (
    detect_language,
    get_language_instruction,
    is_analysis_request,
    should_search,
    load_prompts,
)


class TestLanguageDetection:
    """Test language detection functionality"""

    def test_detect_traditional_chinese(self):
        """Test detection of traditional Chinese"""
        text = "這是繁體中文的測試"
        assert detect_language(text) == "zh-TW"

    def test_detect_simplified_chinese(self):
        """Test detection of simplified Chinese"""
        text = "这是简体中文的测试"
        assert detect_language(text) == "zh-CN"

    def test_detect_english(self):
        """Test detection of English"""
        text = "This is an English test"
        assert detect_language(text) == "en"

    def test_detect_japanese(self):
        """Test detection of Japanese"""
        text = "これは日本語のテストです"
        assert detect_language(text) == "ja"

    def test_detect_korean(self):
        """Test detection of Korean"""
        text = "이것은 한국어 테스트입니다"
        assert detect_language(text) == "ko"


class TestLanguageInstructions:
    """Test language instruction generation"""

    def test_traditional_chinese_instruction(self):
        """Test traditional Chinese instruction"""
        instruction = get_language_instruction("zh-TW")
        assert "Traditional Chinese" in instruction
        assert "繁體中文" in instruction

    def test_simplified_chinese_instruction(self):
        """Test simplified Chinese instruction"""
        instruction = get_language_instruction("zh-CN")
        assert "Simplified Chinese" in instruction
        assert "简体中文" in instruction

    def test_english_instruction(self):
        """Test English instruction"""
        instruction = get_language_instruction("en")
        assert "English" in instruction

    def test_unknown_language_instruction(self):
        """Test default instruction for unknown language"""
        instruction = get_language_instruction("unknown")
        assert "same language" in instruction


class TestAnalysisRequestDetection:
    """Test DEI analysis request detection"""

    def test_chinese_analysis_keywords(self):
        """Test Chinese analysis keywords"""
        assert is_analysis_request("請幫我檢查這個文件") is True
        assert is_analysis_request("分析這段內容") is True
        assert is_analysis_request("評估DEI政策") is True

    def test_english_analysis_keywords(self):
        """Test English analysis keywords"""
        assert is_analysis_request("Please check this document") is True
        assert is_analysis_request("Analyze this content") is True
        assert is_analysis_request("Review the policy") is True

    def test_casual_conversation(self):
        """Test casual conversation is not flagged as analysis"""
        assert is_analysis_request("Hello, how are you?") is False
        assert is_analysis_request("你好嗎？") is False
        assert is_analysis_request("What can you help me with?") is False


class TestSearchTrigger:
    """Test web search trigger detection"""

    def test_chinese_search_keywords(self):
        """Test Chinese search keywords"""
        assert should_search("最新的DEI趨勢") is True
        assert should_search("查詢最近的案例") is True
        assert should_search("搜尋研究") is True

    def test_english_search_keywords(self):
        """Test English search keywords"""
        assert should_search("What are the latest trends?") is True
        assert should_search("Search for recent cases") is True
        assert should_search("Current statistics") is True

    def test_year_keywords(self):
        """Test year-based search triggers"""
        assert should_search("What happened in 2024?") is True
        assert should_search("2025 trends") is True

    def test_no_search_needed(self):
        """Test content that doesn't need search"""
        assert should_search("Hello") is False
        assert should_search("Thank you") is False


class TestPromptsLoading:
    """Test prompts.json loading"""

    def test_load_prompts_success(self):
        """Test successful loading of prompts"""
        prompts = load_prompts()
        assert isinstance(prompts, dict)
        assert "executive_orders" in prompts
        assert isinstance(prompts["executive_orders"], list)

    def test_prompts_structure(self):
        """Test prompts data structure"""
        prompts = load_prompts()
        if prompts.get("executive_orders"):
            order = prompts["executive_orders"][0]
            assert "title" in order
            assert "description" in order


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
