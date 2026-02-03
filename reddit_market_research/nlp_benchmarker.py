#!/usr/bin/env python3
"""
NLP Benchmarker

Runs text analysis, statistics, and visualization for VADER and DistilBERT backends,
then produces a markdown report comparing outputs.
"""

import argparse
import csv
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from data_preparation import DataPreprocessor
from setup_and_validation import SetupValidator
from text_analysis import TextAnalysisProcessor
from statistical_analysis import StatisticsCalculator
from visualization import Visualizer


def _ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def _find_json_files(input_dir: Path) -> List[Path]:
    return sorted(input_dir.glob("*.json"))


def _summarize_stats(stats_dir: Path) -> Dict[str, str]:
    stats_file = stats_dir / "statistics_product.csv"
    if not stats_file.exists():
        return {}

    totals = {
        "total_objects": 0,
        "posts": 0,
        "positive_posts": 0,
        "negative_posts": 0,
        "neutral_posts": 0
    }
    category_counts = {}

    with open(stats_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            for key in totals:
                totals[key] += int(float(row.get(key, 0) or 0))
            try:
                counts = json.loads(row.get("category_counts_json", "{}"))
            except json.JSONDecodeError:
                counts = {}
            for category, count in counts.items():
                category_counts[category] = category_counts.get(category, 0) + int(count)

    sentiment_total = totals["positive_posts"] + totals["negative_posts"] + totals["neutral_posts"]
    positive_percent = (totals["positive_posts"] / sentiment_total * 100) if sentiment_total else 0
    top_category = max(category_counts, key=category_counts.get) if category_counts else "Unknown"
    top_category_count = category_counts.get(top_category, 0)

    return {
        "total_objects": str(totals["total_objects"]),
        "posts": str(totals["posts"]),
        "positive_posts": str(totals["positive_posts"]),
        "neutral_posts": str(totals["neutral_posts"]),
        "negative_posts": str(totals["negative_posts"]),
        "positive_percent": f"{positive_percent:.1f}%",
        "top_category": f"{top_category} ({top_category_count})"
    }


def _write_report(report_path: Path, sections: Dict[str, Dict[str, Path]]) -> None:
    lines = ["# NLP Benchmark Report", "", f"Generated: {datetime.now().isoformat()}", ""]

    for backend, paths in sections.items():
        lines.append(f"## {backend.capitalize()} Backend")
        lines.append("")
        lines.append("### Summary")
        summary = paths.get("summary", {})
        if summary:
            lines.append("| Metric | Value |")
            lines.append("| --- | --- |")
            lines.append(f"| Total objects | {summary.get('total_objects', '0')} |")
            lines.append(f"| Total posts | {summary.get('posts', '0')} |")
            lines.append(f"| Positive | {summary.get('positive_posts', '0')} |")
            lines.append(f"| Neutral | {summary.get('neutral_posts', '0')} |")
            lines.append(f"| Negative | {summary.get('negative_posts', '0')} |")
            lines.append(f"| Positive % | {summary.get('positive_percent', '0.0%')} |")
            lines.append(f"| Top category | {summary.get('top_category', 'Unknown')} |")
        else:
            lines.append("No summary available.")
        lines.append("")
        lines.append("### Outputs")
        lines.append(f"- Stats directory: `{paths['stats']}`")
        lines.append(f"- Visualization directory: `{paths['visuals']}`")
        lines.append("")
        lines.append("### Charts")
        lines.append(f"![{backend} Sentiment Bar]({paths['visuals'].name}/sentiment_bar_chart.png)")
        lines.append(f"![{backend} Category Bar]({paths['visuals'].name}/category_bar_chart.png)")
        lines.append(f"![{backend} Stacked Category]({paths['visuals'].name}/stacked_category_chart.png)")
        lines.append("")
        lines.append("### Reports")
        lines.append(f"- `executive_summary.md`: `{paths['visuals'].name}/executive_summary.md`")
        lines.append(f"- `final_report.md`: `{paths['visuals'].name}/final_report.md`")
        lines.append("")

    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark VADER vs DistilBERT NLP backends")
    parser.add_argument("--input", "-i", required=True, type=Path, help="Input directory of JSON files")
    parser.add_argument("--output", "-o", default=None, type=Path, help="Output directory for benchmark results")
    args = parser.parse_args()

    input_dir = args.input.resolve()
    if not input_dir.exists() or not input_dir.is_dir():
        print(f"Input directory not found: {input_dir}")
        return 1

    timestamp = datetime.now().strftime("%Y_%m_%d_%H%M")
    base_output = args.output or (input_dir / "output" / f"nlp_benchmark_{timestamp}")
    base_output = _ensure_dir(base_output)

    # Stage 0: Setup & Validation (for mapping file)
    stage0_dir = _ensure_dir(base_output / "stage0")
    setup = SetupValidator(input_dir, stage0_dir)
    if not setup.run():
        return 1

    mapping_file = stage0_dir / "product_mapping.json"

    # Stage 1: Data Preparation (shared)
    stage1_dir = _ensure_dir(base_output / "stage1")
    json_files = _find_json_files(input_dir)
    if not json_files:
        print("No JSON files found in input directory")
        return 1

    processed_files = []
    for json_file in json_files:
        processor = DataPreprocessor(json_file, stage1_dir)
        if not processor.run():
            return 1
        processed_files.append(processor.processed_file)

    backends = ["vader", "distilbert"]
    report_sections = {}

    for backend in backends:
        print(f"\n=== Running backend: {backend} ===")
        stage2_dir = _ensure_dir(base_output / f"stage2_{backend}")
        stage3_dir = _ensure_dir(base_output / f"stage3_{backend}")
        visuals_dir = _ensure_dir(base_output / f"final_output_{backend}")

        # Stage 2: Text Analysis
        for processed_file in processed_files:
            processor = TextAnalysisProcessor(processed_file, stage2_dir, level=backend)
            if not processor.run():
                return 1

        # Stage 3: Statistics
        calculator = StatisticsCalculator(stage2_dir, stage3_dir, mapping_file)
        if not calculator.run():
            return 1

        # Stage 5: Visualization
        # Ensure matplotlib cache is writable for benchmarks
        os.environ.setdefault("MPLCONFIGDIR", str(base_output / "mpl_cache"))
        visualizer = Visualizer(stage3_dir, visuals_dir, mapping_file, stage2_dir)
        if not visualizer.run():
            return 1

        report_sections[backend] = {
            "stats": stage3_dir,
            "visuals": visuals_dir,
            "summary": _summarize_stats(stage3_dir)
        }

    report_path = base_output / "nlp_benchmark_report.md"
    _write_report(report_path, report_sections)

    print(f"\n✅ Benchmark report generated: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
