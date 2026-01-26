# workers/document_worker/main.py
import asyncio
from workers.document_worker.consumer import consume


def main():
    asyncio.run(consume())


if __name__ == "__main__":
    main()
