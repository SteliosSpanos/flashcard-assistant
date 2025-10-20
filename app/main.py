from fastapi import FastAPI
from .database import engine, Base
from . import models
from .routes import authentication, topics, flashcards

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Study Assistant API",
    version="1.0.0",
    description="AI-powered flashcard platform with automation"
)

app.include_router(authentication.router)

app.include_router(topics.router)

app.include_router(flashcards.router)

@app.get("/")
async def root():
    return {
        "message" : "Study Assistant API",
        "version" : "1.0.0",
        "docs" : "/docs"
    }
