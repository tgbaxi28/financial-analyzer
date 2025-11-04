"""
Vector database service using pgvector for semantic search.
Handles embedding storage, retrieval, and similarity search.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text
import numpy as np

from models import Report, Chunk, AuditLog

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for managing embeddings and vector search."""

    def __init__(self, session: Session):
        self.session = session

    def store_embeddings(
        self,
        report_id: str,
        chunks: List[Dict[str, Any]],
        embeddings: List[List[float]],
        provider: str,
        model: str,
    ) -> int:
        """Store document chunks with embeddings in database."""
        try:
            stored_count = 0

            for chunk_data, embedding in zip(chunks, embeddings):
                chunk = Chunk(
                    report_id=report_id,
                    chunk_text=chunk_data["text"],
                    chunk_index=chunk_data["chunk_index"],
                    page_number=chunk_data.get("page_number"),
                    section_type=chunk_data.get("section_type", "text"),
                    embedding=embedding,
                    embedding_model=model,
                )
                self.session.add(chunk)
                stored_count += 1

            self.session.commit()

            # Update report status
            report = self.session.query(Report).filter(Report.id == report_id).first()
            if report:
                report.chunks_created = stored_count
                report.embedding_provider = provider
                report.embedding_model = model
                report.processing_status = "indexed"
                self.session.commit()

            logger.info(
                f"Stored {stored_count} embeddings for report {report_id}"
            )
            return stored_count

        except Exception as e:
            self.session.rollback()
            logger.error(f"Error storing embeddings: {e}")
            raise

    def semantic_search(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        similarity_threshold: float = 0.7,
        report_ids: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search using vector similarity.
        Returns top-k most similar chunks.
        """
        try:
            # Convert to numpy for distance calculation
            query_vec = np.array(query_embedding, dtype=np.float32)

            query = self.session.query(
                Chunk.id,
                Chunk.chunk_text,
                Chunk.report_id,
                Chunk.page_number,
                Chunk.section_type,
                Chunk.chunk_index,
                Report.filename,
            ).join(Report, Chunk.report_id == Report.id)

            # Filter by report IDs if provided
            if report_ids:
                query = query.filter(Chunk.report_id.in_(report_ids))

            chunks = query.all()

            # Calculate similarities
            results = []
            for chunk in chunks:
                if chunk.Chunk.embedding is None:
                    continue

                # Calculate cosine similarity
                chunk_vec = np.array(chunk.Chunk.embedding, dtype=np.float32)
                similarity = self._cosine_similarity(query_vec, chunk_vec)

                if similarity >= similarity_threshold:
                    results.append(
                        {
                            "chunk_id": chunk.Chunk.id,
                            "text": chunk.Chunk.chunk_text,
                            "report_id": chunk.Chunk.report_id,
                            "report_filename": chunk.Report.filename,
                            "page_number": chunk.Chunk.page_number,
                            "section_type": chunk.Chunk.section_type,
                            "similarity": similarity,
                        }
                    )

            # Sort by similarity and return top-k
            results.sort(key=lambda x: x["similarity"], reverse=True)
            results = results[:top_k]

            logger.info(
                f"Semantic search found {len(results)} relevant chunks"
            )
            return results

        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return []

    @staticmethod
    def _cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors."""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot_product / (norm1 * norm2))

    def hybrid_search(
        self,
        query_embedding: List[float],
        keyword_filters: Optional[Dict[str, Any]] = None,
        top_k: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid search combining vector similarity and keyword filters.
        Supports filtering by date range, report type, etc.
        """
        # Start with semantic search
        results = self.semantic_search(query_embedding, top_k=top_k * 2)

        # Apply keyword filters
        if keyword_filters:
            if "report_ids" in keyword_filters:
                results = [
                    r
                    for r in results
                    if r["report_id"] in keyword_filters["report_ids"]
                ]

            if "section_types" in keyword_filters:
                results = [
                    r
                    for r in results
                    if r["section_type"] in keyword_filters["section_types"]
                ]

        return results[:top_k]

    def get_report_chunks(
        self,
        report_id: str,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get all chunks for a specific report."""
        try:
            chunks = (
                self.session.query(Chunk)
                .filter(Chunk.report_id == report_id)
                .order_by(Chunk.chunk_index)
                .limit(limit)
                .all()
            )

            return [
                {
                    "id": chunk.id,
                    "text": chunk.chunk_text,
                    "page": chunk.page_number,
                    "type": chunk.section_type,
                    "index": chunk.chunk_index,
                }
                for chunk in chunks
            ]

        except Exception as e:
            logger.error(f"Error retrieving report chunks: {e}")
            return []

    def delete_report_embeddings(self, report_id: str) -> int:
        """Delete all embeddings for a report."""
        try:
            deleted_count = (
                self.session.query(Chunk)
                .filter(Chunk.report_id == report_id)
                .delete()
            )
            self.session.commit()

            logger.info(
                f"Deleted {deleted_count} embeddings for report {report_id}"
            )
            return deleted_count

        except Exception as e:
            self.session.rollback()
            logger.error(f"Error deleting embeddings: {e}")
            raise

    def reindex_report(
        self,
        report_id: str,
        chunks: List[Dict[str, Any]],
        embeddings: List[List[float]],
        new_provider: str,
        new_model: str,
    ) -> int:
        """Re-index a report with new embeddings (e.g., different provider)."""
        try:
            # Delete old embeddings
            self.delete_report_embeddings(report_id)

            # Store new embeddings
            stored = self.store_embeddings(
                report_id, chunks, embeddings, new_provider, new_model
            )

            logger.info(
                f"Re-indexed report {report_id} with {stored} new embeddings"
            )
            return stored

        except Exception as e:
            logger.error(f"Error re-indexing report: {e}")
            raise