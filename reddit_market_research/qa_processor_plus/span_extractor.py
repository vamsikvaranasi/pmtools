"""
PainSpanExtractor — Focused Extraction with Guards

Extracts pain spans from filtered QA conversations with:
- Sentence segmentation
- Pain keyword detection
- Co-occurrence guard (pain keyword + negative/neutral sentiment)
- Promotional pattern rejection
- Confidence scoring
"""

import re
from typing import List, Dict, Any
from typing import List, Dict, Any


class PainSpanExtractor:
    """Extracts pain-related spans from QA conversations with confidence scores."""
    
    # Pain keywords by category
    PAIN_KEYWORDS = {
        'error': ['error', 'exception', 'fail', 'crash', 'bug', 'issue', 'problem', 'broken'],
        'performance': ['slow', 'lag', 'timeout', 'hang', 'freeze', 'performance', 'latency', 'throughput'],
        'usability': ['confusing', 'unclear', 'hard', 'difficult', 'complex', 'complicated', 'unintuitive'],
        'compatibility': ['incompatible', 'not working', 'doesn\'t work', 'conflict', 'compatibility'],
        'cost': ['expensive', 'costly', 'price', 'billing', 'overcharge', 'fee', 'subscription']
    }
    
    # Promotional patterns to reject
    PROMOTIONAL_TERMS = ['love', 'amazing', 'great', 'awesome', 'wonderful', 'excellent', 'perfect']
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the PainSpanExtractor.
        
        Args:
            config: Dictionary with keys:
                - max_span_length: Maximum length of extracted span (default: 200)
                - max_spans_per_question: Max spans per question (default: 3)
                - min_span_words: Minimum words in span (default: 5)
        """
        self.max_span_length = config.get('max_span_length', 200)
        self.max_spans_per_question = config.get('max_spans_per_question', 3)
        self.min_span_words = config.get('min_span_words', 5)
    
    def extract_spans(self, question: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract pain spans from a question with guards.
        
        Args:
            question: Question object with text, sentiment, and other metadata
            
        Returns:
            List of extracted spans with confidence scores
        """
        spans = []
        
        # GUARD: Check question-level sentiment
        sentiment = question.get('sentiment', 'neutral')
        if sentiment not in ['negative', 'neutral']:
            return []  # Only negative/neutral questions can have pain spans
        
        text = question.get('text', '')
        # Sentence segmentation (simple: split by . ! ?)
        sentences = re.split(r'[.!?]+', text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # Skip very short sentences
            if len(sentence.split()) < self.min_span_words:
                continue
            
            # GUARD: Reject promotional patterns
            if self._is_promotional(sentence):
                continue
            
            # GUARD: Reject pure questions without pain indicators
            if sentence.endswith('?') and not self._has_pain_keyword(sentence):
                continue
            
            # Check for pain keywords
            pain_keywords = self._find_pain_keywords(sentence)
            if pain_keywords:
                # Truncate if too long
                span_text = sentence[:self.max_span_length]
                
                # Calculate confidence
                confidence = self._calculate_confidence(sentence, pain_keywords)
                
                spans.append({
                    'text': span_text,
                    'sentence': sentence,
                    'pain_keywords': pain_keywords,
                    'confidence': confidence,
                    'post_id': question.get('post_id'),
                    'post_url': question.get('post_url')
                })
                
                if len(spans) >= self.max_spans_per_question:
                    break
        
        return spans
    
    def _is_promotional(self, sentence: str) -> bool:
        """Check if sentence contains promotional patterns."""
        sentence_lower = sentence.lower()
        for term in self.PROMOTIONAL_TERMS:
            if term in sentence_lower:
                # Additional check: if it contains both promotional term and product name
                # (simple heuristic, can be expanded)
                if any(sentiment in sentence_lower for sentiment in self.PROMOTIONAL_TERMS):
                    return True
        return False
    
    def _has_pain_keyword(self, sentence: str) -> bool:
        """Check if sentence contains any pain keyword."""
        sentence_lower = sentence.lower()
        for keywords in self.PAIN_KEYWORDS.values():
            for kw in keywords:
                if kw in sentence_lower:
                    return True
        return False
    
    def _find_pain_keywords(self, sentence: str) -> List[str]:
        """Find all pain keywords in sentence."""
        sentence_lower = sentence.lower()
        found = []
        for keywords in self.PAIN_KEYWORDS.values():
            for kw in keywords:
                if kw in sentence_lower and kw not in found:
                    found.append(kw)
        return found
    
    def _calculate_confidence(self, sentence: str, pain_keywords: List[str]) -> float:
        """
        Calculate confidence score for pain span.
        
        Confidence = (number of unique pain keywords) / (length of sentence in words)
        Capped at 1.0
        """
        num_keywords = len(pain_keywords)
        num_words = len(sentence.split())
        if num_words == 0:
            return 0.0
        confidence = min(num_keywords / (num_words / 10.0), 1.0)
        return round(confidence, 3)
