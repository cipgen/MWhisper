"""
Tests for the filler filter module
"""

import pytest
from src.filler_filter import filter_fillers, add_custom_filler


class TestFillerFilter:
    """Test cases for filler word removal"""
    
    def test_russian_fillers(self):
        """Test removal of Russian filler words"""
        # Single filler
        assert filter_fillers("Ээ, привет") == "Привет"
        assert filter_fillers("Мм, да") == "Да"
        
        # Multiple fillers
        text = "Ээ, ну, хм, это интересно"
        result = filter_fillers(text)
        assert "ээ" not in result.lower()
        assert "хм" not in result.lower()
        assert "интересно" in result
    
    def test_english_fillers(self):
        """Test removal of English filler words"""
        assert "uh" not in filter_fillers("Uh, I think so").lower()
        assert "um" not in filter_fillers("Um, yes").lower()
        
        text = "So, like, you know, it's good"
        result = filter_fillers(text)
        assert "good" in result
    
    def test_preserves_punctuation(self):
        """Test that punctuation is preserved correctly"""
        result = filter_fillers("Ээ, это хорошо!")
        assert "хорошо" in result
        assert result.endswith("!")
    
    def test_capitalizes_first_letter(self):
        """Test that first letter is capitalized after filtering"""
        result = filter_fillers("ээ, привет")
        assert result[0].isupper() if result else True
    
    def test_empty_string(self):
        """Test handling of empty string"""
        assert filter_fillers("") == ""
    
    def test_disabled_filter(self):
        """Test that filter can be disabled"""
        text = "Ээ, привет"
        assert filter_fillers(text, enabled=False) == text
    
    def test_no_fillers(self):
        """Test text without fillers"""
        text = "Это нормальное предложение."
        assert filter_fillers(text) == text
    
    def test_german_fillers(self):
        """Test German filler words"""
        assert "äh" not in filter_fillers("Äh, ich denke").lower()
    
    def test_multiple_spaces_cleanup(self):
        """Test that multiple spaces are cleaned up"""
        result = filter_fillers("Ээ    привет")
        assert "  " not in result


class TestCustomFillers:
    """Test custom filler patterns"""
    
    def test_add_custom_pattern(self):
        """Test adding custom filler pattern"""
        add_custom_filler(r'\btest_word\b')
        result = filter_fillers("I test_word think so")
        assert "test_word" not in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
