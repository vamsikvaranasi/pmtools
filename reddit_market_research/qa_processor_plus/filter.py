"""
InputFilter — Gate Step for Stage 4 Mode A/B/C

Filters QA conversations based on upvotes, word count, sentiment, and categories.
Per PM Decision #3: sentiment filtering uses ['negative', 'neutral']
"""

from typing import List, Dict, Any


class InputFilter:
    """Filters QA conversations according to configured thresholds."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the InputFilter.
        
        Args:
            config: Dictionary with keys:
                - min_upvotes: Minimum upvotes threshold (default: 5)
                - min_word_count: Minimum word count in question (default: 10)
                - sentiment: List of allowed sentiments (default: ['negative', 'neutral'])
                - categories: List of allowed categories (default: ['Question', 'Complaint', 'Suggestion'])
        """
        self.min_upvotes = config.get('min_upvotes', 5)
        self.min_word_count = config.get('min_word_count', 10)
        self.allowed_sentiments = config.get('sentiment', ['negative', 'neutral'])  # PM Decision 3
        self.allowed_categories = config.get('categories', ['Question', 'Complaint', 'Suggestion'])
    
    def filter_objects(self, objects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Apply all filters and return passing objects with filter metadata.
        
        Args:
            objects: List of QA objects to filter (questions or comments)
            
        Returns:
            List of objects that pass all filters, with metadata about which filters passed
        """
        filtered = []
        
        for obj in objects:
            # Initialize filter results
            filter_metadata = {
                'passed_upvotes': False,
                'passed_word_count': False,
                'passed_sentiment': False,
                'passed_category': False,
                'passed_all': False
            }
            
            # Check upvotes
            upvotes = obj.get('upvotes', 0)
            if upvotes >= self.min_upvotes:
                filter_metadata['passed_upvotes'] = True
            
            # Check word count
            text = obj.get('text', '')
            word_count = len(text.split())
            if word_count >= self.min_word_count:
                filter_metadata['passed_word_count'] = True
            
            # Check sentiment
            sentiment = obj.get('sentiment', 'neutral')
            if sentiment in self.allowed_sentiments:
                filter_metadata['passed_sentiment'] = True
            
            # Check category
            category = obj.get('category', 'Question')
            if category in self.allowed_categories:
                filter_metadata['passed_category'] = True
            
            # All filters must pass
            if all([
                filter_metadata['passed_upvotes'],
                filter_metadata['passed_word_count'],
                filter_metadata['passed_sentiment'],
                filter_metadata['passed_category']
            ]):
                filter_metadata['passed_all'] = True
                obj['_filter_metadata'] = filter_metadata
                filtered.append(obj)
        
        return filtered
