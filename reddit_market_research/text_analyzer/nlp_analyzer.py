"""
NLP Analyzer

Balanced analysis using NLP libraries (VADER, TextBlob).
"""

import re
import time
from typing import Dict, Any, List, Optional
from .base_analyzer import BaseAnalyzer

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    from textblob import TextBlob
    VADER_AVAILABLE = True
except ImportError:
    VADER_AVAILABLE = False


class NLPAnalyzer(BaseAnalyzer):
    """NLP-based analyzer using VADER and TextBlob."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        if not VADER_AVAILABLE:
            raise ImportError("VADER and TextBlob required for NLP analyzer")

        self.vader = SentimentIntensityAnalyzer()

        # Question patterns
        self.question_words = {
            'how', 'can', 'what', 'why', 'when', 'where', 'who',
            'is', 'are', 'do', 'does', 'did', 'should', 'would', 'could'
        }

    def analyze_object(self, obj: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze object using NLP libraries."""
        start_time = time.time()
        
        text = self._get_text(obj)
        if not text:
            analysis = {
                'sentiment': 'neutral',
                'category': 'Statement',
                'confidence': 0.5,
                'processing_time_ms': 0.0
            }
            return self._add_analysis_metadata(obj, analysis)

        # Sentiment analysis
        sentiment, confidence = self._analyze_sentiment(text)

        # Category analysis
        category = self._analyze_category(text, obj.get('dataType', 'post'))

        processing_time_ms = (time.time() - start_time) * 1000

        analysis = {
            'sentiment': sentiment,
            'category': category,
            'confidence': confidence,
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
        return ' '.join(text_parts)

    def _analyze_sentiment(self, text: str) -> tuple[str, float]:
        """Analyze sentiment using VADER."""
        scores = self.vader.polarity_scores(text)
        compound = scores['compound']

        if compound >= 0.05:
            sentiment = 'positive'
        elif compound <= -0.05:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'

        confidence = abs(compound)
        return sentiment, confidence

    def _analyze_category(self, text: str, data_type: str) -> str:
        """Categorize content using NLP patterns."""
        blob = TextBlob(text)

        # Question detection
        if self._detect_question(text):
            return 'Question'

        # Sentiment-based categorization
        polarity = blob.sentiment.polarity

        if polarity > 0.1:
            if data_type == 'comment':
                # Check for solution patterns in comments
                solution_patterns = [
                    r'i (used|try|recommend)',
                    r'you can',
                    r'try using',
                    r'solution is',
                    r'fixed it by'
                ]
                if any(re.search(pattern, text, re.IGNORECASE) for pattern in solution_patterns):
                    return 'Answer'
                else:
                    return 'Praise'
            else:
                return 'Praise'

        elif polarity < -0.1:
            return 'Complaint'

        # Neutral content
        if data_type == 'comment':
            # Check for agreement/disagreement
            agreement_words = {'agree', 'yes', 'true', 'correct', 'good point'}
            disagreement_words = {'disagree', 'no', 'wrong', 'bad', 'terrible'}

            text_lower = text.lower()
            if any(word in text_lower for word in agreement_words):
                return 'Agreement'
            elif any(word in text_lower for word in disagreement_words):
                return 'Disagreement'
            else:
                return 'Statement'
        else:
            return 'Statement'

    def _detect_question(self, text: str) -> bool:
        """Detect questions using NLP."""
        # Check for question mark
        if '?' in text:
            return True

        # Check for question words at start of sentences
        sentences = re.split(r'[.!?]+', text)
        for sentence in sentences:
            sentence = sentence.strip().lower()
            if sentence:
                words = sentence.split()
                if words and words[0] in self.question_words:
                    return True

        # Check for auxiliary verbs + subject pattern
        question_patterns = [
            r'\b(do|does|did|is|are|was|were|have|has|had|can|could|should|would|will)\s+\w+',
            r'\b(what|how|why|when|where|who|which)\s+\w+'
        ]

        for pattern in question_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True

        return False