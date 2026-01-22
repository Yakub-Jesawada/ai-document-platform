from uuid import UUID
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from database import get_db
from dependencies import get_current_active_user
from models.document import Document
from models.user import User, Collection
from schemas.document import (
    CollectionCreate,
    CollectionAddDocuments,
    CollectionDocumentResponseSchema,
    CollectionResponseSchema,
)
from schemas.base import StandardResponse, ResponseLevel


router = APIRouter(
    prefix="/collections",
    tags=["collections"],
)

# ---------------------------------------------------------
# Create collection (NO documents here)
# ---------------------------------------------------------

@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=StandardResponse[CollectionResponseSchema],
)
async def create_collection(
    collection_data: CollectionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    collection = Collection(
        user_id=current_user.id,
        name=collection_data.name,
    )

    db.add(collection)
    await db.commit()
    await db.refresh(collection)

    return StandardResponse(
        level=ResponseLevel.SUCCESS,
        detail="Collection created successfully",
        results=CollectionResponseSchema.model_validate(collection),
    )


# ---------------------------------------------------------
# List collections (with documents)
# ---------------------------------------------------------

@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=StandardResponse[List[CollectionDocumentResponseSchema]],
)
async def list_collections(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    stmt = (
        select(Collection)
        .options(selectinload(Collection.documents))
        .where(
            Collection.user_id == current_user.id,
            Collection.is_deleted == False,
        )
        .order_by(Collection.created_at.desc())
    )

    result = await db.execute(stmt)
    collections = result.scalars().all()

    return StandardResponse(
        level=ResponseLevel.SUCCESS,
        detail=f"Found {len(collections)} collections",
        results=[
            CollectionDocumentResponseSchema.model_validate(c)
            for c in collections
        ],
    )


# ---------------------------------------------------------
# Get collection detail
# ---------------------------------------------------------

@router.get(
    "/{collection_uuid}",
    status_code=status.HTTP_200_OK,
    response_model=StandardResponse[CollectionDocumentResponseSchema],
)
async def get_collection_detail(
    collection_uuid: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    stmt = (
        select(Collection)
        .options(selectinload(Collection.documents))
        .where(
            Collection.uuid == collection_uuid,
            Collection.user_id == current_user.id,
            Collection.is_deleted == False,
        )
    )

    result = await db.execute(stmt)
    collection = result.scalar_one_or_none()

    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    return StandardResponse(
        level=ResponseLevel.SUCCESS,
        detail="Collection retrieved successfully",
        results=CollectionDocumentResponseSchema.model_validate(collection),
    )


# ---------------------------------------------------------
# Add documents to collection
# ---------------------------------------------------------

@router.post(
    "/{collection_uuid}/documents",
    status_code=status.HTTP_200_OK,
    response_model=StandardResponse[CollectionDocumentResponseSchema],
)
async def add_documents_to_collection(
    collection_uuid: UUID,
    payload: CollectionAddDocuments,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    if not payload.document_uuids:
        raise HTTPException(
            status_code=400,
            detail="document_uuids cannot be empty",
        )

    # Fetch collection
    stmt = select(Collection).where(
        Collection.uuid == collection_uuid,
        Collection.user_id == current_user.id,
        Collection.is_deleted == False,
    )
    result = await db.execute(stmt)
    collection = result.scalar_one_or_none()

    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    # Fetch documents (ownership check)
    stmt = select(Document).where(
        Document.uuid.in_(payload.document_uuids),
        Document.user_id == current_user.id,
        Document.is_deleted == False,
    )
    result = await db.execute(stmt)
    documents = result.scalars().all()

    if len(documents) != len(payload.document_uuids):
        raise HTTPException(
            status_code=400,
            detail="One or more document UUIDs are invalid",
        )

    # Link documents
    collection.documents.extend(documents)

    await db.commit()
    await db.refresh(collection)

    return StandardResponse(
        level=ResponseLevel.SUCCESS,
        detail="Documents added to collection",
        results=CollectionDocumentResponseSchema.model_validate(collection),
    )


# -----------------------------------------
# Remove document(s) from a collection
# -----------------------------------------
@router.post("/{collection_uuid}/documents/remove", status_code=status.HTTP_200_OK)
async def remove_documents_from_collection(
    collection_uuid: UUID,
    payload: CollectionAddDocuments,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Remove document(s) from a collection only.
    Document itself is not deleted and may exist in other collections.
    """
    if not payload.document_uuids:
        raise HTTPException(status_code=400, detail="document_uuids cannot be empty")

    # Fetch collection
    stmt = select(Collection).where(
        Collection.uuid == collection_uuid,
        Collection.user_id == current_user.id
    )
    result = await db.execute(stmt)
    collection = result.scalar_one_or_none()

    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    # Fetch documents (ownership check)
    stmt = select(Document).where(
        Document.uuid.in_(payload.document_uuids),
        Document.user_id == current_user.id
    )
    result = await db.execute(stmt)
    documents = result.scalars().all()

    if not documents:
        raise HTTPException(status_code=400, detail="No valid documents found")

    # Remove documents from collection
    for doc in documents:
        if doc in collection.documents:
            collection.documents.remove(doc)

    await db.commit()
    await db.refresh(collection)

    return StandardResponse(
        level=ResponseLevel.SUCCESS,
        detail=f"Removed {len(documents)} document(s) from collection",
        results=CollectionDocumentResponseSchema.model_validate(collection)
    )


@router.delete("/{collection_uuid}", status_code=status.HTTP_200_OK)
async def delete_collection(
    collection_uuid: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Hard delete a collection.
    Documents remain intact.
    """
    stmt = select(Collection).where(
        Collection.uuid == collection_uuid,
        Collection.user_id == current_user.id
    )
    result = await db.execute(stmt)
    collection = result.scalar_one_or_none()

    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    # Remove all links to documents
    collection.documents.clear()

    # Delete the collection row
    await db.delete(collection)
    await db.commit()

    return StandardResponse(
        level=ResponseLevel.SUCCESS,
        detail="Collection deleted successfully",
        results=None
    )
