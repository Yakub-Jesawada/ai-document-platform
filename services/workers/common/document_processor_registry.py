from workers.common.pdf_ocr_helper import extract_text, persist_ocr_result
from workers.common.document_chunking_helper import chunk_document, persist_chunking_result

class PdfDocumentProcessor:

    async def extract(self, document_uuid, s3_key) -> dict:
        return await extract_text(document_uuid, s3_key)

    async def persist(self, document_uuid, extracted_data: dict):
        await persist_ocr_result(document_uuid, extracted_data)

class DocumentChunker:
    async def create_chunks(self, document_id):
        return await chunk_document(document_id)


    async def persist_chunks(self, document_id, chunks):
        await persist_chunking_result(document_id, chunks)

PROCESSOR_REGISTRY = {
    "pdf": PdfDocumentProcessor(),
    "chunk": DocumentChunker(),
}
