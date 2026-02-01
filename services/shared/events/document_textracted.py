from .base import BaseEvent
from uuid import UUID
from datetime import datetime
from shared.constant import DOCUMENT_TEXTRACTED

class DocumentTextracted(BaseEvent):
    event_type: str = DOCUMENT_TEXTRACTED