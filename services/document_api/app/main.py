from fastapi import FastAPI
from database import engine, settings
from routes import auth, user, document, collection

app = FastAPI(
    title="API services for document processing platform",
    version="0.1.0",
    debug=settings.DEBUG
)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Include routers
app.include_router(auth.router)
app.include_router(user.router)
app.include_router(document.router)
app.include_router(collection.router)