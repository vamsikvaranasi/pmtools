"""
ProductAreaClassifier + JourneyStageClassifier with Confidence Scoring

Per PM Decision #1: Journey stage computed with confidence threshold (≥0.4)
with priority ordering to break ties.
"""

from typing import List, Dict, Any, Tuple, Optional


class ProductAreaClassifier:
    """Classifies pain spans into product areas with confidence scoring."""
    
    # Product area keywords
    PRODUCT_AREA_KEYWORDS = {
        'deployment': ['deploy', 'deployment', 'release', 'rollout', 'production', 'staging'],
        'reliability': ['crash', 'down', 'outage', 'downtime', 'error', 'fail', 'timeout'],
        'performance': ['slow', 'lag', 'latency', 'performance', 'throughput', 'cpu', 'memory'],
        'pricing_billing': ['price', 'pricing', 'billing', 'cost', 'subscription', 'charge', 'fee'],
        'data_management': ['data', 'database', 'backup', 'recovery', 'corruption', 'loss'],
        'security': ['security', 'auth', 'permission', 'encryption', 'vulnerability', 'breach'],
        'usability': ['ui', 'ux', 'confusing', 'unclear', 'interface', 'workflow'],
    }
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the ProductAreaClassifier.
        
        Args:
            config: Dictionary with keys:
                - min_product_area_confidence: Threshold for classification (default: 0.3)
        """
        self.min_confidence = config.get('min_product_area_confidence', 0.3)
    
    def classify(self, text: str) -> Tuple[Optional[str], float]:
        """
        Classify text into a product area with confidence.
        
        Requires ≥2 keyword matches per category.
        Confidence = (matched keywords) / (total keywords in category)
        
        Args:
            text: Text to classify
            
        Returns:
            Tuple of (product_area, confidence) or (None, 0.0) if below threshold
        """
        text_lower = text.lower()
        scores = {}
        
        for area, keywords in self.PRODUCT_AREA_KEYWORDS.items():
            matched_count = sum(1 for kw in keywords if kw in text_lower)
            
            # Require ≥2 keyword matches
            if matched_count < 2:
                scores[area] = 0.0
            else:
                confidence = matched_count / len(keywords)
                scores[area] = confidence
        
        # Find best area
        best_area = None
        best_score = 0.0
        
        for area, score in scores.items():
            if score > best_score:
                best_area = area
                best_score = score
        
        # Apply confidence threshold
        if best_score < self.min_confidence:
            return None, best_score
        
        return best_area, round(best_score, 3)


class JourneyStageClassifier:
    """Classifies text into customer journey stages with priority-based tie-breaking."""
    
    # Priority ordering: shipping > scaling > building > first_use > evaluation > troubleshooting
    STAGE_PRIORITY = ['shipping', 'scaling', 'building', 'first_use', 'evaluation', 'troubleshooting']
    
    STAGE_KEYWORDS = {
        'shipping': ['ship', 'shipped', 'delivery', 'deliver', 'arrival', 'received', 'arrived'],
        'scaling': ['scale', 'scaling', 'growth', 'scale up', 'handle load', 'growth'],
        'building': ['build', 'building', 'develop', 'developing', 'implementation', 'architect'],
        'first_use': ['first time', 'getting started', 'onboarding', 'new user', 'first run', 'setup'],
        'evaluation': ['evaluate', 'evaluate', 'considering', 'trying out', 'test', 'poc'],
        'troubleshooting': ['troubleshoot', 'debug', 'fix', 'issue', 'problem', 'error']
    }
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the JourneyStageClassifier.
        
        Args:
            config: Dictionary with keys:
                - min_journey_stage_confidence: Threshold for classification (default: 0.4)
        """
        self.min_confidence = config.get('min_journey_stage_confidence', 0.4)
    
    def classify(self, text: str) -> Tuple[Optional[str], float]:
        """
        Classify text into a journey stage with confidence.
        
        Confidence = (matched keywords) / (total keywords in stage)
        Priority ordering breaks ties.
        Only return stage if confidence ≥ 0.4
        
        Args:
            text: Text to classify
            
        Returns:
            Tuple of (stage, confidence) or (None, score) if below threshold
        """
        text_lower = text.lower()
        scores = {}
        
        for stage, keywords in self.STAGE_KEYWORDS.items():
            matched = sum(1 for kw in keywords if kw in text_lower)
            confidence = matched / len(keywords) if keywords else 0.0
            scores[stage] = confidence
        
        # Find best stage using priority ordering
        best_stage = None
        best_score = 0.0
        
        for stage in self.STAGE_PRIORITY:
            if scores[stage] > best_score:
                best_stage = stage
                best_score = scores[stage]
        
        # Apply confidence threshold
        if best_score < self.min_confidence:
            return None, best_score
        
        return best_stage, round(best_score, 3)
