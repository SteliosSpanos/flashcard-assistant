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

@router.get("", response_model=OverallProgressResponse)
async def get_overall_progress(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    topics = db.query(Topic).filter(
        Topic.user_id == current_user.id
    ).all()

    all_progress = db.query(UserProgress).filter(
        UserProgress.user_id == current_user.id
    ).all()

    total_flashcards_reviewed = sum(p.flashcards_reviewed for p in all_progress)
    total_correct = sum(p.correct_answers for p in all_progress)
    total_answers = sum(p.total_answers for p in all_progress)
    overall_accuracy = (total_correct / total_answers * 100) if total_answers > 0 else 0
    current_streak = max((p.streak_days for p in all_progress), default=0)

    topics_progress = []
    for topic in topics:
        progress = next((p for p in all_progress if p.topic_id == topic.id), None)

        if progress:
            accuracy = (progress.correct_answers / progress.total_answers * 100) if progress.total_answers > 0 else 0
            topics_progress.append(ProgressResponse(
                topic_id=topic.id,
                topic_name=topic.name,
                flashcards_reviewed=progress.flashcards_reviewed,
                accuracy=round(accuracy, 2),
                streak_days=progress.streak_days,
                last_study_date=progress.last_study_date
            ))
        else:
            topics_progress.append(ProgressResponse(
                topic_id=topic.id,
                topic_name=topic.name,
                flashcards_reviewed=0,
                accuracy=0.0,
                streak_days=0,
                last_study_date=None
            ))

    return OverallProgressResponse(
        total_topics=len(topics),
        total_flashcards_reviewed=total_flashcards_reviewed,
        overall_accuracy=round(overall_accuracy,2),
        current_streak=current_streak,
        longest_streak=current_streak,
        topics=topics_progress
    )

@router.delete("/{topic_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_topic_progress(
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

    progress = db.query(UserProgress).filter(
        UserProgress.user_id == current_user.id,
        UserProgress.topic_id == topic_id
    ).first()

    if progress:
        db.delete(progress)
        db.commit()
