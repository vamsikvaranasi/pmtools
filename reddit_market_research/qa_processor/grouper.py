"""
Q&A Grouper Module

Groups questions with their corresponding answers from enriched Reddit data.
"""

from typing import Any, Dict, List, Optional
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class QAGrouper:
    """
    Groups questions with their answers based on postId and analysis categories.
    """

    def __init__(self):
        self.logger = logger

    def group_qa_conversations(self, enriched_objects: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """
        Group enriched objects into Q&A conversations.

        Args:
            enriched_objects: List of enriched Reddit objects with analysis

        Returns:
            Dictionary mapping postId to conversation data
        """
        conversations = {}

        # Separate posts and comments
        posts = [obj for obj in enriched_objects if obj.get('dataType') == 'post']
        comments = [obj for obj in enriched_objects if obj.get('dataType') == 'comment']

        # Create lookup for comments by postId
        comments_by_post = defaultdict(list)
        for comment in comments:
            post_id = comment.get('postId')
            if post_id:
                comments_by_post[post_id].append(comment)

        # Process each post
        for post in posts:
            post_id = post.get('id')
            analysis = post.get('analysis', {})

            # Check if this post is a question or complaint with a question
            if analysis.get('category') == 'Question' or (analysis.get('category') == 'Complaint' and analysis.get('is_question', False)):
                conversation = {
                    'postId': post_id,
                    'question': self._extract_question_data(post),
                    'answers': [],
                    'metadata': {
                        'total_answers': 0,
                        'top_answer_upvotes': 0,
                        'conversation_depth': 0
                    }
                }

                # Find answers for this question
                post_comments = comments_by_post.get(post_id, [])
                answers = []

                for comment in post_comments:
                    comment_analysis = comment.get('analysis', {})
                    if comment_analysis.get('category') == 'Answer':
                        answer_data = self._extract_answer_data(comment)
                        answers.append(answer_data)

                # Sort answers by upvotes (highest first)
                answers.sort(key=lambda x: x.get('upvotes', 0), reverse=True)

                conversation['answers'] = answers
                conversation['metadata']['total_answers'] = len(answers)
                if answers:
                    conversation['metadata']['top_answer_upvotes'] = answers[0].get('upvotes', 0)

                conversations[post_id] = conversation

        self.logger.info(f"Grouped {len(conversations)} Q&A conversations")
        return conversations

    def _extract_question_data(self, post: Dict[str, Any]) -> Dict[str, Any]:
        """Extract relevant question data from a post."""
        return {
            'id': post.get('id'),
            'title': post.get('title', ''),
            'body': post.get('body', ''),
            'upvotes': post.get('upVotes', 0),
            'created_at': post.get('createdAt'),
            'analysis': post.get('analysis', {})
        }

    def _extract_answer_data(self, comment: Dict[str, Any]) -> Dict[str, Any]:
        """Extract relevant answer data from a comment."""
        return {
            'id': comment.get('id'),
            'body': comment.get('body', ''),
            'upvotes': comment.get('upVotes', 0),
            'created_at': comment.get('createdAt'),
            'analysis': comment.get('analysis', {})
        }