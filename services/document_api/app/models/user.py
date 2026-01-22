# app/models/user.py
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from .base import IDMixin, TimeMixin, BaseModel
from .document import CollectionDocumentLink



# Many-to-many link table
class UserRoleLink(SQLModel, table=True):
    __tablename__ = 'user_role_link'

    user_id: int = Field(foreign_key="users.id", primary_key=True)
    role_id: int = Field(foreign_key="roles.id", primary_key=True)


# Role model
class Role(SQLModel, table=True):
    __tablename__ = "roles"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True, max_length=50)

    users: List["User"] = Relationship(
        back_populates="roles",   # ✅ MUST match User.roles
        link_model=UserRoleLink
    )

# User model
class User(IDMixin, TimeMixin, BaseModel, table=True):
    __tablename__ = "users"

    first_name: str = Field(max_length=255)
    last_name: str = Field(max_length=255)
    middle_name: Optional[str] = Field(default=None, max_length=255)
    email: str = Field(unique=True, index=True, max_length=255)
    hashed_password: str = Field(max_length=255)
    is_superuser: bool = Field(default=False)

    roles: List["Role"] = Relationship(
        back_populates="users",
        link_model=UserRoleLink
    )

class Collection(IDMixin, TimeMixin, BaseModel, table=True):
    __tablename__ = "collections"

    user_id: int = Field(foreign_key="users.id")

    name: str = Field(index=True)
    documents: List["Document"] = Relationship(
        back_populates="collections",
        link_model=CollectionDocumentLink
    )
