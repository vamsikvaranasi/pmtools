#!/usr/bin/env python3
"""
Q&A Processing - Stage 4

Extract, group, and summarize questions and answers from enriched Reddit data.
Supports both standard and plus variants based on config.
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import click
from tqdm import tqdm


def get_qa_processor_class(variant: str = "plus"):
    """Get the appropriate QA processor class based on variant."""
    if variant == "plus":
        try:
            # relative Try import first (when running as module)
            from .qa_processor_plus.qa_processor_plus import QAProcessorPlus
            return QAProcessorPlus
        except ImportError:
            # Fallback to absolute import (when running as script)
            from qa_processor_plus.qa_processor_plus import QAProcessorPlus
            return QAProcessorPlus
    else:
        # Standard qa_processor
        try:
            from .qa_processor import QAProcessor
            return QAProcessor
        except ImportError:
            from qa_processor import QAProcessor
            return QAProcessor


# Handle imports for both module and script execution
try:
    from .config_loader import Config
    from .qa_processor import QAGrouper, PainPointExtractor, SolutionExtractor, QAReportGenerator
except ImportError:
    from config_loader import Config
    from qa_processor import QAGrouper, PainPointExtractor, SolutionExtractor, QAReportGenerator


class QAProcessor:
    """Handles Q&A processing for Stage 4."""

    def __init__(self, input_file: Path, output_dir: Path, community: Optional[str] = None,
                 config: Optional[Dict[str, Any]] = None):
        self.input_file = input_file
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.community = community or self._detect_community()
        self.config = config or {}

        # Output files
        community_name = self.community.replace('r/', '') if self.community.startswith('r/') else self.community
        self.qa_report_json = output_dir / f"qa_report_{community_name}.json"
        self.qa_report_md = output_dir / f"qa_report_{community_name}.md"
        self.conversations_json = output_dir / f"qa_conversations_{community_name}.json"
        self.pain_points_json = output_dir / f"pain_points_{community_name}.json"
        self.solutions_json = output_dir / f"solutions_{community_name}.json"
        self.processing_summary = output_dir / "qa_processing_summary.md"

        # Initialize processors
        self.grouper = QAGrouper()
        self.pain_point_extractor = PainPointExtractor()
        self.solution_extractor = SolutionExtractor()
        self.report_generator = QAReportGenerator()

        # Stats
        self.stats = {
            'input_file': str(input_file),
            'community': self.community,
            'total_objects': 0,
            'questions_found': 0,
            'answers_found': 0,
            'conversations_created': 0,
            'pain_points_identified': 0,
            'solutions_identified': 0
        }

    def _detect_community(self) -> str:
        """Detect community from input file data."""
        try:
            with open(self.input_file, 'r', encoding='utf-8') as f:
                # Read first few objects to detect community
                content = f.read(10000)  # Read first 10KB
                # Simple detection - look for communityName in JSON
                if '"communityName"' in content:
                    # Extract first community name found
                    lines = content.split('\n')
                    for line in lines:
                        if '"communityName"' in line and 'r/' in line:
                            start = line.find('r/')
                            end = line.find('"', start)
                            if end > start:
                                return line[start:end]
        except Exception as e:
            print(f"Warning: Could not detect community from file: {e}")

        return "unknown"

    def process(self) -> Dict[str, Any]:
        """Main processing pipeline."""
        print(f"🔍 Processing Q&A data from {self.input_file}")
        print(f"📊 Target community: {self.community}")

        # Load enriched data
        enriched_objects = self._load_enriched_data()
        self.stats['total_objects'] = len(enriched_objects)

        # Group Q&A conversations
        conversations = self._group_conversations(enriched_objects)
        self.stats['conversations_created'] = len(conversations)

        # Extract pain points
        pain_points_data = self._extract_pain_points(conversations)

        # Extract solutions
        solutions_data = self._extract_solutions(conversations)

        # Generate reports
        self._generate_reports(conversations, pain_points_data, solutions_data)

        # Generate processing summary
        self._generate_processing_summary()

        return self.stats

    def _load_enriched_data(self) -> list:
        """Load enriched JSON data."""
        print("📂 Loading enriched data...")
        
        try:
            with open(self.input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    print(f"✅ Loaded {len(data)} enriched objects")
                    return data
                else:
                    print("Warning: Expected JSON array but got object")
                    return []
        except json.JSONDecodeError as e:
            print(f"Error loading JSON: {e}")
            return []

    def _group_conversations(self, enriched_objects: list) -> Dict[str, Dict[str, Any]]:
        """Group objects into Q&A conversations."""
        print("🔗 Grouping Q&A conversations...")

        conversations = self.grouper.group_qa_conversations(enriched_objects)

        # Update stats
        total_questions = len(conversations)
        total_answers = sum(len(conv.get('answers', [])) for conv in conversations.values())

        self.stats['questions_found'] = total_questions
        self.stats['answers_found'] = total_answers

        print(f"✅ Created {total_questions} question threads with {total_answers} answers")
        return conversations

    def _extract_pain_points(self, conversations: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Extract pain points from conversations."""
        print("🎯 Extracting pain points...")

        pain_points_data = self.pain_point_extractor.extract_pain_points(conversations)

        self.stats['pain_points_identified'] = len(pain_points_data.get('pain_points', []))

        print(f"✅ Identified {len(pain_points_data.get('pain_points', []))} unique pain points")
        return pain_points_data

    def _extract_solutions(self, conversations: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Extract solutions from conversations."""
        print("💡 Extracting solutions...")

        solutions_data = self.solution_extractor.extract_solutions(conversations)

        self.stats['solutions_identified'] = len(solutions_data.get('solutions', []))

        print(f"✅ Identified {len(solutions_data.get('solutions', []))} unique solutions")
        return solutions_data

    def _generate_reports(self, conversations: Dict[str, Dict[str, Any]],
                         pain_points_data: Dict[str, Any], solutions_data: Dict[str, Any]):
        """Generate all output reports."""
        print("📄 Generating reports...")

        reports = self.report_generator.generate_reports(
            self.community, conversations, pain_points_data, solutions_data, self.output_dir
        )

        print(f"✅ Generated {len(reports)} report files:")
        for report_type, file_path in reports.items():
            print(f"   - {report_type}: {file_path.name}")

    def _generate_processing_summary(self):
        """Generate processing summary markdown."""
        summary_content = f"""# Q&A Processing Summary

## Input
- **File**: {self.input_file}
- **Community**: {self.community}
- **Total objects**: {self.stats['total_objects']}

## Processing Results
- **Questions found**: {self.stats['questions_found']}
- **Answers found**: {self.stats['answers_found']}
- **Conversations created**: {self.stats['conversations_created']}
- **Pain points identified**: {self.stats['pain_points_identified']}
- **Solutions identified**: {self.stats['solutions_identified']}

## Output Files
 - `qa_report_{self.community.replace('r/', '')}.json` - Comprehensive JSON report
- `qa_report_{self.community.replace('r/', '')}.md` - Human-readable Markdown report
- `qa_conversations_{self.community.replace('r/', '')}.json` - Conversation threads
- `pain_points_{self.community.replace('r/', '')}.json` - Pain points analysis
- `solutions_{self.community.replace('r/', '')}.json` - Solutions analysis

## Status: ✅ Processing Complete
"""

        with open(self.processing_summary, 'w', encoding='utf-8') as f:
            f.write(summary_content)

        print(f"✅ Processing summary saved to {self.processing_summary}")


@click.command()
@click.argument('input_file', type=click.Path(exists=True, path_type=Path))
@click.option('--output', '-o', 'output_dir', type=click.Path(path_type=Path), default=None,
              help='Output directory (auto-generated if not provided)')
@click.option('--community', '-c', help='Target community (auto-detected if not provided)')
@click.option('--variant', '-v', type=click.Choice(['standard', 'plus']), default=None,
              help='QA processor variant (overrides config)')
def main(input_file: Path, output_dir: Path, community: Optional[str], variant: Optional[str]):
    """Process Q&A data from enriched Reddit JSON."""
    # Use config loader for output directory and settings
    if output_dir is None:
        from config_loader import get_output_dir
        output_dir = get_output_dir("qa_processing")
    
    # Get processor variant from config or command line
    processor_variant = variant
    if processor_variant is None:
        config = Config()
        processor_variant = config.get('qa_processor.variant', 'plus')
    
    # Get the appropriate processor class
    QAProcessorClass = get_qa_processor_class(processor_variant)
    
    click.echo(f"🔍 Q&A Processing - Stage 4 (variant: {processor_variant})")
    click.echo(f"📁 Input: {input_file}")
    click.echo(f"📁 Output: {output_dir}")
    
    if processor_variant == "plus":
        # Use QAProcessorPlus from qa_processor_plus
        try:
            from qa_processor_plus.qa_processor_plus import QAProcessorPlus
            plus_processor = QAProcessorPlus()
            
            # Set up input/output
            plus_processor.input_file = input_file
            plus_processor.output_dir = output_dir
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Detect community
            if community:
                plus_processor.community = community
            elif hasattr(plus_processor, '_detect_community'):
                plus_processor.community = plus_processor._detect_community()
            else:
                plus_processor.community = "unknown"
            
            # Set output files
            community_name = plus_processor.community.replace('r/', '') if plus_processor.community and plus_processor.community.startswith('r/') else 'unknown'
            plus_processor.qa_report_json = output_dir / f"qa_report_{community_name}.json"
            plus_processor.qa_report_md = output_dir / f"qa_report_{community_name}.md"
            plus_processor.processing_summary = output_dir / "qa_processing_summary.md"
            
            # Run processing using the public method
            if hasattr(plus_processor, 'process_conversations'):
                with open(input_file, 'r') as f:
                    conversations = json.load(f)
                stats = plus_processor.process_conversations(conversations)
            else:
                stats = plus_processor.process()
        except ImportError as e:
            click.echo(f"⚠️ QAProcessorPlus not available: {e}")
            click.echo("Falling back to standard QAProcessor")
            processor = QAProcessorClass(input_file, output_dir, community)
            stats = processor.process()
    else:
        # Use standard QAProcessor
        processor = QAProcessorClass(input_file, output_dir, community)
        stats = processor.process()

    click.echo("\n🎉 Q&A Processing Complete!")
    click.echo(f"📊 Processed {stats.get('total_objects', 0)} objects")
    if 'questions_found' in stats:
        click.echo(f"🔍 Found {stats['questions_found']} questions and {stats['answers_found']} answers")
    click.echo(f"📁 Reports saved to {output_dir}")


if __name__ == '__main__':
    main()
