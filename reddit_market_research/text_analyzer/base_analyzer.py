"""
Base Analyzer Interface

Abstract base class for all text analysis implementations.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import time


class BaseAnalyzer(ABC):
    """Abstract base class for text analyzers."""

    # Valid categories
    VALID_CATEGORIES = [
        "Question", "Statement", "Praise", "Complaint", "Sharing",
        "Answer", "Agreement", "Disagreement"
    ]

    # Valid sentiments
    VALID_SENTIMENTS = ["positive", "neutral", "negative"]

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    @abstractmethod
    def analyze_object(self, obj: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a single object and return enriched version.

        Args:
            obj: The processed Reddit object

        Returns:
            Object with added analysis fields
        """
        pass

    @abstractmethod
    def analyze_batch(self, objects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyze multiple objects.

        Args:
            objects: List of processed Reddit objects

        Returns:
            List of enriched objects
        """
        pass

    def _add_analysis_metadata(self, obj: Dict[str, Any], analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Add analysis metadata to object."""
        enriched = obj.copy()
        enriched['analysis'] = analysis
        enriched['analysis']['processed_at'] = datetime.now(timezone.utc).isoformat()
        enriched['analysis']['analysis_level'] = self.__class__.__name__.replace('Analyzer', '').lower()
        return enriched

    def _validate_category(self, category: str) -> str:
        """Ensure category is valid."""
        if category not in self.VALID_CATEGORIES:
            return "Statement"  # Default fallback
        return category

    def _validate_sentiment(self, sentiment: str) -> str:
        """Ensure sentiment is valid."""
        if sentiment not in self.VALID_SENTIMENTS:
            return "positive"  # Default fallback
        return sentiment