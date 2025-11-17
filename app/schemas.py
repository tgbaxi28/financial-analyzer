"""Pydantic schemas for API request/response models."""
from datetime import datetime
from typing import Optional, Any, Dict
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, ConfigDict


# User Schemas
class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)


class UserCreate(UserBase):
    """Schema for user registration."""
    pass


class UserResponse(UserBase):
    """Schema for user response."""
    id: UUID
    created_at: datetime
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


# Family Member Schemas
class FamilyMemberBase(BaseModel):
    """Base family member schema."""
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    relationship: Optional[str] = Field(None, max_length=50)


class FamilyMemberCreate(FamilyMemberBase):
    """Schema for creating family member."""
    pass


class FamilyMemberUpdate(BaseModel):
    """Schema for updating family member."""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    relationship: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None


class FamilyMemberResponse(FamilyMemberBase):
    """Schema for family member response."""
    id: UUID
    user_id: UUID
    created_at: datetime
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


# Authentication Schemas
class MagicLinkRequest(BaseModel):
    """Schema for requesting magic link."""
    email: EmailStr


class MagicLinkResponse(BaseModel):
    """Schema for magic link response."""
    message: str
    email: EmailStr


class MagicLinkVerify(BaseModel):
    """Schema for verifying magic link."""
    token: str


class TokenResponse(BaseModel):
    """Schema for token response."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# Document Schemas
class DocumentUpload(BaseModel):
    """Schema for document upload metadata."""
    owner_type: str = Field(..., pattern="^(user|family_member)$")
    owner_id: Optional[UUID] = None
    password: Optional[str] = None


class DocumentResponse(BaseModel):
    """Schema for document response."""
    id: UUID
    owner_id: UUID
    owner_type: str
    filename: str
    file_type: str
    file_size_bytes: Optional[int]
    upload_date: datetime
    processing_status: str
    chunk_count: int
    metadata: Optional[Dict[str, Any]]

    model_config = ConfigDict(from_attributes=True)


class DocumentListResponse(BaseModel):
    """Schema for document list response."""
    documents: list[DocumentResponse]
    total: int


# AI Provider Schemas
class AIProviderCredentials(BaseModel):
    """Schema for AI provider credentials (session-only)."""
    provider: str = Field(..., pattern="^(openai|azure_openai|aws_bedrock|google_gemini)$")
    api_key: str = Field(..., min_length=1)
    endpoint: Optional[str] = None
    model_name: Optional[str] = None
    region: Optional[str] = None


class ChatMessage(BaseModel):
    """Schema for chat message."""
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str = Field(..., min_length=1)


class ChatRequest(BaseModel):
    """Schema for chat request."""
    query: str = Field(..., min_length=1)
    owner_id: UUID
    owner_type: str = Field(..., pattern="^(user|family_member)$")
    provider_credentials: AIProviderCredentials
    conversation_history: Optional[list[ChatMessage]] = []


class ChatResponse(BaseModel):
    """Schema for chat response."""
    response: str
    sources: list[Dict[str, Any]]
    tokens_used: Optional[int]
    processing_time_ms: int


# Query History Schemas
class QueryHistoryResponse(BaseModel):
    """Schema for query history response."""
    id: UUID
    query_text: str
    response_text: Optional[str]
    ai_provider: Optional[str]
    processing_time_ms: Optional[int]
    created_at: datetime
    success: bool

    model_config = ConfigDict(from_attributes=True)


# Financial Metrics Schemas
class FinancialMetricCreate(BaseModel):
    """Schema for creating financial metric."""
    owner_id: UUID
    owner_type: str = Field(..., pattern="^(user|family_member)$")
    metric_type: str
    metric_name: str
    metric_value: Optional[float]
    metric_data: Optional[Dict[str, Any]]
    period_start: Optional[datetime]
    period_end: Optional[datetime]


class FinancialMetricResponse(BaseModel):
    """Schema for financial metric response."""
    id: UUID
    owner_id: UUID
    owner_type: str
    metric_type: str
    metric_name: str
    metric_value: Optional[float]
    metric_data: Optional[Dict[str, Any]]
    period_start: Optional[datetime]
    period_end: Optional[datetime]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Audit Log Schemas
class AuditLogResponse(BaseModel):
    """Schema for audit log response."""
    id: UUID
    user_id: Optional[UUID]
    action: str
    resource_type: Optional[str]
    resource_id: Optional[UUID]
    details: Optional[Dict[str, Any]]
    created_at: datetime
    status: str

    model_config = ConfigDict(from_attributes=True)


# Health Check Schema
class HealthCheckResponse(BaseModel):
    """Schema for health check response."""
    status: str
    timestamp: datetime
    version: str
    database: str
    qdrant: str
