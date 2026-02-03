import pytest

pytest.importorskip("transformers")

from reddit_market_research.text_analyzer.distilbert_analyzer import DistilBERTAnalyzer


def test_distilbert_analyzer_runs():
    try:
        analyzer = DistilBERTAnalyzer({
            'distilbert_model': 'iam-tsr/distilbert-finetuned-sentiment-analysis',
            'distilbert_label_map': {
                'label_0': 'negative',
                'label_1': 'neutral',
                'label_2': 'positive'
            }
        })
    except OSError:
        pytest.skip("DistilBERT model not available locally")

    obj = {
        'title': 'Great product',
        'body': 'This is awesome and helpful.',
        'dataType': 'post'
    }

    result = analyzer.analyze_object(obj)
    assert result['analysis']['category'] == 'Praise'
    assert result['analysis']['sentiment'] in {'positive', 'neutral', 'negative'}
