#!/usr/bin/env python3
"""
Reddit Market Research Orchestrator

Automates running all 5 stages of the toolchain on JSON files in a specified directory.

Usage:
    python3 orchestrator.py --input /path/to/json/files --level toy
    python3 orchestrator.py -i /path/to/json/files -l nlp
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class Orchestrator:
    """Orchestrates the complete Reddit Market Research toolchain."""

    STAGES = [
        ("setup_and_validation.py", "Stage 0: Setup & Validation"),
        ("data_preparation.py", "Stage 1: Data Preparation"),
        ("text_analysis.py", "Stage 2: Text Analysis"),
        ("statistical_analysis.py", "Stage 3: Statistical Analysis"),
        ("qa_processing.py", "Stage 4: Q&A Processing"),
        ("visualization.py", "Stage 5: Visualization & Reporting")
    ]

    def __init__(self, input_dir: Path, level: str = "toy"):
        self.input_dir = Path(input_dir).resolve()
        self.level = level
        self.timestamp = datetime.now().strftime("%Y_%m_%d_%H%M")
        self.output_base = self.input_dir / "output"
        self.output_base.mkdir(parents=True, exist_ok=True)

        # Stage output directories (will be set during execution)
        self.stage_outputs = {}
        self.product_mapping = None

    def run(self) -> bool:
        """Execute the complete toolchain."""
        print("=" * 60)
        print("Reddit Market Research Toolchain Orchestrator")
        print("=" * 60)
        print(f"📁 Input directory: {self.input_dir}")
        print(f"📊 Analysis level: {self.level}")
        print(f"📁 Output directory: {self.output_base}")
        print("=" * 60)

        # Stage 0: Setup & Validation
        if not self._run_stage_0():
            return False

        # Stage 1: Data Preparation
        if not self._run_stage_1():
            return False

        # Stage 2: Text Analysis
        if not self._run_stage_2():
            return False

        # Stage 3: Statistical Analysis
        if not self._run_stage_3():
            return False

        # Stage 4: Q&A Processing
        if not self._run_stage_4():
            return False

        # Stage 5: Visualization
        if not self._run_stage_5():
            return False

        self._print_summary()
        return True

    def _get_stage_output(self, stage_num: int) -> Path:
        """Get or create output directory for a stage."""
        if stage_num not in self.stage_outputs:
            stage_name = f"stage{stage_num}_{self.timestamp}"
            output_dir = self.output_base / stage_name
            output_dir.mkdir(parents=True, exist_ok=True)
            self.stage_outputs[stage_num] = output_dir
        return self.stage_outputs[stage_num]

    def _find_json_files(self, directory: Path) -> List[Path]:
        """Find all JSON files in a directory."""
        return sorted(directory.glob("*.json"))

    def _run_stage_0(self) -> bool:
        """Run Stage 0: Setup & Validation."""
        print("\n" + "=" * 60)
        print("STAGE 0: Setup & Validation")
        print("=" * 60)

        output_dir = self._get_stage_output(0)
        cmd = [
            sys.executable, "setup_and_validation.py",
            "--input", str(self.input_dir),
            "--output", str(output_dir)
        ]

        success = self._run_command(cmd, "Setup & Validation")
        
        if success:
            # Load product mapping for later stages
            mapping_file = output_dir / "product_mapping.json"
            if mapping_file.exists():
                with open(mapping_file, 'r') as f:
                    data = json.load(f)
                    self.product_mapping = data.get('mappings', {})
                print(f"✅ Product mapping loaded: {self.product_mapping}")
            else:
                print("⚠️  Warning: product_mapping.json not found")

        return success

    def _run_stage_1(self) -> bool:
        """Run Stage 1: Data Preparation."""
        print("\n" + "=" * 60)
        print("STAGE 1: Data Preparation")
        print("=" * 60)

        json_files = self._find_json_files(self.input_dir)
        if not json_files:
            print("❌ No JSON files found in input directory")
            return False

        print(f"📄 Found {len(json_files)} JSON files to process")
        
        output_dir = self._get_stage_output(1)
        success_count = 0
        fail_count = 0

        for json_file in json_files:
            print(f"\n📝 Processing: {json_file.name}")
            cmd = [
                sys.executable, "data_preparation.py",
                "--input", str(json_file),
                "--output", str(output_dir)
            ]

            if self._run_command(cmd, f"Data Preparation ({json_file.name})"):
                success_count += 1
            else:
                fail_count += 1

        print(f"\n📊 Stage 1 Summary: {success_count} succeeded, {fail_count} failed")
        return fail_count == 0

    def _run_stage_2(self) -> bool:
        """Run Stage 2: Text Analysis."""
        print("\n" + "=" * 60)
        print("STAGE 2: Text Analysis")
        print("=" * 60)

        stage1_output = self._get_stage_output(1)
        processed_files = self._find_json_files(stage1_output)
        processed_files = [f for f in processed_files if "_processed.json" in f.name]

        if not processed_files:
            print("❌ No processed files found from Stage 1")
            return False

        print(f"📄 Found {len(processed_files)} processed files to analyze")
        print(f"📊 Analysis level: {self.level}")

        output_dir = self._get_stage_output(2)
        success_count = 0
        fail_count = 0

        for processed_file in processed_files:
            print(f"\n🧠 Analyzing: {processed_file.name}")
            cmd = [
                sys.executable, "text_analysis.py",
                "--input", str(processed_file),
                "--output", str(output_dir),
                "--level", self.level
            ]

            if self._run_command(cmd, f"Text Analysis ({processed_file.name})"):
                success_count += 1
            else:
                fail_count += 1

        print(f"\n📊 Stage 2 Summary: {success_count} succeeded, {fail_count} failed")
        return fail_count == 0

    def _run_stage_3(self) -> bool:
        """Run Stage 3: Statistical Analysis."""
        print("\n" + "=" * 60)
        print("STAGE 3: Statistical Analysis")
        print("=" * 60)

        stage2_output = self._get_stage_output(2)
        enriched_files = self._find_json_files(stage2_output)
        enriched_files = [f for f in enriched_files if "_enriched.json" in f.name]

        if not enriched_files:
            print("❌ No enriched files found from Stage 2")
            return False

        print(f"📄 Found {len(enriched_files)} enriched files to analyze")

        output_dir = self._get_stage_output(3)

        # Find product mapping from Stage 0
        stage0_output = self._get_stage_output(0)
        mapping_file = stage0_output / "product_mapping.json"

        cmd = [
            sys.executable, "statistical_analysis.py",
            "--input", str(stage2_output),
            "--output", str(output_dir),
            "--mapping", str(mapping_file)
        ]

        return self._run_command(cmd, "Statistical Analysis")

    def _run_stage_4(self) -> bool:
        """Run Stage 4: Q&A Processing."""
        print("\n" + "=" * 60)
        print("STAGE 4: Q&A Processing")
        print("=" * 60)

        stage2_output = self._get_stage_output(2)
        enriched_files = self._find_json_files(stage2_output)
        enriched_files = [f for f in enriched_files if "_enriched.json" in f.name]

        if not enriched_files:
            print("❌ No enriched files found from Stage 2")
            return False

        print(f"📄 Found {len(enriched_files)} enriched files to process")

        output_dir = self._get_stage_output(4)
        
        # Get QA processor variant from config
        try:
            from config_loader import Config
            config = Config()
            qa_variant = config.get('qa_processor.variant', 'plus')
        except ImportError:
            qa_variant = 'plus'
        
        print(f"📊 QA Processor variant: {qa_variant}")
        
        success_count = 0
        fail_count = 0

        for enriched_file in enriched_files:
            print(f"\n🔍 Processing Q&A: {enriched_file.name}")
            cmd = [
                sys.executable, "qa_processing.py",
                str(enriched_file),
                "--output", str(output_dir),
                "--variant", qa_variant
            ]

            if self._run_command(cmd, f"Q&A Processing ({enriched_file.name})"):
                success_count += 1
            else:
                fail_count += 1

        print(f"\n📊 Stage 4 Summary: {success_count} succeeded, {fail_count} failed")
        return fail_count == 0

    def _run_stage_5(self) -> bool:
        """Run Stage 5: Visualization & Reporting."""
        print("\n" + "=" * 60)
        print("STAGE 5: Visualization & Reporting")
        print("=" * 60)

        stage3_output = self._get_stage_output(3)
        stage2_output = self._get_stage_output(2)
        stage0_output = self._get_stage_output(0)

        # Check for required inputs
        stats_product = stage3_output / "statistics_product.csv"
        if not stats_product.exists():
            print("❌ Statistical analysis output not found")
            return False

        print(f"📊 Statistics found: {stats_product.name}")

        mapping_file = stage0_output / "product_mapping.json"
        if not mapping_file.exists():
            print("❌ Product mapping not found")
            return False

        # Final output directory
        final_output = self.output_base / f"final_output_{self.timestamp}"
        final_output.mkdir(parents=True, exist_ok=True)

        cmd = [
            sys.executable, "visualization.py",
            "--stats", str(stage3_output),
            "--output", str(final_output),
            "--mapping", str(mapping_file),
            "--enriched", str(stage2_output)
        ]

        success = self._run_command(cmd, "Visualization & Reporting")
        
        if success:
            self.final_output = final_output

        return success

    def _run_command(self, cmd: List[str], stage_name: str) -> bool:
        """Run a subprocess command and return success status."""
        print(f"\n{'─' * 40}")
        print(f"▶️  Running: {' '.join(cmd[2:])}")
        print(f"{'─' * 40}")

        try:
            result = subprocess.run(
                cmd,
                cwd=Path(__file__).parent.resolve(),
                capture_output=False,
                text=True
            )
            
            if result.returncode == 0:
                print(f"✅ {stage_name} completed successfully")
                return True
            else:
                print(f"❌ {stage_name} failed with exit code {result.returncode}")
                return False

        except Exception as e:
            print(f"❌ {stage_name} error: {e}")
            return False

    def _print_summary(self):
        """Print final summary."""
        print("\n" + "=" * 60)
        print("TOOLCHAIN EXECUTION COMPLETE")
        print("=" * 60)

        print("\n📁 Output Locations:")
        for stage_num in range(6):
            if stage_num in self.stage_outputs:
                print(f"  Stage {stage_num}: {self.stage_outputs[stage_num]}")

        if hasattr(self, 'final_output'):
            print(f"\n📊 Final Report: {self.final_output}")
            print(f"   - executive_summary.md")
            print(f"   - final_report.md")
            print(f"   - sentiment_bar_chart.png")
            print(f"   - sentiment_pie_*.png")
            print(f"   - category_bar_chart.png")
            print(f"   - stacked_category_chart.png")
            print(f"   - wordcloud_*.png")

        print("\n" + "=" * 60)
        print("✅ All stages completed successfully!")
        print("=" * 60)


def main():
    """Main entry point."""
    # Get absolute paths BEFORE changing directory
    # This ensures relative input paths work correctly regardless of cwd
    original_cwd = Path.cwd()
    script_dir = Path(__file__).parent.resolve()
    
    # Now safe to change directory
    os.chdir(script_dir)

    parser = argparse.ArgumentParser(
        description="Reddit Market Research Toolchain Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with toy analysis level (fast, for testing)
  python3 orchestrator.py --input /path/to/data --level toy

  # Run with NLP analysis level (balanced)
  python3 orchestrator.py -i /path/to/data -l nlp

  # Run with LLM analysis level (accurate, requires Ollama)
  python3 orchestrator.py -i /path/to/data -l llm
        """
    )

    parser.add_argument(
        "--input", "-i",
        required=True,
        type=Path,
        help="Input directory containing JSON files"
    )

    parser.add_argument(
        "--level", "-l",
        type=str,
        choices=["toy", "nlp", "llm"],
        default="toy",
        help="Text analysis level (default: toy, options: toy/nlp/llm)"
    )

    args = parser.parse_args()

    # Resolve input path to absolute BEFORE chdir to ensure correct resolution
    # If the input is already absolute, resolve() returns it unchanged
    # If the input is relative, resolve() makes it absolute based on original cwd
    input_dir = (original_cwd / args.input).resolve()

    # Validate input directory
    if not input_dir.exists():
        print(f"❌ Error: Input directory does not exist: {input_dir}")
        sys.exit(1)

    if not input_dir.is_dir():
        print(f"❌ Error: Input path is not a directory: {input_dir}")
        sys.exit(1)

    # Run orchestrator
    orchestrator = Orchestrator(input_dir, args.level)
    success = orchestrator.run()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
