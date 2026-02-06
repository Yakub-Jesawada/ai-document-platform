import asyncio
from workers.embedding_worker.consumer import consume
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


def main():
    asyncio.run(consume())


if __name__ == "__main__":
    main()
