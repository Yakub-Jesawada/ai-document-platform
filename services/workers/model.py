from typing import Optional, Dict, Any
from enum import Enum
from uuid import UUID

from sqlmodel import SQLModel, Field
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import Enum as SAEnum
from uuid import UUID, uuid4
from datetime import datetime

class BaseModel(SQLModel):
    """Base class for all SQLModel models."""
    is_active: bool = Field(default=True)
    is_deleted: bool = Field(default=False)


class IDMixin:
    """Provides id (PK) and uuid for all models."""
    id: Optional[int] = Field(default=None, primary_key=True, sa_column_kwargs={"autoincrement": True})
    uuid: UUID = Field(default_factory=uuid4, unique=True, index=True, nullable=False)


class TimeMixin:
    """Provides automatic timestamp columns."""
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class UserMixin:
    """Tracks which user created/updated the record."""
    created_by_id: Optional[int] = Field(default=None, foreign_key="users.id")
    updated_by_id: Optional[int] = Field(default=None, foreign_key="users.id")


# ======================================================
# Enums (same semantics as FastAPI, no relationships)
# ======================================================

class UploadStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentCategory(str, Enum):
    RESUME = "resume"
    LEGAL = "legal"
    MEDICAL = "medical"
    FINANCIAL = "financial"
    OTHER = "other"


class ProcessingStatus(str, Enum):
    UPLOADED = "uploaded"
    OCR_IN_PROGRESS = "ocr_in_progress"
    OCR_DONE = "ocr_done"
    EMBEDDING_IN_PROGRESS = "embedding_in_progress"
    EMBEDDING_DONE = "embedding_done"
    OCR_FAILED = "ocr_failed"
    EMBEDDING_FAILED = "embedding_failed"


# ======================================================
# Documents
# ======================================================

class Document(IDMixin, TimeMixin, BaseModel, table=True):
    __tablename__ = "documents"

    user_id: int
    filename: str
    file_type: str

    document_category: DocumentCategory = Field(
        sa_column=Column(
            SAEnum(DocumentCategory, native_enum=False)
        )
    )

    upload_status: UploadStatus = Field(
        sa_column=Column(
            SAEnum(UploadStatus, native_enum=False)
        )
    )

    storage_uri: str
    page_count: Optional[int] = None

    ai_metadata: Dict[str, Any] = Field(
        sa_column=Column(JSONB),
        default_factory=dict
    )
    # flags (fast filtering)
    ocr_completed: bool = Field(default=False)
    embedding_completed: bool = Field(default=False)
    # pipeline status
    status: ProcessingStatus = Field(
        sa_column=Column(
            SAEnum(ProcessingStatus, native_enum=False)
        )
    )


# ======================================================
# Document Pages
# ======================================================

class DocumentPage(IDMixin, TimeMixin, BaseModel, table=True):
    __tablename__ = "document_pages"

    document_id: int

    page_number: int
    width: float
    height: float

    confidence: Optional[float] = None


# ======================================================
# Document Lines
# ======================================================

class DocumentLine(IDMixin, TimeMixin, BaseModel, table=True):
    __tablename__ = "document_lines"

    page_id: int

    text: str
    confidence: Optional[float] = None

    bbox: Dict[str, Any] = Field(
        sa_column=Column(JSONB)
    )


# ======================================================
# Document Words
# ======================================================

class DocumentWord(IDMixin, TimeMixin, BaseModel, table=True):
    __tablename__ = "document_words"

    line_id: int

    text: str
    confidence: Optional[float] = None

    bbox: Dict[str, Any] = Field(
        sa_column=Column(JSONB)
    )
