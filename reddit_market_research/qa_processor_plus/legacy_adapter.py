"""
LegacyAdapter — Backward Compatibility

Converts new insight cards format to old pain_points format.
"""

from typing import List, Dict, Any


class LegacyAdapter:
    """Converts new output format to legacy pain_points format."""
    
    def __init__(self):
        """Initialize the LegacyAdapter."""
        pass
    
    def convert_to_legacy_pain_points(self, insight_cards: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Convert new insight cards to old pain_points format.
        
        Args:
            insight_cards: List of insight card dictionaries
            
        Returns:
            Legacy format dictionary with pain_points
        """
        pain_points = []
        
        for card in insight_cards:
            pain_point = {
                'pain_point': card.get('label', ''),
                'frequency': card.get('evidence_count', 0),
                'intensity': self._map_severity_to_intensity(card.get('severity', 'low')),
                'category': card.get('product_area', 'uncategorized'),
                'sentiment_impact': 'negative',
                'examples': self._extract_examples(card.get('evidence', [])),
                'associated_solutions': []
            }
            pain_points.append(pain_point)
        
        return {
            'pain_points': pain_points,
            'total_count': len(pain_points),
            'format': 'legacy'
        }
    
    def _map_severity_to_intensity(self, severity: str) -> int:
        """Map severity string to intensity number."""
        mapping = {
            'low': 1,
            'medium': 2,
            'high': 3
        }
        return mapping.get(severity, 1)
    
    def _extract_examples(self, evidence: List[Dict[str, Any]]) -> List[str]:
        """Extract example texts from evidence."""
        return [e.get('text', '')[:100] for e in evidence[:3]]
