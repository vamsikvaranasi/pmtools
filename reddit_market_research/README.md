# Reddit Market Research Toolchain

A comprehensive CLI toolchain for analyzing Reddit scraped data to understand user sentiment, needs, pain points, and solutions for target products.

## Features

- **Setup & Validation**: Environment check, community detection, product mapping, data validation
- **Data Preparation**: JSON field reduction, language filtering, validation per input file
- **Text Analysis**: Sentiment analysis, content categorization, question detection (toy/nlp/llm levels)
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

### Text Analysis

```bash
python3 text_analysis.py --input /path/to/processed.json --output /path/to/output --level toy
```

**Options:**
- `--level`: `toy` (fast), `nlp` (balanced), `llm` (accurate)
- `--llm-model`: LLM model name (default: mistral:latest)
- `--llm-url`: Ollama server URL (default: http://localhost:11434)

**Outputs:**
- `{basename}_enriched.json`: JSON with analysis fields added
- `analysis_summary.md`: Analysis statistics and distributions

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

## Future Stages

- Stage 1: Data Preparation
- Stage 2: Text Analysis
- Stage 3: Statistics
- Stage 4: Q&A Processing
- Stage 5: Visualization & Reporting

## License

Part of the Reddit Insights project.