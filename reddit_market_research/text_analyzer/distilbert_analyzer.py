"""
DistilBERT Analyzer

Transformer-based sentiment analysis (POS/NEU/NEG) for social text.
"""

import re
import time
from typing import Dict, Any, List, Optional, Tuple

from .base_analyzer import BaseAnalyzer

try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False


class DistilBERTAnalyzer(BaseAnalyzer):
    """Transformer-based analyzer using a 3-class DistilBERT model."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        if not TRANSFORMERS_AVAILABLE:
            raise ImportError("transformers required for DistilBERT analyzer")

        model_name = self.config.get('distilbert_model', 'iam-tsr/distilbert-finetuned-sentiment-analysis')
        label_map = self.config.get('distilbert_label_map', {})

        self.label_map = {str(k).lower(): str(v).lower() for k, v in label_map.items()}
        self.sentiment_pipeline = pipeline(
            "sentiment-analysis",
            model=model_name,
            tokenizer=model_name,
            return_all_scores=False
        )

        self.question_words = {
            'how', 'can', 'what', 'why', 'when', 'where', 'who',
            'is', 'are', 'do', 'does', 'did', 'should', 'would', 'could'
        }

        self.subcategory_keywords = {
            'pricing': ['price', 'pricing', 'cost', 'expensive', 'cheap', 'subscription', 'billing'],
            'performance': ['slow', 'latency', 'performance', 'lag', 'freeze', 'crash', 'timeout'],
            'usability': ['confusing', 'hard to', 'difficult', 'not intuitive', 'ux', 'ui', 'workflow'],
            'support': ['support', 'help', 'documentation', 'docs', 'guide', 'tutorial'],
            'bug': ['bug', 'error', 'broken', 'issue', 'problem', 'fail', 'failing'],
            'feature_request': ['feature request', 'should add', 'would be great', 'i wish', 'please add', 'missing'],
            'comparison': ['vs', 'versus', 'compared to', 'better than', 'worse than', 'alternative'],
            'setup': ['install', 'setup', 'configure', 'configuration', 'deploy', 'deployment'],
            'recommendation': ['recommend', 'suggest', 'use', 'try', 'best way']
        }

    def analyze_object(self, obj: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze object using DistilBERT sentiment and heuristic categorization."""
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

        sentiment, confidence = self._analyze_sentiment(text)
        category, subcategory = self._analyze_category(text, obj.get('dataType', 'post'), sentiment)

        processing_time_ms = (time.time() - start_time) * 1000

        analysis = {
            'sentiment': sentiment,
            'category': category,
            'confidence': confidence,
            'processing_time_ms': round(processing_time_ms, 3)
        }
        if subcategory:
            analysis['subcategory'] = subcategory

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

    def _analyze_sentiment(self, text: str) -> Tuple[str, float]:
        """Analyze sentiment using transformers pipeline."""
        result = self.sentiment_pipeline(text[:512])[0]
        label = str(result.get('label', '')).lower()
        score = float(result.get('score', 0.5))

        if label in self.label_map:
            sentiment = self.label_map[label]
        elif 'neg' in label:
            sentiment = 'negative'
        elif 'pos' in label:
            sentiment = 'positive'
        elif 'neu' in label:
            sentiment = 'neutral'
        elif label == 'label_0':
            sentiment = 'negative'
        elif label == 'label_1':
            sentiment = 'neutral'
        elif label == 'label_2':
            sentiment = 'positive'
        else:
            sentiment = 'neutral'

        return sentiment, max(0.0, min(1.0, score))

    def _analyze_category(self, text: str, data_type: str, sentiment: str) -> Tuple[str, Optional[str]]:
        """Categorize content using NLP patterns."""
        text_lower = text.lower()

        if self._detect_question(text):
            return 'Question', self._detect_subcategory(text_lower)

        if data_type == 'comment' and self._detect_answer(text_lower):
            return 'Answer', self._detect_answer_subcategory(text_lower)

        if self._detect_suggestion(text_lower):
            return 'Suggestion', self._detect_subcategory(text_lower) or 'feature_request'

        if self._detect_comparison(text_lower):
            return 'Comparison', 'comparison'

        if sentiment == 'negative' or self._detect_complaint(text_lower):
            return 'Complaint', self._detect_subcategory(text_lower)

        if sentiment == 'positive' or self._detect_praise(text_lower):
            return 'Praise', self._detect_subcategory(text_lower)

        if data_type == 'comment':
            if self._detect_agreement(text_lower):
                return 'Agreement', None
            if self._detect_disagreement(text_lower):
                return 'Disagreement', None

        if self._detect_sharing(text_lower):
            return 'Sharing', None

        return 'Statement', None

    def _detect_subcategory(self, text_lower: str) -> Optional[str]:
        for subcategory, keywords in self.subcategory_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return subcategory
        return None

    def _detect_answer(self, text_lower: str) -> bool:
        patterns = [
            r'\btry\b',
            r'\byou can\b',
            r'\bsolution\b',
            r'\bfix(ed)?\b',
            r'\bworked for me\b',
            r'\bsteps?\b'
        ]
        return any(re.search(pattern, text_lower) for pattern in patterns)

    def _detect_answer_subcategory(self, text_lower: str) -> Optional[str]:
        if 'workaround' in text_lower or 'hack' in text_lower:
            return 'workaround'
        if 'recommend' in text_lower or 'suggest' in text_lower:
            return 'recommendation'
        if 'step' in text_lower or 'first' in text_lower:
            return 'solution'
        return None

    def _detect_suggestion(self, text_lower: str) -> bool:
        patterns = [
            r'\bshould add\b',
            r'\bi wish\b',
            r'\bplease add\b',
            r'\bwould be great\b',
            r'\bfeature request\b'
        ]
        return any(re.search(pattern, text_lower) for pattern in patterns)

    def _detect_comparison(self, text_lower: str) -> bool:
        patterns = [
            r'\bvs\b',
            r'\bversus\b',
            r'\bcompared to\b',
            r'\bbetter than\b',
            r'\bworse than\b',
            r'\balternative\b'
        ]
        return any(re.search(pattern, text_lower) for pattern in patterns)

    def _detect_complaint(self, text_lower: str) -> bool:
        complaint_words = [
            'bug', 'error', 'issue', 'broken', 'crash', 'slow', 'problem', 'fail', 'failing',
            'annoying', 'frustrating', 'terrible', 'bad', 'unusable'
        ]
        return any(word in text_lower for word in complaint_words)

    def _detect_praise(self, text_lower: str) -> bool:
        praise_words = ['love', 'great', 'awesome', 'amazing', 'fantastic', 'thanks', 'helpful']
        return any(word in text_lower for word in praise_words)

    def _detect_agreement(self, text_lower: str) -> bool:
        agreement_words = ['agree', 'yes', 'true', 'correct', 'good point', 'exactly']
        return any(word in text_lower for word in agreement_words)

    def _detect_disagreement(self, text_lower: str) -> bool:
        disagreement_words = ['disagree', 'no', 'wrong', 'not true', 'bad take']
        return any(word in text_lower for word in disagreement_words)

    def _detect_sharing(self, text_lower: str) -> bool:
        sharing_patterns = [
            r'\bi built\b',
            r'\bi made\b',
            r'\bsharing\b',
            r"\bhere is\b",
            r"\bhere's\b"
        ]
        return any(re.search(pattern, text_lower) for pattern in sharing_patterns)

    def _detect_question(self, text: str) -> bool:
        if '?' in text:
            return True

        sentences = re.split(r'[.!?]+', text)
        for sentence in sentences:
            sentence = sentence.strip().lower()
            if sentence:
                words = sentence.split()
                if words and words[0] in self.question_words:
                    return True

        question_patterns = [
            r'\b(do|does|did|is|are|was|were|have|has|had|can|could|should|would|will)\s+(i|you|we|they|he|she|it)\b',
            r'\b(what|how|why|when|where|who|which)\s+\w+'
        ]

        for pattern in question_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True

        return False
