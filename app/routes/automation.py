from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from ..models import User, Topic, Flashcard, UserProgress
from ..schemas import DailyFlashcardResponse
from ..auth import get_current_user
import random

router = APIRouter(
        prefix="/automation",
        tags=["Automation"]
)

@router.get("/daily-flashcard", response_model=DailyFlashcardResponse)
async def get_daily_flashcard(
        current_user: User=Depends(get_current_user),
        db: Session=Depends(get_db)
):
    all_progress = db.query(UserProgress).filter(
            UserProgress.user_id == current_user.id
    ).all()

    user_topics = db.query(Topic).filter(
            Topic.user_id == current_user.id
    ).all()

    if not user_topics:
        raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No topics found. Create a topic first"
        )

    lowest_accuracy_topic = None
    lowest_accuracy = float('inf')


    for topic in user_topics:
        flashcard_count = db.query(func.count(Flashcard.id)).filter(
                Flashcard.topic_id == topic.id
        )

        if flashcard_count == 0:
            continue

        progress = next((p for p in all_progress if p.topic_id == topic.id), None)

        if progress and progress.total_answers > 0:
            accuracy = (progress.correct_answers / progress.total_answers) * 100
        else:
            accuracy = 0.0

        if accuracy < lowest_accuracy:
            lowest_accuracy = accuracy
            lowest_accuracy_topic = topic


    if not lowest_accuracy_topic:
        raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No topics with flashcard found"
        )

    fashcards = db.query(Flashcard).filter(
            Flashcard.topic_id == topic.id,
    ).all()

    if not flashcards:
        raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No flashcards found"
        )

    selected_flashcard = random.choice(flashcards)

    topic_progress = db.query(UserProgress).filter(
            UserProgress.user_id == current_user.id,
            UserProgress.topic_id == lowest_accuracy_topic.id
    ).first()

    if topic_progress:
        progress_data = {
                "accuracy" : round((topic_progress.correct_answers / topic_progress.total_answers) * 100, 2) if topic_progress.total_answers > 0 else 0.0,
                "streak_days" : topic_progress.streak_days,
                "flashcards_reviewed" : topic_progress.flashcards_reviewed
        }
    else:
        progress_data = {
                "accuracy" : 0.0,
                "streak_days" : 0,
                "flashcards_reviewed" : 0
        }

    return DailyFlashcardResponse(
            flashcard_id=selected_flashcard.id,
            topic_id=lowest_accuracy_topic.id,
            topic_name=lowest_accuracy_topic.name,
            question=selected_flashcard.question,
            answer=selected_flashcard.answer,
            difficulty=selected_flashcard.difficulty,
            user_progress=progress.data
    )

