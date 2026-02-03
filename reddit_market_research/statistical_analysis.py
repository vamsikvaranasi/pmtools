#!/usr/bin/env python3
"""
Stage 3: Statistical Analysis

Roll up statistics from enriched data at file → community → target-product levels.
Uses config.yaml for settings and creates timestamped output directories.
"""

import csv
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import click
from tqdm import tqdm

# Handle imports for both module and script execution
try:
    from .models.analysis_models import (
        CommunityStats,
        EnrichedObject,
        FileStats,
        ProductStats
    )
    from .config_loader import Config, get_output_dir, get_product_name
except ImportError:
    from models.analysis_models import (
        CommunityStats,
        EnrichedObject,
        FileStats,
        ProductStats
    )
    from config_loader import Config, get_output_dir, get_product_name


class StatisticsCalculator:
    """Handles statistical analysis and rollup for Stage 3."""

    def __init__(self, input_dir: Path, output_dir: Optional[Path] = None, mapping_file: Optional[Path] = None):
        self.input_dir = input_dir
        
        # Use config-managed output directory
        if output_dir is None:
            self.output_dir = get_output_dir("statistical_analysis")
        else:
            self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.mapping_file = mapping_file
        
        # Load config for product mappings
        self.config = Config()
        self.config_mappings = self.config.product_mappings

        # Output files - directly in output_dir (no subfolders)
        self.file_stats_csv = self.output_dir / "statistics_file.csv"
        self.community_stats_csv = self.output_dir / "statistics_community.csv"
        self.product_stats_csv = self.output_dir / "statistics_product.csv"

        # Load product mapping
        self.product_mapping = self._load_product_mapping()

    def _load_product_mapping(self) -> Dict[str, str]:
        """Load community to product mapping from file or config."""
        if self.mapping_file and self.mapping_file.exists():
            try:
                with open(self.mapping_file, 'r') as f:
                    data = json.load(f)
                    return data.get('mappings', {})
            except Exception as e:
                click.echo(f"Error loading product mapping from file: {e}")
        
        # Fall back to config mappings
        return self.config_mappings

    def run(self) -> bool:
        """Run the complete statistical analysis."""
        try:
            click.echo(f"🚀 Starting Stage 3: Statistical Analysis")
            click.echo(f"📁 Input: {self.input_dir}")
            click.echo(f"📁 Output: {self.output_dir}")
            
            # Find all enriched JSON files (search recursively)
            enriched_files = list(self.input_dir.glob("**/*_enriched.json"))
            if not enriched_files:
                click.echo(f"❌ No enriched JSON files found in {self.input_dir}")
                return False

            click.echo(f"✅ Found {len(enriched_files)} enriched files")

            # Process file-level statistics
            file_stats = []
            for file_path in tqdm(enriched_files, desc="Processing files"):
                stats = self._calculate_file_stats(file_path)
                if stats:
                    file_stats.append(stats)

            # Write file-level CSV
            self._write_file_stats_csv(file_stats)

            # Roll up to community level
            community_stats = self._rollup_to_community(file_stats)

            # Write community-level CSV
            self._write_community_stats_csv(community_stats)

            # Roll up to product level
            product_stats = self._rollup_to_product(community_stats)

            # Write product-level CSV
            self._write_product_stats_csv(product_stats)

            click.echo("✅ Statistical analysis completed successfully")
            return True

        except Exception as e:
            click.echo(f"❌ Error in statistical analysis: {e}")
            return False

    def _calculate_file_stats(self, file_path: Path) -> Optional[FileStats]:
        """Calculate statistics for a single enriched file."""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)

            # Parse enriched objects
            objects = [EnrichedObject(**obj) for obj in data]

            # Basic counts
            total_objects = len(objects)
            posts = sum(1 for obj in objects if obj.dataType == 'post')
            comments = sum(1 for obj in objects if obj.dataType == 'comment')

            # Sentiment analysis (for all objects, not just posts)
            positive_posts = sum(1 for obj in objects if obj.analysis.sentiment == 'positive')
            negative_posts = sum(1 for obj in objects if obj.analysis.sentiment == 'negative')
            neutral_posts = sum(1 for obj in objects if obj.analysis.sentiment == 'neutral')
            positive_percent = (positive_posts / total_objects * 100) if total_objects > 0 else 0

            # Category counts
            category_counts = Counter(obj.analysis.category for obj in objects)
            questions = category_counts.get('Question', 0)
            answers = category_counts.get('Answer', 0)
            praise = category_counts.get('Praise', 0)
            complaint = category_counts.get('Complaint', 0)
            top_category = category_counts.most_common(1)[0][0] if category_counts else "Unknown"
            category_counts_json = json.dumps(category_counts)

            # Issues and solutions (placeholder - would need actual extraction logic)
            issues_found = 0  # TODO: Implement issue extraction
            solutions_found = 0  # TODO: Implement solution extraction

            # Get community name (assume all objects in file have same community)
            community = objects[0].communityName if objects else "unknown"

            # Placeholder JSON strings for issues/solutions
            issues_json = "{}"
            solutions_json = "{}"

            return FileStats(
                file_name=file_path.name,
                community=community,
                total_objects=total_objects,
                posts=posts,
                comments=comments,
                positive_posts=positive_posts,
                negative_posts=negative_posts,
                neutral_posts=neutral_posts,
                positive_percent=round(positive_percent, 1),
                questions=questions,
                answers=answers,
                praise=praise,
                complaint=complaint,
                category_counts_json=category_counts_json,
                top_category=top_category,
                issues_found=issues_found,
                solutions_found=solutions_found,
                issues_json=issues_json,
                solutions_json=solutions_json
            )

        except Exception as e:
            click.echo(f"Error processing {file_path}: {e}")
            return None

    def _rollup_to_community(self, file_stats: List[FileStats]) -> List[CommunityStats]:
        """Roll up file statistics to community level."""
        community_groups = defaultdict(list)

        # Group files by community
        for stats in file_stats:
            community_groups[stats.community].append(stats)

        community_stats = []
        for community, files in community_groups.items():
            # Aggregate numeric metrics
            total_files = len(files)
            total_objects = sum(f.total_objects for f in files)
            posts = sum(f.posts for f in files)
            comments = sum(f.comments for f in files)
            positive_posts = sum(f.positive_posts for f in files)
            negative_posts = sum(f.negative_posts for f in files)
            neutral_posts = sum(f.neutral_posts for f in files)
            questions = sum(f.questions for f in files)
            answers = sum(f.answers for f in files)
            praise = sum(f.praise for f in files)
            complaint = sum(f.complaint for f in files)
            category_counts = Counter()
            for f in files:
                try:
                    category_counts.update(json.loads(f.category_counts_json))
                except Exception:
                    continue
            issues_count = sum(f.issues_found for f in files)
            solutions_count = sum(f.solutions_found for f in files)

            # Weighted average for positive percentage
            total_posts = sum(f.posts for f in files)
            positive_percent = (positive_posts / total_posts * 100) if total_posts > 0 else 0

            # Answer rate
            answer_rate = (answers / questions * 100) if questions > 0 else 0

            # Top category (simplified - just pick the highest count)
            top_category = category_counts.most_common(1)[0][0] if category_counts else 'Unknown'

            # Get product mapping
            product = self.product_mapping.get(community, "Unknown")

            # Placeholder top pain point/solution
            top_pain_point = "deployment complexity"  # TODO: Calculate from issues_json
            top_solution = "built-in deployment"  # TODO: Calculate from solutions_json

            community_stats.append(CommunityStats(
                community=community,
                product=product,
                total_files=total_files,
                total_objects=total_objects,
                posts=posts,
                comments=comments,
                positive_posts=positive_posts,
                negative_posts=negative_posts,
                neutral_posts=neutral_posts,
                positive_percent=round(positive_percent, 1),
                questions=questions,
                answers=answers,
                answer_rate=round(answer_rate, 1),
                praise=praise,
                complaint=complaint,
                top_category=top_category,
                category_counts_json=json.dumps(category_counts),
                issues_count=issues_count,
                solutions_count=solutions_count,
                top_pain_point=top_pain_point,
                top_solution=top_solution
            ))

        return community_stats

    def _rollup_to_product(self, community_stats: List[CommunityStats]) -> List[ProductStats]:
        """Roll up community statistics to product level."""
        product_groups = defaultdict(list)

        # Group communities by product
        for stats in community_stats:
            product_groups[stats.product].append(stats)

        product_stats = []
        total_market_objects = sum(s.total_objects for s in community_stats)

        for product, communities in product_groups.items():
            # Aggregate metrics
            total_communities = len(communities)
            total_files = sum(c.total_files for c in communities)
            total_objects = sum(c.total_objects for c in communities)
            posts = sum(c.posts for c in communities)
            comments = sum(c.comments for c in communities)
            positive_posts = sum(c.positive_posts for c in communities)
            negative_posts = sum(c.negative_posts for c in communities)
            neutral_posts = sum(c.neutral_posts for c in communities)
            questions = sum(c.questions for c in communities)
            answers = sum(c.answers for c in communities)
            category_counts = Counter()
            for c in communities:
                try:
                    category_counts.update(json.loads(c.category_counts_json))
                except Exception:
                    continue

            # Weighted averages
            total_posts = sum(c.posts for c in communities)
            positive_percent = (positive_posts / total_posts * 100) if total_posts > 0 else 0
            total_questions = sum(c.questions for c in communities)
            answer_rate = (answers / total_questions * 100) if total_questions > 0 else 0

            # Market share
            market_share_percent = (total_objects / total_market_objects * 100) if total_market_objects > 0 else 0

            # Top pain point/solution (simplified - take from first community)
            top_pain_point = communities[0].top_pain_point if communities else "Unknown"
            top_solution = communities[0].top_solution if communities else "Unknown"

            product_stats.append(ProductStats(
                target_product=product,
                total_communities=total_communities,
                total_files=total_files,
                total_objects=total_objects,
                posts=posts,
                comments=comments,
                positive_posts=positive_posts,
                negative_posts=negative_posts,
                neutral_posts=neutral_posts,
                positive_percent=round(positive_percent, 1),
                questions=questions,
                answers=answers,
                answer_rate=round(answer_rate, 1),
                top_pain_point=top_pain_point,
                top_solution=top_solution,
                market_share_percent=round(market_share_percent, 1),
                category_counts_json=json.dumps(category_counts)
            ))

        return product_stats

    def _write_file_stats_csv(self, stats: List[FileStats]):
        """Write file-level statistics to CSV."""
        with open(self.file_stats_csv, 'w', newline='') as f:
            writer = csv.writer(f)
            # Write header
            writer.writerow([
                'level', 'file_name', 'community', 'total_objects', 'posts', 'comments',
                'positive_posts', 'negative_posts', 'neutral_posts', 'positive_percent', 'questions', 'answers',
                'praise', 'complaint', 'category_counts_json', 'top_category', 'issues_found', 'solutions_found',
                'issues_json', 'solutions_json'
            ])
            # Write data
            for stat in stats:
                writer.writerow([
                    stat.level, stat.file_name, stat.community, stat.total_objects, stat.posts, stat.comments,
                    stat.positive_posts, stat.negative_posts, stat.neutral_posts, stat.positive_percent, stat.questions, stat.answers,
                    stat.praise, stat.complaint, stat.category_counts_json, stat.top_category,
                    stat.issues_found, stat.solutions_found, stat.issues_json, stat.solutions_json
                ])

    def _write_community_stats_csv(self, stats: List[CommunityStats]):
        """Write community-level statistics to CSV."""
        with open(self.community_stats_csv, 'w', newline='') as f:
            writer = csv.writer(f)
            # Write header
            writer.writerow([
                'level', 'community', 'product', 'total_files', 'total_objects', 'posts', 'comments',
                'positive_posts', 'negative_posts', 'neutral_posts', 'positive_percent', 'questions', 'answers',
                'answer_rate', 'praise', 'complaint', 'top_category', 'category_counts_json',
                'issues_count', 'solutions_count', 'top_pain_point', 'top_solution'
            ])
            # Write data
            for stat in stats:
                writer.writerow([
                    stat.level, stat.community, stat.product, stat.total_files, stat.total_objects, stat.posts, stat.comments,
                    stat.positive_posts, stat.negative_posts, stat.neutral_posts, stat.positive_percent, stat.questions, stat.answers,
                    stat.answer_rate, stat.praise, stat.complaint, stat.top_category, stat.category_counts_json,
                    stat.issues_count, stat.solutions_count, stat.top_pain_point, stat.top_solution
                ])

    def _write_product_stats_csv(self, stats: List[ProductStats]):
        """Write product-level statistics to CSV."""
        with open(self.product_stats_csv, 'w', newline='') as f:
            writer = csv.writer(f)
            # Write header
            writer.writerow([
                'level', 'target_product', 'total_communities', 'total_files', 'total_objects', 'posts', 'comments',
                'positive_posts', 'negative_posts', 'neutral_posts', 'positive_percent', 'questions', 'answers',
                'answer_rate', 'top_pain_point', 'top_solution', 'market_share_percent', 'category_counts_json'
            ])
            # Write data
            for stat in stats:
                writer.writerow([
                    stat.level, stat.target_product, stat.total_communities, stat.total_files, stat.total_objects, stat.posts, stat.comments,
                    stat.positive_posts, stat.negative_posts, stat.neutral_posts, stat.positive_percent, stat.questions, stat.answers,
                    stat.answer_rate, stat.top_pain_point, stat.top_solution, stat.market_share_percent, stat.category_counts_json
                ])


