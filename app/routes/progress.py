from fastapi import APIrouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from datetime import datetime, timedelta, timezone
from ..database import get_db
from ..models import User, Topic, Flashcard, UserProgress
from ..schemas import
from ..auth import get_current_user

router = APIRouter(
	prefix="/progress",
	tags=["Progress"]
)

def calculate_streak(last_study_date: datetime, current_streak: int) -> int:
	if not last_study_date:
		return 1

	now = datetime.now(timezone.utc)
	if last_study_date.tzinfo is None:
		last_study_date = last_study_date.replace(tzinfo=timezone.utc)

	days_diff = (now.date() - last_study_date.date()).days()

	if days_diff == 0:
		return current_streak
	elif days_diff == 1:
		return current_streak + 1
	else:
		return 1


@router.post("/study-session")
async def record_study_session(
	session_data: StudySessionBatchCreate,
	current_user: User=Depends(get_current_user),
	db: Session=Depends(get_db)
):
	topic = db.query(Topic).filter(
		Topic.id == session_data.topic_id,
		Topic.user_id == current_user.id
	).first()

	if not topic:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail="Topic not found"
		)

	flashcard_ids = [result.flashcard_id for result in session_data.results]
	flashcards = db.query(Flashcard).filter(
		Flashcard.id.in_(flashcard_ids),
		Flashcard.topic_id == session_data.topic_id
	).all()

	if len(flashcards) != len(flashcard_ids):
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail="Some flashcards do not belong to this topic"
		)

	progress = db.query(UserProgress).filter(
		UserProgress.user_id == current_user.id,
		UserProgress.topic_id == session_data.topic_id
	).first()

	if not progress:
		progress = UserProgress(
			user_id=current_user.id,
			topic_id=session_data.topic_id,
			flashcards_reviewed=0,
			correct_answers=0,
			total_answers=0,
			streak_days=0
	)
	db.add(progress)

	correct_count = sum(1 for result in session_data.results if result.is_correct)
	total_count = len(session_data.results)

	progress.flashcards_reviewed += total_count
	progress.correct_answers += correct_count
	progress.total_answers += total_count
	progress.streak_days = calculate_streak(progress.last_study_date, progress.streak_days)
	progress.last_study_date = datetime.now(timezone.utc)

	db.commit()
	db.refresh(progress)

	accuracy = (progress.correct_answers / progress.total_answers * 100) if progress.total_answers > 0 else 0

	return {
		"message" : "Study session recorded successfully",
		"topic_id" : progress.topic_id,
		"flashcards_reviewed" : total_count,
		"correct_answers" : correct_count,
		"accuracy" : round(accuracy, 2),
		"streak_days" : progress.streak_days
	}


