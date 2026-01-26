# shared/events/base.py
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class BaseEvent(BaseModel):
    event_id: UUID
    event_type: str
    occurred_at: datetime
    document_uuid: UUID
