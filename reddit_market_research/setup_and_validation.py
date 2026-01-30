#!/usr/bin/env python3
"""
Stage 0: Setup & Validation

Detect communities, get user product mappings, validate environment and data.
Uses config.yaml for settings and creates timestamped output directories.
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import click

# Handle imports for both module and script execution
try:
    from .config_loader import Config, get_output_dir, get_product_name
except ImportError:
    from config_loader import Config, get_output_dir, get_product_name


class SetupValidator:
    """Handles setup and validation for Stage 0."""

    REQUIRED_PACKAGES = [
        'click', 'tqdm', 'jsonschema', 'textblob', 'vaderSentiment',
        'matplotlib', 'plotly', 'wordcloud', 'langdetect'
    ]

    def __init__(self, input_dir: Path, output_dir: Optional[Path] = None):
        self.input_dir = input_dir
        
        # Use config-managed output directory
        if output_dir is None:
            self.output_dir = get_output_dir("setup_and_validation")
        else:
            self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Load config for product mappings
        self.config = Config()
        self.product_mappings = self.config.product_mappings

        # Log files
        self.env_log = self.output_dir / "environment_check.log"
        self.data_log = self.output_dir / "data_validation.log"
        self.validation_report = self.output_dir / "validation_report.md"
        self.product_mapping = self.output_dir / "product_mapping.json"

    def run(self) -> bool:
        """Run the complete setup and validation process."""
        try:
            click.echo(f"🚀 Reddit Market Research - Stage 0: Setup & Validation")
            click.echo(f"📁 Input: {self.input_dir}")
            click.echo(f"📁 Output: {self.output_dir}")

            # 1. Environment validation
            env_ok = self.validate_environment()
            if not env_ok:
                click.echo("❌ Environment validation failed. Check environment_check.log")
                return False

            # 2. Community detection
            communities = self.detect_communities()
            if not communities:
                click.echo("❌ No communities found in input files.")
                return False

            click.echo(f"\n📋 Detected communities:")
            for community in sorted(communities):
                click.echo(f"  - {community}")

            # 3. Product mapping (use config mappings, fallback to auto-detection)
            mapping = self.get_product_mapping(communities)
            if not mapping:
                click.echo("❌ Product mapping failed.")
                return False

            # 4. Data validation
            data_ok = self.validate_data()
            if not data_ok:
                click.echo("❌ Data validation failed. Check data_validation.log")
                return False

            # 5. Generate report
            self.generate_validation_report(env_ok, communities, mapping, data_ok)

            click.echo("\n✅ Setup complete! Ready for processing.")
            return True

        except Exception as e:
            click.echo(f"❌ Setup failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    def validate_environment(self) -> bool:
        """Validate Python environment and dependencies."""
        issues = []

        # Python version
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        if sys.version_info < (3, 8):
            issues.append(f"Python {python_version} < 3.8 (minimum required)")

        # Required packages
        missing_packages = []
        for package in self.REQUIRED_PACKAGES:
            try:
                __import__(package)
            except ImportError:
                missing_packages.append(package)

        if missing_packages:
            issues.append(f"Missing packages: {', '.join(missing_packages)}")

        # Ollama check (optional)
        ollama_ok = self.check_ollama()

        # System resources (basic check)
        import psutil
        ram_gb = psutil.virtual_memory().total / (1024**3)
        if ram_gb < 4:
            issues.append(f"Low RAM: {ram_gb:.1f}GB (recommended: 4GB+)")

        # Write log
        with open(self.env_log, 'w') as f:
            f.write(f"Environment Check - {datetime.now(timezone.utc).isoformat()}\n")
            f.write(f"Python version: {python_version}\n")
            f.write(f"Required packages: {'OK' if not missing_packages else f'Missing: {missing_packages}'}\n")
            f.write(f"Ollama: {'Available' if ollama_ok else 'Not available'}\n")
            f.write(f"RAM: {ram_gb:.1f}GB\n")
            if issues:
                f.write(f"Issues: {'; '.join(issues)}\n")

        return len(issues) == 0

    def check_ollama(self) -> bool:
        """Check if Ollama is available."""
        try:
            import requests
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False

    def detect_communities(self) -> Set[str]:
        """Detect unique communities from input files."""
        communities = set()

        for json_file in self.input_dir.glob("*.json"):
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        for obj in data:
                            if isinstance(obj, dict) and 'communityName' in obj:
                                communities.add(obj['communityName'])
                    elif isinstance(data, dict) and 'communityName' in data:
                        communities.add(data['communityName'])

            except Exception as e:
                click.echo(f"Warning: Could not scan {json_file}: {e}")

        return communities

    def get_product_mapping(self, communities: Set[str]) -> Optional[Dict[str, str]]:
        """Get product mappings using config or auto-detection."""
        mapping = {}

        # Use config mappings first, then auto-detect for unknown communities
        for community in communities:
            # Check if we have a config mapping
            if community in self.product_mappings:
                mapping[community] = self.product_mappings[community]
            else:
                # Auto-detect: capitalize and clean
                product_name = community.replace('r/', '').replace('_', ' ').title()
                mapping[community] = product_name

        click.echo("\n💡 Product mappings:")
        for community, product in sorted(mapping.items()):
            click.echo(f"  {community} → {product}")

        # Save mapping
        mapping_data = {
            "mappings": mapping,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "input_files_scanned": len(list(self.input_dir.glob("*.json")))
        }

        with open(self.product_mapping, 'w') as f:
            json.dump(mapping_data, f, indent=2)

        return mapping

    def validate_data(self) -> bool:
        """Validate all input JSON files."""
        total_objects = 0
        valid_objects = 0
        errors = []

        with open(self.data_log, 'w') as log_f:
            log_f.write(f"Data Validation - {datetime.now(timezone.utc).isoformat()}\n\n")

            for json_file in self.input_dir.glob("*.json"):
                log_f.write(f"Validating file: {json_file}\n")
                try:
                    with open(json_file, 'r') as f:
                        data = json.load(f)

                    if not isinstance(data, list):
                        errors.append(f"{json_file}: Not a JSON array")
                        log_f.write(f"  ERROR: Not a JSON array\n")
                        continue

                    file_objects = 0
                    file_valid = 0

                    for i, obj in enumerate(data):
                        file_objects += 1
                        if self.validate_object(obj):
                            file_valid += 1
                        else:
                            errors.append(f"{json_file}[{i}]: Invalid object")
                            log_f.write(f"  ERROR: Object {i} invalid\n")

                    log_f.write(f"  File valid: {file_valid}/{file_objects} objects parsed successfully\n")
                    total_objects += file_objects
                    valid_objects += file_valid

                    # Extract communities
                    communities = set()
                    for obj in data:
                        if isinstance(obj, dict) and 'communityName' in obj:
                            communities.add(obj['communityName'])
                    if communities:
                        log_f.write(f"  Communities found: {', '.join(sorted(communities))}\n")

                except json.JSONDecodeError as e:
                    errors.append(f"{json_file}: Invalid JSON - {e}")
                    log_f.write(f"  ERROR: Invalid JSON - {e}\n")
                except Exception as e:
                    errors.append(f"{json_file}: {e}")
                    log_f.write(f"  ERROR: {e}\n")

                log_f.write("\n")

        click.echo(f"\n📊 Data validation: {valid_objects}/{total_objects} objects valid")
        return len(errors) == 0

    def validate_object(self, obj: dict) -> bool:
        """Validate a single data object."""
        if not isinstance(obj, dict):
            return False

        # Required fields based on dataType
        data_type = obj.get('dataType')
        if data_type not in ['community', 'post', 'comment']:
            return False

        required_fields = ['id', 'dataType']
        if data_type in ['post', 'comment']:
            required_fields.extend(['body', 'communityName'])

        for field in required_fields:
            if field not in obj:
                return False

        # Validate communityName
        community = obj.get('communityName')
        if community and not community.startswith('r/'):
            return False

        # Validate timestamp if present
        created_at = obj.get('createdAt')
        if created_at:
            try:
                datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            except:
                return False

        # Validate numeric fields
        numeric_fields = ['upVotes', 'numberOfComments']
        for field in numeric_fields:
            if field in obj and not isinstance(obj[field], (int, float)):
                return False

        return True

    def generate_validation_report(self, env_ok: bool, communities: Set[str],
                                 mapping: Dict[str, str], data_ok: bool) -> None:
        """Generate the final validation report."""
        with open(self.validation_report, 'w') as f:
            f.write("# Validation Report\n\n")
            f.write(f"Generated: {datetime.now(timezone.utc).isoformat()}\n\n")

            f.write("## Environment Check\n")
            if env_ok:
                f.write("- ✅ Python 3.8+\n")
                f.write("- ✅ Required packages installed\n")
                f.write("- ✅ Ollama available (optional)\n")
                f.write("- ✅ System resources OK\n")
            else:
                f.write("- ❌ Environment issues found (see environment_check.log)\n")

            f.write("\n## Data Validation\n")
            total_files = len(list(self.input_dir.glob("*.json")))
            f.write(f"- Files scanned: {total_files}\n")
            if data_ok:
                f.write("- ✅ All files valid\n")
            else:
                f.write("- ❌ Validation errors found (see data_validation.log)\n")

            f.write("\n## Product Mapping\n")
            f.write(f"- Communities detected: {len(communities)}\n")
            for community, product in sorted(mapping.items()):
                f.write(f"  - {community} → {product}\n")
            f.write("- ✅ Mappings saved\n")

            f.write("\n## Status\n")
            if env_ok and data_ok:
                f.write("Ready for processing\n")
            else:
                f.write("Issues found - review logs before proceeding\n")


@click.command()
@click.option('--input', 'input_dir', type=click.Path(exists=True, path_type=Path),
              default='data', help='Input directory containing JSON files')
@click.option('--output', 'output_dir', type=click.Path(path_type=Path),
              default=None, help='Output directory (auto-managed if not specified)')
def main(input_dir: Path, output_dir: Path):
    """Stage 0: Setup & Validation for Reddit Market Research Toolchain."""
    validator = SetupValidator(input_dir, output_dir)
    success = validator.run()

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
