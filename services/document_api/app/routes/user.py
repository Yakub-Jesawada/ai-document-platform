from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from database import get_db
from schemas.user import UserResponseSchema, UserCreate
from schemas.base import StandardResponse, ResponseLevel
from models.user import User
from dependencies import get_password_hash

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)


@router.post("/", response_model=StandardResponse[UserResponseSchema], status_code=status.HTTP_201_CREATED)
async def create_user(
    user: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new user"""
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
        level=ResponseLevel.SUCCESS,
        detail="User created successfully",
        results=UserResponseSchema.model_validate(db_user)
    )
