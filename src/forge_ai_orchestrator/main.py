from fastapi import FastAPI

app = FastAPI(
    title="Forge API",
    description="AI-powered software engineering automation",
    version="0.1.0",
)


@app.get("/")
def root():
    return {
        "name": "Forge",
        "status": "running",
        "message": "Forge backend is ready",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}