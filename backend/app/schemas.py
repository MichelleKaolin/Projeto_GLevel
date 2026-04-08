from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


# --- Student ---
class StudentCreate(BaseModel):
    name: str
    email: str
    university: str
    password: str


class StudentLogin(BaseModel):
    email: str
    password: str


class StudentOut(BaseModel):
    id: int
    name: str
    email: str
    university: str
    created_at: datetime

    class Config:
        from_attributes = True


class StudentUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    university: Optional[str] = None


# --- Subject ---
class SubjectOut(BaseModel):
    id: int
    name: str
    color_start: str
    color_end: str

    class Config:
        from_attributes = True


class SubjectCreate(BaseModel):
    name: str
    color_start: str = "#007AFF"
    color_end: str = "#6000DD"


# --- Topic ---
class TopicOut(BaseModel):
    id: int
    name: str
    subject_id: int
    difficulty_score: float

    class Config:
        from_attributes = True


# --- Study Session ---
class StudySessionCreate(BaseModel):
    subject_id: int
    date: date
    duration_minutes: int
    start_hour: int = 0


class StudySessionOut(BaseModel):
    id: int
    student_id: int
    subject_id: int
    date: date
    duration_minutes: int
    start_hour: int

    class Config:
        from_attributes = True


# --- Performance ---
class PerformanceCreate(BaseModel):
    subject_id: int
    date: date
    questions_answered: int
    questions_correct: int


class PerformanceOut(BaseModel):
    id: int
    student_id: int
    subject_id: int
    date: date
    questions_answered: int
    questions_correct: int
    accuracy: float

    class Config:
        from_attributes = True


# --- Milestone ---
class MilestoneOut(BaseModel):
    id: int
    student_id: int
    title: str
    description: Optional[str]
    icon: str
    achieved_at: date

    class Config:
        from_attributes = True


# --- Dashboard aggregates ---
class WeeklyOverview(BaseModel):
    accuracy_rate: float
    accuracy_change: float
    total_questions: int
    questions_change: int
    ranking_position: int
    ranking_change: int
    study_hours: float
    study_goal: float
    streak_days: int
    streak_record: int


class SubjectPerformance(BaseModel):
    subject_name: str
    accuracy: float
    color_start: str
    color_end: str


class DailyScore(BaseModel):
    day: str
    score: float


class StudyTimeBreakdown(BaseModel):
    subject_name: str
    hours: float
    minutes: int
    color_start: str
    color_end: str
    percentage: float


class DifficultyItem(BaseModel):
    subject_name: str
    accuracy: float
    color_start: str
    color_end: str


class CriticalTopic(BaseModel):
    topic_name: str
    subject_name: str
    accuracy: float
    total_questions: int
    severity: str


class MonthlyProgress(BaseModel):
    month: str
    accuracy: float
    trend: str


class InsightItem(BaseModel):
    type: str
    title: str
    message: str
    color: str
