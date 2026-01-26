from .base import BaseEvent
from uuid import UUID
from datetime import datetime
from shared.constant import DOCUMENT_UPLOAD_EVENT

class DocumentUploaded(BaseEvent):
    event_type: str = DOCUMENT_UPLOAD_EVENT
    uploaded_at: datetime
    uploader_uuid: UUID
