"""RAG (Retrieval-Augmented Generation) service."""
from typing import List, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session

from app.services.llm_providers import LLMProviderFactory
from app.services.qdrant_service import qdrant_service
from app.services.pii_service import pii_service
from app.schemas import AIProviderCredentials, ChatMessage
from app.models import Document, QueryHistory
from app.utils.logger import logger


class RAGService:
    """Service for RAG-based question answering."""

    def __init__(self):
        """Initialize RAG service."""
        self.context_window_size = 5
        self.similarity_threshold = 0.7

    async def query(
        self,
        db: Session,
        user_id: UUID,
        owner_id: UUID,
        owner_type: str,
        query_text: str,
        provider_credentials: AIProviderCredentials,
        conversation_history: List[ChatMessage] = None
    ) -> Dict[str, Any]:
        """
        Process RAG query.

        Args:
            db: Database session
            user_id: User ID (for logging)
            owner_id: Owner ID (user or family member)
            owner_type: Type of owner
            query_text: User's query
            provider_credentials: AI provider credentials
            conversation_history: Previous conversation messages

        Returns:
            Response with answer and sources
        """
        import time
        start_time = time.time()

        try:
            # Create LLM provider
            llm_provider = LLMProviderFactory.create_provider(provider_credentials)

            # Generate query embedding
            query_embedding = llm_provider.generate_embedding(query_text)

            # Search Qdrant for relevant chunks
            search_results = qdrant_service.search(
                owner_id=owner_id,
                owner_type=owner_type,
                query_vector=query_embedding,
                limit=self.context_window_size,
                score_threshold=self.similarity_threshold
            )

            if not search_results:
                logger.warning(f"No relevant documents found for query: {query_text[:50]}...")
                return {
                    "response": "I couldn't find any relevant information in your uploaded documents. Please upload financial documents first.",
                    "sources": [],
                    "tokens_used": 0,
                    "processing_time_ms": int((time.time() - start_time) * 1000)
                }

            # Build context from search results
            context = self._build_context(search_results)

            # Build messages for LLM
            messages = self._build_messages(query_text, context, conversation_history)

            # Generate response
            completion = llm_provider.generate_completion(
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )

            # Extract sources
            sources = self._extract_sources(search_results, db)

            # Calculate processing time
            processing_time_ms = int((time.time() - start_time) * 1000)

            # Log query
            self._log_query(
                db=db,
                user_id=user_id,
                query_text=query_text,
                response_text=completion["response"],
                provider=provider_credentials.provider,
                tokens_used=completion["tokens_used"],
                processing_time_ms=processing_time_ms,
                success=True
            )

            logger.info(f"RAG query completed in {processing_time_ms}ms")

            return {
                "response": completion["response"],
                "sources": sources,
                "tokens_used": completion.get("tokens_used", 0),
                "processing_time_ms": processing_time_ms
            }

        except Exception as e:
            logger.error(f"RAG query error: {str(e)}")

            # Log failed query
            self._log_query(
                db=db,
                user_id=user_id,
                query_text=query_text,
                response_text=None,
                provider=provider_credentials.provider,
                tokens_used=0,
                processing_time_ms=int((time.time() - start_time) * 1000),
                success=False
            )

            raise

    def _build_context(self, search_results: List[Dict[str, Any]]) -> str:
        """Build context from search results."""
        context_parts = []

        for idx, result in enumerate(search_results, start=1):
            text = result["text"]
            score = result["score"]
            page = result.get("page_number", "N/A")

            context_parts.append(
                f"[Source {idx}] (Relevance: {score:.2f}, Page: {page})\n{text}"
            )

        return "\n\n---\n\n".join(context_parts)

    def _build_messages(
        self,
        query_text: str,
        context: str,
        conversation_history: List[ChatMessage] = None
    ) -> List[Dict[str, str]]:
        """Build messages for LLM."""
        system_message = {
            "role": "system",
            "content": """You are a helpful financial analyst assistant. Your role is to answer questions about financial documents using the provided context.

Instructions:
1. Answer questions based ONLY on the provided context from the user's documents
2. If the answer is not in the context, say so - don't make up information
3. Be specific and cite relevant numbers, dates, and details from the documents
4. Use professional but friendly language
5. For financial calculations, show your work
6. If you're uncertain, express appropriate caution

Remember: The user has uploaded their personal financial documents. Maintain confidentiality and professionalism."""
        }

        # Add conversation history
        messages = [system_message]

        if conversation_history:
            for msg in conversation_history:
                messages.append({
                    "role": msg.role,
                    "content": msg.content
                })

        # Add context and current query
        user_message = {
            "role": "user",
            "content": f"""Context from your documents:

{context}

---

Question: {query_text}

Please answer based on the context above."""
        }

        messages.append(user_message)

        return messages

    def _extract_sources(
        self,
        search_results: List[Dict[str, Any]],
        db: Session
    ) -> List[Dict[str, Any]]:
        """Extract source information from search results."""
        sources = []
        seen_documents = set()

        for result in search_results:
            doc_id = result["document_id"]

            if doc_id not in seen_documents:
                seen_documents.add(doc_id)

                # Get document info from database
                document = db.query(Document).filter(Document.id == doc_id).first()

                if document:
                    sources.append({
                        "document_id": str(doc_id),
                        "filename": document.filename,
                        "page_number": result.get("page_number"),
                        "relevance_score": result["score"]
                    })

        return sources

    def _log_query(
        self,
        db: Session,
        user_id: UUID,
        query_text: str,
        response_text: str,
        provider: str,
        tokens_used: int,
        processing_time_ms: int,
        success: bool
    ):
        """Log query to database."""
        try:
            query_log = QueryHistory(
                user_id=user_id,
                query_text=query_text,
                response_text=response_text,
                ai_provider=provider,
                tokens_used=tokens_used,
                processing_time_ms=processing_time_ms,
                success=success
            )

            db.add(query_log)
            db.commit()

        except Exception as e:
            logger.error(f"Failed to log query: {str(e)}")
            db.rollback()


# Global RAG service instance
rag_service = RAGService()
