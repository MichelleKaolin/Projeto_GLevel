"""GLevel Backend — FastAPI application with SQLite and integrated dashboard."""
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .database import engine, Base, SessionLocal
from .models import Student, Subject, StudentSubject, Topic, StudySession, PerformanceRecord, Milestone
from .routes import router
from .seed import seed_database

Base.metadata.create_all(bind=engine)

# Seed demo data
db = SessionLocal()
try:
    seed_database(db)
finally:
    db.close()

app = FastAPI(
    title="GLevel API",
    description="Backend API for GLevel — student performance analytics platform",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static frontend files
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "..", "frontend")
if os.path.isdir(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

# Templates for dashboard
templates_dir = os.path.join(os.path.dirname(__file__), "templates")
os.makedirs(templates_dir, exist_ok=True)
templates = Jinja2Templates(directory=templates_dir)

# Include API routes
app.include_router(router, prefix="/api")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Redirect to the dashboard."""
    return """
    <html>
    <head><meta http-equiv="refresh" content="0;url=/dashboard"></head>
    <body><p>Redirecting to <a href="/dashboard">GLevel Dashboard</a>...</p></body>
    </html>
    """


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Serve the integrated analytics dashboard."""
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/health")
async def health():
    return {"status": "ok", "app": "GLevel", "version": "1.0.0"}
