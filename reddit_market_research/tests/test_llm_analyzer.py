"""
Tests for LLM Analyzer with Ollama Text Client integration.
"""

import pytest
from reddit_market_research.text_analyzer import LLMAnalyzer


def test_llm_analyzer_import():
    """Test that LLMAnalyzer can be imported."""
    assert LLMAnalyzer is not None


def test_llm_analyzer_initialization():
    """Test that LLMAnalyzer can be initialized."""
    analyzer = LLMAnalyzer()
    assert analyzer is not None
    assert hasattr(analyzer, 'client')  # Check if client is initialized
    assert hasattr(analyzer, 'analyze_object')  # Check if analyze_object method exists


def test_llm_analyzer_analyze_object():
    """Test the analyze_object method with sample input."""
    analyzer = LLMAnalyzer()
    sample_obj = {
        'title': 'Test Title',
        'body': 'This is a test body text.',
        'dataType': 'post'
    }
    result = analyzer.analyze_object(sample_obj)
    
    # Verify the result has expected fields
    assert 'analysis' in result
    analysis = result['analysis']
    assert 'sentiment' in analysis
    assert 'category' in analysis
    assert 'confidence' in analysis
    assert 'processing_time_ms' in analysis
    
    # Check sentiment values are valid
    assert analysis['sentiment'] in ['positive', 'neutral', 'negative']
    
    # Check confidence is between 0 and 1
    assert 0 <= analysis['confidence'] <= 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
