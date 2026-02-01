from sqlalchemy import select
from workers.common.database import get_kafka_db_session
from workers.common.model import DocumentPage, DocumentLine, DocumentChunk, Document, ProcessingStatus
from langchain_text_splitters import RecursiveCharacterTextSplitter, TokenTextSplitter
import tiktoken


encoder = tiktoken.get_encoding("cl100k_base")

def count_tokens(text: str) -> int:
    return len(encoder.encode(text))



async def fetch_pages_with_lines(document_id: int):
    async with get_kafka_db_session() as session:
        page_result = await session.execute(
            select(DocumentPage)
            .where(DocumentPage.document_id == document_id)
            .order_by(DocumentPage.page_number)
        )

        pages = page_result.scalars().all()

        pages_with_lines = []

        for page in pages:
            line_result = await session.execute(
                select(DocumentLine)
                .where(DocumentLine.page_id == page.id)
                .order_by(DocumentLine.created_at)
            )

            lines = line_result.scalars().all()

            pages_with_lines.append(
                {
                    "page_number": page.page_number,
                    "lines": lines,
                }
            )

        return pages_with_lines



def build_document_text(pages_with_lines) -> str:
    parts = []

    for page in pages_with_lines:
        parts.append(f"\n\n=== Page {page['page_number']} ===\n\n")

        for line in page["lines"]:
            if line.text:
                parts.append(line.text)

    return "\n".join(parts)


def split_by_structure(
    text: str,
    chunk_size: int = 3000,
    chunk_overlap: int = 200,
) -> list[str]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    return splitter.split_text(text)


def split_by_tokens(
    blocks: list[str],
    chunk_size: int = 256,
    chunk_overlap: int = 50,
) -> list[str]:
    splitter = TokenTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    chunks = []
    for block in blocks:
        chunks.extend(splitter.split_text(block))

    return chunks


async def chunk_document(document_id: int) -> list[str]:
    pages_with_lines = await fetch_pages_with_lines(document_id)

    document_text = build_document_text(pages_with_lines)

    structured_blocks = split_by_structure(document_text)

    chunks = split_by_tokens(structured_blocks)

    return chunks


async def persist_chunking_result(
    document_id: int,
    chunks: list[str],
):
    async with get_kafka_db_session() as session:
        for idx, text in enumerate(chunks):
            session.add(
                DocumentChunk(
                    document_id=document_id,
                    chunk_index=idx,
                    text=text,
                    token_count=count_tokens(text),
                )
            )
        stmt = select(Document).where(Document.id == document_id)
        result = await session.execute(stmt)
        document = result.scalar_one_or_none()
        # ✅ Final document state
        document.chunk_completed = True
        document.status = ProcessingStatus.CHUNKING_DONE
        await session.commit()