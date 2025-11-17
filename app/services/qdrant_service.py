"""Qdrant vector database service."""
from typing import List, Dict, Any, Optional
from uuid import UUID
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct, Filter,
    FieldCondition, MatchValue, SearchRequest
)

from app.config import settings
from app.utils.logger import logger


class QdrantService:
    """Service for managing Qdrant vector database operations."""

    def __init__(self):
        """Initialize Qdrant client."""
        try:
            self.client = QdrantClient(
                host=settings.QDRANT_HOST,
                port=settings.QDRANT_PORT,
                api_key=settings.QDRANT_API_KEY
            )
            logger.info(f"Qdrant client initialized: {settings.QDRANT_HOST}:{settings.QDRANT_PORT}")
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant client: {str(e)}")
            raise

    def get_collection_name(self, owner_id: UUID, owner_type: str) -> str:
        """
        Get collection name for owner (user or family member).

        Args:
            owner_id: Owner's UUID
            owner_type: Type of owner (user or family_member)

        Returns:
            Collection name
        """
        return f"{settings.QDRANT_COLLECTION_PREFIX}_{owner_type}_{str(owner_id).replace('-', '_')}"

    def create_collection(
        self,
        owner_id: UUID,
        owner_type: str,
        vector_size: int = 1536
    ) -> bool:
        """
        Create a new collection for an owner.

        Args:
            owner_id: Owner's UUID
            owner_type: Type of owner
            vector_size: Size of embedding vectors (default 1536 for OpenAI)

        Returns:
            True if created successfully
        """
        collection_name = self.get_collection_name(owner_id, owner_type)

        try:
            # Check if collection exists
            collections = self.client.get_collections().collections
            if any(col.name == collection_name for col in collections):
                logger.info(f"Collection already exists: {collection_name}")
                return True

            # Create collection
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
            )

            logger.info(f"Created collection: {collection_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to create collection {collection_name}: {str(e)}")
            return False

    def add_chunks(
        self,
        owner_id: UUID,
        owner_type: str,
        document_id: UUID,
        chunks: List[Dict[str, Any]]
    ) -> bool:
        """
        Add document chunks to collection.

        Args:
            owner_id: Owner's UUID
            owner_type: Type of owner
            document_id: Document UUID
            chunks: List of chunks with text, embedding, and metadata

        Returns:
            True if added successfully
        """
        collection_name = self.get_collection_name(owner_id, owner_type)

        try:
            # Ensure collection exists
            self.create_collection(owner_id, owner_type, vector_size=len(chunks[0]["embedding"]))

            # Prepare points
            points = []
            for idx, chunk in enumerate(chunks):
                point = PointStruct(
                    id=f"{str(document_id)}_{idx}",
                    vector=chunk["embedding"],
                    payload={
                        "document_id": str(document_id),
                        "chunk_index": idx,
                        "text": chunk["text"],
                        "page_number": chunk.get("page_number"),
                        "metadata": chunk.get("metadata", {})
                    }
                )
                points.append(point)

            # Upsert points
            self.client.upsert(
                collection_name=collection_name,
                points=points
            )

            logger.info(f"Added {len(chunks)} chunks to collection {collection_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to add chunks to collection {collection_name}: {str(e)}")
            return False

    def search(
        self,
        owner_id: UUID,
        owner_type: str,
        query_vector: List[float],
        limit: int = 5,
        score_threshold: float = 0.7,
        document_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar chunks in collection.

        Args:
            owner_id: Owner's UUID
            owner_type: Type of owner
            query_vector: Query embedding vector
            limit: Maximum number of results
            score_threshold: Minimum similarity score
            document_id: Optional document ID to filter by

        Returns:
            List of search results with text and metadata
        """
        collection_name = self.get_collection_name(owner_id, owner_type)

        try:
            # Build filter
            query_filter = None
            if document_id:
                query_filter = Filter(
                    must=[
                        FieldCondition(
                            key="document_id",
                            match=MatchValue(value=str(document_id))
                        )
                    ]
                )

            # Search
            search_result = self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit,
                score_threshold=score_threshold,
                query_filter=query_filter
            )

            # Format results
            results = []
            for hit in search_result:
                results.append({
                    "id": hit.id,
                    "score": hit.score,
                    "text": hit.payload.get("text"),
                    "document_id": hit.payload.get("document_id"),
                    "chunk_index": hit.payload.get("chunk_index"),
                    "page_number": hit.payload.get("page_number"),
                    "metadata": hit.payload.get("metadata", {})
                })

            logger.info(f"Found {len(results)} results in collection {collection_name}")
            return results

        except Exception as e:
            logger.error(f"Search failed in collection {collection_name}: {str(e)}")
            return []

    def delete_document_chunks(
        self,
        owner_id: UUID,
        owner_type: str,
        document_id: UUID
    ) -> bool:
        """
        Delete all chunks for a specific document.

        Args:
            owner_id: Owner's UUID
            owner_type: Type of owner
            document_id: Document UUID to delete

        Returns:
            True if deleted successfully
        """
        collection_name = self.get_collection_name(owner_id, owner_type)

        try:
            # Delete points with matching document_id
            self.client.delete(
                collection_name=collection_name,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="document_id",
                            match=MatchValue(value=str(document_id))
                        )
                    ]
                )
            )

            logger.info(f"Deleted chunks for document {document_id} from collection {collection_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete chunks for document {document_id}: {str(e)}")
            return False

    def delete_collection(
        self,
        owner_id: UUID,
        owner_type: str
    ) -> bool:
        """
        Delete entire collection for an owner.

        Args:
            owner_id: Owner's UUID
            owner_type: Type of owner

        Returns:
            True if deleted successfully
        """
        collection_name = self.get_collection_name(owner_id, owner_type)

        try:
            self.client.delete_collection(collection_name=collection_name)
            logger.info(f"Deleted collection: {collection_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete collection {collection_name}: {str(e)}")
            return False

    def get_collection_info(
        self,
        owner_id: UUID,
        owner_type: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get information about a collection.

        Args:
            owner_id: Owner's UUID
            owner_type: Type of owner

        Returns:
            Collection information or None
        """
        collection_name = self.get_collection_name(owner_id, owner_type)

        try:
            info = self.client.get_collection(collection_name=collection_name)
            return {
                "name": collection_name,
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "status": info.status
            }

        except Exception as e:
            logger.error(f"Failed to get collection info for {collection_name}: {str(e)}")
            return None


# Global Qdrant service instance
qdrant_service = QdrantService()
