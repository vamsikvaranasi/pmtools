"""
Sentence Transformers Plugin

Embedding plugin using sentence-transformers library.
"""

import numpy as np
from typing import List, Dict, Any
from .base import EmbeddingPlugin


class SentenceTransformersPlugin(EmbeddingPlugin):
    """Embedding plugin using sentence-transformers."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the SentenceTransformersPlugin.
        
        Args:
            config: Configuration with keys:
                - model_name: Model name (default: 'sentence-transformers/all-MiniLM-L6-v2')
                - dimension: Embedding dimension (default: 384)
                - device: Device to use ('cpu' or 'cuda', default: 'cpu')
        """
        self._model_name = config.get('model_name', 'sentence-transformers/all-MiniLM-L6-v2')
        self._dimension = config.get('dimension', 384)
        self._device = config.get('device', 'cpu')
        
        # Lazy load the model
        self._model = None
    
    def _get_model(self):
        """Lazy load the sentence-transformers model."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self._model_name, device=self._device)
            except ImportError:
                raise ImportError("sentence-transformers library not installed")
        return self._model
    
    def encode(self, texts: List[str]) -> np.ndarray:
        """
        Encode texts using sentence-transformers.
        
        Args:
            texts: List of texts to encode
            
        Returns:
            NumPy array of embeddings
        """
        if not texts:
            return np.array([], dtype=np.float32).reshape(0, self._dimension)
        
        model = self._get_model()
        embeddings = model.encode(texts, convert_to_numpy=True)
        return embeddings.astype(np.float32)
    
    @property
    def dimension(self) -> int:
        """Get embedding dimension."""
        return self._dimension
    
    @property
    def model_name(self) -> str:
        """Get model name for identification."""
        return self._model_name
