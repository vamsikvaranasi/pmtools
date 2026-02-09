"""
Evidence-Preserving Grouper

Groups QA conversations while preserving post_id, post_url, and created_at.
Includes ALL comments (not just Answer category).
"""

from typing import List, Dict, Any


class EvidencePreservingGrouper:
    """Groups conversations while preserving evidence metadata."""
    
    def __init__(self):
        """Initialize the grouper."""
        pass
    
    def group_conversations(self, conversations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Group conversations preserving evidence data.
        
        Each grouped conversation preserves:
        - post_id on question and all comments
        - post_url on question and all comments
        - created_at timestamp
        - All comments (not filtered by category)
        - Original category tags on each comment
        
        Args:
            conversations: List of raw conversation data
            
        Returns:
            Grouped conversations with preserved metadata
        """
        grouped = []
        
        for conv in conversations:
            # Extract question data
            question = conv.get('question', {})
            comments = conv.get('comments', [])
            
            # Ensure all evidence items have post metadata
            grouped_conv = {
                'question': {
                    **question,
                    'post_id': question.get('post_id'),
                    'post_url': question.get('post_url'),
                    'created_at': question.get('created_at')
                },
                'comments': []
            }
            
            # Include ALL comments with preserved metadata
            for comment in comments:
                tagged_comment = {
                    **comment,
                    'post_id': comment.get('post_id', question.get('post_id')),
                    'post_url': comment.get('post_url', question.get('post_url')),
                    'created_at': comment.get('created_at'),
                    'original_category': comment.get('category', 'Comment')  # Preserve original category
                }
                grouped_conv['comments'].append(tagged_comment)
            
            grouped.append(grouped_conv)
        
        return grouped
