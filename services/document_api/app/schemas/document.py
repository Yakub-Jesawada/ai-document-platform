from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class DocumentCreate(BaseModel):
    filename: str
    file_type: str                 # pdf, jpg, docx
    document_category: str         # resume, legal, etc
    storage_uri: str
    page_count: Optional[int] = None


class CollectionAddDocuments(BaseModel):
    document_uuids: List[UUID]


class DocumentResponseSchema(BaseModel):
    uuid: UUID
    filename: str
    file_type: str
    document_category: str
    upload_status: str
    storage_uri: str
    page_count: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentListResponseSchema(BaseModel):
    uuid: UUID
    filename: str
    file_type: str
    document_category: str
    upload_status: str
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentUploadResponseSchema(BaseModel):
    uuid: UUID
    filename: str
    file_type: str
    upload_status: str
    message: str

    class Config:
        from_attributes = True


class CollectionCreate(BaseModel):
    name: str


class CollectionAddDocuments(BaseModel):
    document_uuids: Optional[List[UUID]] = Field(default_factory=list)



class CollectionResponseSchema(BaseModel):
    uuid: UUID
    name: str
    created_at: datetime

    class Config:
        from_attributes = True


class CollectionDocumentResponseSchema(BaseModel):
    uuid: UUID
    name: str
    created_at: datetime
    documents: List[DocumentListResponseSchema]

    class Config:
        from_attributes = True

class FileItem(BaseModel):
    filename: str
    category: str