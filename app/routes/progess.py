from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User, Topic, UserProgress
from ..schemas import ProgressResponse, OverallProgressResponse
from ..auth import get_current_user

router = APIRouter(
    prefix="/progress",
    tags=["Progress"]
)

@router.get("/{topic_id}", response_model=ProgressResponse)
async def get_topic_progress(
        topic_id: int,
        current_user: User = Depends(get_current_user),
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

    progress = db.query(UserProgress).filter(
        UserProgress.user_id == current_user.id,
        UserProgress.topic_id == topic_id
    ).first()

    if not progress:
        return ProgressResponse(
            topic_id=topic_id,
            topic_name=topic.name,
            flashcards_reviewed=0,
            accuracy=0.0,
            streak_days=0,
            last_study_date=None
        )

    accuracy = (progress.correct_answers / progress.total_answers * 100) if progress.total_answers > 0 else 0

    return ProgressResponse(
        topic_id=topic_id,
        topic_name=topic.name,
        flashcards_reviewed=progress.flashcards_reviewed,
        accuracy=round(accuracy, 2),
        streak_days=progress.streak_days,
        last_study_date=progress.last_study_date
    )

