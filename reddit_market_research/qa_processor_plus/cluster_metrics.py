"""
ClusterQualityMetrics — Silhouette and Intra/Inter-cluster Metrics

Issue #12 fix: Computes cluster quality metrics for evaluation.
Uses sklearn.metrics.silhouette_score for validation.
"""

import numpy as np
from typing import List, Dict, Any, Optional


class ClusterQualityMetrics:
    """Computes metrics to evaluate clustering quality."""
    
    def __init__(self):
        """Initialize the ClusterQualityMetrics."""
        pass
    
    def compute(self, vectors: np.ndarray, labels: np.ndarray) -> Dict[str, Any]:
        """
        Compute cluster quality metrics.
        
        Args:
            vectors: Vector array of shape (n_samples, embedding_dim)
            labels: Cluster labels (-1 for noise)
            
        Returns:
            Dictionary with metrics:
            - silhouette_score: Silhouette coefficient (-1 to 1)
            - avg_intra_cluster_cosine_similarity: Average within-cluster similarity
            - avg_inter_cluster_separation: Average between-cluster separation
            - noise_percentage: Fraction of noise points
            - num_clusters: Number of clusters (excluding noise)
            - num_noise_points: Number of noise points
        """
        # Filter out noise points for silhouette and cluster counts
        valid_mask = labels >= 0
        num_clusters = len(set(labels[valid_mask])) if valid_mask.sum() > 0 else 0
        noise_points = (labels == -1).sum()
        
        metrics = {
            'silhouette_score': None,
            'avg_intra_cluster_cosine_similarity': None,
            'avg_inter_cluster_separation': None,
            'noise_percentage': round(noise_points / len(labels), 3) if len(labels) > 0 else 0,
            'num_clusters': num_clusters,
            'num_noise_points': int(noise_points)
        }
        
        # Need at least 2 clusters with 2 points each for silhouette
        if valid_mask.sum() >= 4 and len(set(labels[valid_mask])) >= 2:
            try:
                from sklearn.metrics import silhouette_score
                sil = silhouette_score(
                    vectors[valid_mask],
                    labels[valid_mask],
                    metric='cosine'
                )
                metrics['silhouette_score'] = round(sil, 3)
            except Exception:
                pass
        
        # Compute intra-cluster similarity
        intra_sim = self._compute_intra_cluster_similarity(vectors, labels)
        if intra_sim is not None:
            metrics['avg_intra_cluster_cosine_similarity'] = round(intra_sim, 3)
        
        # Compute inter-cluster separation
        inter_sep = self._compute_inter_cluster_separation(vectors, labels)
        if inter_sep is not None:
            metrics['avg_inter_cluster_separation'] = round(inter_sep, 3)
        
        return metrics
    
    def _compute_intra_cluster_similarity(self, vectors: np.ndarray, 
                                        labels: np.ndarray) -> Optional[float]:
        """
        Compute average cosine similarity within clusters.
        
        Args:
            vectors: Vector array
            labels: Cluster labels
            
        Returns:
            Average intra-cluster similarity or None
        """
        valid_mask = labels >= 0
        if valid_mask.sum() < 2:
            return None
        
        similarities = []
        
        for cluster_id in set(labels[valid_mask]):
            cluster_indices = np.where(labels == cluster_id)[0]
            if len(cluster_indices) < 2:
                continue
            
            cluster_vectors = vectors[cluster_indices]
            
            # Normalize vectors for cosine similarity
            norms = np.linalg.norm(cluster_vectors, axis=1, keepdims=True)
            norms[norms == 0] = 1
            normalized = cluster_vectors / norms
            
            # Compute pairwise cosine similarities
            similarity_matrix = normalized @ normalized.T
            
            # Get average of upper triangle (excluding diagonal)
            for i in range(len(cluster_indices)):
                for j in range(i + 1, len(cluster_indices)):
                    similarities.append(similarity_matrix[i, j])
        
        if not similarities:
            return None
        
        return float(np.mean(similarities))
    
    def _compute_inter_cluster_separation(self, vectors: np.ndarray, 
                                         labels: np.ndarray) -> Optional[float]:
        """
        Compute average separation between clusters.
        
        Separation = 1 - max_cosine_similarity between different clusters
        
        Args:
            vectors: Vector array
            labels: Cluster labels
            
        Returns:
            Average inter-cluster separation or None
        """
        valid_mask = labels >= 0
        unique_clusters = sorted(set(labels[valid_mask]))
        
        if len(unique_clusters) < 2:
            return None
        
        separations = []
        
        # Compute cluster centroids
        centroids = {}
        for cluster_id in unique_clusters:
            cluster_indices = np.where(labels == cluster_id)[0]
            centroid = np.mean(vectors[cluster_indices], axis=0)
            norm = np.linalg.norm(centroid)
            if norm > 0:
                centroid = centroid / norm
            centroids[cluster_id] = centroid
        
        # Compute pairwise separations between cluster centroids
        for i, c1 in enumerate(unique_clusters):
            for c2 in unique_clusters[i+1:]:
                # Cosine similarity between centroids
                sim = np.dot(centroids[c1], centroids[c2])
                separation = 1.0 - sim  # Convert to separation metric
                separations.append(separation)
        
        if not separations:
            return None
        
        return float(np.mean(separations))
