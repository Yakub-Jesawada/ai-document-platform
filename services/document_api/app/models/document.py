# app/models/document.py
from typing import Optional, List, Dict, Any, TypedDict
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


class BBox(TypedDict):
    x: float
    y: float
    w: float
    h: float



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

    pages: List["DocumentPage"] = Relationship(
        back_populates="document",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

class DocumentPage(IDMixin, TimeMixin, BaseModel, table=True):
    __tablename__ = "document_pages"

    document_id: int = Field(foreign_key="documents.id", index=True)
    page_number: int = Field(index=True)
    # Page dimensions (coordinate space)
    width: float
    height: float
    confidence: Optional[float] = Field(default=None)
    # Relationships
    document: Optional[Document] = Relationship(back_populates="pages")
    lines: List["DocumentLine"] = Relationship(back_populates="page", sa_relationship_kwargs={"cascade": "all, delete-orphan"})



class DocumentLine(IDMixin, TimeMixin, BaseModel, table=True):
    __tablename__ = "document_lines"

    page_id: int = Field(foreign_key="document_pages.id", index=True)
    text: str
    confidence: Optional[float] = Field(default=None)
    # Normalized bounding box
    bbox: BBox = Field(sa_column=Column(JSONB))
    # Relationships
    page: Optional[DocumentPage] = Relationship(back_populates="lines")
    words: List["DocumentWord"] = Relationship(back_populates="line", sa_relationship_kwargs={"cascade": "all, delete-orphan"})


class DocumentWord(IDMixin, TimeMixin, BaseModel, table=True):
    __tablename__ = "document_words"

    line_id: int = Field(foreign_key="document_lines.id", index=True)
    text: str
    confidence: Optional[float] = Field(default=None)
    # Normalized bounding box
    bbox: BBox = Field(sa_column=Column(JSONB))
    # Relationships
    line: Optional[DocumentLine] = Relationship(back_populates="words")