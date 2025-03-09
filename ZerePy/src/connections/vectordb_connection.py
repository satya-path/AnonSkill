import os
import logging
from typing import Dict, Any, List
from pathlib import Path
import numpy as np
from hnswlib import Index
from src.connections.base_connection import BaseConnection, Action, ActionParameter
from src.helpers import print_h_bar

logger = logging.getLogger("connections.vectordb_connection")

class VectorDBError(Exception):
    """Base exception for VectorDB errors"""
    pass

class VectorDBConnection(BaseConnection):
    """A vector database connection that provides similarity search capabilities.

    This class implements a vector database using HNSW (Hierarchical Navigable Small World) graphs
    for efficient similarity search. It supports adding, updating, deleting, and searching vector embeddings
    with associated metadata.

    Args:
        config (Dict[str, Any]): Configuration dictionary containing:
            - dimension (int): Dimensionality of vectors
            - db_path (str): Path to store the vector database
            - index_type (str): Type of index to use

    Examples:
        >>> config = {
        ...     "dimension": 768,
        ...     "db_path": "path/to/db",
        ...     "index_type": "hnsw"
        ... }
        >>> vdb = VectorDBConnection(config)
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.index = None
        self.dimension = config["dimension"]
        self.db_path = Path(config["db_path"])
        self.index_type = config["index_type"]
        self.metadata = {}
        self._initialize_db()

    @property
    def is_llm_provider(self) -> bool:
        return False

    def validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate VectorDB configuration parameters.

        Args:
            config (Dict[str, Any]): Configuration dictionary to validate

        Returns:
            Dict[str, Any]: Validated configuration dictionary

        Raises:
            ValueError: If required fields are missing or invalid

        Examples:
            >>> config = {
            ...     "dimension": 768,
            ...     "db_path": "path/to/db",
            ...     "index_type": "hnsw"
            ... }
            >>> validated_config = vdb.validate_config(config)
        """
        required_fields = ["db_path", "dimension", "index_type"]
        missing_fields = [field for field in required_fields if field not in config]
        
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
            
        if not isinstance(config["dimension"], int) or config["dimension"] <= 0:
            raise ValueError("dimension must be a positive integer")
            
        return config

    def _initialize_db(self):
        """Initialize or load the vector database"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        index_path = self.db_path / "index.bin"
        metadata_path = self.db_path / "metadata.npz"

        if index_path.exists() and metadata_path.exists():
            # Load existing database
            self.index = Index(space='cosine', dim=self.dimension)
            self.index.load_index(str(index_path))
            loaded = np.load(str(metadata_path), allow_pickle=True)
            self.metadata = loaded['metadata'].item()
        else:
            # Create new database
            self.index = Index(space='cosine', dim=self.dimension)
            self.index.init_index(max_elements=100000, ef_construction=200, M=16)
            self.metadata = {}

    def register_actions(self) -> None:
        """Register available VectorDB actions"""
        self.actions = {
            "add-item": Action(
                name="add-item",
                parameters=[
                    ActionParameter("vector", True, list, "Vector representation"),
                    ActionParameter("metadata", True, dict, "Associated metadata")
                ],
                description="Add an item to the database"
            ),
            "search": Action(
                name="search",
                parameters=[
                    ActionParameter("query_vector", True, list, "Query vector"),
                    ActionParameter("k", False, int, "Number of results"),
                    ActionParameter("filters", False, dict, "Metadata filters")
                ],
                description="Search for similar items"
            ),
            "update-item": Action(
                name="update-item",
                parameters=[
                    ActionParameter("id", True, int, "Item ID"),
                    ActionParameter("vector", False, list, "New vector"),
                    ActionParameter("metadata", False, dict, "New metadata")
                ],
                description="Update an existing item"
            ),
            "delete-item": Action(
                name="delete-item",
                parameters=[
                    ActionParameter("id", True, int, "Item ID")
                ],
                description="Delete an item"
            ),
            "get-item": Action(
                name="get-item",
                parameters=[
                    ActionParameter("id", True, int, "Item ID")
                ],
                description="Get item by ID"
            )
        }

    def configure(self) -> bool:
        """Configure the vector database"""
        logger.info("\n📊 Vector Database Setup")
        
        if self.is_configured():
            logger.info("Vector database is already configured.")
            return True

        try:
            self._initialize_db()
            logger.info("✅ Vector database configured successfully!")
            return True
        except Exception as e:
            logger.error(f"Configuration failed: {e}")
            return False

    def is_configured(self, verbose=False) -> bool:
        """Check if vector database is configured"""
        try:
            return self.index is not None
        except Exception as e:
            if verbose:
                logger.error(f"Configuration check failed: {e}")
            return False

    def add_item(self, vector: List[float], metadata: Dict[str, Any]) -> int:
        """Add a vector embedding and its metadata to the database.

        Args:
            vector (List[float]): Vector embedding to store
            metadata (Dict[str, Any]): Associated metadata for the vector

        Returns:
            int: ID of the added item

        Raises:
            VectorDBError: If adding the item fails

        Examples:
            >>> vector = [0.1, 0.2, 0.3, ..., 0.768]  # 768-dimensional vector
            >>> metadata = {
            ...     "text": "example document",
            ...     "source": "book",
            ...     "author": "John Doe"
            ... }
            >>> item_id = vdb.add_item(vector, metadata)
        """
        try:
            idx = len(self.metadata)
            self.index.add_items(np.array([vector]), [idx])
            self.metadata[idx] = metadata
            self._save_db()
            return idx
        except Exception as e:
            raise VectorDBError(f"Failed to add item: {e}")

    def search(self, query_vector: List[float], k: int = 10, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Search for similar vectors in the database.

        Args:
            query_vector (List[float]): Query vector to search for
            k (int, optional): Number of results to return. Defaults to 10.
            filters (Dict[str, Any], optional): Metadata filters to apply. Defaults to None.

        Returns:
            List[Dict[str, Any]]: List of similar items with their metadata and similarity scores

        Examples:
            >>> query = [0.1, 0.2, 0.3, ..., 0.768]  # Query vector
            >>> # Basic search
            >>> results = vdb.search(query, k=5)
            >>> 
            >>> # Search with filters
            >>> filtered_results = vdb.search(
            ...     query,
            ...     k=5,
            ...     filters={"source": "book"}
            ... )
        """
        try:
            labels, distances = self.index.knn_query(np.array([query_vector]), k=k)
            results = []
            
            for idx, dist in zip(labels[0], distances[0]):
                if idx in self.metadata:
                    item = self.metadata[idx].copy()
                    if filters:
                        matches = all(
                            key in item and item[key] == value
                            for key, value in filters.items()
                        )
                        if not matches:
                            continue
                    item['id'] = int(idx)
                    item['similarity'] = float(1 - dist)
                    results.append(item)
                    
            return results
        except Exception as e:
            raise VectorDBError(f"Search failed: {e}")

    def update_item(self, id: int, vector: List[float] = None, metadata: Dict[str, Any] = None) -> None:
        """Update an existing item's vector and/or metadata.

        Args:
            id (int): ID of the item to update
            vector (List[float], optional): New vector embedding. Defaults to None.
            metadata (Dict[str, Any], optional): New metadata to update. Defaults to None.

        Raises:
            VectorDBError: If item doesn't exist or update fails

        Examples:
            >>> # Update only metadata
            >>> vdb.update_item(
            ...     id=1,
            ...     metadata={"author": "Jane Doe"}
            ... )
            >>> 
            >>> # Update both vector and metadata
            >>> new_vector = [0.2, 0.3, 0.4, ..., 0.769]
            >>> vdb.update_item(
            ...     id=1,
            ...     vector=new_vector,
            ...     metadata={"author": "Jane Doe"}
            ... )
        """
        try:
            if id not in self.metadata:
                raise VectorDBError(f"Item {id} not found")
                
            if vector is not None:
                self.index.mark_deleted(id)
                self.index.add_items(np.array([vector]), [id])
                
            if metadata is not None:
                self.metadata[id].update(metadata)
                
            self._save_db()
        except Exception as e:
            raise VectorDBError(f"Update failed: {e}")

    def delete_item(self, id: int) -> None:
        """Delete an item from the database.

        Args:
            id (int): ID of the item to delete

        Raises:
            VectorDBError: If deletion fails

        Examples:
            >>> vdb.delete_item(1)  # Delete item with ID 1
        """
        try:
            if id in self.metadata:
                self.index.mark_deleted(id)
                del self.metadata[id]
                self._save_db()
        except Exception as e:
            raise VectorDBError(f"Deletion failed: {e}")

    def get_item(self, id: int) -> Dict[str, Any]:
        """Retrieve an item by its ID.

        Args:
            id (int): ID of the item to retrieve

        Returns:
            Dict[str, Any]: Item metadata including its ID

        Raises:
            VectorDBError: If item doesn't exist or retrieval fails

        Examples:
            >>> item = vdb.get_item(1)
            >>> print(item)
            {
                'id': 1,
                'text': 'example document',
                'source': 'book',
                'author': 'John Doe'
            }
        """
        try:
            if id not in self.metadata:
                raise VectorDBError(f"Item {id} not found")
            return {'id': id, **self.metadata[id]}
        except Exception as e:
            raise VectorDBError(f"Failed to get item: {e}")

    def _save_db(self):
        """Save the database to disk.

        This internal method saves both the vector index and metadata to the specified database path.

        Raises:
            VectorDBError: If saving fails
        """
        try:
            self.index.save_index(str(self.db_path / "index.bin"))
            np.savez(str(self.db_path / "metadata.npz"), metadata=self.metadata)
        except Exception as e:
            raise VectorDBError(f"Failed to save database: {e}") 