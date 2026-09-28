from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import get_settings
from app.core.database import engine, Base
from app.api import auth, students, subjects, attendance, dashboard

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
origins = [
    settings.FRONTEND_URL,
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
]

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
app.include_router(subjects.router)
app.include_router(attendance.router)
app.include_router(dashboard.router)


@app.get("/", tags=["Health"])
def health_check():
    return {"status": "ok", "app": "AttendX API", "version": "1.0.0"}


@app.get("/api/health", tags=["Health"])
def api_health():
    return {"status": "ok"}


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please try again later."},
    )
