# app/models/document.py
import uuid
from typing import Optional, List, Dict, Any
from sqlmodel import Field, Relationship
from .base import IDMixin, TimeMixin, BaseModel
from sqlalchemy import Enum as SAEnum
from enum import Enum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import Column

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



class CollectionDocumentLink(TimeMixin, BaseModel, table=True):
    __tablename__ = "collection_documents"

    collection_id: int = Field(
        foreign_key="collections.id",
        primary_key=True
    )
    document_id: int = Field(
        foreign_key="documents.id",
        primary_key=True
    )


class Document(IDMixin, TimeMixin, BaseModel, table=True):
    __tablename__ = "documents"

    user_id: int = Field(foreign_key="users.id")

    filename: str
    file_type: str                         # pdf, jpg, docx
    document_category: DocumentCategory = Field(
    sa_column=Column(
            SAEnum(DocumentCategory, native_enum=False)
        ),
        default=DocumentCategory.OTHER
    )
    upload_status: UploadStatus = Field(
        sa_column=Column(
            SAEnum(UploadStatus, native_enum=False)
        ),
        default=UploadStatus.UPLOADED
    )
    storage_uri: str
    page_count: Optional[int] = None
    ai_metadata: Dict[str, Any] = Field(
        sa_column=Column(JSONB),
        default_factory=dict
    )

    collections: List["Collection"] = Relationship(
        back_populates="documents",
        link_model=CollectionDocumentLink
    )
