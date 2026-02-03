"""
Toy Analyzer

Fast rule-based analysis for testing and quick previews.
"""

import re
import time
from typing import Dict, Any, List
from .base_analyzer import BaseAnalyzer


class ToyAnalyzer(BaseAnalyzer):
    """Rule-based analyzer for fast analysis."""

    # Sentiment keywords
    POSITIVE_WORDS = {
        'love', 'great', 'amazing', 'awesome', 'thanks', 'helpful',
        'excellent', 'perfect', 'fantastic', 'wonderful', 'brilliant'
    }

    NEGATIVE_WORDS = {
        'bug', 'problem', 'issue', 'hate', 'terrible', 'worst',
        'frustrat', 'crash', 'error', 'broken', 'fail'
    }

    # Question patterns
    QUESTION_WORDS = {'how', 'can', 'what', 'why', 'when', 'where', 'who', 'is', 'are', 'do', 'does'}
    SUGGESTION_PATTERNS = {'should add', 'would be great', 'i wish', 'please add', 'feature request'}
    COMPARISON_PATTERNS = {' vs ', ' versus ', ' compared to ', ' better than ', ' worse than ', ' alternative '}

    def analyze_object(self, obj: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a single object with rule-based methods."""
        start_time = time.time()
        
        text = self._get_text(obj)
        if not text:
            analysis = {
                'sentiment': 'neutral',  # Default for empty text
                'category': 'Statement',
                'confidence': 0.0,
                'processing_time_ms': 0.0
            }
            return self._add_analysis_metadata(obj, analysis)

        # Sentiment analysis
        sentiment = self._analyze_sentiment(text)

        # Category analysis
        category = self._analyze_category(text, obj.get('dataType', 'post'))

        processing_time_ms = (time.time() - start_time) * 1000

        analysis = {
            'sentiment': sentiment,
            'category': category,
            'confidence': 0.7,  # Fixed confidence for toy mode
            'processing_time_ms': round(processing_time_ms, 3)
        }

        return self._add_analysis_metadata(obj, analysis)

    def analyze_batch(self, objects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze multiple objects."""
        return [self.analyze_object(obj) for obj in objects]

    def _get_text(self, obj: Dict[str, Any]) -> str:
        """Extract text content from object."""
        text_parts = []
        if 'title' in obj and obj['title']:
            text_parts.append(obj['title'])
        if 'body' in obj and obj['body']:
            text_parts.append(obj['body'])
        return ' '.join(text_parts).lower()

    def _analyze_sentiment(self, text: str) -> str:
        """Simple keyword-based sentiment analysis."""
        positive_count = sum(1 for word in self.POSITIVE_WORDS if word in text)
        negative_count = sum(1 for word in self.NEGATIVE_WORDS if word in text)

        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        else:
            return 'neutral'

    def _analyze_category(self, text: str, data_type: str) -> str:
        """Rule-based content categorization."""
        # Question detection
        if self._detect_question(text):
            return 'Question'

        # Answer detection (comments only)
        if data_type == 'comment' and self._detect_answer(text):
            return 'Answer'

        # Suggestion / feature request
        if any(pattern in text for pattern in self.SUGGESTION_PATTERNS):
            return 'Suggestion'

        # Comparison
        if any(pattern in text for pattern in self.COMPARISON_PATTERNS):
            return 'Comparison'

        # Praise detection
        if any(word in text for word in self.POSITIVE_WORDS):
            if data_type == 'comment':
                # Check for action verbs in comments (sharing solutions)
                action_verbs = {'built', 'created', 'made', 'developed', 'fixed', 'solved'}
                if any(verb in text for verb in action_verbs):
                    return 'Sharing'
                else:
                    return 'Praise'
            else:
                return 'Praise'

        # Complaint detection
        if any(word in text for word in self.NEGATIVE_WORDS):
            return 'Complaint'

        if data_type == 'comment':
            if any(word in text for word in {'agree', 'yes', 'true', 'correct'}):
                return 'Agreement'
            if any(word in text for word in {'disagree', 'no', 'wrong'}):
                return 'Disagreement'

        # Default
        return 'Statement'

    def _detect_question(self, text: str) -> bool:
        """Detect if text contains a question."""
        # Check for question mark
        if '?' in text:
            return True

        # Check for question words
        words = set(text.split())
        if any(qword in words for qword in self.QUESTION_WORDS):
            return True

        return False

    def _detect_answer(self, text: str) -> bool:
        return any(phrase in text for phrase in {'try ', 'you can', 'solution', 'fixed', 'works for me'})
