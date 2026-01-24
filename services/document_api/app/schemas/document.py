from pydantic import BaseModel, Field, computed_field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from helpers import get_s3_storage

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
    page_count: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    # 👇 INTERNAL ONLY (used to generate presigned URL)
    storage_uri: str

    @computed_field
    @property
    def download_url(self) -> str:
        """
        Ephemeral presigned URL generated at response time.
        """
        storage = get_s3_storage()
        return storage.generate_presigned_url(self.storage_uri)

    model_config = {
        "from_attributes": True,
        "fields": {
            "storage_uri": {"exclude": True},
        },
    }


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
    documents: List[DocumentResponseSchema]

    class Config:
        from_attributes = True

class FileItem(BaseModel):
    filename: str
    category: str