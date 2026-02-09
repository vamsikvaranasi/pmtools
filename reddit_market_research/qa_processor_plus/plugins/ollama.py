"""
Ollama Plugin

Embedding plugin using Ollama for local LLM embeddings.
"""

import numpy as np
import requests
from typing import List, Dict, Any
from .base import EmbeddingPlugin


class OllamaPlugin(EmbeddingPlugin):
    """Embedding plugin using Ollama."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the OllamaPlugin.
        
        Args:
            config: Configuration with keys:
                - base_url: Ollama server URL (default: 'http://localhost:11434')
                - model_name: Model name (default: 'nomic-embed-text')
                - dimension: Embedding dimension (default: 768)
        """
        self._base_url = config.get('base_url', 'http://localhost:11434')
        self._model_name = config.get('model_name', 'nomic-embed-text')
        self._dimension = config.get('dimension', 768)
    
    def encode(self, texts: List[str]) -> np.ndarray:
        """
        Encode texts using Ollama.
        
        Args:
            texts: List of texts to encode
            
        Returns:
            NumPy array of embeddings
        """
        if not texts:
            return np.array([], dtype=np.float32).reshape(0, self._dimension)
        
        embeddings = []
        for text in texts:
            try:
                response = requests.post(
                    f"{self._base_url}/api/embed",
                    json={
                        "model": self._model_name,
                        "input": text
                    },
                    timeout=30
                )
                response.raise_for_status()
                data = response.json()
                embedding = data.get('embeddings', [[]])[0]
                embeddings.append(embedding)
            except (requests.RequestException, KeyError, IndexError) as e:
                # On error, pad with zeros
                embeddings.append([0.0] * self._dimension)
        
        return np.array(embeddings, dtype=np.float32)
    
    @property
    def dimension(self) -> int:
        """Get embedding dimension."""
        return self._dimension
    
    @property
    def model_name(self) -> str:
        """Get model name for identification."""
        return self._model_name
