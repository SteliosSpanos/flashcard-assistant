from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TopicCreate(BaseModel):
    name: str
    description: Optional[str]=None

class TopicUpdate(BaseModel):
    name: Optional[str]=None
    description: Optional[str]=None

class TopicResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    created_at: datetime
    flashcard_count: int=0

    class Config:
        from_attributes = True

class FlashcardCreate(BaseModel):
    question: str
    answer: str
    difficulty: Optional[str]="medium"

class FlashcardUpdate(BaseModel):
    question: Optional[str]=None
    answer: Optional[str]=None
    difficulty: Optional[str]=None

class FlashcardResponse(BaseModel):
    id: int
    question: str
    answer: str
    difficulty: str
    created_at: datetime

    class Config:
        from_attributes = True

class AIFlashcardRequest(BaseModel):
    topic_name: str
    count: int=5
    difficulty: Optional[str]="medium"

class ProgressResponse(BaseModel):
    topic_id: int
    topic_name: str
    flashcards_reviewed: int
    accuracy: float
    streak_days: int
    last_study_date: Optional[datetime]

    class Config:
        from_attributes = True