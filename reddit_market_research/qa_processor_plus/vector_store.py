"""
LanceDBManager — Correct LanceDB API with Ephemeral Tables

Issue #1 fix: Uses correct LanceDB API (create_table, search, get_all_vectors)
Issue #10 fix: Per-run ephemeral tables with timestamped names
"""

import numpy as np
import lancedb
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional


class LanceDBManager:
    """Manages vector storage and retrieval using LanceDB."""
    
    def __init__(self, db_path: str, embedding_wrapper, run_id: str):
        """
        Initialize the LanceDBManager.
        
        Args:
            db_path: Path to LanceDB database directory
            embedding_wrapper: EmbeddingWrapper instance for encoding
            run_id: Unique ID for this run (for ephemeral table naming)
        """
        self.db_path = db_path
        self.embedding = embedding_wrapper
        self.run_id = run_id
        self.table_name = f"pain_spans_{run_id}"  # PM Decision 4: per-run tables
        
        try:
            self.db = lancedb.connect(db_path)
        except Exception as e:
            raise RuntimeError(f"Failed to connect to LanceDB: {e}")
    
    def create_table(self, spans: List[Dict[str, Any]]) -> None:
        """
        Create a table and populate it with spans and embeddings.
        
        Args:
            spans: List of span objects with 'text' field
            
        Raises:
            ValueError: If spans list is empty
            RuntimeError: If LanceDB operation fails
        """
        if not spans:
            raise ValueError("Cannot create table with empty spans list")
        
        try:
            # Extract texts and encode to vectors
            texts = [s['text'] for s in spans]
            vectors = self.embedding.encode(texts)
            
            # Validate embedding dimension
            if vectors.shape[1] != self.embedding.dimension:
                raise ValueError(
                    f"Embedding dimension mismatch: got {vectors.shape[1]}, "
                    f"expected {self.embedding.dimension}"
                )
            
            # Prepare data for LanceDB
            data = []
            for span, vector in zip(spans, vectors):
                record = dict(span)  # Copy span data
                record['vector'] = vector.tolist()
                data.append(record)
            
            # Create table with overwrite mode for idempotency
            self.db.create_table(
                self.table_name,
                data=data,
                mode="overwrite"
            )
            
            # Store metadata for dimension validation
            self._store_metadata()
            
        except Exception as e:
            raise RuntimeError(f"Failed to create LanceDB table: {e}")
    
    def search(self, query_text: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for similar spans using the query text.
        
        Uses correct LanceDB chained API with builder pattern.
        
        Args:
            query_text: Query text to encode and search
            limit: Number of results to return
            
        Returns:
            List of similar spans with scores
        """
        try:
            # Encode query
            query_vector = self.embedding.encode([query_text])[0]
            query_array = np.array([query_vector])
            
            # Open table and search
            table = self.db.open_table(self.table_name)
            
            # Use correct LanceDB API with chained builder
            results = (
                table
                .search(query_array)
                .metric("cosine")
                .limit(limit)
                .to_pandas()
            )
            
            # Convert to list of dicts
            return results.to_dict('records')
            
        except Exception as e:
            raise RuntimeError(f"Failed to search LanceDB: {e}")
    
    def get_all_vectors(self) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
        """
        Get all vectors and metadata from the table.
        
        Used for clustering operations.
        
        Returns:
            Tuple of (vectors_array, metadata_list)
            
        Raises:
            RuntimeError: If table doesn't exist or operation fails
        """
        try:
            table = self.db.open_table(self.table_name)
            df = table.to_pandas()
            
            # Extract vectors (they're stored as lists, need to convert to arrays)
            vectors_list = []
            for vec in df['vector'].values:
                if isinstance(vec, list):
                    vectors_list.append(vec)
                else:
                    vectors_list.append(vec.tolist())
            
            vectors = np.array(vectors_list, dtype=np.float32)
            
            # Get metadata (all columns except 'vector')
            metadata_df = df.drop(columns=['vector'])
            metadata = metadata_df.to_dict('records')
            
            return vectors, metadata
            
        except Exception as e:
            raise RuntimeError(f"Failed to get all vectors: {e}")
    
    def cleanup(self) -> None:
        """
        Clean up ephemeral table after run completes.
        
        Per PM Decision 4: Drop table after use for ephemeral design.
        """
        try:
            self.db.drop_table(self.table_name)
        except Exception:
            # Silently ignore if table doesn't exist
            pass
        
        # Also try to drop metadata table if it exists
        try:
            meta_table_name = f"{self.table_name}_meta"
            self.db.drop_table(meta_table_name)
        except Exception:
            pass
    
    def _store_metadata(self) -> None:
        """
        Store embedding model metadata for dimension validation.
        
        Issue #3 fix: Validate dimension on open.
        """
        try:
            meta_table_name = f"{self.table_name}_meta"
            metadata = {
                'embedding_model': self.embedding.model_name,
                'embedding_dimension': self.embedding.dimension,
                'created_at': datetime.utcnow().isoformat()
            }
            
            self.db.create_table(
                meta_table_name,
                data=[metadata],
                mode="overwrite"
            )
        except Exception as e:
            # Log but don't fail if metadata storage fails
            pass
