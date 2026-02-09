"""
TemplateLabelGenerator — Mode A Label Generation

Generates template-based labels for pain points (Mode A has no embeddings/LLM).
Format: "{ProductArea} — {top_keyword} {context_word}"
"""

from typing import List, Dict, Any, Optional
import re


class TemplateLabelGenerator:
    """Generates concise template-based labels for pain spans."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the TemplateLabelGenerator.
        
        Args:
            config: Optional configuration dictionary
        """
        if config is None:
            config = {}
        self.config = config
    
    def generate_label(self, product_area: str, pain_keywords: List[str], 
                      span_text: str) -> str:
        """
        Generate a template-based label for a pain point.
        
        Format: "{ProductArea} — {top_keyword} {context_word}"
        Example: "Deployment/Reliability — timeout error"
        Example: "Pricing/Billing — unexpected charges"
        
        Fallback: first 60 chars of span if no good template match
        
        Args:
            product_area: Product area classification
            pain_keywords: List of pain keywords found
            span_text: Original span text
            
        Returns:
            Generated label
        """
        if not product_area or product_area == 'uncategorized':
            # Fallback: use first 60 chars of span
            return span_text[:60].strip()
        
        # Get top keyword(s)
        if not pain_keywords:
            return f"{self._format_area(product_area)}"
        
        top_keyword = pain_keywords[0]
        
        # Find context word (noun or descriptor near the keyword)
        context_word = self._find_context_word(span_text, top_keyword)
        
        # Build label
        label = f"{self._format_area(product_area)} — {top_keyword}"
        if context_word and context_word != top_keyword:
            label = f"{label} {context_word}"
        
        return label[:100]  # Truncate if too long
    
    def _format_area(self, area: str) -> str:
        """Format product area name for display."""
        area_display = {
            'deployment': 'Deployment',
            'reliability': 'Reliability',
            'performance': 'Performance',
            'pricing_billing': 'Pricing/Billing',
            'data_management': 'Data Management',
            'security': 'Security',
            'usability': 'Usability',
        }
        return area_display.get(area, area.replace('_', '/').title())
    
    def _find_context_word(self, text: str, keyword: str) -> Optional[str]:
        """
        Find a context word near the keyword.
        
        Looks for nearby nouns or descriptive words.
        
        Args:
            text: Text to search
            keyword: Keyword to find context for
            
        Returns:
            Context word or None
        """
        # Simple heuristic: find words adjacent to keyword
        text_lower = text.lower()
        keyword_pos = text_lower.find(keyword)
        
        if keyword_pos == -1:
            return None
        
        # Get a window around the keyword
        start = max(0, keyword_pos - 50)
        end = min(len(text), keyword_pos + len(keyword) + 50)
        window = text[start:end]
        
        # Common context nouns and descriptors
        context_terms = [
            'error', 'issue', 'problem', 'failure', 'crash',
            'timeout', 'lag', 'delay', 'slowness',
            'charges', 'cost', 'price', 'billing',
            'data', 'information', 'records',
            'user', 'customer', 'client'
        ]
        
        for term in context_terms:
            if term in window.lower() and term != keyword:
                return term
        
        return keyword
