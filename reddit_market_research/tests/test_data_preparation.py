import json
from pathlib import Path

import pytest

from reddit_market_research.data_preparation import DataPreprocessor


def _make_base_object(data_type: str) -> dict:
    base = {
        'id': '1',
        'url': 'http://example.com/post/1',
        'communityName': 'r/test',
        'body': 'word ' * 120,
        'dataType': data_type,
        'createdAt': '2024-01-01T00:00:00Z',
        'upVotes': 5
    }
    if data_type == 'post':
        base['title'] = 'Test title'
    if data_type == 'comment':
        base['postId'] = 'post_1'
        base['parentId'] = 'parent_1'
    return base


def test_filters_low_upvotes(monkeypatch, tmp_path: Path):
    monkeypatch.setattr('reddit_market_research.data_preparation.detect', lambda _: 'en')
    input_file = tmp_path / 'input.json'
    input_file.write_text('[]', encoding='utf-8')

    processor = DataPreprocessor(input_file, tmp_path / 'out')
    processor.min_upvotes = 3
    obj = _make_base_object('post')
    obj['upVotes'] = 2

    reduced = processor.reduce_object(obj)

    assert reduced is None
    assert processor.stats['upvotes_filtered'] == 1


def test_filters_low_word_count(monkeypatch, tmp_path: Path):
    monkeypatch.setattr('reddit_market_research.data_preparation.detect', lambda _: 'en')
    input_file = tmp_path / 'input.json'
    input_file.write_text('[]', encoding='utf-8')

    processor = DataPreprocessor(input_file, tmp_path / 'out')
    processor.min_word_count = 100
    obj = _make_base_object('comment')
    obj['body'] = 'too short'

    reduced = processor.reduce_object(obj)

    assert reduced is None
    assert processor.stats['word_count_filtered'] == 1


def test_normalizes_text_fields(monkeypatch, tmp_path: Path):
    monkeypatch.setattr('reddit_market_research.data_preparation.detect', lambda _: 'en')
    input_file = tmp_path / 'input.json'
    input_file.write_text('[]', encoding='utf-8')

    processor = DataPreprocessor(input_file, tmp_path / 'out')
    obj = _make_base_object('post')
    obj['title'] = 'Check [link](http://example.com) now'
    obj['body'] = 'Visit https://example.com   for more. ' + ('word ' * 120)

    reduced = processor.reduce_object(obj)

    assert reduced is not None
    assert 'http' not in reduced['title']
    assert 'http' not in reduced['body']
    assert '  ' not in reduced['body']
