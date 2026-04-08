"""Seed the database with sample data for demonstration."""
import hashlib
from datetime import date, timedelta, datetime
import random

from sqlalchemy.orm import Session
from .models import Student, Subject, StudentSubject, Topic, StudySession, PerformanceRecord, Milestone


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def seed_database(db: Session) -> None:
    if db.query(Student).first():
        return

    # Create demo student
    student = Student(
        name="Alex Estudante",
        email="alex@universidade.edu.br",
        university="Universidade Federal do Brasil",
        password_hash=hash_password("demo1234"),
    )
    db.add(student)
    db.flush()

    # Create subjects with colors matching the frontend
    subjects_data = [
        ("Fisica", "#00C851", "#007AFF"),
        ("Algoritmos", "#007AFF", "#6000DD"),
        ("Banco de Dados", "#FFD700", "#FF6B00"),
        ("Calculo I", "#FF6B00", "#FF2D55"),
        ("Quimica", "#FF2D55", "#C0006B"),
        ("Algebra Linear", "#6000DD", "#007AFF"),
        ("Redes", "#00C851", "#FFD700"),
        ("Estatistica", "#FF6B00", "#FFD700"),
    ]
    subjects = []
    for name, c1, c2 in subjects_data:
        s = Subject(name=name, color_start=c1, color_end=c2)
        db.add(s)
        db.flush()
        subjects.append(s)
        db.add(StudentSubject(student_id=student.id, subject_id=s.id))

    # Create topics with difficulty scores
    topics_data = [
        ("Mecanica Classica", subjects[0].id, 0.15),
        ("Termodinamica", subjects[0].id, 0.25),
        ("Eletromagnetismo", subjects[0].id, 0.30),
        ("Ordenacao e Busca", subjects[1].id, 0.20),
        ("Grafos", subjects[1].id, 0.35),
        ("Programacao Dinamica", subjects[1].id, 0.45),
        ("SQL Avancado", subjects[2].id, 0.40),
        ("Normalizacao", subjects[2].id, 0.30),
        ("Modelagem ER", subjects[2].id, 0.25),
        ("Limites", subjects[3].id, 0.35),
        ("Derivadas", subjects[3].id, 0.40),
        ("Integrais por Partes", subjects[3].id, 0.65),
        ("Ligacoes Ionicas", subjects[4].id, 0.80),
        ("Estequiometria", subjects[4].id, 0.60),
        ("Matrizes", subjects[5].id, 0.50),
        ("Espacos Vetoriais", subjects[5].id, 0.55),
        ("Protocolos TCP/IP", subjects[6].id, 0.25),
        ("Roteamento", subjects[6].id, 0.35),
        ("Probabilidade", subjects[7].id, 0.40),
        ("Distribuicoes", subjects[7].id, 0.45),
    ]
    for tname, sid, diff in topics_data:
        db.add(Topic(name=tname, subject_id=sid, difficulty_score=diff))

    # Target accuracies per subject (matching frontend display)
    target_accuracy = {
        "Fisica": 0.91,
        "Algoritmos": 0.78,
        "Banco de Dados": 0.64,
        "Calculo I": 0.55,
        "Quimica": 0.30,
        "Algebra Linear": 0.45,
        "Redes": 0.70,
        "Estatistica": 0.58,
    }

    # Generate 8 months of performance data (Sep 2025 - Apr 2026)
    monthly_overall = [0.58, 0.62, 0.68, 0.75, 0.80, 0.82, 0.87, None]
    month_starts = []
    for i in range(8):
        m = 9 + i
        y = 2025 if m <= 12 else 2026
        m = m if m <= 12 else m - 12
        month_starts.append(date(y, m, 1))

    today = date(2026, 4, 7)
    random.seed(42)

    for month_idx, month_start in enumerate(month_starts):
        if monthly_overall[month_idx] is None:
            continue
        overall_factor = monthly_overall[month_idx]
        if month_idx < 7:
            next_month = month_starts[month_idx + 1]
        else:
            next_month = date(2026, 5, 1)
        days_in_month = (next_month - month_start).days

        for subj in subjects:
            base_acc = target_accuracy[subj.name]
            # Scale accuracy by month progression
            month_factor = overall_factor / 0.87
            acc = min(1.0, base_acc * month_factor * random.uniform(0.9, 1.1))

            for day_offset in range(days_in_month):
                d = month_start + timedelta(days=day_offset)
                if d > today:
                    break
                if random.random() < 0.3:
                    continue

                questions = random.randint(5, 25)
                correct = max(0, min(questions, round(questions * acc + random.uniform(-2, 2))))
                actual_acc = correct / questions if questions > 0 else 0.0

                db.add(PerformanceRecord(
                    student_id=student.id,
                    subject_id=subj.id,
                    date=d,
                    questions_answered=questions,
                    questions_correct=correct,
                    accuracy=round(actual_acc, 4),
                ))

    # Study sessions - generate realistic study time data
    study_hours_target = {
        "Fisica": 6.25,
        "Algoritmos": 8.5,
        "Banco de Dados": 4.25,
        "Calculo I": 5.0,
        "Quimica": 2.0,
        "Algebra Linear": 3.0,
        "Redes": 3.5,
        "Estatistica": 2.5,
    }

    for month_idx, month_start in enumerate(month_starts):
        if monthly_overall[month_idx] is None:
            continue
        if month_idx < 7:
            next_month = month_starts[month_idx + 1]
        else:
            next_month = date(2026, 5, 1)
        days_in_month = (next_month - month_start).days

        for subj in subjects:
            weekly_hrs = study_hours_target[subj.name]
            for day_offset in range(days_in_month):
                d = month_start + timedelta(days=day_offset)
                if d > today:
                    break
                if random.random() < 0.35:
                    continue
                mins = int(weekly_hrs / 5 * 60 * random.uniform(0.5, 1.5))
                mins = max(15, min(180, mins))
                start_hr = random.choice([8, 9, 10, 14, 15, 16, 19, 20, 21, 22])
                db.add(StudySession(
                    student_id=student.id,
                    subject_id=subj.id,
                    date=d,
                    duration_minutes=mins,
                    start_hour=start_hr,
                ))

    # Milestones
    milestones_data = [
        ("Primeiro top 3 no ranking", "Alcanou o top 3 pela primeira vez!", "🥇", date(2026, 2, 15)),
        ("Sequencia de 12 dias", "Estudou por 12 dias consecutivos", "🔥", date(2026, 3, 20)),
        ("100% em Fisica", "Nota maxima em uma sessao de Fisica", "🎯", date(2026, 3, 25)),
        ("500 questoes respondidas", "Marco de meio milhar de questoes", "📚", date(2025, 12, 10)),
        ("Primeira semana completa", "Estudou todos os dias da semana", "⭐", date(2025, 10, 7)),
    ]
    for title, desc, icon, achieved in milestones_data:
        db.add(Milestone(
            student_id=student.id,
            title=title,
            description=desc,
            icon=icon,
            achieved_at=achieved,
        ))

    db.commit()
