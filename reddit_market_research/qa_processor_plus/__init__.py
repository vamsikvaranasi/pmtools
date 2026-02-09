"""
Core QA processor module for the PMTools project.

This module serves as the main entry point for the QA processing pipeline,
coordinating all components to analyze and extract insights from QA conversations.
"""

__version__ = "1.0.0"
__author__ = "PM Tools Team"
__license__ = "MIT"

# Import core components needed for data processing
from .legacy_adapter import LegacyAdapter
from .report_generator import ReportGenerator

# Import optional components with fallback
try:
    from .filter import InputFilter
except ImportError:
    InputFilter = None

try:
    from .span_extractor import PainSpanExtractor
except ImportError:
    PainSpanExtractor = None

try:
    from .classifier import ProductAreaClassifier, JourneyStageClassifier
except ImportError:
    ProductAreaClassifier = None
    JourneyStageClassifier = None

try:
    from .label_generator import TemplateLabelGenerator
except ImportError:
    TemplateLabelGenerator = None

try:
    from .solution_extractor import SolutionExtractorV2
except ImportError:
    SolutionExtractorV2 = None

try:
    from .embedding_wrapper import EmbeddingWrapper
except ImportError:
    EmbeddingWrapper = None

try:
    from .vector_store import LanceDBManager
except ImportError:
    LanceDBManager = None

try:
    from .clustering import HDBSCANClustering
except ImportError:
    HDBSCANClustering = None

try:
    from .cluster_metrics import ClusterQualityMetrics
except ImportError:
    ClusterQualityMetrics = None

try:
    from .llm_synthesizer import OllamaLLMSynthesizer
except ImportError:
    OllamaLLMSynthesizer = None

try:
    from .insight_generator import InsightCardGenerator
except ImportError:
    InsightCardGenerator = None

try:
    from .grouper import EvidencePreservingGrouper
except ImportError:
    EvidencePreservingGrouper = None

try:
    from .qa_processor_plus import QAProcessorPlus
except ImportError:
    QAProcessorPlus = None

__all__ = [
    "InputFilter",
    "PainSpanExtractor", 
    "ProductAreaClassifier",
    "JourneyStageClassifier",
    "TemplateLabelGenerator",
    "SolutionExtractorV2",
    "EmbeddingWrapper",
    "LanceDBManager",
    "HDBSCANClustering",
    "ClusterQualityMetrics",
    "OllamaLLMSynthesizer",
    "InsightCardGenerator",
    "LegacyAdapter",
    "EvidencePreservingGrouper",
    "ReportGenerator",
    "QAProcessorPlus"
]