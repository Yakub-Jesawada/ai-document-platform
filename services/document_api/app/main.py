from contextlib import asynccontextmanager
from fastapi import FastAPI
from database import engine, settings
from routes import auth, user, document, collection
from shared.kafka.producer import start_producer, stop_producer
from core.embedding import embedding_provider


@asynccontextmanager
async def lifespan(app: FastAPI):
    await start_producer()
    await embedding_provider.start()
    yield
    await stop_producer()
    await embedding_provider.close()


app = FastAPI(
    title="API services for document processing platform",
    version="0.1.0",
    debug=settings.DEBUG,
    lifespan=lifespan,
)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# Include routers
app.include_router(auth.router)
app.include_router(user.router)
app.include_router(document.router)
app.include_router(collection.router)