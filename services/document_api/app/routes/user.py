from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, select, or_, func
from typing import List, Dict, Optional
from database import get_db
from schemas.user import UserResponseSchema, UserCreate
from schemas.base import StandardResponse
import logging
from config import settings
from models.user import User
from dependencies import get_password_hash

logger = logging.getLogger(__name__)

# Configure users router with prefix and tags
router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)

# User registration endpoint
@router.post("/", response_model=StandardResponse[UserResponseSchema], status_code=status.HTTP_201_CREATED)
async def create_user(
    user: UserCreate, 
    db: AsyncSession = Depends(get_db),
):
    """Create a new user (admin only)"""
    # Check if email or username already exists
    query = select(User).where(
        or_(
            User.email == user.email,
        )
    )
    result = await db.execute(query)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )
    try:
        # Create new user with hashed password
        hashed_password = get_password_hash(user.password)
        db_user = User(
            email=user.email,
            first_name=user.first_name,
            middle_name=user.middle_name,
            last_name=user.last_name,
            hashed_password=hashed_password,
        )
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)

        return StandardResponse(
            level="success",
            detail="User created successfully",
            results=UserResponseSchema.model_validate(db_user)
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating user: {str(e)}"
        )