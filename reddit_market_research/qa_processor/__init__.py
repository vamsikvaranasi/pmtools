"""
Q&A Processor Module - Stage 4

Processes questions and answers from enriched Reddit data to identify pain points and solutions.
"""

from .grouper import QAGrouper
from .extractors import PainPointExtractor, SolutionExtractor
from .report_generator import QAReportGenerator

__all__ = ["QAGrouper", "PainPointExtractor", "SolutionExtractor", "QAReportGenerator"]