@click.command()
@click.option('--input', 'input_dir', type=click.Path(exists=True, path_type=Path),
              required=True, help='Directory containing enriched JSON files')
@click.option('--output', 'output_dir', type=click.Path(path_type=Path), default=None,
              help='Output directory for CSV files (auto-generated if not provided)')
@click.option('--mapping', 'mapping_file', type=click.Path(exists=True, path_type=Path), default=None,
              help='Product mapping JSON file (auto-loaded from config if not provided)')
def main(input_dir: Path, output_dir: Path, mapping_file: Path):
    """Run Stage 3: Statistical Analysis."""
    # DEBUG: Log the import attempt
    import sys
    print("DEBUG: Attempting to import get_output_dir from config_loader...")
    
    # Use config loader for output directory
    if output_dir is None:
        try:
            from config_loader import get_output_dir
            print("DEBUG: Successfully imported get_output_dir")
            output_dir = get_output_dir("statistical_analysis")
        except ImportError as e:
            print(f"DEBUG: Failed to import get_output_dir: {e}")
            # Fallback to default
            from pathlib import Path
            output_dir = Path("output") / "statistical_analysis"
            output_dir.mkdir(parents=True, exist_ok=True)
    
    # Use config loader for mapping file if not provided
    if mapping_file is None:
        try:
            from config_loader import get_product_mapping_path
            mapping_file = get_product_mapping_path()
        except:
            pass
    
    # Use config loader for mapping file if not provided
    if mapping_file is None:
        try:
            from config_loader import config_loader
            mapping_file = config_loader.get_product_mapping_path()
        except:
            pass
    
    click.echo("🚀 Starting Stage 3: Statistical Analysis")
    click.echo(f"📁 Input: {input_dir}")
    click.echo(f"📁 Output: {output_dir}")
    
    calculator = StatisticsCalculator(input_dir, output_dir, mapping_file)
    success = calculator.run()

    if success:
        click.echo(f"✅ Statistics generated in {output_dir}")
        click.echo(f"   - {calculator.file_stats_csv}")
        click.echo(f"   - {calculator.community_stats_csv}")
        click.echo(f"   - {calculator.product_stats_csv}")
    else:
        click.echo("❌ Statistical analysis failed")
        sys.exit(1)


if __name__ == '__main__':
    main()
