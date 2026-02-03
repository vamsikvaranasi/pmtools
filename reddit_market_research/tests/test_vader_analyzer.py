import pytest

from reddit_market_research.text_analyzer.vader_analyzer import VADERAnalyzer


pytest.importorskip("vaderSentiment")
pytest.importorskip("textblob")


def test_vader_analyzer_categories_and_sentiment():
    analyzer = VADERAnalyzer()

    question = {
        'title': 'How do I configure this?',
        'body': 'Any setup tips would help.',
        'dataType': 'post'
    }
    result = analyzer.analyze_object(question)
    assert result['analysis']['category'] == 'Question'

    suggestion = {
        'title': 'Feature request',
        'body': 'You should add dark mode support.',
        'dataType': 'post'
    }
    result = analyzer.analyze_object(suggestion)
    assert result['analysis']['category'] == 'Suggestion'

    complaint = {
        'title': 'App keeps crashing',
        'body': 'The app is slow and crashes often.',
        'dataType': 'post'
    }
    result = analyzer.analyze_object(complaint)
    assert result['analysis']['category'] == 'Complaint'
    assert result['analysis']['subcategory'] in {'performance', 'bug'}

    praise = {
        'title': 'Love this tool',
        'body': 'It is amazing and super helpful.',
        'dataType': 'post'
    }
    result = analyzer.analyze_object(praise)
    assert result['analysis']['sentiment'] == 'positive'
    assert result['analysis']['category'] == 'Praise'
