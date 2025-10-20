from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import uuid
import random
from ..database import get_db
from ..models import User, Topic, Flashcard, UserProgress
from ..schemas import StudySessionResponse, FlashcardAnswerSubmit, FlashcardAnswerResponse, SessionSummary
from ..auth import get_current_user

router = APIRouter(
	prefix="/study",
	tags=["Study Sessions"]
)

active_sessions = {}

@router.post("/topics/{topic_id}/start", response_model=StudySessionResponse, status_code=status.HTTP_201_CREATED)
async def start_study_session(
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

    flashcards = db.query(Flashcard).filter(
        Flashcard.topic_id == topic_id
    ).all()

    if not flashcards:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No flashcards found for this topic"
        )

    random.shuffle(flashcards)

    session_id = str(uuid.uuid4())
    active_sessions[session_id] = {
        "user_id" : current_user.id,
        "topic_id" : topic.id,
        "flashcards" : [fc.id for fc in flashcards],
        "current_index" : 0,
        "results" : []
    }

    first_flashcard = flashcards[0]

    return StudySessionResponse(
        session_id=session_id,
        topic_id=topic.id,
        topic_name=topic.name,
        total_flashcards=len(flashcards),
        current_index=1,
        flashcard={
            "id" : first_flashcard.id,
            "question" : first_flashcard.question,
            "answer" : first_flashcard.answer
        }
    )

@router.post("/answer", response_model=FlashcardAnswerResponse, status_code=status.HTTP_201_CREATED)
async def submit_answer(
        answer: FlashcardAnswerSubmit,
        current_user: User=Depends(get_current_user),
        db: Session=Depends(get_db)
):
    if answer.session_id not in active_sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    session = active_sessions[answer.session_id]

    if session["user_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not your session"
        )

    flashcard = db.query(Flashcard).filter(
        Flashcard.id == answer.flashcard_id
    ).first()

    if not flashcard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Flashcard not found"
        )

    session["results"].append({
        "flashcard_id" : answer.flashcard_id,
        "is_correct" : answer.is_correct
    })

    session["current_index"] += 1
    has_next = session["current_index"] < len(session["flashcards"])

    total_answered = len(session["results"])
    correct_count = sum(1 for r in session["results"] if r["flashcards"])
    accuracy = (correct_count / total_answered * 100) if total_answered > 0 else 0

    return FlashcardAnswerResponse(
        correct=answer.is_correct,
        correct_answer=flashcard.answer,
        has_next=has_next,
        progress={
            "answered" : total_answered,
            "correct" : correct_count,
            "accuracy" : round(accuracy, 2),
            "remaining" : len(session["flashcards"]) - total_answered
        }
    )

@router.get("/next/{session_id}", response_model=StudySessionResponse)
async def get_next_flashcard(
        session_id: int,
        current_user: User=Depends(get_current_user),
        db: Session=Depends(get_db)
):
    if session_id not in active_sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    session = active_sessions[session_id]

    if session["user_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not your session"
        )

    if session["current_index"] >= len(session["flashcards"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session complete. Get summary"
            )

    topic = db.query(Topic).filter(
        Topic.id == session["topic_id"]
    ).first()

    current_flashcard_id = session["flashcards"][session["current_index"]]
    flashcard = db.query(Flashcard).filter(
        Flashcard.id == current_flashcard_id
    ).first()

    return StudySessionResponse(
        session_id=session_id,
        topic_id=topic.id,
        topic_name=topic.name,
        total_flashcards=len(session["flashcards"]),
        current_index=session["current_index"] + 1,
        flashcard={
            "id" : flashcard.id,
            "question" : flashcard.question,
            "answer" : flashcard.answer
        }
    )

@router.get("/summary/{session_id}", response_model=SessionSummary)
async def get_session_summary(
        session_id: int,
        current_user: User=Depends(get_current_user),
        db: Session=Depends(get_db)
):
    if session_id not in active_sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    session = active_sessions[session_id]

    if session["user_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not your session"
        )

    topic = db.query(Topic).filter(
        Topic.id == session["topic_id"]
    ).first()

    total_reviewed = len(session["results"])
    correct_count = sum(1 for r in session["results"] if r["is_correct"])
    accuracy = (correct_count / total_reviewed * 100) if total_reviewed > 0 else 0

    progress = db.query(UserProgress).filter(
        UserProgress.user_id == current_user.id,
        UserProgress.topic_id == session["topic_id"]
    ).first()

    if not progress:
        progress = UserProgress(
            user_id=current_user.id,
            topic_id=session["topic_id"],
            flashcards_reviewed=0,
            correct_answers=0,
            total_answers=0,
            streak_days=0
        )
        db.add(progress)

    progress.flashcards_reviewed += total_reviewed
    progress.correct_answers += correct_count
    progress.total_answers += total_reviewed

    now = datetime.now(timezone.utc)
    if progress.last_study_date:
        last_date = progress.last_study_date.replace(tzinfo=timezone.utc) if progress.last_study_date.tzinfo is None else progress.last_study_date
        days_diff = (now.date() - last_date.date()).days

        if days_diff == 1:
            progress.streak_days += 1
        elif days_diff > 1:
            progress.streak_days = 1
    else:
        progress.streak_days = 1

    progress.last_study_date = now

    db.commit()
    db.refresh(progress)

    del active_sessions[session_id]

    return SessionSummary(
        session_id=session_id,
        topic_name=topic.name,
        total_reviewed=total_reviewed,
        correct_count=correct_count,
        accuracy=round(accuracy, 2),
        streak_days=progress.streak_days,
    )