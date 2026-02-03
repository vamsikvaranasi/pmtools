from reddit_market_research.qa_processor.grouper import QAGrouper


def test_grouper_uses_question_category():
    grouper = QAGrouper()
    enriched = [
        {
            'id': 'post1',
            'dataType': 'post',
            'title': 'How to deploy?',
            'body': 'Any guidance?',
            'upVotes': 5,
            'createdAt': '2024-01-01T00:00:00Z',
            'analysis': {
                'category': 'Question',
                'sentiment': 'neutral',
                'confidence': 0.5
            }
        },
        {
            'id': 'comment1',
            'dataType': 'comment',
            'postId': 'post1',
            'body': 'Try using the CLI deploy command.',
            'upVotes': 3,
            'createdAt': '2024-01-01T00:00:00Z',
            'analysis': {
                'category': 'Answer',
                'sentiment': 'neutral',
                'confidence': 0.6
            }
        }
    ]

    conversations = grouper.group_qa_conversations(enriched)

    assert 'post1' in conversations
    assert len(conversations['post1']['answers']) == 1
