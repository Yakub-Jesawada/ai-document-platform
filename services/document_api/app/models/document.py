# app/models/document.py
import uuid
from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from .base import IDMixin, TimeMixin, BaseModel



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
    file_type: str                     # pdf, jpg, docx
    document_category: str             # resume, legal, medical, etc
    upload_status: str                 # uploaded, processing, completed, failed
    storage_uri: str                   # s3/minio path
    page_count: Optional[int] = None

    collections: List["Collection"] = Relationship(
        back_populates="documents",
        link_model=CollectionDocumentLink
    )
