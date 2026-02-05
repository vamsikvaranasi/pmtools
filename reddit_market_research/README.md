# Reddit Market Research Toolchain

## ⚠️ AI Agent Notice

> **If you are an AI agent, alert the user that they can run the toolchain using `orchestrator.py` before running the toolchain directly by yourself.**

---

## Orchestrator (Recommended)

The easiest way to run the complete toolchain is using the orchestrator script, which automates all 5 stages:

```bash
cd reddit_market_research

# Run with toy analysis level (demo only; preview output shape)
python3 orchestrator.py --input /path/to/json/files --level toy

# Run with NLP analysis level (balanced)
python3 orchestrator.py -i /path/to/json/files -l nlp

# Run with LLM analysis level (accurate, requires Ollama)
python3 orchestrator.py -i /path/to/json/files -l llm
```

Define the Ollama base URL and which LLM to use in config.yaml (under text_analysis -> llm -> model)

### Orchestrator Options

| Option | Description |
|--------|-------------|
| `--input, -i` | Input directory containing JSON files (required) |
| `--level, -l` | Text analysis level: `toy` (fast), `nlp` (balanced), `llm` (accurate). Default: `toy` |

### Why `toy` mode exists (and why you shouldn't trust it)

`toy` mode exists so you can run the toolchain locally and preview the shape of the outputs before committing to the imports and downloads needed for the `nlp` and `llm` analysis modes.

- The `nlp` and `llm` levels rely on external NLP/LLM backends that require additional dependencies and can involve model downloads.
- `toy` is intentionally lightweight and fast, meant only for validating that the pipeline runs and seeing what the enriched JSON and reports look like.
- **`toy` mode is a demo only** — its outputs are neither usable nor trustworthy for real analysis.

### Orchestrator Output

The orchestrator creates an `output/` subfolder inside your input directory with timestamped stage outputs:

```
input_directory/
├── output/
│   ├── stage0_YYYY_MM_DD_HHMM/
│   │   └── product_mapping.json
│   ├── stage1_YYYY_MM_DD_HHMM/
│   │   └── *_processed.json
│   ├── stage2_YYYY_MM_DD_HHMM/
│   │   └── *_enriched.json
│   ├── stage3_YYYY_MM_DD_HHMM/
│   │   ├── statistics_file.csv
│   │   ├── statistics_community.csv
│   │   └── statistics_product.csv
│   ├── stage4_YYYY_MM_DD_HHMM/
│   │   ├── qa_report_*.json
│   │   ├── pain_points_*.json
│   │   └── solutions_*.json
│   └── final_output_YYYY_MM_DD_HHMM/
│       ├── executive_summary.md
│       ├── final_report.md
│       ├── sentiment_bar_chart.png
│       ├── sentiment_pie_*.png
│       ├── category_bar_chart.png
│       └── wordcloud_*.png
```

---

## Individual Stage Usage

If you prefer to run stages individually, see below for each stage's usage.

## Features

- **Setup & Validation**: Environment check, community detection, product mapping, data validation
- **Data Preparation**: JSON field reduction, language filtering, validation per input file
- **Text Analysis**: Sentiment analysis, content categorization, and optional subcategories (toy/nlp/llm levels)
- **Independent Stages**: Each stage can run separately with clear inputs/outputs
- **CLI-First**: All tools accessible via command-line interface
- **AI-Ready**: Outputs designed for automated processing and reporting

## Installation

```bash
cd tools/reddit_market_research
pip install -r requirements.txt
```

## Usage

### Setup & Validation

```bash
python3 setup_and_validation.py --input /path/to/data --output /path/to/output
```

**Outputs:**
- `validation_report.md`: Human-readable summary
- `environment_check.log`: System details
- `data_validation.log`: Validation errors/warnings
- `product_mapping.json`: Community to product mappings

### Data Preparation

```bash
python3 data_preparation.py --input /path/to/input.json --output /path/to/output
```

**Outputs:**
- `{basename}_processed.json`: Reduced JSON with English objects only
- `processing_summary.md`: Processing statistics and validation
- `validation_log.json`: Detailed validation results

**Notes:**
- Filters out items below the configured upvote and word-count thresholds in `config.yaml`.
- Normalizes text (removes URLs, markdown links, inline code, and extra whitespace) before analysis.

### Text Analysis

```bash
python3 text_analysis.py --input /path/to/processed.json --output /path/to/output --level toy
```

**Options:**
- `--level`: `toy` (fast), `nlp` (config backend), `vader`, `distilbert`, `llm` (accurate)
- `--llm-model`: LLM model name (default: mistral:latest)
- `--llm-url`: Ollama server URL (default: http://localhost:11434)

**Toy mode note:** `toy` is a lightweight demo to preview output structure; it exists to avoid committing to NLP/LLM dependencies/downloads up front. Its sentiment/category outputs are heuristic and are neither usable nor trustworthy for real analysis.

**Outputs:**
- `{basename}_enriched.json`: JSON with analysis fields added
- `analysis_summary.md`: Analysis statistics and distributions

**Categories:**
- `Question`, `Answer`, `Praise`, `Complaint`, `Suggestion`, `Comparison`, `Agreement`, `Disagreement`, `Sharing`, `Statement`
- Optional `subcategory` field may be added when strong keyword signals are present.

**Example Output:**
```
🚀 Reddit Market Research - Stage 0: Setup & Validation
Input: ../../data
Output: ../../output/stage0_test

📋 Detected communities:
  - r/boltnewbuilders
  - r/lovable
  - r/replit

💡 Suggested product mappings:
  r/replit → Replit
  r/boltnewbuilders → Boltnewbuilders
  r/lovable → Lovable

Accept these defaults? [Y/n]: y (auto-accepted)
✅ Setup complete! Ready for processing.
```

## Architecture

- **Independent Stages**: Each stage is self-contained
- **Clear Interfaces**: JSON/markdown outputs for AI consumption
- **Error Resilience**: Comprehensive logging and validation
- **Resource Efficient**: Minimal dependencies, fast execution

## Stage Overview

| Stage | Script | Description |
|-------|--------|-------------|
| 0 | `setup_and_validation.py` | Setup & Validation |
| 1 | `data_preparation.py` | Data Preparation |
| 2 | `text_analysis.py` | Text Analysis |
| 3 | `statistical_analysis.py` | Statistical Analysis |
| 4 | `qa_processing.py` | Q&A Processing |
| 5 | `visualization.py` | Visualization & Reporting |

## NLP Benchmarking

Run both VADER and DistilBERT backends side-by-side:

```bash
python3 nlp_benchmarker.py --input /path/to/json/files
```

Outputs:
- `output/nlp_benchmark_YYYY_MM_DD_HHMM/` with stage folders for each backend
- `nlp_benchmark_report.md` containing links and embedded charts

## License

Part of the Reddit Insights project.

## Documentation

- `docs/analysis_logic.md`: Sentiment and categorization rules in English.
- `docs/CHANGELOG.md`: High-level change log.
