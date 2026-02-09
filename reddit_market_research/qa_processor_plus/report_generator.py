"""
ReportGenerator — Output Format Generation

Generates both new and legacy format outputs.
"""

import json
from typing import List, Dict, Any, Optional
from pathlib import Path


class ReportGenerator:
    """Generates reports in both new and legacy formats."""
    
    def __init__(self, output_dir: str):
        """
        Initialize the ReportGenerator.
        
        Args:
            output_dir: Directory to write reports to
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def write_insight_cards(self, insight_cards: List[Dict[str, Any]], 
                           community: str) -> str:
        """
        Write insight cards in new format.
        
        Args:
            insight_cards: List of insight card dictionaries
            community: Community name for file naming
            
        Returns:
            Path to written file
        """
        filename = self.output_dir / f"insight_cards_{community}.json"
        
        output = {
            'format': 'insight_cards',
            'community': community,
            'insights': insight_cards,
            'total_insights': len(insight_cards)
        }
        
        with open(filename, 'w') as f:
            json.dump(output, f, indent=2)
        
        return str(filename)
    
    def write_legacy_pain_points(self, pain_points: Dict[str, Any], 
                                community: str) -> str:
        """
        Write pain points in legacy format.
        
        Args:
            pain_points: Legacy format pain points dictionary
            community: Community name for file naming
            
        Returns:
            Path to written file
        """
        filename = self.output_dir / f"pain_points_{community}.json"
        
        with open(filename, 'w') as f:
            json.dump(pain_points, f, indent=2)
        
        return str(filename)
    
    def write_cluster_metrics(self, metrics: Dict[str, Any], 
                             community: str) -> str:
        """
        Write cluster quality metrics.
        
        Args:
            metrics: Metrics dictionary
            community: Community name for file naming
            
        Returns:
            Path to written file
        """
        filename = self.output_dir / f"cluster_metrics_{community}.json"
        
        output = {
            'community': community,
            'metrics': metrics
        }
        
        with open(filename, 'w') as f:
            json.dump(output, f, indent=2)
        
        return str(filename)
    
    def write_solutions_summary(self, solutions: List[Dict[str, Any]], 
                               community: str) -> str:
        """
        Write solutions summary.
        
        Args:
            solutions: List of solutions
            community: Community name for file naming
            
        Returns:
            Path to written file
        """
        filename = self.output_dir / f"solutions_{community}.json"
        
        output = {
            'community': community,
            'solutions': solutions,
            'total_solutions': len(solutions)
        }
        
        with open(filename, 'w') as f:
            json.dump(output, f, indent=2)
        
        return str(filename)
