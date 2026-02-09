"""
EmbeddingWrapper — Plugin-Based Abstraction for Embeddings

Provides a unified interface for different embedding backends:
- sentence-transformers (local)
- ollama (local LLM-based)

Issue #3 fix: Dimension validation prevents mismatch errors
"""

import numpy as np
from typing import List, Dict, Any
from abc import ABC, abstractmethod


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


class EmbeddingWrapper:
    """Wrapper that loads embedding plugins dynamically."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the EmbeddingWrapper.
        
        Args:
            config: Configuration dictionary with keys:
                - embedding_plugin: 'sentence_transformers' or 'ollama'
                - embedding_models: sub-config for model settings
        """
        self.config = config
        plugin_name = config.get('embedding_plugin', 'sentence_transformers')
        self.plugin = self._load_plugin(plugin_name, config)
    
    def _load_plugin(self, plugin_name: str, config: Dict[str, Any]) -> EmbeddingPlugin:
        """
        Load the appropriate embedding plugin.
        
        Args:
            plugin_name: Name of plugin ('sentence_transformers' or 'ollama')
            config: Configuration dictionary
            
        Returns:
            Initialized EmbeddingPlugin instance
        """
        if plugin_name == 'sentence_transformers':
            from reddit_market_research.qa_processor_plus.plugins.sentence_transformers import SentenceTransformersPlugin
            model_config = config.get('embedding_models', {}).get('sentence_transformers', {})
            return SentenceTransformersPlugin(model_config)
        
        elif plugin_name == 'ollama':
            from reddit_market_research.qa_processor_plus.plugins.ollama import OllamaPlugin
            model_config = config.get('embedding_models', {}).get('ollama', {})
            return OllamaPlugin(model_config)
        
        else:
            raise ValueError(f"Unknown embedding plugin: {plugin_name}")
    
    def encode(self, texts: List[str]) -> np.ndarray:
        """
        Encode texts using the loaded plugin.
        
        Args:
            texts: List of texts to encode
            
        Returns:
            NumPy array of embeddings
        """
        return self.plugin.encode(texts)
    
    @property
    def dimension(self) -> int:
        """Get embedding dimension from plugin."""
        return self.plugin.dimension
    
    @property
    def model_name(self) -> str:
        """Get model name from plugin."""
        return self.plugin.model_name
