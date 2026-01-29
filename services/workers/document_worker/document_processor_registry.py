from workers.pdf_ocr_helper import PdfDocumentProcessor

PROCESSOR_REGISTRY = {
    "pdf": PdfDocumentProcessor(),
}
