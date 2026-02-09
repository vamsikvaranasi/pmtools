"""
HDBSCANClustering — Correct sklearn HDBSCAN Parameters

Issue #2 fix: Uses min_cluster_size + min_samples (not similarity_threshold)
Issue #4 fix: Uses sklearn.cluster.HDBSCAN (not standalone package)
Issue #9 fix: Handles noise points per configuration
"""

import numpy as np
from sklearn.cluster import HDBSCAN
from typing import List, Dict, Any


class HDBSCANClustering:
    """HDBSCAN clustering with correct sklearn parameters."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the HDBSCAN clustering.
        
        Args:
            config: Configuration with keys:
                - min_cluster_size: Minimum cluster size (default: 3)
                - min_samples: Core point density (default: 2)
                - cluster_selection_method: 'eom' or 'leaf' (default: 'eom')
                - max_clusters: Maximum clusters allowed (default: 50)
                - noise_handling: 'include_as_singletons' or 'discard' (default: 'include_as_singletons')
        """
        self.min_cluster_size = config.get('min_cluster_size', 3)
        self.min_samples = config.get('min_samples', 2)
        self.cluster_selection_method = config.get('cluster_selection_method', 'eom')
        self.max_clusters = config.get('max_clusters', 50)
        self.noise_handling = config.get('noise_handling', 'include_as_singletons')
    
    def cluster(self, vectors: np.ndarray, metadata: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Cluster vectors using HDBSCAN.
        
        Args:
            vectors: Vector array of shape (n_samples, embedding_dim)
            metadata: Metadata for each vector
            
        Returns:
            Dictionary with keys:
                - clusters: List of cluster assignments
                - noise_items: Items identified as noise
                - labels: Original cluster labels (-1 for noise)
        """
        if vectors.shape[0] == 0:
            return {
                'clusters': [],
                'noise_items': [],
                'labels': np.array([])
            }
        
        # Issue #2 fix: Use correct HDBSCAN parameters
        # Normalize vectors for cosine-like behavior with euclidean metric
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms[norms == 0] = 1  # Avoid division by zero
        normalized_vectors = vectors / norms
        
        # Create and fit HDBSCAN
        clusterer = HDBSCAN(
            min_cluster_size=self.min_cluster_size,
            min_samples=self.min_samples,
            cluster_selection_method=self.cluster_selection_method,
            metric='euclidean'  # On normalized vectors, euclidean ≈ cosine
        )
        
        labels = clusterer.fit_predict(normalized_vectors)
        
        # Build clusters from labels
        clusters = self._build_clusters(labels, metadata)
        
        # Issue #9 fix: Handle noise points
        noise_items = self._handle_noise(labels, metadata)
        
        return {
            'clusters': clusters,
            'noise_items': noise_items,
            'labels': labels,
            'vectors': normalized_vectors
        }
    
    def _build_clusters(self, labels: np.ndarray, metadata: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Build cluster structures from labels.
        
        Args:
            labels: HDBSCAN labels (-1 = noise)
            metadata: Metadata for each vector
            
        Returns:
            List of cluster dictionaries
        """
        clusters = {}
        
        for idx, label in enumerate(labels):
            if label == -1:
                # Skip noise points here, handle separately
                continue
            
            if label not in clusters:
                clusters[label] = []
            
            clusters[label].append({
                'index': idx,
                'metadata': metadata[idx]
            })
        
        # Convert to list of cluster dicts
        result = []
        for cluster_id in sorted(clusters.keys()):
            if len(clusters[cluster_id]) > 0:
                result.append({
                    'id': cluster_id,
                    'items': clusters[cluster_id],
                    'size': len(clusters[cluster_id])
                })
        
        return result
    
    def _handle_noise(self, labels: np.ndarray, metadata: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Handle noise points according to configuration.
        
        Issue #9 fix: Noise handling strategy per config.
        
        Args:
            labels: HDBSCAN labels
            metadata: Metadata for each vector
            
        Returns:
            List of noise items (empty if discard mode)
        """
        noise_indices = [i for i, label in enumerate(labels) if label == -1]
        
        if not noise_indices:
            return []
        
        if self.noise_handling == 'include_as_singletons':
            # Each noise point becomes its own single-item cluster
            return [
                {
                    'singleton': True,
                    'index': idx,
                    'metadata': metadata[idx]
                }
                for idx in noise_indices
            ]
        
        elif self.noise_handling == 'discard':
            # Noise points are dropped (but could be logged)
            return []
        
        return []
