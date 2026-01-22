from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta
import logging

from config import settings
from database import get_db
from dependencies import (
    authenticate_user_by_email,
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
    get_user_by_email,
)
from schemas.auth import (
    LoginRequest,
    LoginResponseSchema,
    RefreshTokenRequest,
    RefreshTokenResponseSchema,
)
from schemas.base import StandardResponse, ResponseLevel

logger = logging.getLogger(__name__)

ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS

router = APIRouter(
    prefix='/auth',
    tags=["authentication"]
)


@router.post("/login", response_model=StandardResponse[LoginResponseSchema])
async def login(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate user with email and password, returns JWT access and refresh tokens.
    """
    user = await authenticate_user_by_email(db, login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account is inactive"
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )

    refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token = create_refresh_token(
        data={"sub": user.email}, expires_delta=refresh_token_expires
    )

    return StandardResponse(
        level=ResponseLevel.SUCCESS,
        detail="Login successful",
        results=LoginResponseSchema(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user=user
        )
    )


@router.post("/refresh", response_model=StandardResponse[RefreshTokenResponseSchema])
async def refresh_token(
    token_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Get new access and refresh tokens using a valid refresh token.
    """
    email = verify_refresh_token(token_data.refresh_token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await get_user_by_email(db, email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account is inactive"
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    new_access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )

    refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    new_refresh_token = create_refresh_token(
        data={"sub": user.email}, expires_delta=refresh_token_expires
    )

    return StandardResponse(
        level=ResponseLevel.SUCCESS,
        detail="Tokens refreshed successfully",
        results=RefreshTokenResponseSchema(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer"
        )
    )
