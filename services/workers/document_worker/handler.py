from shared.events.document_uploaded import DocumentUploaded

def handle_document_upload(event: DocumentUploaded):
    print(
        f"Document {event.document_uuid} received. "
        "Waiting for OCR & text normalization."
    )
