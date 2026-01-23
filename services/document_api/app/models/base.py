# app/models/base.py
from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, Integer


class BaseModel(SQLModel):
    """Base class for all SQLModel models."""
    is_active: bool = Field(default=True)
    is_deleted: bool = Field(default=False)


class IDMixin:
    """Provides id (PK) and uuid for all models."""
    id: Optional[int] = Field(default=None, primary_key=True, sa_column_kwargs={"autoincrement": True})
    uuid: UUID = Field(default_factory=uuid4, unique=True, index=True, nullable=False)


class TimeMixin:
    """Provides automatic timestamp columns."""
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class UserMixin:
    """Tracks which user created/updated the record."""
    created_by_id: Optional[int] = Field(default=None, foreign_key="users.id")
    updated_by_id: Optional[int] = Field(default=None, foreign_key="users.id")
