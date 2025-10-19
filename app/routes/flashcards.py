from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import json
import openai
from ..database import get_db
from ..models import User, Topic, Flashcard, UserProgress
from ..schemas import FlashcardResponse, FlashcardCreate, FlashcardUpdate, AIFlashcardRequest
from ..auth import get_current_user, decode_access_token
from ..settings import settings
from datetime import datetime, timezone

router = APIRouter(
    prefix="/topics/{topic_id}/flashcards",
    tags=["Flashcards"]
)
openai.api_key = settings.openai_api_key

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

    prompt = (
        f"Generate {request.count} flashcards about {request.topic_name} "
        f"with {request.difficulty} difficulty. "
        "Return as a JSON array, where each item has 'question' and 'answer' fields."
    )

    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role" : "system", "content" : "You are a helpful study assistant that creates educational flashcards"},
                {"role" : "user", "content" : prompt}
            ],
            response_format={"type" : "json_object"},
            temperature=0.7
        )

        content = response.choices[0].message.content.strip()
        try:
            parsed = json.loads(content)
            flashcards_data = parsed.get("flashcards", parsed)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Invalid JSON returned from OpenAI API"
            )

        flashcards = []
        for fc in flashcards_data[:request.count]:
            db_flashcard = Flashcard(
                topic_id=topic.id,
                question=fc.get("question", "No question"),
                answer=fc.get("answer", "No answer"),
                difficulty=request.difficulty
            )
            db.add(db_flashcard)
            flashcards.append(db_flashcard)

        db.commit()
        return flashcards

    except openai.APIError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )