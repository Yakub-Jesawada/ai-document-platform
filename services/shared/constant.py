import os
from dotenv import load_dotenv

load_dotenv()

KAFKA_FASTAPI_PRODUCER_CLIENT_ID=os.getenv('KAFKA_FASTAPI_PRODUCER_CLIENT_ID')
KAFKA_BROKER_URL=os.getenv('KAFKA_BROKER_URL')

DOCUMENT_UPLOAD_EVENT= 'document_uploaded'
DOCUMENT_TEXTRACTED= 'document_textracted'
DOCUMENT_CHUNKED = 'document_chunked'