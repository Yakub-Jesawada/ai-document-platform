from .base import BaseEvent
from shared.constant import DOCUMENT_CHUNKED

class DocumentChunked(BaseEvent):
    event_type: str = DOCUMENT_CHUNKED