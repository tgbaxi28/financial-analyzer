"""Document management API routes."""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from pathlib import Path
import shutil

from app.database import get_db
from app.schemas import DocumentResponse, DocumentListResponse, ChatRequest, ChatResponse
from app.models import User, Document
from app.dependencies import get_current_user
from app.services.document_processor import document_processor
from app.services.pii_service import pii_service
from app.services.qdrant_service import qdrant_service
from app.services.llm_providers import LLMProviderFactory
from app.services.rag_service import rag_service
from app.config import settings
from app.utils.logger import logger


router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    owner_type: str = Form(...),
    owner_id: Optional[str] = Form(None),
    password: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload and process a financial document.

    Args:
        file: Uploaded file
        owner_type: Type of owner (user or family_member)
        owner_id: Owner ID (defaults to current user if not provided)
        password: Optional password for protected files
        current_user: Current authenticated user
        db: Database session

    Returns:
        Created document metadata
    """
    # Validate file extension
    file_ext = file.filename.split(".")[-1].lower()
    if file_ext not in settings.allowed_extensions_list:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed types: {settings.ALLOWED_EXTENSIONS}"
        )

    # Determine owner
    if owner_type == "user":
        final_owner_id = current_user.id
    elif owner_type == "family_member":
        if not owner_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="owner_id required for family_member"
            )
        final_owner_id = UUID(owner_id)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="owner_type must be 'user' or 'family_member'"
        )

    # Save uploaded file temporarily
    temp_file_path = settings.UPLOAD_DIR / f"{current_user.id}_{file.filename}"

    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        file_size = temp_file_path.stat().st_size

        # Check file size
        if file_size > settings.max_file_size_bytes:
            temp_file_path.unlink()
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE_MB}MB"
            )

        # Create document record
        document = Document(
            owner_id=final_owner_id,
            owner_type=owner_type,
            filename=file.filename,
            file_type=file_ext,
            file_size_bytes=file_size,
            processing_status="processing"
        )

        db.add(document)
        db.commit()
        db.refresh(document)

        logger.info(f"Document uploaded: {document.id} - {file.filename}")

        # Process document in background (for now, do it synchronously)
        try:
            # Process file and extract chunks
            chunks = document_processor.process_file(
                file_path=temp_file_path,
                file_type=file_ext,
                password=password
            )

            if not chunks:
                document.processing_status = "failed"
                db.commit()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to extract content from document"
                )

            # Anonymize PII/PHI in chunks
            anonymized_chunks = []
            for chunk in chunks:
                anonymized_text = pii_service.anonymize_text(chunk["text"])
                chunk["text"] = anonymized_text
                anonymized_chunks.append(chunk)

            logger.info(f"Anonymized {len(anonymized_chunks)} chunks")

            # Generate embeddings and store in Qdrant
            # We'll need to create a provider for embeddings
            # For now, we'll skip embedding and just store text

            # Store chunks in Qdrant (embedding will be added when queried)
            # This is a simplified version - in production, embed all chunks here

            document.chunk_count = len(anonymized_chunks)
            document.processing_status = "completed"
            document.qdrant_collection_name = qdrant_service.get_collection_name(
                final_owner_id, owner_type
            )

            db.commit()

            logger.info(f"Document processing completed: {document.id}")

        except Exception as e:
            logger.error(f"Document processing error: {str(e)}")
            document.processing_status = "failed"
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Document processing failed: {str(e)}"
            )

        finally:
            # Clean up temporary file
            document_processor.cleanup_file(temp_file_path)

        return DocumentResponse.model_validate(document)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        if temp_file_path.exists():
            temp_file_path.unlink()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Upload failed"
        )


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    owner_type: str = "user",
    owner_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List documents for current user or family member.

    Args:
        owner_type: Type of owner
        owner_id: Owner ID (defaults to current user)
        current_user: Current authenticated user
        db: Database session

    Returns:
        List of documents
    """
    # Determine owner
    if owner_type == "user":
        final_owner_id = current_user.id
    elif owner_type == "family_member":
        if not owner_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="owner_id required for family_member"
            )
        final_owner_id = owner_id
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="owner_type must be 'user' or 'family_member'"
        )

    # Query documents
    documents = db.query(Document).filter(
        Document.owner_id == final_owner_id,
        Document.owner_type == owner_type,
        Document.deleted_at.is_(None)
    ).all()

    return DocumentListResponse(
        documents=[DocumentResponse.model_validate(doc) for doc in documents],
        total=len(documents)
    )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get document by ID."""
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.deleted_at.is_(None)
    ).first()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    return DocumentResponse.model_validate(document)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete document (soft delete)."""
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.deleted_at.is_(None)
    ).first()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    # Delete from Qdrant
    qdrant_service.delete_document_chunks(
        owner_id=document.owner_id,
        owner_type=document.owner_type,
        document_id=document_id
    )

    # Soft delete
    from datetime import datetime
    document.deleted_at = datetime.utcnow()
    db.commit()

    logger.info(f"Document deleted: {document_id}")


@router.post("/chat", response_model=ChatResponse)
async def chat_with_documents(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Chat with documents using RAG.

    Args:
        request: Chat request
        current_user: Current authenticated user
        db: Database session

    Returns:
        Chat response with sources
    """
    try:
        response = await rag_service.query(
            db=db,
            user_id=current_user.id,
            owner_id=request.owner_id,
            owner_type=request.owner_type,
            query_text=request.query,
            provider_credentials=request.provider_credentials,
            conversation_history=request.conversation_history
        )

        return ChatResponse(**response)

    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat failed: {str(e)}"
        )
