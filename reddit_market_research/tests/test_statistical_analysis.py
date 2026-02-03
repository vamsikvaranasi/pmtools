import json
from pathlib import Path

from reddit_market_research.statistical_analysis import StatisticsCalculator


def test_file_stats_include_category_counts(tmp_path: Path):
    enriched_dir = tmp_path / 'enriched'
    enriched_dir.mkdir()
    enriched_file = enriched_dir / 'sample_enriched.json'

    data = [
        {
            'id': '1',
            'url': 'u1',
            'title': 'Great tool',
            'communityName': 'r/test',
            'body': 'Love it',
            'dataType': 'post',
            'createdAt': '2024-01-01T00:00:00Z',
            'upVotes': 5,
            'analysis': {
                'sentiment': 'positive',
                'category': 'Praise',
                'confidence': 0.9,
                'analysis_level': 'nlp',
                'processed_at': '2024-01-01T00:00:00Z'
            }
        },
        {
            'id': '2',
            'url': 'u2',
            'title': 'How do I install?',
            'communityName': 'r/test',
            'body': 'Need help',
            'dataType': 'post',
            'createdAt': '2024-01-01T00:00:00Z',
            'upVotes': 3,
            'analysis': {
                'sentiment': 'neutral',
                'category': 'Question',
                'confidence': 0.6,
                'analysis_level': 'nlp',
                'processed_at': '2024-01-01T00:00:00Z'
            }
        }
    ]

    enriched_file.write_text(json.dumps(data), encoding='utf-8')

    calculator = StatisticsCalculator(enriched_dir, tmp_path / 'out')
    stats = calculator._calculate_file_stats(enriched_file)

    assert stats.questions == 1
    assert stats.praise == 1
    category_counts = json.loads(stats.category_counts_json)
    assert category_counts['Praise'] == 1
    assert category_counts['Question'] == 1
