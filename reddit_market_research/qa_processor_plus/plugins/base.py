"""
Base Plugin Module

Abstract base class for embedding plugins.
"""

from abc import ABC, abstractmethod
import numpy as np
from typing import List


class EmbeddingPlugin(ABC):
    """Abstract base class for embedding plugins."""
    
    @abstractmethod
    def encode(self, texts: List[str]) -> np.ndarray:
        """
        Encode texts to embeddings.
        
        Args:
            texts: List of texts to encode
            
        Returns:
            NumPy array of shape (n_texts, embedding_dimension)
        """
        pass
    
    @property
    @abstractmethod
    def dimension(self) -> int:
        """Get embedding dimension."""
        pass
    
    @property
    @abstractmethod
    def model_name(self) -> str:
        """Get model name for identification."""
        pass
