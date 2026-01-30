"""
LLM Analyzer

Advanced analysis using local LLM (Ollama) for maximum accuracy.
"""

import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from .base_analyzer import BaseAnalyzer

try:
    from ollama_text_client import OllamaTextClient
    OLLAMA_CLIENT_AVAILABLE = True
except ImportError:
    OLLAMA_CLIENT_AVAILABLE = False


class LLMAnalyzer(BaseAnalyzer):
    """LLM-based analyzer using Ollama."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        if not OLLAMA_CLIENT_AVAILABLE:
            raise ImportError("ollama_text_client required for LLM analyzer")

        self.base_url = self.config.get('llm_base_url', 'http://localhost:11434')
        self.model = self.config.get('llm_model', 'mistral:latest')
        self.max_retries = self.config.get('max_retries', 3)
        self.retry_delay = self.config.get('retry_delay', 1.0)
        
        # Initialize Ollama client
        self.client = OllamaTextClient(
            base_url=self.base_url,
            timeout=30,
            max_retries=self.max_retries,
            retry_delay=self.retry_delay
        )

        # Load prompt template
        self.prompt_template = self._load_prompt_template()

    def analyze_object(self, obj: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze object using LLM."""
        start_time = time.time()
        
        text = self._get_text(obj)
        if not text:
            analysis = {
                'sentiment': 'neutral',
                'category': 'Statement',
                'confidence': 0.5,
                'llm_response': None,
                'processing_time_ms': 0.0
            }
            return self._add_analysis_metadata(obj, analysis)

        # Single LLM call for both sentiment and category
        analysis = self._analyze_with_llm(text)
        analysis['processing_time_ms'] = round((time.time() - start_time) * 1000, 3)

        return self._add_analysis_metadata(obj, analysis)

    def analyze_batch(self, objects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze multiple objects with progress tracking."""
        results = []
        for obj in objects:
            result = self.analyze_object(obj)
            results.append(result)
        return results

    def _get_text(self, obj: Dict[str, Any]) -> str:
        """Extract text content from object."""
        text_parts = []
        if 'title' in obj and obj['title']:
            text_parts.append(obj['title'])
        if 'body' in obj and obj['body']:
            text_parts.append(obj['body'])
        return ' '.join(text_parts)

    def _load_prompt_template(self) -> str:
        """Load the LLM prompt template."""
        # Check if custom prompt file is specified in config
        prompt_file = self.config.get('prompt_file')
        if prompt_file:
            prompt_path = Path(prompt_file)
            if prompt_path.exists():
                try:
                    with open(prompt_path, 'r', encoding='utf-8') as f:
                        return f.read()
                except Exception as e:
                    print(f"Error loading prompt file {prompt_file}: {e}")
        
        # Default inline template
        return """Analyze the following Reddit post/comment text and provide a JSON response with sentiment and category analysis.

Text: {text}

Respond with valid JSON in this exact format:
{{
    "sentiment": "positive" or "neutral" or "negative",
    "category": "Question|Statement|Praise|Complaint|Sharing|Answer|Agreement|Disagreement",
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation"
}}

Rules:
- Sentiment: "positive" for favorable content, "neutral" for neutral content, "negative" for unfavorable
- Category: Choose the most appropriate from the list
- confidence: Your certainty level
- reasoning: 1-2 sentence explanation"""

    def _analyze_with_llm(self, text: str) -> Dict[str, Any]:
        """Analyze text using LLM with retry logic."""
        prompt = self.prompt_template.format(text=text)

        for attempt in range(self.max_retries):
            try:
                response = self._call_llm(prompt)
                if response:
                    parsed = self._parse_llm_response(response)
                    if parsed:
                        parsed['llm_response'] = response
                        return parsed

            except Exception as e:
                print(f"LLM call failed (attempt {attempt + 1}): {e}")

            if attempt < self.max_retries - 1:
                time.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff

        # Fallback to basic analysis
        print("LLM analysis failed, using fallback")
        return {
            'sentiment': 'neutral',
            'category': 'Statement',
            'confidence': 0.0,
            'reasoning': 'LLM analysis failed',
            'llm_response': None
        }

    def _call_llm(self, prompt: str) -> Optional[str]:
        """Make API call to Ollama using OllamaTextClient."""
        try:
            response = self.client.generate(
                model=self.model,
                prompt=prompt,
                stream=False,
                options={
                    "temperature": 0.1,  # Low temperature for consistent analysis
                    "top_p": 0.9
                }
            )
            return response.get('response', '').strip()
        except Exception as e:
            raise Exception(f"LLM API error: {str(e)}")

    def _parse_llm_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Parse JSON response from LLM."""
        try:
            # Try to extract JSON from response
            start = response.find('{')
            end = response.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = response[start:end]
                data = json.loads(json_str)

                # Validate required fields
                required = ['sentiment', 'category', 'is_question', 'confidence']
                if all(key in data for key in required):
                    # Validate values
                    data['sentiment'] = self._validate_sentiment(data['sentiment'])
                    data['category'] = self._validate_category(data['category'])
                    data['is_question'] = bool(data['is_question'])
                    data['confidence'] = max(0.0, min(1.0, float(data.get('confidence', 0.5))))
                    return data

        except (json.JSONDecodeError, ValueError, KeyError) as e:
            print(f"Failed to parse LLM response: {e}")
            print(f"Response: {response[:200]}...")

        return None