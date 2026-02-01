import time
import boto3
import asyncio
import logging
from sqlmodel import select, delete
from collections import defaultdict
from workers.common.database import get_kafka_db_session
from workers.common.model import Document, DocumentPage, DocumentLine, DocumentWord, ProcessingStatus
from workers.common.env import TEXTRACT_SECRET_ACCESS_KEY, TEXTRACT_ACCESS_KEY, TEXTRACT_BUCKET_NAME, TEXTRACT_BUCKET_REGION


logger = logging.getLogger(__name__)

def invoke_text_detect_job(textract, textract_bucket, key):
    response = textract.start_document_text_detection(
        DocumentLocation={
            "S3Object": {"Bucket": textract_bucket, "Name": key}
        }
    )
    return response["JobId"]


async def wait_for_job_completion_async(textract, job_id, poll_interval=3, timeout=300):
    start_time = time.time()

    while True:
        response = await asyncio.to_thread(
            textract.get_document_text_detection,
            JobId=job_id,
        )

        status = response["JobStatus"]
        logger.info(f"Textract job {job_id} status: {status}")

        if status == "SUCCEEDED":
            return True

        if status in ("FAILED", "PARTIAL_SUCCESS"):
            raise RuntimeError(f"Textract job failed with status: {status}")

        if time.time() - start_time > timeout:
            raise TimeoutError("Textract job timed out")

        await asyncio.sleep(poll_interval)



def job_results_structured(textract, job_id):
    pages = defaultdict(lambda: {
        "text": "",
        "lines": [],
        "page_bbox": None   # <-- page dimensions live here
    })


    word_map = {}

    next_token = None

    while True:
        kwargs = {"JobId": job_id}
        if next_token:
            kwargs["NextToken"] = next_token

        response = textract.get_document_text_detection(**kwargs)

        # 0️⃣ Process PAGE blocks (page metadata)
        for block in response["Blocks"]:
            if block["BlockType"] == "PAGE":
                page_no = block["Page"]
                pages[page_no]["page_bbox"] = block["Geometry"]["BoundingBox"]

        # 1️⃣ Index WORD blocks
        for block in response["Blocks"]:
            if block["BlockType"] == "WORD":
                word_map[block["Id"]] = {
                    "text": block["Text"],
                    "confidence": block["Confidence"],
                    "bbox": block["Geometry"]["BoundingBox"]
                }

        # 2️⃣ Process LINE blocks
        for block in response["Blocks"]:
            if block["BlockType"] != "LINE":
                continue

            page_no = block["Page"]

            words = []
            for rel in block.get("Relationships", []):
                if rel["Type"] == "CHILD":
                    for word_id in rel["Ids"]:
                        if word_id in word_map:
                            words.append(word_map[word_id])

            line_obj = {
                "text": block["Text"],
                "confidence": block["Confidence"],
                "bbox": block["Geometry"]["BoundingBox"],
                "words": words
            }

            pages[page_no]["lines"].append(line_obj)

        if "NextToken" not in response:
            break

        next_token = response["NextToken"]

    # 3️⃣ Build page text AFTER collecting all lines
    for page_no, page in pages.items():
        page["text"] = "\n".join(line["text"] for line in page["lines"])
        page["lines"].sort(key=lambda l: l["bbox"]["Top"])

    return dict(pages)


async def extract_text(document_uuid, s3_key):
    logger.info(f"Starting text extraction for document={document_uuid}")

    textract = boto3.client(
        "textract",
        region_name=TEXTRACT_BUCKET_REGION,
        aws_access_key_id=TEXTRACT_ACCESS_KEY,
        aws_secret_access_key=TEXTRACT_SECRET_ACCESS_KEY,
    )

    # 1️⃣ Start job (thread)
    job_id = await asyncio.to_thread(
        invoke_text_detect_job,
        textract,
        TEXTRACT_BUCKET_NAME,
        s3_key,
    )

    # 2️⃣ Wait for completion (async polling)
    await wait_for_job_completion_async(textract, job_id)

    # 3️⃣ Fetch + structure results (thread)
    pages = await asyncio.to_thread(
        job_results_structured,
        textract,
        job_id,
    )

    return pages



async def persist_ocr_result(document_uuid, ocr_pages: dict):
    async with get_kafka_db_session() as session:
        try:
            # 🔍 Fetch document
            stmt = select(Document).where(Document.uuid == document_uuid)
            result = await session.execute(stmt)
            document = result.scalar_one_or_none()

            if not document:
                logger.error(
                    "OCR persistence failed: document not found (uuid=%s)",
                    document_uuid,
                )
                raise ValueError("Document not found")

            # 🛑 Idempotency guard
            if document.ocr_completed:
                logger.info(
                    "OCR already completed, skipping persistence (uuid=%s)",
                    document_uuid,
                )
                return

            await session.execute(
                delete(DocumentWord).where(
                    DocumentWord.line_id.in_(
                        select(DocumentLine.id)
                        .join(
                            DocumentPage,
                            DocumentLine.page_id == DocumentPage.id  # ✅ explicit ON
                        )
                        .where(DocumentPage.document_id == document.id)
                    )
                )
            )

            await session.execute(
                delete(DocumentLine).where(
                    DocumentLine.page_id.in_(
                        select(DocumentPage.id)
                        .where(DocumentPage.document_id == document.id)
                    )
                )
            )
            await session.execute(
                delete(DocumentPage).where(
                    DocumentPage.document_id == document.id
                )
            )
            await session.flush()

            # 📄 Persist OCR hierarchy
            for page_no, page_data in ocr_pages.items():
                page = DocumentPage(
                    document_id=document.id,
                    page_number=int(page_no),
                    text=page_data["text"],
                    height=page_data["page_bbox"]["Height"],
                    width=page_data["page_bbox"]["Width"],
                    is_active=True,
                    is_deleted=False,
                )
                session.add(page)
                await session.flush()

                for line_data in page_data["lines"]:
                    line = DocumentLine(
                        page_id=page.id,
                        text=line_data["text"],
                        confidence=line_data["confidence"],
                        bbox=line_data["bbox"],
                        is_active=True,
                        is_deleted=False,
                    )
                    session.add(line)
                    await session.flush()

                    for word_data in line_data["words"]:
                        word = DocumentWord(
                            line_id=line.id,
                            text=word_data["text"],
                            confidence=word_data["confidence"],
                            bbox=word_data["bbox"],
                            is_active=True,
                            is_deleted=False,
                        )
                        session.add(word)

            # ✅ Final document state
            document.ocr_completed = True
            document.status = ProcessingStatus.OCR_DONE

            await session.commit()

            logger.info(
                "OCR data persisted successfully (uuid=%s)",
                document_uuid,
            )

        except Exception as exc:
            await session.rollback()

            logger.exception(
                "OCR persistence failed (uuid=%s): %s",
                document_uuid,
                exc,
            )

            async with get_kafka_db_session() as fail_session:
                stmt = select(Document).where(Document.uuid == document_uuid)
                result = await fail_session.execute(stmt)
                document = result.scalar_one_or_none()

                if document:
                    document.ocr_completed = False
                    document.status = ProcessingStatus.OCR_FAILED
                    await fail_session.commit()

            raise