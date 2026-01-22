import os
from uuid import UUID
from typing import List, Optional

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    UploadFile,
    File,
    Form,
)
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import settings, get_db
from dependencies import get_current_active_user
from models.document import Document
from models.user import User, Collection
from schemas.document import (
    DocumentResponseSchema,
    DocumentListResponseSchema,
    DocumentUploadResponseSchema,
)
from schemas.base import StandardResponse, ResponseLevel


router = APIRouter(
    prefix="/documents",
    tags=["documents"],
)

BASE_FILE_PATH = settings.BASE_FILE_PATH


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def get_file_extension(filename: str) -> str:
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


async def get_or_create_default_collection(
    db: AsyncSession,
    user: User,
) -> Collection:
    stmt = select(Collection).where(
        Collection.user_id == user.id,
        Collection.name == "default_collection",
        Collection.is_deleted == False,
    )
    result = await db.execute(stmt)
    collection = result.scalar_one_or_none()

    if collection:
        return collection

    collection = Collection(
        user_id=user.id,
        name="default_collection",
    )
    db.add(collection)
    await db.flush()  # get PK without committing

    return collection


# ---------------------------------------------------------
# Upload multiple documents
# ---------------------------------------------------------

@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=StandardResponse[List[DocumentUploadResponseSchema]],
)
async def upload_documents(
    files: List[UploadFile] = File(...),
    document_category: str = Form(default="general"),
    collection_uuid: Optional[UUID] = Form(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Upload one or more documents.
    - If collection_uuid is provided → add documents to that collection
    - Else → add documents to default_collection (auto-created)
    """

    # -----------------------------------------------------
    # Resolve collection
    # -----------------------------------------------------
    if collection_uuid:
        stmt = select(Collection).where(
            Collection.uuid == collection_uuid,
            Collection.user_id == current_user.id,
            Collection.is_deleted == False,
        )
        result = await db.execute(stmt)
        collection = result.scalar_one_or_none()

        if not collection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Collection not found",
            )
    else:
        collection = await get_or_create_default_collection(db, current_user)

    # -----------------------------------------------------
    # Prepare filesystem
    # -----------------------------------------------------
    user_dir = os.path.join(BASE_FILE_PATH, str(current_user.uuid))
    os.makedirs(user_dir, exist_ok=True)

    uploaded_documents: List[Document] = []

    # -----------------------------------------------------
    # Save files + create documents
    # -----------------------------------------------------
    for file in files:
        file_type = get_file_extension(file.filename)
        file_path = os.path.join(user_dir, file.filename)

        try:
            contents = await file.read()
            with open(file_path, "wb") as f:
                f.write(contents)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save file {file.filename}: {str(e)}",
            )

        document = Document(
            user_id=current_user.id,
            filename=file.filename,
            file_type=file_type,
            document_category=document_category,
            upload_status="uploaded",
            storage_uri=file_path,
        )

        db.add(document)
        uploaded_documents.append(document)

    # -----------------------------------------------------
    # Link documents to collection & commit once
    # -----------------------------------------------------
    await db.flush()  # assign IDs

    if collection:
        collection.documents.extend(uploaded_documents)

    await db.commit()

    # -----------------------------------------------------
    # Response
    # -----------------------------------------------------
    return StandardResponse(
        level=ResponseLevel.SUCCESS,
        detail=f"{len(uploaded_documents)} document(s) uploaded successfully",
        results=[
            DocumentUploadResponseSchema(
                uuid=doc.uuid,
                filename=doc.filename,
                file_type=doc.file_type,
                upload_status=doc.upload_status,
                message="Uploaded successfully",
            )
            for doc in uploaded_documents
        ],
    )


# ---------------------------------------------------------
# List documents
# ---------------------------------------------------------

@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=StandardResponse[List[DocumentListResponseSchema]],
)
async def list_documents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    stmt = select(Document).where(
        Document.user_id == current_user.id,
        Document.is_deleted == False,
    ).order_by(Document.created_at.desc())

    result = await db.execute(stmt)
    documents = result.scalars().all()

    return StandardResponse(
        level=ResponseLevel.SUCCESS,
        detail=f"Found {len(documents)} documents",
        results=[DocumentListResponseSchema.model_validate(doc) for doc in documents],
    )


# ---------------------------------------------------------
# Document detail
# ---------------------------------------------------------

@router.get(
    "/{document_uuid}",
    status_code=status.HTTP_200_OK,
    response_model=StandardResponse[DocumentResponseSchema],
)
async def get_document_detail(
    document_uuid: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    stmt = select(Document).where(
        Document.uuid == document_uuid,
        Document.user_id == current_user.id,
        Document.is_deleted == False,
    )

    result = await db.execute(stmt)
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    return StandardResponse(
        level=ResponseLevel.SUCCESS,
        detail="Document retrieved successfully",
        results=DocumentResponseSchema.model_validate(document),
    )


# ---------------------------------------------------------
# Download document
# ---------------------------------------------------------

@router.get("/{document_uuid}/download", status_code=status.HTTP_200_OK)
async def download_document(
    document_uuid: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    stmt = select(Document).where(
        Document.uuid == document_uuid,
        Document.user_id == current_user.id,
        Document.is_deleted == False,
    )

    result = await db.execute(stmt)
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if not os.path.exists(document.storage_uri):
        raise HTTPException(status_code=404, detail="File not found on server")

    return FileResponse(
        path=document.storage_uri,
        filename=document.filename,
        media_type="application/octet-stream",
    )


# -----------------------------------------
# Delete a document
# -----------------------------------------
@router.delete("/{document_uuid}", status_code=status.HTTP_200_OK)
async def delete_document(
    document_uuid: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Delete a document.
    - If remove_from_all_collections=True → delete document completely + remove links + delete file
    - Otherwise, document remains in other collections
    """
    stmt = select(Document).where(
        Document.uuid == document_uuid,
        Document.user_id == current_user.id
    )
    result = await db.execute(stmt)
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Remove all links
    document.collections.clear()

    # Delete document row
    await db.delete(document)

    await db.commit()
    return StandardResponse(
        level=ResponseLevel.SUCCESS,
        detail="Document deleted successfully",
        results=None
    )
