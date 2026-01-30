#!/usr/bin/env python3
"""
Text Analysis - Stage 2

Enrich processed Reddit data with sentiment and category analysis.
Uses config.yaml for settings and creates timestamped output directories.
"""

import json
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional

import click
from tqdm import tqdm

# Handle imports for both module and script execution
try:
    from .text_analyzer import BaseAnalyzer, ToyAnalyzer, NLPAnalyzer, LLMAnalyzer
    from .config_loader import Config, get_output_dir
except ImportError:
    from text_analyzer import BaseAnalyzer, ToyAnalyzer, NLPAnalyzer, LLMAnalyzer
    from config_loader import Config, get_output_dir


class TextAnalysisProcessor:
    """Handles text analysis processing for Stage 2."""

    ANALYSIS_LEVELS = {
        'toy': ToyAnalyzer,
        'nlp': NLPAnalyzer,
        'llm': LLMAnalyzer
    }

    def __init__(self, input_file: Path, output_dir: Optional[Path] = None, level: str = 'toy',
                 config: Optional[Dict[str, Any]] = None):
        self.input_file = input_file
        
        # Use config-managed output directory
        if output_dir is None:
            self.output_dir = get_output_dir("text_analysis")
        else:
            self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.level = level
        
        # Load config for settings
        self.config_obj = Config()
        text_config = self.config_obj.text_analysis_config
        
        # Merge provided config with defaults from config.yaml
        default_llm_config = text_config.get('llm', {})
        self.config = {
            'llm_model': config.get('llm_model', default_llm_config.get('model', 'mistral:latest')) if config else default_llm_config.get('model', 'mistral:latest'),
            'llm_base_url': config.get('llm_url', default_llm_config.get('base_url', 'http://localhost:11434')) if config else default_llm_config.get('base_url', 'http://localhost:11434'),
            'max_retries': config.get('max_retries', default_llm_config.get('max_retries', 3)) if config else default_llm_config.get('max_retries', 3),
            'retry_delay': config.get('retry_delay', default_llm_config.get('retry_delay', 1.0)) if config else default_llm_config.get('retry_delay', 1.0),
            'prompt_file': config.get('prompt_file', text_config.get('prompt_file')) if config else text_config.get('prompt_file'),
        }

        # Output files - directly in output_dir (no subfolders)
        basename = input_file.stem
        self.enriched_file = self.output_dir / f"{basename}_enriched.json"
        self.analysis_summary = self.output_dir / "analysis_summary.md"

        # Initialize analyzer
        self.analyzer = self._create_analyzer()

        # Stats
        self.stats = {
            'input_file': str(input_file),
            'analysis_level': level,
            'total_objects': 0,
            'processed_objects': 0,
            'sentiment_distribution': {'positive': 0, 'neutral': 0, 'negative': 0},
            'category_distribution': {},
            'errors': []
        }

    def _create_analyzer(self) -> BaseAnalyzer:
        """Create the appropriate analyzer based on level."""
        analyzer_class = self.ANALYSIS_LEVELS.get(self.level)
        if not analyzer_class:
            raise ValueError(f"Unknown analysis level: {self.level}")

        try:
            return analyzer_class(self.config)
        except ImportError as e:
            raise ImportError(f"Required dependencies not available for {self.level} analysis: {e}")

    def run(self) -> bool:
        """Run the complete text analysis."""
        try:
            # Load processed data
            click.echo(f"Loading processed data from {self.input_file}...")
            with open(self.input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.stats['total_objects'] = len(data)

            # Analyze objects
            click.echo(f"Analyzing {len(data)} objects using {self.level} analysis...")
            start_time = time.time()
            enriched_data = self._analyze_objects(data)
            total_time_ms = (time.time() - start_time) * 1000

            # Calculate time statistics
            self.stats['total_time_ms'] = round(total_time_ms, 3)
            if self.stats['processed_objects'] > 0:
                self.stats['average_time_ms'] = round(total_time_ms / self.stats['processed_objects'], 3)
            else:
                self.stats['average_time_ms'] = 0.0

            # Write outputs
            self._write_enriched_data(enriched_data)
            self._write_analysis_summary()

            click.echo(f"✅ Analysis complete! {self.stats['processed_objects']} objects enriched.")
            click.echo(f"⏱️  Total time: {self._format_time(total_time_ms / 1000)}")
            click.echo(f"⚡ Average time per object: {self._format_time(self.stats['average_time_ms'] / 1000)}")
            return True

        except Exception as e:
            click.echo(f"❌ Analysis failed: {e}")
            return False

    def _analyze_objects(self, objects: list) -> list:
        """Analyze all objects with progress bar."""
        enriched = []

        with tqdm(total=len(objects), desc=f"{self.level.upper()} Analysis") as pbar:
            for obj in objects:
                try:
                    enriched_obj = self.analyzer.analyze_object(obj)
                    enriched.append(enriched_obj)

                    # Update stats
                    self._update_stats(enriched_obj)
                    self.stats['processed_objects'] += 1

                except Exception as e:
                    error_msg = f"Failed to analyze object {obj.get('id', 'unknown')}: {e}"
                    self.stats['errors'].append(error_msg)
                    click.echo(f"Warning: {error_msg}")

                pbar.update(1)

        return enriched

    def _update_stats(self, obj: Dict[str, Any]) -> None:
        """Update statistics from analyzed object."""
        analysis = obj.get('analysis', {})

        # Sentiment
        sentiment = analysis.get('sentiment')
        if sentiment in self.stats['sentiment_distribution']:
            self.stats['sentiment_distribution'][sentiment] += 1

        # Category
        category = analysis.get('category')
        if category:
            self.stats['category_distribution'][category] = \
                self.stats['category_distribution'].get(category, 0) + 1



    def _write_enriched_data(self, data: list) -> None:
        """Write enriched data to JSON file."""
        with open(self.enriched_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)

    def _format_time(self, seconds: float) -> str:
        """Format time in human-readable format (ns, μs, ms, s, m, h)."""
        if seconds < 1e-6:
            return f"{seconds * 1e9:.0f}ns"
        elif seconds < 1e-3:
            return f"{seconds * 1e6:.0f}μs"
        elif seconds < 1:
            return f"{seconds * 1e3:.1f}ms"
        elif seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            remaining_seconds = seconds % 60
            return f"{minutes}m {remaining_seconds:.0f}s"
        else:
            hours = int(seconds // 3600)
            remaining_minutes = int((seconds % 3600) // 60)
            remaining_seconds = seconds % 60
            if remaining_seconds > 0:
                return f"{hours}h {remaining_minutes}m {remaining_seconds:.0f}s"
            return f"{hours}h {remaining_minutes}m"

    def _write_analysis_summary(self) -> None:
        """Write analysis summary to markdown."""
        from datetime import datetime, timezone

        with open(self.analysis_summary, 'w', encoding='utf-8') as f:
            f.write("# Text Analysis Summary\n\n")
            f.write(f"**Input file**: {self.input_file}\n")
            f.write(f"**Output file**: {self.enriched_file}\n")
            f.write(f"**Analysis level**: {self.level.upper()}\n")
            if self.level == 'llm':
                f.write(f"**LLM Model**: {self.config.get('llm_model', 'mistral:latest')}\n")
            f.write(f"**Processed at**: {datetime.now(timezone.utc).isoformat()}\n\n")

            f.write("## Processing Statistics\n\n")
            f.write(f"- **Total objects**: {self.stats['total_objects']}\n")
            f.write(f"- **Processed objects**: {self.stats['processed_objects']}\n")
            if 'total_time_ms' in self.stats:
                f.write(f"- **Total time**: {self._format_time(self.stats['total_time_ms'] / 1000)}\n")
                f.write(f"- **Average time per object**: {self._format_time(self.stats['average_time_ms'] / 1000)}\n")
                # Calculate projected time for 3000 objects
                projected_time = (self.stats['average_time_ms'] / 1000) * 3000
                f.write(f"- **Projected time for 3000 objects**: {self._format_time(projected_time)}\n")
            f.write("\n")

            f.write("## Sentiment Distribution\n\n")
            total = sum(self.stats['sentiment_distribution'].values())
            for sentiment, count in self.stats['sentiment_distribution'].items():
                percentage = (count / total * 100) if total > 0 else 0
                f.write(f"- **{sentiment.title()}**: {count} ({percentage:.1f}%)\n")
            f.write("\n")

            f.write("## Category Distribution\n\n")
            for category, count in sorted(self.stats['category_distribution'].items(),
                                        key=lambda x: x[1], reverse=True):
                percentage = (count / total * 100) if total > 0 else 0
                f.write(f"- **{category}**: {count} ({percentage:.1f}%)\n")
            f.write("\n")

            if self.stats['errors']:
                f.write("## Errors\n\n")
                for error in self.stats['errors'][:10]:  # Show first 10
                    f.write(f"- {error}\n")
                if len(self.stats['errors']) > 10:
                    f.write(f"- ... and {len(self.stats['errors']) - 10} more errors\n")


@click.command()
@click.option('--input', 'input_file', type=click.Path(exists=True, path_type=Path),
              required=True, help='Processed JSON file to analyze')
@click.option('--output', 'output_dir', type=click.Path(path_type=Path),
              default=None, help='Output directory for results (auto-managed if not specified)')
@click.option('--level', type=click.Choice(['toy', 'nlp', 'llm']),
              default='toy', help='Analysis level (toy=fast, nlp=balanced, llm=accurate)')
@click.option('--llm-model', default=None, help='LLM model for LLM analysis')
@click.option('--llm-url', default=None, help='Ollama server URL')
@click.option('--prompt-file', default=None, help='Custom prompt file for LLM analysis')
def main(input_file: Path, output_dir: Optional[Path], level: str, llm_model: str, llm_url: str, prompt_file: str):
    """Text Analysis - Stage 2 for Reddit Market Research Toolchain."""
    click.echo("🧠 Reddit Market Research - Stage 2: Text Analysis")
    click.echo(f"Input: {input_file}")
    click.echo(f"Output: {output_dir or 'auto-managed'}")
    click.echo(f"Level: {level}")
    if prompt_file:
        click.echo(f"Using custom prompt: {prompt_file}")

    # Config for analyzers (only override if explicitly provided)
    config = {}
    if llm_model:
        config['llm_model'] = llm_model
    if llm_url:
        config['llm_url'] = llm_url
    if prompt_file:
        config['prompt_file'] = prompt_file

    processor = TextAnalysisProcessor(input_file, output_dir, level, config)
    success = processor.run()

    sys.exit(0 if success else 1)
    config = {
        'llm_model': llm_model,
        'llm_base_url': llm_url,
        'max_retries': 3,
        'retry_delay': 1.0,
        'prompt_file': prompt_file
    }

    processor = TextAnalysisProcessor(input_file, output_dir, level, config)
    success = processor.run()

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()