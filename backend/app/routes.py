"""API routes for GLevel backend."""
import hashlib
from datetime import date, timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, desc
from sqlalchemy.orm import Session

from .database import get_db
from .models import Student, Subject, StudentSubject, Topic, StudySession, PerformanceRecord, Milestone


def _reference_date(db: Session, student_id: int) -> date:
    """Return the most recent date with performance data for this student, or today."""
    latest = (
        db.query(func.max(PerformanceRecord.date))
        .filter(PerformanceRecord.student_id == student_id)
        .scalar()
    )
    return latest if latest else date.today()
from .schemas import (
    StudentCreate, StudentLogin, StudentOut, StudentUpdate,
    SubjectOut, SubjectCreate, TopicOut,
    StudySessionCreate, StudySessionOut,
    PerformanceCreate, PerformanceOut,
    MilestoneOut,
    WeeklyOverview, SubjectPerformance, DailyScore,
    StudyTimeBreakdown, DifficultyItem, CriticalTopic,
    MonthlyProgress, InsightItem,
)

router = APIRouter()


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


# ─── Auth ────────────────────────────────────────────────────────────────────

@router.post("/auth/register", response_model=StudentOut)
def register(data: StudentCreate, db: Session = Depends(get_db)):
    existing = db.query(Student).filter(Student.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    student = Student(
        name=data.name,
        email=data.email,
        university=data.university,
        password_hash=hash_password(data.password),
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


@router.post("/auth/login", response_model=StudentOut)
def login(data: StudentLogin, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.email == data.email).first()
    if not student or student.password_hash != hash_password(data.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return student


# ─── Students ────────────────────────────────────────────────────────────────

@router.get("/students/{student_id}", response_model=StudentOut)
def get_student(student_id: int, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


@router.put("/students/{student_id}", response_model=StudentOut)
def update_student(student_id: int, data: StudentUpdate, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    if data.name is not None:
        student.name = data.name
    if data.email is not None:
        student.email = data.email
    if data.university is not None:
        student.university = data.university
    db.commit()
    db.refresh(student)
    return student


# ─── Subjects ────────────────────────────────────────────────────────────────

@router.get("/subjects", response_model=List[SubjectOut])
def list_subjects(db: Session = Depends(get_db)):
    return db.query(Subject).all()


@router.post("/subjects", response_model=SubjectOut)
def create_subject(data: SubjectCreate, db: Session = Depends(get_db)):
    subject = Subject(name=data.name, color_start=data.color_start, color_end=data.color_end)
    db.add(subject)
    db.commit()
    db.refresh(subject)
    return subject


@router.get("/subjects/{subject_id}/topics", response_model=List[TopicOut])
def list_topics(subject_id: int, db: Session = Depends(get_db)):
    return db.query(Topic).filter(Topic.subject_id == subject_id).all()


# ─── Study Sessions ─────────────────────────────────────────────────────────

@router.post("/students/{student_id}/study-sessions", response_model=StudySessionOut)
def create_study_session(student_id: int, data: StudySessionCreate, db: Session = Depends(get_db)):
    session = StudySession(
        student_id=student_id,
        subject_id=data.subject_id,
        date=data.date,
        duration_minutes=data.duration_minutes,
        start_hour=data.start_hour,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.get("/students/{student_id}/study-sessions", response_model=List[StudySessionOut])
def list_study_sessions(student_id: int, days: int = 7, db: Session = Depends(get_db)):
    since = date.today() - timedelta(days=days)
    return (
        db.query(StudySession)
        .filter(StudySession.student_id == student_id, StudySession.date >= since)
        .order_by(StudySession.date.desc())
        .all()
    )


# ─── Performance Records ────────────────────────────────────────────────────

@router.post("/students/{student_id}/performance", response_model=PerformanceOut)
def create_performance(student_id: int, data: PerformanceCreate, db: Session = Depends(get_db)):
    accuracy = data.questions_correct / data.questions_answered if data.questions_answered > 0 else 0.0
    record = PerformanceRecord(
        student_id=student_id,
        subject_id=data.subject_id,
        date=data.date,
        questions_answered=data.questions_answered,
        questions_correct=data.questions_correct,
        accuracy=round(accuracy, 4),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/students/{student_id}/performance", response_model=List[PerformanceOut])
def list_performance(student_id: int, days: int = 30, db: Session = Depends(get_db)):
    since = date.today() - timedelta(days=days)
    return (
        db.query(PerformanceRecord)
        .filter(PerformanceRecord.student_id == student_id, PerformanceRecord.date >= since)
        .order_by(PerformanceRecord.date.desc())
        .all()
    )


# ─── Milestones ──────────────────────────────────────────────────────────────

@router.get("/students/{student_id}/milestones", response_model=List[MilestoneOut])
def list_milestones(student_id: int, db: Session = Depends(get_db)):
    return (
        db.query(Milestone)
        .filter(Milestone.student_id == student_id)
        .order_by(Milestone.achieved_at.desc())
        .all()
    )


# ─── Dashboard Aggregates ───────────────────────────────────────────────────

@router.get("/students/{student_id}/dashboard/overview", response_model=WeeklyOverview)
def dashboard_overview(student_id: int, db: Session = Depends(get_db)):
    today = _reference_date(db, student_id)
    week_start = today - timedelta(days=6)
    prev_week_start = week_start - timedelta(days=7)
    prev_week_end = week_start - timedelta(days=1)

    # This week
    this_week = (
        db.query(PerformanceRecord)
        .filter(
            PerformanceRecord.student_id == student_id,
            PerformanceRecord.date >= week_start,
            PerformanceRecord.date <= today,
        )
        .all()
    )
    tw_questions = sum(r.questions_answered for r in this_week)
    tw_correct = sum(r.questions_correct for r in this_week)
    tw_accuracy = round((tw_correct / tw_questions * 100) if tw_questions > 0 else 0, 1)

    # Previous week
    prev_week = (
        db.query(PerformanceRecord)
        .filter(
            PerformanceRecord.student_id == student_id,
            PerformanceRecord.date >= prev_week_start,
            PerformanceRecord.date <= prev_week_end,
        )
        .all()
    )
    pw_questions = sum(r.questions_answered for r in prev_week)
    pw_correct = sum(r.questions_correct for r in prev_week)
    pw_accuracy = round((pw_correct / pw_questions * 100) if pw_questions > 0 else 0, 1)

    # Study hours this week
    study_sessions = (
        db.query(StudySession)
        .filter(
            StudySession.student_id == student_id,
            StudySession.date >= week_start,
            StudySession.date <= today,
        )
        .all()
    )
    total_minutes = sum(s.duration_minutes for s in study_sessions)
    study_hours = round(total_minutes / 60, 1)

    # Streak: count consecutive days with activity
    streak = 0
    check_date = today
    while True:
        has_activity = (
            db.query(PerformanceRecord)
            .filter(
                PerformanceRecord.student_id == student_id,
                PerformanceRecord.date == check_date,
            )
            .first()
        )
        if has_activity:
            streak += 1
            check_date -= timedelta(days=1)
        else:
            break

    return WeeklyOverview(
        accuracy_rate=tw_accuracy,
        accuracy_change=round(tw_accuracy - pw_accuracy, 1),
        total_questions=tw_questions,
        questions_change=tw_questions - pw_questions,
        ranking_position=3,
        ranking_change=2,
        study_hours=study_hours,
        study_goal=28.0,
        streak_days=streak,
        streak_record=max(streak, 18),
    )


@router.get("/students/{student_id}/dashboard/daily-scores", response_model=List[DailyScore])
def dashboard_daily_scores(student_id: int, days: int = 7, db: Session = Depends(get_db)):
    today = _reference_date(db, student_id)
    day_names = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sab", "Dom"]
    results = []
    for i in range(days - 1, -1, -1):
        d = today - timedelta(days=i)
        records = (
            db.query(PerformanceRecord)
            .filter(PerformanceRecord.student_id == student_id, PerformanceRecord.date == d)
            .all()
        )
        total_q = sum(r.questions_answered for r in records)
        total_c = sum(r.questions_correct for r in records)
        score = round((total_c / total_q * 100) if total_q > 0 else 0, 1)
        day_label = day_names[d.weekday()]
        results.append(DailyScore(day=day_label, score=score))
    return results


@router.get("/students/{student_id}/dashboard/subject-performance", response_model=List[SubjectPerformance])
def dashboard_subject_performance(student_id: int, days: int = 30, db: Session = Depends(get_db)):
    today = _reference_date(db, student_id)
    since = today - timedelta(days=days)
    enrolled = (
        db.query(StudentSubject)
        .filter(StudentSubject.student_id == student_id)
        .all()
    )
    results = []
    for enrollment in enrolled:
        subj = db.query(Subject).filter(Subject.id == enrollment.subject_id).first()
        records = (
            db.query(PerformanceRecord)
            .filter(
                PerformanceRecord.student_id == student_id,
                PerformanceRecord.subject_id == subj.id,
                PerformanceRecord.date >= since,
            )
            .all()
        )
        total_q = sum(r.questions_answered for r in records)
        total_c = sum(r.questions_correct for r in records)
        acc = round((total_c / total_q * 100) if total_q > 0 else 0, 1)
        results.append(SubjectPerformance(
            subject_name=subj.name,
            accuracy=acc,
            color_start=subj.color_start,
            color_end=subj.color_end,
        ))
    results.sort(key=lambda x: x.accuracy, reverse=True)
    return results


@router.get("/students/{student_id}/dashboard/study-time", response_model=List[StudyTimeBreakdown])
def dashboard_study_time(student_id: int, days: int = 7, db: Session = Depends(get_db)):
    today = _reference_date(db, student_id)
    since = today - timedelta(days=days)
    enrolled = (
        db.query(StudentSubject)
        .filter(StudentSubject.student_id == student_id)
        .all()
    )
    results = []
    total_all = 0
    for enrollment in enrolled:
        subj = db.query(Subject).filter(Subject.id == enrollment.subject_id).first()
        sessions = (
            db.query(StudySession)
            .filter(
                StudySession.student_id == student_id,
                StudySession.subject_id == subj.id,
                StudySession.date >= since,
            )
            .all()
        )
        total_mins = sum(s.duration_minutes for s in sessions)
        total_all += total_mins
        results.append({
            "subject_name": subj.name,
            "minutes": total_mins,
            "color_start": subj.color_start,
            "color_end": subj.color_end,
        })

    output = []
    for r in results:
        hrs = round(r["minutes"] / 60, 1)
        pct = round((r["minutes"] / total_all * 100) if total_all > 0 else 0, 1)
        output.append(StudyTimeBreakdown(
            subject_name=r["subject_name"],
            hours=hrs,
            minutes=r["minutes"],
            color_start=r["color_start"],
            color_end=r["color_end"],
            percentage=pct,
        ))
    output.sort(key=lambda x: x.minutes, reverse=True)
    return output


@router.get("/students/{student_id}/dashboard/difficulty-map", response_model=List[DifficultyItem])
def dashboard_difficulty_map(student_id: int, db: Session = Depends(get_db)):
    today = _reference_date(db, student_id)
    since = today - timedelta(days=60)
    enrolled = (
        db.query(StudentSubject)
        .filter(StudentSubject.student_id == student_id)
        .all()
    )
    results = []
    for enrollment in enrolled:
        subj = db.query(Subject).filter(Subject.id == enrollment.subject_id).first()
        records = (
            db.query(PerformanceRecord)
            .filter(
                PerformanceRecord.student_id == student_id,
                PerformanceRecord.subject_id == subj.id,
                PerformanceRecord.date >= since,
            )
            .all()
        )
        total_q = sum(r.questions_answered for r in records)
        total_c = sum(r.questions_correct for r in records)
        acc = round((total_c / total_q * 100) if total_q > 0 else 0, 1)
        results.append(DifficultyItem(
            subject_name=subj.name,
            accuracy=acc,
            color_start=subj.color_start,
            color_end=subj.color_end,
        ))
    results.sort(key=lambda x: x.accuracy, reverse=True)
    return results


@router.get("/students/{student_id}/dashboard/critical-topics", response_model=List[CriticalTopic])
def dashboard_critical_topics(student_id: int, db: Session = Depends(get_db)):
    topics = db.query(Topic).order_by(Topic.difficulty_score.desc()).limit(10).all()
    results = []
    for topic in topics:
        subj = db.query(Subject).filter(Subject.id == topic.subject_id).first()
        acc = round((1.0 - topic.difficulty_score) * 100, 1)
        severity = "critical" if acc < 40 else "warning" if acc < 60 else "moderate"
        results.append(CriticalTopic(
            topic_name=topic.name,
            subject_name=subj.name,
            accuracy=acc,
            total_questions=15,
            severity=severity,
        ))
    results.sort(key=lambda x: x.accuracy)
    return results


@router.get("/students/{student_id}/dashboard/monthly-progress", response_model=List[MonthlyProgress])
def dashboard_monthly_progress(student_id: int, db: Session = Depends(get_db)):
    month_labels = ["Set", "Out", "Nov", "Dez", "Jan", "Fev", "Mar", "Abr"]
    month_dates = [
        (date(2025, 9, 1), date(2025, 9, 30)),
        (date(2025, 10, 1), date(2025, 10, 31)),
        (date(2025, 11, 1), date(2025, 11, 30)),
        (date(2025, 12, 1), date(2025, 12, 31)),
        (date(2026, 1, 1), date(2026, 1, 31)),
        (date(2026, 2, 1), date(2026, 2, 28)),
        (date(2026, 3, 1), date(2026, 3, 31)),
        (date(2026, 4, 1), _reference_date(db, student_id)),
    ]
    results = []
    prev_acc = 0
    for i, (label, (start, end)) in enumerate(zip(month_labels, month_dates)):
        records = (
            db.query(PerformanceRecord)
            .filter(
                PerformanceRecord.student_id == student_id,
                PerformanceRecord.date >= start,
                PerformanceRecord.date <= end,
            )
            .all()
        )
        total_q = sum(r.questions_answered for r in records)
        total_c = sum(r.questions_correct for r in records)
        acc = round((total_c / total_q * 100) if total_q > 0 else 0, 1)
        trend = "up" if acc > prev_acc else "down" if acc < prev_acc else "stable"
        results.append(MonthlyProgress(month=label, accuracy=acc, trend=trend))
        prev_acc = acc
    return results


@router.get("/students/{student_id}/dashboard/insights", response_model=List[InsightItem])
def dashboard_insights(student_id: int, db: Session = Depends(get_db)):
    today = _reference_date(db, student_id)
    since = today - timedelta(days=30)

    # Find best subject
    enrolled = (
        db.query(StudentSubject)
        .filter(StudentSubject.student_id == student_id)
        .all()
    )
    best_subj = None
    best_acc = -1
    worst_subj = None
    worst_acc = 101
    for enrollment in enrolled:
        subj = db.query(Subject).filter(Subject.id == enrollment.subject_id).first()
        records = (
            db.query(PerformanceRecord)
            .filter(
                PerformanceRecord.student_id == student_id,
                PerformanceRecord.subject_id == subj.id,
                PerformanceRecord.date >= since,
            )
            .all()
        )
        total_q = sum(r.questions_answered for r in records)
        total_c = sum(r.questions_correct for r in records)
        acc = (total_c / total_q * 100) if total_q > 0 else 0
        if acc > best_acc:
            best_acc = acc
            best_subj = subj.name
        if acc < worst_acc:
            worst_acc = acc
            worst_subj = subj.name

    if not enrolled or best_subj is None:
        return [
            InsightItem(
                type="trend",
                title="Bem-vindo!",
                message="Comece a responder questoes para receber insights personalizados sobre seu desempenho.",
                color="#00F5FF",
            ),
        ]

    return [
        InsightItem(
            type="strength",
            title="Ponto Forte",
            message=f"Sua performance em {best_subj} esta excelente ({best_acc:.0f}%). Continue praticando para manter o 1o lugar na materia.",
            color="#B5FF2D",
        ),
        InsightItem(
            type="warning",
            title="Atencao",
            message=f"{worst_subj} esta abaixo da sua media ({worst_acc:.0f}%). Recomendamos 2h extras por semana nesta materia.",
            color="#FF6B6B",
        ),
        InsightItem(
            type="trend",
            title="Tendencia",
            message="Seu progresso semanal esta acima da media da turma em 15%. Voce esta no caminho certo!",
            color="#00F5FF",
        ),
    ]


@router.get("/students/{student_id}/dashboard/peak-hours")
def dashboard_peak_hours(student_id: int, days: int = 30, db: Session = Depends(get_db)):
    today = _reference_date(db, student_id)
    since = today - timedelta(days=days)
    sessions = (
        db.query(StudySession)
        .filter(
            StudySession.student_id == student_id,
            StudySession.date >= since,
        )
        .all()
    )
    hour_totals: dict[int, int] = {}
    for s in sessions:
        hour_totals[s.start_hour] = hour_totals.get(s.start_hour, 0) + s.duration_minutes

    results = [{"hour": h, "minutes": m} for h, m in sorted(hour_totals.items())]
    return results
