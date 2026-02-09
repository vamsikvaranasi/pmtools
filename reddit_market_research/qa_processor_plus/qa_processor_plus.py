"""
QA Processor Plus Main Class
Main entry point for the QA Processor Plus system.
"""

from typing import List, Dict, Any, Optional
import os
import json
import yaml
from pathlib import Path

from .filter import InputFilter
from .span_extractor import PainSpanExtractor
from .classifier import ProductAreaClassifier, JourneyStageClassifier
from .label_generator import TemplateLabelGenerator
from .solution_extractor import SolutionExtractorV2
from .embedding_wrapper import EmbeddingWrapper
from .vector_store import LanceDBManager
from .clustering import HDBSCANClustering
from .cluster_metrics import ClusterQualityMetrics
from .llm_synthesizer import OllamaLLMSynthesizer
from .insight_generator import InsightCardGenerator
from .legacy_adapter import LegacyAdapter
from .grouper import EvidencePreservingGrouper
from .report_generator import ReportGenerator


class QAProcessorPlus:
    """Main processing system for QA conversations."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the QA processor.
        
        Args:
            config_path: Path to the configuration file (uses global config if not specified)
        """
        # Use global config by default
        if config_path is None:
            # Look for global config.yaml in parent directory
            global_config = Path(__file__).parent.parent / "config.yaml"
            if global_config.exists():
                config_path = str(global_config)
            else:
                config_path = "config.yaml"
        
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Initialize all components
        filter_config = self.config.get("filter", {
            "min_upvotes": 5,
            "min_word_count": 10,
            "sentiment": ["negative", "neutral"],
            "categories": ["Question", "Complaint", "Suggestion"]
        })
        self.filter = InputFilter(filter_config)
        self.span_extractor = PainSpanExtractor()
        self.product_area_classifier = ProductAreaClassifier()
        self.journey_stage_classifier = JourneyStageClassifier()
        self.label_generator = TemplateLabelGenerator()
        self.solution_extractor = SolutionExtractorV2()
        self.embedding_wrapper = EmbeddingWrapper(
            self.config.get("embedding", {}).get("model", "default")
        )
        self.vector_store = LanceDBManager(
            self.config.get("storage", {}).get("vector_store", "vector_store.db")
        )
        self.clusterer = HDBSCANClustering(
            self.config.get("clustering", {}).get("min_cluster_size", 5)
        )
        self.cluster_metrics = ClusterQualityMetrics()
        self.llm_synthesizer = OllamaLLMSynthesizer(
            self.config.get("llm", {}).get("model", "ollama")
        )
        self.insight_generator = InsightCardGenerator()
        self.legacy_adapter = LegacyAdapter()
        self.grouper = EvidencePreservingGrouper()
        # ReportGenerator needs output_dir
        output_dir = self.config.get("output", {}).get("insights_dir", "insights")
        self.report_generator = ReportGenerator(output_dir)
        
        # Create output directories if they don't exist
        self._create_output_directories()
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file.
        
        Args:
            config_path: Path to the configuration file
            
        Returns:
            Configuration dictionary
        """
        default_config = {
            "processing": {"batch_size": 100},
            "embedding": {"model": "default"},
            "clustering": {"n_clusters": 5},
            "storage": {"vector_store": "vector_store.db"},
            "llm": {"model": "default"},
            "output": {
                "reports_dir": "reports",
                "visualizations_dir": "visualizations",
                "insights_dir": "insights"
            }
        }
        
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    user_config = yaml.safe_load(f)
                default_config.update(user_config)
            except Exception as e:
                print(f"Error loading config file: {e}")
                print("Using default configuration")
        
        return default_config
    
    def _create_output_directories(self):
        """Create output directories if they don't exist."""
        for dir_name in ["reports_dir", "visualizations_dir", "insights_dir"]:
            dir_path = self.config["output"].get(dir_name, "output")
            Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    def process_conversations(self, conversations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process a list of conversations through all stages.
        
        Args:
            conversations: List of QA conversations to process
            
        Returns:
            Dictionary containing all processing results
        """
        results = {}
        
        # Step 1: Filter and preprocess conversations
        print(f"Processing {len(conversations)} conversations...")
        filtered_conversations = self.filter.filter_conversations(conversations)
        print(f"Filtered to {len(filtered_conversations)} conversations")
        
        # Step 2: Extract spans (questions, answers, key phrases)
        question_spans = self.span_extractor.extract_question_spans(filtered_conversations)
        answer_spans = self.span_extractor.extract_answer_spans(filtered_conversations)
        
        # Step 3: Classify conversations
        classifications = self.classifier.classify_conversations(filtered_conversations)
        
        # Step 4: Generate labels and tags
        labels = [
            {
                "id": conv["id"],
                "summary": self.label_generator.generate_summary(conv),
                "tags": self.label_generator.generate_tags(conv),
                "keywords": self.label_generator.generate_keywords(
                    conv.get("body", "") + " " + conv.get("title", "")
                )
            }
            for conv in filtered_conversations
        ]
        
        # Step 5: Extract solutions and recommendations
        solutions = [
            {
                "id": conv["id"],
                "solutions": self.solution_extractor.extract_solutions(conv),
                "recommendations": self.solution_extractor.extract_recommendations(conv),
                "actionable_items": self.solution_extractor.extract_actionable_items(conv)
            }
            for conv in filtered_conversations
        ]
        
        # Step 6: Cluster conversations
        clusters = self.clusterer.cluster_conversations(filtered_conversations)
        
        # Step 7: Generate LLM synthesis and insights
        llm_summary = self.llm_synthesizer.generate_summary(filtered_conversations)
        llm_insights = self.llm_synthesizer.generate_insights(filtered_conversations)
        llm_recommendations = self.llm_synthesizer.generate_recommendations(filtered_conversations)
        llm_action_items = self.llm_synthesizer.generate_action_items(filtered_conversations)
        
        # Step 8: Generate insights
        trends = self.insight_generator.identify_trends(filtered_conversations)
        common_issues = self.insight_generator.identify_common_issues(filtered_conversations)
        opportunities = self.insight_generator.identify_opportunities(filtered_conversations)
        patterns = self.insight_generator.identify_patterns(filtered_conversations)
        analytics = self.insight_generator.generate_analytics(filtered_conversations)
        
        # Compile results
        results = {
            "conversations": filtered_conversations,
            "question_spans": question_spans,
            "answer_spans": answer_spans,
            "classifications": classifications,
            "labels": labels,
            "solutions": solutions,
            "clusters": clusters,
            "llm_summary": llm_summary,
            "llm_insights": llm_insights,
            "llm_recommendations": llm_recommendations,
            "llm_action_items": llm_action_items,
            "trends": trends,
            "common_issues": common_issues,
            "opportunities": opportunities,
            "patterns": patterns,
            "analytics": analytics
        }
        
        return results
    
    def process_conversations_from_directory(self, input_dir: str) -> Dict[str, Any]:
        """Process conversations from all JSON files in a directory.
        
        Args:
            input_dir: Directory containing JSON files with conversations
            
        Returns:
            Dictionary containing all processing results
        """
        all_conversations = []
        
        # Find all JSON files in the input directory
        for filename in os.listdir(input_dir):
            if filename.endswith(".json"):
                file_path = os.path.join(input_dir, filename)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        conversations = json.load(f)
                    all_conversations.extend(conversations)
                    print(f"Loaded {len(conversations)} conversations from {filename}")
                except Exception as e:
                    print(f"Error loading file {filename}: {e}")
        
        if not all_conversations:
            print("No conversations found in the input directory")
            return {}
        
        return self.process_conversations(all_conversations)
    
    def save_results(self, results: Dict[str, Any], output_dir: str, output_format: str = "json"):
        """Save processing results to output directory.
        
        Args:
            results: Processing results to save
            output_dir: Output directory
            output_format: Output format (json, csv, or excel)
        """
        # Create output directory if it doesn't exist
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        if output_format == "json":
            output_file = os.path.join(output_dir, "processed_results.json")
            try:
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
                print(f"Results saved to {output_file}")
            except Exception as e:
                print(f"Error saving results: {e}")
        else:
            print(f"Output format '{output_format}' not supported")
    
    def generate_report(self, results: Dict[str, Any], output_path: str, report_type: str = "summary"):
        """Generate a report from processing results.
        
        Args:
            results: Processing results
            output_path: Output file path for the report
            report_type: Type of report to generate (summary, detailed, insight)
        """
        if report_type == "summary":
            report = self.report_generator.generate_summary_report(results["conversations"])
        elif report_type == "detailed":
            report = self.report_generator.generate_detailed_report(results["conversations"])
        elif report_type == "insight":
            report = self.report_generator.generate_insight_report(results["conversations"])
        else:
            print(f"Report type '{report_type}' not supported")
            return
        
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(report)
            print(f"Report saved to {output_path}")
        except Exception as e:
            print(f"Error saving report: {e}")
