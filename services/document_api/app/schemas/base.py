from pydantic import BaseModel
from typing import Optional 
from typing import TypeVar, Generic, Optional
from pydantic import BaseModel
from enum import Enum


# Define possible response levels
class ResponseLevel(str, Enum):
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"

# Use TypeVar for generic type handling
T = TypeVar('T')

class StandardResponse(BaseModel, Generic[T]):
    level: ResponseLevel = ResponseLevel.SUCCESS
    detail: str
    results: Optional[T] = None


    class Config:
        from_attributes = True