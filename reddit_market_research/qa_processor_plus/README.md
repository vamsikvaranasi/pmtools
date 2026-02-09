# QA Processor Plus

> **Note**: This module is now part of the Reddit Market Research Toolchain.
> Documentation has been merged into the global [README.md](../README.md).

See the **QA Processor Plus** section in the global README for full documentation.

## Quick Links

- [Reddit Market Research README](../README.md)
- [Configuration](../config.yaml)

Advanced QA processing system for product management insights.

## Overview

QA Processor Plus is a comprehensive system for analyzing and extracting insights from QA conversations. It provides advanced NLP capabilities, clustering, and synthesis to help product teams understand user needs and identify opportunities.

## Features

- **Conversation Filtering**: Remove noise and irrelevant content
- **Span Extraction**: Identify key questions, answers, and phrases
- **Classification**: Categorize conversations by topic and intent
- **Label Generation**: Create descriptive summaries and tags
- **Solution Extraction**: Identify actionable insights and recommendations
- **Embedding Support**: Advanced text embeddings with multiple models
- **Vector Storage**: Efficient similarity search and storage
- **Clustering**: Group similar conversations for analysis
- **Metrics**: Evaluate clustering quality and characteristics
- **LLM Synthesis**: Generate comprehensive insights using large language models
- **Insight Generation**: Identify trends, issues, and opportunities
- **Legacy Support**: Compatibility with existing systems
- **Grouping**: Flexible grouping by various criteria
- **Reporting**: Generate comprehensive reports and visualizations
- **Plugin System**: Extensible architecture with plugin support

## Installation

```bash
pip install -e .
```

## Quick Start

```python
from qa_processor_plus import QAProcessorPlus

# Initialize processor
processor = QAProcessorPlus()

# Process conversations
results = processor.process_conversations(conversations)

# Access results
print(results["llm_summary"])
print(results["clusters"])
```

## Configuration

Configuration is managed through `config.yaml`. Key settings include:

- **Core Settings**: Version, debug mode, logging
- **Processing**: Batch size, timeout, parallel processing
- **Embedding**: Model selection, similarity thresholds
- **Clustering**: Number of clusters, algorithms
- **Plugins**: Enabled plugins and their configurations
- **Storage**: Database paths and cache settings
- **LLM**: Model selection and API settings
- **Output**: Report formats and directories

## Plugin System

The system supports plugins for extended functionality:

### Built-in Plugins

- **Sentence Transformers**: Advanced text embeddings
- **Ollama**: Local LLM processing

### Creating Plugins

Plugins should inherit from `BasePlugin` and implement required methods:

```python
from qa_processor_plus.plugins.base import BasePlugin

class CustomPlugin(BasePlugin):
    def process(self, conversations):
        # Process conversations
        return conversations
    
    def get_info(self):
        return {
            "name": "custom",
            "version": "1.0.0",
            "description": "Custom plugin description"
        }
```

## API Reference

### Main Classes

- `QAProcessorPlus`: Main processing system
- `QAFilter`: Conversation filtering
- `SpanExtractor`: Span extraction
- `QAClassifier`: Conversation classification
- `QALabelGenerator`: Label generation
- `SolutionExtractor`: Solution extraction
- `EmbeddingWrapper`: Embedding management
- `VectorStore`: Vector storage and search
- `QACluster`: Conversation clustering
- `ClusterMetrics`: Clustering evaluation
- `LLMSynthesizer`: LLM-based synthesis
- `InsightGenerator`: Insight generation
- `LegacyAdapter`: Legacy system compatibility
- `QAGrouper`: Conversation grouping
- `ReportGenerator`: Report generation

### Plugin Classes

- `BasePlugin`: Base plugin class
- `SentenceTransformersPlugin`: Sentence transformers integration
- `OllamaPlugin`: Ollama integration

## Templates

The system uses Jinja2 templates for report generation:

- `cluster_label.jinja2`: Cluster label generation
- `why_it_matters.jinja2`: Impact explanation
- `open_questions.jinja2`: Investigation questions

## Development

### Requirements

```bash
pip install -r requirements.txt
```

### Testing

```bash
pytest
```

### Code Quality

```bash
black .
flake8 .
mypy .
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

For support and questions:
- Create an issue on GitHub
- Check the documentation
- Review the examples

## Roadmap

- [ ] Enhanced plugin system
- [ ] Real-time processing
- [ ] Advanced visualization
- [ ] Multi-language support
- [ ] Cloud deployment options
- [ ] API integration
- [ ] Advanced analytics

## Related Projects

- [PM Tools Core](https://github.com/pmtools/core)
- [Reddit Data Processor](https://github.com/pmtools/reddit_data)
- [Ollama Clients](https://github.com/pmtools/ollama_clients)

## Acknowledgments

- Hugging Face for transformers and sentence-transformers
- OpenAI for LLM technology
- Ollama for local LLM processing
- Python community for excellent libraries