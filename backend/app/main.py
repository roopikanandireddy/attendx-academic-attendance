import sys
from pathlib import Path

# Add backend directory to sys.path so running main.py directly works
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.core.config import get_settings
from app.core.database import engine, Base
from app.api import auth, students, subjects, attendance, dashboard, notifications, lecturers, assignments

settings = get_settings()

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AttendX API",
    description="Student Attendance Management System — REST API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
raw_origins = [
    settings.FRONTEND_URL,
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
]
if hasattr(settings, "ALLOWED_ORIGINS") and settings.ALLOWED_ORIGINS:
    extra = [o.strip() for o in settings.ALLOWED_ORIGINS.split(",") if o.strip()]
    raw_origins.extend(extra)

# Sanitize origins: strip whitespace and trailing slashes (e.g. 'https://attendx.onrender.com/' -> 'https://attendx.onrender.com')
origins = []
for o in raw_origins:
    if o and isinstance(o, str):
        cleaned = o.strip().rstrip("/")
        if cleaned and cleaned not in origins:
            origins.append(cleaned)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(auth.router)
app.include_router(students.router)
app.include_router(students.admin_router)
app.include_router(lecturers.router)
app.include_router(lecturers.admin_router)
app.include_router(lecturers.lecturer_router)
app.include_router(subjects.router)
app.include_router(subjects.admin_router)
app.include_router(assignments.router)
app.include_router(assignments.admin_router)
app.include_router(attendance.router)
app.include_router(dashboard.router)
app.include_router(dashboard.admin_router)
app.include_router(notifications.router)


@app.get("/", tags=["Health"])
def health_check():
    return {"status": "ok", "app": "AttendX API", "version": "1.0.0"}


@app.get("/api/health", tags=["Health"])
def api_health():
    return {"status": "ok"}


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers=getattr(exc, "headers", None),
        )
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please try again later."},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

