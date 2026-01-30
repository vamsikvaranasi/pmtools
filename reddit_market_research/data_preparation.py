#!/usr/bin/env python3
"""
Stage 1: Data Preparation

Preprocess and clean JSON data per input file, reducing fields and preparing for analysis.
Uses config.yaml for settings and creates timestamped output directories.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import click
from langdetect import detect
from tqdm import tqdm

# Handle imports for both module and script execution
try:
    from .config_loader import Config, get_output_dir
except ImportError:
    from config_loader import Config, get_output_dir


class DataPreprocessor:
    """Handles data preprocessing for Stage 1."""

    def __init__(self, input_file: Path, output_dir: Optional[Path] = None):
        self.input_file = input_file
        
        # Use config-managed output directory
        if output_dir is None:
            self.output_dir = get_output_dir("data_preparation")
        else:
            self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Load config for field definitions
        self.config = Config()
        data_config = self.config.data_processing_config
        
        # Minimal required fields for each data type
        self.MINIMAL_FIELDS = {
            'post': data_config.get('post_fields', ['id', 'url', 'title', 'communityName', 'body', 'dataType', 'createdAt', 'upVotes']),
            'comment': data_config.get('comment_fields', ['id', 'url', 'postId', 'parentId', 'communityName', 'body', 'dataType', 'createdAt', 'upVotes'])
        }

        # Output files - directly in output_dir (no subfolders)
        basename = input_file.stem
        self.processed_file = self.output_dir / f"{basename}_processed.json"
        self.summary_file = self.output_dir / "processing_summary.md"
        self.validation_log = self.output_dir / "validation_log.json"

        # Stats
        self.stats = {
            'input_file': str(input_file),
            'processed_at': datetime.now(timezone.utc).isoformat(),
            'total_objects': 0,
            'processed_objects': 0,
            'skipped_objects': 0,
            'language_filtered': 0,
            'invalid_objects': 0,
            'object_types': {'post': 0, 'comment': 0},
            'communities': set(),
            'errors': []
        }

    def run(self) -> bool:
        """Run the complete data preprocessing."""
        try:
            # Load and validate input
            data = self.load_data()
            if data is None:
                return False

            # Process objects
            processed_data = self.process_objects(data)

            # Write outputs
            self.write_processed_data(processed_data)
            self.write_summary()
            self.write_validation_log()

            click.echo(f"✅ Processing complete! {self.stats['processed_objects']} objects processed.")
            return True

        except Exception as e:
            click.echo(f"❌ Processing failed: {e}")
            return False

    def load_data(self) -> Optional[List[Dict[str, Any]]]:
        """Load JSON data from input file."""
        try:
            with open(self.input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if not isinstance(data, list):
                if click.confirm("Invalid structure detected - attempt recovery?"):
                    return self.attempt_recovery()
                else:
                    click.echo("Aborting processing.")
                    return None

            self.stats['total_objects'] = len(data)
            return data

        except json.JSONDecodeError as e:
            if click.confirm(f"JSON decode error: {e}. Attempt recovery?"):
                return self.attempt_recovery()
            else:
                click.echo("Aborting processing.")
                return None
        except Exception as e:
            click.echo(f"Error loading file: {e}")
            return None

    def attempt_recovery(self) -> Optional[List[Dict[str, Any]]]:
        """Attempt to recover data by parsing line by line."""
        data = []
        try:
            with open(self.input_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if line:
                        try:
                            obj = json.loads(line)
                            if isinstance(obj, dict):
                                data.append(obj)
                        except json.JSONDecodeError:
                            # Skip invalid lines
                            continue

            if data:
                click.echo(f"Recovered {len(data)} objects from file.")
                self.stats['total_objects'] = len(data)
                return data
            else:
                click.echo("No valid objects recovered.")
                return None

        except Exception as e:
            click.echo(f"Recovery failed: {e}")
            return None

    def process_objects(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process and reduce objects."""
        processed = []

        with tqdm(total=len(data), desc="Processing objects") as pbar:
            for obj in data:
                reduced = self.reduce_object(obj)
                if reduced:
                    processed.append(reduced)
                    self.stats['processed_objects'] += 1

                    # Update stats
                    data_type = reduced.get('dataType')
                    if data_type in self.stats['object_types']:
                        self.stats['object_types'][data_type] += 1

                    community = reduced.get('communityName')
                    if community:
                        self.stats['communities'].add(community)
                else:
                    self.stats['skipped_objects'] += 1

                pbar.update(1)

        return processed

    def reduce_object(self, obj: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Reduce object to minimal fields and validate."""
        if not isinstance(obj, dict):
            self.stats['invalid_objects'] += 1
            self.stats['errors'].append({'type': 'invalid_type', 'object': str(obj)[:100]})
            return None

        data_type = obj.get('dataType')
        if data_type not in ['post', 'comment']:
            self.stats['invalid_objects'] += 1
            self.stats['errors'].append({'type': 'invalid_data_type', 'data_type': data_type})
            return None

        # Check language
        text = obj.get('body', '') + ' ' + obj.get('title', '')
        if text.strip():
            try:
                lang = detect(text)
                if lang != 'en':
                    self.stats['language_filtered'] += 1
                    return None
            except Exception:
                # If detection fails, assume English
                pass

        # Reduce to minimal fields
        reduced = {}
        required_fields = self.MINIMAL_FIELDS.get(data_type, [])

        for field in required_fields:
            if field in obj:
                reduced[field] = obj[field]
            else:
                self.stats['invalid_objects'] += 1
                self.stats['errors'].append({
                    'type': 'missing_field',
                    'data_type': data_type,
                    'field': field,
                    'id': obj.get('id')
                })
                return None

        # Validate community name
        community = reduced.get('communityName')
        if not community or not community.startswith('r/'):
            self.stats['invalid_objects'] += 1
            self.stats['errors'].append({
                'type': 'invalid_community',
                'community': community,
                'id': obj.get('id')
            })
            return None

        # Validate timestamp
        created_at = reduced.get('createdAt')
        if created_at:
            try:
                datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            except:
                self.stats['invalid_objects'] += 1
                self.stats['errors'].append({
                    'type': 'invalid_timestamp',
                    'timestamp': created_at,
                    'id': obj.get('id')
                })
                return None

        return reduced

    def write_processed_data(self, data: List[Dict[str, Any]]) -> None:
        """Write processed data to JSON file."""
        with open(self.processed_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def write_summary(self) -> None:
        """Write processing summary to markdown."""
        with open(self.summary_file, 'w', encoding='utf-8') as f:
            f.write("# Processing Summary\n\n")
            f.write(f"**Input file**: {self.input_file}\n")
            f.write(f"**Output file**: {self.processed_file}\n")
            f.write(f"**Processed at**: {self.stats['processed_at']}\n\n")

            f.write("## File Statistics\n\n")
            f.write(f"- **Total objects**: {self.stats['total_objects']}\n")
            f.write(f"- **Processed objects**: {self.stats['processed_objects']}\n")
            f.write(f"- **Skipped objects**: {self.stats['skipped_objects']}\n")
            f.write(f"- **Language filtered**: {self.stats['language_filtered']}\n")
            f.write(f"- **Invalid objects**: {self.stats['invalid_objects']}\n\n")

            f.write("## Object Types\n\n")
            for obj_type, count in self.stats['object_types'].items():
                f.write(f"- **{obj_type.title()}s**: {count}\n")
            f.write("\n")

            f.write("## Communities\n\n")
            for community in sorted(self.stats['communities']):
                f.write(f"- **{community}**\n")
            f.write("\n")

            f.write("## Validation\n\n")
            if self.stats['errors']:
                f.write(f"- ⚠️ {len(self.stats['errors'])} validation errors\n")
                f.write("- See validation_log.json for details\n")
            else:
                f.write("- ✅ All objects valid\n")

            f.write("\n## Processing Time\n\n")
            f.write("- **Status**: Complete\n")

    def write_validation_log(self) -> None:
        """Write detailed validation log."""
        log_data = {
            'input_file': str(self.input_file),
            'processed_at': self.stats['processed_at'],
            'validation_results': {
                'total_objects': self.stats['total_objects'],
                'processed_objects': self.stats['processed_objects'],
                'skipped_objects': self.stats['skipped_objects'],
                'language_filtered': self.stats['language_filtered'],
                'invalid_objects': self.stats['invalid_objects'],
                'errors': self.stats['errors']
            },
            'field_reduction': {
                'original_fields_avg': 25,  # Approximate
                'reduced_fields': len(self.MINIMAL_FIELDS['post']),
                'reduction_ratio': ".1f"
            }
        }

        with open(self.validation_log, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)

    def generate_markdown_output(self, data: List[Dict[str, Any]]) -> None:
        """Generate Markdown output from processed data."""
        try:
            # Import the markdown conversion function
            from convert_reddit_to_md import process_reddit_data, generate_markdown

            # Process data for markdown generation
            posts, comments = process_reddit_data(data)

            # Get community name from first post
            community_name = "Unknown Community"
            if posts:
                first_post = next(iter(posts.values()))
                community_name = first_post.get('communityName', 'Unknown Community')

            # Generate markdown
            md_content = generate_markdown(posts, comments, community_name)

            # Write to file
            md_file = self.output_dir / f"{self.input_file.stem}_processed.md"
            with open(md_file, 'w', encoding='utf-8') as f:
                f.write(md_content)

            click.echo(f"📝 Markdown output generated: {md_file}")

        except Exception as e:
            click.echo(f"⚠️  Warning: Could not generate Markdown output: {e}")


@click.command()
@click.option('--input', 'input_file', type=click.Path(exists=True, path_type=Path),
              required=True, help='Input JSON file to process')
@click.option('--output', 'output_dir', type=click.Path(path_type=Path),
              default=None, help='Output directory for results (auto-managed if not specified)')
def main(input_file: Path, output_dir: Optional[Path]):
    """Stage 1: Data Preparation for Reddit Market Research Toolchain."""
    click.echo("🛠️ Reddit Market Research - Stage 1: Data Preparation")
    click.echo(f"Input: {input_file}")
    click.echo(f"Output: {output_dir or 'auto-managed'}")

    processor = DataPreprocessor(input_file, output_dir)
    success = processor.run()

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()