#!/usr/bin/env python3
"""
Reddit Dataset QA Processing Script
Processes three Reddit datasets through QAProcessorPlus
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple
import time

# Add reddit_market_research to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'reddit_market_research'))

from qa_processor_plus.qa_processor_plus import QAProcessorPlus
from qa_processor_plus.report_generator import ReportGenerator
from qa_processor_plus.legacy_adapter import LegacyAdapter
from qa_processor_plus.insight_generator import InsightGenerator


def extract_dataset_name(filename: str) -> str:
    """Extract dataset name from filename."""
    # Remove the suffix and common patterns
    name = filename.replace('_processed_enriched.json', '').replace(' Dataset Jan 26 2026', '')
    return name


def load_json_file(file_path: str) -> List[Dict[str, Any]]:
    """Load and parse JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data if isinstance(data, list) else [data]
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return []


def generate_insight_cards(results: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate insight cards from processing results."""
    insight_cards = []
    
    # Extract clusters and create insight cards
    clusters = results.get('clusters', {})
    labels = results.get('labels', [])
    
    # If clusters exist, create cards from them
    if clusters and isinstance(clusters, dict):
        for cluster_id, cluster_data in clusters.items():
            if isinstance(cluster_data, dict):
                card = {
                    'id': f'insight_{cluster_id}',
                    'label': cluster_data.get('label', f'Cluster {cluster_id}'),
                    'evidence': cluster_data.get('examples', [])[:5],
                    'evidence_count': len(cluster_data.get('examples', [])),
                    'product_area': cluster_data.get('category', 'General'),
                    'journey_stage': cluster_data.get('stage', 'Unknown'),
                    'severity': 'medium'
                }
                insight_cards.append(card)
    
    # If no clusters, create cards from labels
    if not insight_cards and labels:
        for idx, label in enumerate(labels[:10]):  # Limit to top 10
            card = {
                'id': f'insight_{idx}',
                'label': label.get('summary', f'Insight {idx}'),
                'evidence': label.get('keywords', []),
                'evidence_count': len(label.get('keywords', [])),
                'product_area': 'General',
                'journey_stage': 'Unknown',
                'severity': 'medium'
            }
            insight_cards.append(card)
    
    return insight_cards


def generate_solutions_summary(results: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate solutions summary from processing results."""
    solutions = []
    
    solutions_data = results.get('solutions', [])
    for sol in solutions_data:
        solution_entry = {
            'id': sol.get('id', f'sol_{len(solutions)}'),
            'solutions': sol.get('solutions', []),
            'recommendations': sol.get('recommendations', []),
            'actionable_items': sol.get('actionable_items', [])
        }
        solutions.append(solution_entry)
    
    return solutions[:20]  # Top 20 solutions


def generate_cluster_metrics(results: Dict[str, Any]) -> Dict[str, Any]:
    """Generate cluster quality metrics."""
    clusters = results.get('clusters', {})
    
    metrics = {
        'num_clusters': len(clusters) if clusters else 0,
        'total_items': len(results.get('conversations', [])),
        'items_per_cluster': {},
        'silhouette_score': None,
        'avg_intra_cluster_similarity': None,
        'clustering_quality': 'good' if len(clusters) > 1 else 'insufficient'
    }
    
    # Calculate items per cluster
    if clusters and isinstance(clusters, dict):
        for cluster_id, cluster_data in clusters.items():
            if isinstance(cluster_data, dict):
                count = len(cluster_data.get('examples', []))
                metrics['items_per_cluster'][str(cluster_id)] = count
    
    return metrics


def process_dataset(processor: QAProcessorPlus, 
                   input_file: str, 
                   dataset_name: str,
                   output_dir: str,
                   legacy_adapter: LegacyAdapter,
                   report_generator: ReportGenerator) -> Tuple[bool, Dict[str, Any]]:
    """Process a single dataset and generate all outputs."""
    
    print(f"\n{'='*60}")
    print(f"Processing {dataset_name} dataset...")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    # Load conversations
    conversations = load_json_file(input_file)
    if not conversations:
        print(f"ERROR: No conversations loaded from {input_file}")
        return False, {}
    
    print(f"✓ Loaded {len(conversations)} conversations")
    
    # Process conversations
    try:
        results = processor.process_conversations(conversations)
        print(f"✓ Processed {len(results.get('conversations', []))} conversations")
    except Exception as e:
        print(f"ERROR during processing: {e}")
        import traceback
        traceback.print_exc()
        return False, {}
    
    # Generate insight cards
    insight_cards = generate_insight_cards(results)
    
    # Generate solutions summary
    solutions = generate_solutions_summary(results)
    
    # Generate cluster metrics
    metrics = generate_cluster_metrics(results)
    
    # Generate legacy pain points format
    legacy_pain_points = legacy_adapter.convert_to_legacy_pain_points(insight_cards)
    
    # Write all outputs
    output_files = {}
    
    try:
        # Write insight cards
        insight_file = report_generator.write_insight_cards(insight_cards, dataset_name)
        output_files['insight_cards'] = insight_file
        print(f"✓ Saved insight cards: {os.path.basename(insight_file)}")
        
        # Write legacy pain points
        pain_points_file = report_generator.write_legacy_pain_points(legacy_pain_points, dataset_name)
        output_files['pain_points'] = pain_points_file
        print(f"✓ Saved pain points (legacy): {os.path.basename(pain_points_file)}")
        
        # Write cluster metrics
        metrics_file = report_generator.write_cluster_metrics(metrics, dataset_name)
        output_files['cluster_metrics'] = metrics_file
        print(f"✓ Saved cluster metrics: {os.path.basename(metrics_file)}")
        
        # Write solutions summary
        solutions_file = report_generator.write_solutions_summary(solutions, dataset_name)
        output_files['solutions'] = solutions_file
        print(f"✓ Saved solutions: {os.path.basename(solutions_file)}")
        
    except Exception as e:
        print(f"ERROR writing outputs: {e}")
        import traceback
        traceback.print_exc()
        return False, output_files
    
    elapsed = time.time() - start_time
    
    # Compile processing stats
    stats = {
        'dataset_name': dataset_name,
        'input_file': input_file,
        'conversations_loaded': len(conversations),
        'conversations_processed': len(results.get('conversations', [])),
        'insight_cards_generated': len(insight_cards),
        'solutions_extracted': len(solutions),
        'clusters_formed': metrics.get('num_clusters', 0),
        'processing_time_seconds': round(elapsed, 2),
        'output_files': output_files
    }
    
    return True, stats


def main():
    """Main processing function."""
    
    # Configuration
    input_dir = 'reddit_data/output/stage2_2026_02_03_1921'
    output_dir = 'reddit_data/output/stage3_qa_processing'
    
    # Verify input directory
    if not os.path.exists(input_dir):
        print(f"ERROR: Input directory not found: {input_dir}")
        return False
    
    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    print(f"✓ Output directory ready: {output_dir}")
    
    # Initialize components
    print("\nInitializing QA Processor Plus...")
    try:
        processor = QAProcessorPlus()
        print("✓ QA Processor Plus initialized")
    except Exception as e:
        print(f"ERROR: Failed to initialize processor: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    legacy_adapter = LegacyAdapter()
    report_generator = ReportGenerator(output_dir)
    
    # Find JSON files
    json_files = []
    for filename in sorted(os.listdir(input_dir)):
        if filename.endswith('_processed_enriched.json'):
            json_files.append(filename)
    
    if not json_files:
        print(f"ERROR: No JSON files found in {input_dir}")
        return False
    
    print(f"\n✓ Found {len(json_files)} datasets to process:")
    for f in json_files:
        print(f"  - {f}")
    
    # Process each dataset
    all_stats = []
    total_start = time.time()
    
    for idx, filename in enumerate(json_files, 1):
        dataset_name = extract_dataset_name(filename)
        input_file = os.path.join(input_dir, filename)
        
        success, stats = process_dataset(
            processor,
            input_file,
            dataset_name,
            output_dir,
            legacy_adapter,
            report_generator
        )
        
        if success:
            all_stats.append(stats)
        else:
            print(f"✗ Failed to process {dataset_name}")
    
    total_elapsed = time.time() - total_start
    
    # Print summary report
    print(f"\n{'='*60}")
    print("PROCESSING SUMMARY REPORT")
    print(f"{'='*60}\n")
    
    print(f"Total Processing Time: {total_elapsed:.2f} seconds")
    print(f"Datasets Processed: {len(all_stats)}/{len(json_files)}\n")
    
    # Per-dataset stats
    total_conversations = 0
    total_insight_cards = 0
    total_solutions = 0
    created_files = []
    
    for stats in all_stats:
        print(f"Dataset: {stats['dataset_name']}")
        print(f"  Input File: {os.path.basename(stats['input_file'])}")
        print(f"  Conversations Loaded: {stats['conversations_loaded']}")
        print(f"  Conversations Processed: {stats['conversations_processed']}")
        print(f"  Insight Cards Generated: {stats['insight_cards_generated']}")
        print(f"  Solutions Extracted: {stats['solutions_extracted']}")
        print(f"  Clusters Formed: {stats['clusters_formed']}")
        print(f"  Processing Time: {stats['processing_time_seconds']}s")
        print(f"  Output Files Generated:")
        for file_type, file_path in stats['output_files'].items():
            print(f"    - {file_type}: {os.path.basename(file_path)}")
            created_files.append(file_path)
        print()
        
        total_conversations += stats['conversations_processed']
        total_insight_cards += stats['insight_cards_generated']
        total_solutions += stats['solutions_extracted']
    
    # Overall summary
    print(f"{'='*60}")
    print("OVERALL STATISTICS")
    print(f"{'='*60}")
    print(f"Total Conversations Processed: {total_conversations}")
    print(f"Total Insight Cards Generated: {total_insight_cards}")
    print(f"Total Solutions Extracted: {total_solutions}")
    print(f"Total Output Files Created: {len(created_files)}")
    print(f"Output Directory: {output_dir}\n")
    
    # Verify all output files are valid JSON
    print("Verifying output files...")
    valid_count = 0
    for file_path in created_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                json.load(f)
            valid_count += 1
            print(f"  ✓ {os.path.basename(file_path)}")
        except Exception as e:
            print(f"  ✗ {os.path.basename(file_path)}: {e}")
    
    print(f"\nValid JSON Files: {valid_count}/{len(created_files)}")
    
    # Final success status
    success = len(all_stats) == len(json_files) and valid_count == len(created_files)
    
    if success:
        print(f"\n{'='*60}")
        print("✓ ALL DATASETS PROCESSED SUCCESSFULLY")
        print(f"{'='*60}\n")
    else:
        print(f"\n{'='*60}")
        print("✗ SOME DATASETS FAILED TO PROCESS")
        print(f"{'='*60}\n")
    
    return success


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
