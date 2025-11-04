"""
SQLAlchemy database models for the Financial Report Analyzer.
Includes: Reports, Embeddings, Chunks, and Audit Logs (NO Credential Storage).
"""

from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float, DateTime, Boolean, Text, 
    ForeignKey, Index, JSON, create_engine
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from pgvector.sqlalchemy import Vector
import uuid

Base = declarative_base()


class Report(Base):
    """Model for uploaded financial reports."""
    __tablename__ = "reports"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    file_type = Column(String(10), nullable=False)  # pdf, xlsx, csv, json, docx
    
    # Report metadata
    upload_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    processing_status = Column(String(20), default="processing")  # processing, indexed, ready, failed
    error_message = Column(Text, nullable=True)
    
    # Embedding tracking
    embedding_provider = Column(String(50), nullable=True)  # azure, google, aws
    embedding_model = Column(String(100), nullable=True)
    embedding_date = Column(DateTime, nullable=True)
    chunks_created = Column(Integer, default=0)
    
    # Relationships
    chunks = relationship("Chunk", back_populates="report", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="report")
    
    # Indexes
    __table_args__ = (
        Index('idx_upload_date', 'upload_date'),
        Index('idx_status', 'processing_status'),
    )

    def __repr__(self):
        return f"<Report(id={self.id}, filename={self.filename}, status={self.processing_status})>"


class Chunk(Base):
    """Model for document chunks with embeddings."""
    __tablename__ = "chunks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    report_id = Column(String(36), ForeignKey("reports.id"), nullable=False)
    
    # Chunk content and metadata
    chunk_text = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)  # Position in document
    page_number = Column(Integer, nullable=True)
    section_type = Column(String(50), nullable=True)  # table, paragraph, header, etc.
    
    # Vector embedding (1536 dimensions for OpenAI)
    embedding = Column(Vector(1536), nullable=True)
    embedding_model = Column(String(100), nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    report = relationship("Report", back_populates="chunks")
    
    # Indexes for efficient vector search
    __table_args__ = (
        Index('idx_report_id', 'report_id'),
        Index('idx_chunk_index', 'chunk_index'),
    )

    def __repr__(self):
        return f"<Chunk(id={self.id}, report_id={self.report_id}, page={self.page_number})>"


class AuditLog(Base):
    """Model for audit logging of queries and provider usage."""
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Query information
    query_text = Column(Text, nullable=False)
    query_type = Column(String(50), nullable=False)  # chat, bi_bot, embedding
    
    # Provider information (NOT credentials, just which provider was used)
    provider_name = Column(String(50), nullable=False)  # azure, google, aws
    provider_model = Column(String(100), nullable=False)
    
    # Results
    response_length = Column(Integer, nullable=True)
    processing_time_ms = Column(Float, nullable=True)
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    
    # Report context
    report_id = Column(String(36), ForeignKey("reports.id"), nullable=True)
    chunks_used = Column(Integer, default=0)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    session_id = Column(String(36), nullable=True)  # Session identifier for conversation tracking
    
    # Relationships
    report = relationship("Report", back_populates="audit_logs")
    
    # Indexes
    __table_args__ = (
        Index('idx_created_at', 'created_at'),
        Index('idx_provider', 'provider_name'),
        Index('idx_query_type', 'query_type'),
        Index('idx_session_id', 'session_id'),
    )

    def __repr__(self):
        return f"<AuditLog(id={self.id}, query_type={self.query_type}, provider={self.provider_name})>"


class ConversationMessage(Base):
    """Model for storing chat conversation history."""
    __tablename__ = "conversation_messages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Conversation tracking
    session_id = Column(String(36), nullable=False)
    message_index = Column(Integer, nullable=False)
    
    # Message content
    role = Column(String(20), nullable=False)  # user, assistant
    content = Column(Text, nullable=False)
    
    # Context
    provider_used = Column(String(50), nullable=True)
    model_used = Column(String(100), nullable=True)
    chunks_referenced = Column(JSON, nullable=True)  # List of chunk IDs used
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        Index('idx_session_id', 'session_id'),
        Index('idx_created_at', 'created_at'),
    )


def get_db_engine(database_url: str):
    """Create and return database engine."""
    return create_engine(database_url, echo=False, pool_pre_ping=True)


def get_session_maker(database_url: str):
    """Create and return session maker."""
    engine = get_db_engine(database_url)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db(database_url: str):
    """Initialize database tables."""
    engine = get_db_engine(database_url)
    Base.metadata.create_all(bind=engine)