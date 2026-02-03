import csv
import json
from pathlib import Path

from reddit_market_research.visualization import Visualizer


def _write_csv(path: Path, header: list, row: dict):
    with open(path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        writer.writerow(row)


def test_visualizer_parses_category_counts(tmp_path: Path):
    stats_dir = tmp_path / 'stats'
    output_dir = tmp_path / 'output'
    stats_dir.mkdir()
    output_dir.mkdir()

    product_header = [
        'level', 'target_product', 'total_communities', 'total_files', 'total_objects', 'posts', 'comments',
        'positive_posts', 'negative_posts', 'neutral_posts', 'positive_percent', 'questions', 'answers',
        'answer_rate', 'top_pain_point', 'top_solution', 'market_share_percent', 'category_counts_json'
    ]
    community_header = [
        'level', 'community', 'product', 'total_files', 'total_objects', 'posts', 'comments',
        'positive_posts', 'negative_posts', 'neutral_posts', 'positive_percent', 'questions', 'answers',
        'answer_rate', 'praise', 'complaint', 'top_category', 'category_counts_json',
        'issues_count', 'solutions_count', 'top_pain_point', 'top_solution'
    ]

    category_counts = {'Question': 4, 'Praise': 2, 'Complaint': 1}
    _write_csv(
        stats_dir / 'statistics_product.csv',
        product_header,
        {
            'level': 'product',
            'target_product': 'Test',
            'total_communities': 1,
            'total_files': 1,
            'total_objects': 7,
            'posts': 7,
            'comments': 0,
            'positive_posts': 2,
            'negative_posts': 1,
            'neutral_posts': 4,
            'positive_percent': 28.6,
            'questions': 4,
            'answers': 0,
            'answer_rate': 0,
            'top_pain_point': 'n/a',
            'top_solution': 'n/a',
            'market_share_percent': 100,
            'category_counts_json': json.dumps(category_counts)
        }
    )

    _write_csv(
        stats_dir / 'statistics_community.csv',
        community_header,
        {
            'level': 'community',
            'community': 'r/test',
            'product': 'Test',
            'total_files': 1,
            'total_objects': 7,
            'posts': 7,
            'comments': 0,
            'positive_posts': 2,
            'negative_posts': 1,
            'neutral_posts': 4,
            'positive_percent': 28.6,
            'questions': 4,
            'answers': 0,
            'answer_rate': 0,
            'praise': 2,
            'complaint': 1,
            'top_category': 'Question',
            'category_counts_json': json.dumps(category_counts),
            'issues_count': 0,
            'solutions_count': 0,
            'top_pain_point': 'n/a',
            'top_solution': 'n/a'
        }
    )

    mapping_file = tmp_path / 'mapping.json'
    mapping_file.write_text(json.dumps({'mappings': {}}), encoding='utf-8')

    visualizer = Visualizer(stats_dir, output_dir, mapping_file)
    counts = visualizer._parse_category_counts(visualizer.community_stats[0])

    assert counts['Question'] == 4
    assert counts['Praise'] == 2
    assert counts['Complaint'] == 1
