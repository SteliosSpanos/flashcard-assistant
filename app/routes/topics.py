from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import User, Topic
from ..schemas import TopicCreate, TopicResponse, TopicUpdate
from ..auth import get_current_user

router = APIRouter(
    prefix="/topics",
    tags=["Topics"]
)

@router.post("", response_model=TopicResponse, status_code=status.HTTP_201_CREATED)
async def create_topic(
        topic: TopicCreate,
        current_user: User=Depends(get_current_user),
        db: Session=Depends(get_db)
):
    db_topic = Topic(
        name=topic.name,
        description=topic.description,
        user_id=current_user.id
    )
    db.add(db_topic)
    db.commit()
    db.refresh(db_topic)

    return {
        **db_topic.__dict__,
        "flashcard_count" : 0,
    }

@router.get("", response_model=List[TopicResponse])
async def get_topics(
        current_user: User=Depends(get_current_user),
        db: Session=Depends(get_db)
):
    topics = db.query(Topic).filter(Topic.user_id == current_user.id).all()

    return [
        {
            **topic.__dict__,
            "flashcard_count" : len(topic.flashcards) if topic.flashcards else 0
        }
        for topic in topics
    ]

@router.get("/{topic_id}", response_model=TopicResponse)
async def get_topic(
        topic_id: int,
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

    return {
        **topic.__dict__,
        "flashcard_count" : len(topic.flashcards) if topic.flashcards else 0
    }

@router.patch("/{topic_id}", response_model=TopicResponse)
async def update_topic(
        topic_id: int,
        topic_update: TopicUpdate,
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

    if topic_update.name is not None:
        topic.name = topic_update.name
    if topic_update.description is not None:
        topic.description = topic_update.description

    db.commit()
    db.refresh(topic)

    return {
        **topic.__dict__,
        "flashcard_count" : len(topic.flashcards) if topic.flashcards else 0
    }

@router.delete("/{topic_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_topic(
        topic_id: int,
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

    db.delete(topic)
    db.commit()