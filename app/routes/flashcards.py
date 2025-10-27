from fastapi import APIRouter, Depends, HTTPException, status
from openai.types.chat import ChatCompletion
from sqlalchemy.orm import Session
from typing import List
import json
from openai import OpenAI
from ..database import get_db
from ..models import User, Topic, Flashcard, UserProgress
from ..schemas import FlashcardResponse, FlashcardCreate, FlashcardUpdate, AIFlashcardRequest
from ..auth import get_current_user
from ..settings import settings
from datetime import datetime, timezone

router = APIRouter(
    prefix="/topics/{topic_id}/flashcards",
    tags=["Flashcards"]
)

@router.post("", response_model=FlashcardResponse, status_code=status.HTTP_201_CREATED)
async def create_flashcard(
        topic_id: int,
        flashcard: FlashcardCreate,
        current_user: User=Depends(get_current_user),
        db: Session = Depends(get_db)
):
    topic = db.query(Topic).filter(
        Topic.id == topic_id,
        Topic.user_id == current_user.id
    ).first()

    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Topic not found"
        )

    db_flashcard = Flashcard(
        topic_id=topic_id,
        question=flashcard.question,
        answer=flashcard.answer,
        difficulty=flashcard.difficulty
    )
    db.add(db_flashcard)
    db.commit()
    db.refresh(db_flashcard)

    return db_flashcard

@router.get("", response_model=List[FlashcardResponse])
async def get_flashcards(
        topic_id: int,
        current_user: User=Depends(get_current_user),
        db: Session = Depends(get_db)
):
    topic = db.query(Topic).filter(
        Topic.id == topic_id,
        Topic.user_id == current_user.id
    ).first()

    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Topic not found"
        )

    return topic.flashcards

@router.get("/{flashcard_id}", response_model=FlashcardResponse)
async def get_flashcard(
        topic_id: int,
        flashcard_id: int,
        current_user: User=Depends(get_current_user),
        db: Session = Depends(get_db)
):
    topic = db.query(Topic).filter(
        Topic.id == topic_id,
        Topic.user_id == current_user.id
    ).first()

    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Topic not found"
        )

    flashcard = db.query(Flashcard).filter(
        Flashcard.id == flashcard_id,
        Flashcard.topic_id == topic_id
    ).first()

    if not flashcard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Flashcard not found"
        )

    return flashcard

@router.patch("/{flashcard_id}", response_model=FlashcardResponse)
async def update_flashcard(
        topic_id: int,
        flashcard_id: int,
        flashcard_update: FlashcardUpdate,
        current_user: User=Depends(get_current_user),
        db: Session = Depends(get_db)
):
    topic = db.query(Topic).filter(
        Topic.id == topic_id,
        Topic.user_id == current_user.id
    ).first()

    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Topic not found"
        )

    flashcard = db.query(Flashcard).filter(
        Flashcard.id == flashcard_id,
        Flashcard.topic_id == topic_id
    ).first()

    if not flashcard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Flashcard not found"
        )

    if flashcard_update.question is not None:
        flashcard.question = flashcard_update.question
    if flashcard_update.answer is not None:
        flashcard.answer = flashcard_update.answer
    if flashcard_update.difficulty is not None:
        flashcard.difficulty = flashcard_update.difficulty

    db.commit()
    db.refresh(flashcard)

    return flashcard

@router.delete("/{flashcard_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_flashcard(
        topic_id: int,
        flashcard_id: int,
        current_user: User=Depends(get_current_user),
        db: Session = Depends(get_db)
):
    topic = db.query(Topic).filter(
        Topic.id == topic_id,
        Topic.user_id == current_user.id
    ).first()

    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Topic not found"
        )

    flashcard = db.query(Flashcard).filter(
        Flashcard.id == flashcard_id,
        Flashcard.topic_id == topic_id
    ).first()

    if not flashcard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Flashcard not found"
        )

    db.delete(flashcard)
    db.commit()

@router.post("/generate", response_model=List[FlashcardResponse], status_code=status.HTTP_201_CREATED)
async def generate_flashcards(
        topic_id: int,
        request: AIFlashcardRequest,
        current_user: User=Depends(get_current_user),
        db: Session=Depends(get_db)
):
    topic = db.query(Topic).filter(
        Topic.id == topic_id,
        Topic.user_id == current_user.id
    ).first()

    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Topic not found"
        )

    if not settings.openai_api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI generation not configured. Please set OPENAI_API_KEY"
        )

    try:
        client = OpenAI(api_key=settings.openai_api_key)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize OpenAI client: {str(e)}"
        )

    prompt = (
        f"Generate {request.count} flashcards about {topic.name} (the answer cant be more than 5 words) "
        f"with {request.difficulty} difficulty. "
        "Return ONLY valid JSON with this structure: "
        '{"flashcards" : [{"question" : "...", "answer" : "..."}, ...]}'
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role" : "system",
                    "content" : "You are a helpful study assistant that creates educational flashcards. Always return valid JSON only."
                },
                {
                    "role" : "user",
                    "content" : prompt
                }
            ],
            response_format={"type" : "json_object"},
            temperature=0.7
        )

        content = response.choices[0].message.content.strip()
        try:
            parsed = json.loads(content)
            flashcards_data = parsed.get("flashcards", [])
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Invalid JSON returned from OpenAI API: {str(e)}"
            )

        if not flashcards_data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="OpenAI returned empty flashcards list"
            )

        created_flashcards = []
        for fc in flashcards_data[:request.count]:
            db_flashcard = Flashcard(
                topic_id=topic.id,
                question=fc.get("question", "No question"),
                answer=fc.get("answer", "No answer"),
                difficulty=request.difficulty
            )
            db.add(db_flashcard)
            created_flashcards.append(db_flashcard)

        db.commit()

        for flashcard in created_flashcards:
            db.refresh(flashcard)
        return created_flashcards


    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
