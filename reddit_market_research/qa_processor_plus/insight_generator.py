"""
InsightCardGenerator — PM-Usable Output Format

Generates insight cards with evidence, product area, and journey stage.
"""

from typing import List, Dict, Any, Optional


class InsightCardGenerator:
    """Generates insight cards for PM consumption."""
    
    def __init__(self):
        """Initialize the InsightCardGenerator."""
        pass
    
    def generate_insight_card(self, label: str, spans: List[Dict[str, Any]], 
                            product_area: Optional[str] = None,
                            journey_stage: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate an insight card for display.
        
        Args:
            label: Label for the insight
            spans: List of evidence spans
            product_area: Product area classification
            journey_stage: Journey stage classification
            
        Returns:
            Insight card dictionary
        """
        return {
            'label': label,
            'evidence': spans,
            'evidence_count': len(spans),
            'product_area': product_area,
            'journey_stage': journey_stage,
            'severity': self._calculate_severity(spans)
        }
    
    def _calculate_severity(self, spans: List[Dict[str, Any]]) -> str:
        """Calculate severity from span evidence."""
        if not spans:
            return 'low'
        
        # Severity based on evidence count and confidence
        avg_confidence = sum(s.get('confidence', 0.5) for s in spans) / len(spans)
        
        if len(spans) >= 5 and avg_confidence > 0.6:
            return 'high'
        elif len(spans) >= 3 or avg_confidence > 0.5:
            return 'medium'
        else:
            return 'low'
