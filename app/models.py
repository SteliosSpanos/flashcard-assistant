from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Float, func
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    topics = relationship("Topic", back_populates="owner", cascade="all, delete-orphan")
    progress = relationship("UserProgress", back_populates="user", cascade="all, delete-orphan")

class Topic(Base):
    __tablename__ = "topics"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    description = Column(Text)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    owner = relationship("User", back_populates="topics")
    flashcards = relationship("Flashcard", back_populates="topic", cascade="all, delete-orphan")
    progress = relationship("UserProgress", back_populates="topic", cascade="all, delete-orphan")

class Flashcard(Base):
    __tablename__ = "flashcards"

    id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    difficulty = Column(String, default="medium")
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    topic = relationship("Topic", back_populates="flashcards")

class UserProgress(Base):
    __tablename__ = "user_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False)
    flashcards_reviewed = Column(Integer, default=0)
    correct_answers = Column(Integer, default=0)
    total_answers = Column(Integer, default=0)
    last_study_date = Column(DateTime)
    streak_days = Column(Integer, default=0)

    user = relationship("User", back_populates="progress")
    topic = relationship("Topic", back_populates="progress")
