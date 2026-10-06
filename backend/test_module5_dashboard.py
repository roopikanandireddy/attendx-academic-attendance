"""Module 5 Dashboard Query Optimization Verification Test Suite

Covers:
1. Admin Dashboard correctness and query optimization
2. Student Dashboard correctness and query optimization
3. Lecturer Dashboard correctness and query optimization
4. Query correctness & mathematical integrity (attendance percentages, classes needed)
5. Aggregation correctness (set-based vs iterative)
6. N+1 regression prevention (query budget assertions)
7. RBAC & Data Isolation verification
8. Edge cases (zero records, zero assignments, 0% attendance, etc.)
"""

import sys
import math
import uuid
import pytest
from datetime import date, timedelta, datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy import func, event

sys.path.insert(0, ".")
from app.main import app
from app.core.database import SessionLocal, engine, get_db
from app.models.user import User
from app.models.subject import Subject
from app.models.student_subject import StudentSubject
from app.models.lecturer_subject import LecturerSubject
from app.models.attendance import Attendance
from app.models.notification import Notification
from app.core.security import create_access_token
from app.api.dashboard import (
    get_admin_dashboard_data,
    get_lecturer_dashboard_data,
    student_dashboard,
    calculate_classes_needed,
    LOW_ATTENDANCE_THRESHOLD,
)

client = TestClient(app)


class QueryCounter:
    """Helper to monitor and assert on SQL query count within a block."""
    def __init__(self):
        self.queries = []

    def __enter__(self):
        self.queries.clear()
        event.listen(engine, "before_cursor_execute", self._callback)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        event.remove(engine, "before_cursor_execute", self._callback)

    def _callback(self, conn, cursor, statement, parameters, context, executemany):
        self.queries.append(statement)

    @property
    def count(self):
        return len(self.queries)


# ---------------------------------------------------------------------------
# FIXTURES & HELPERS
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module")
def admin_user(db_session):
    admin = db_session.query(User).filter(User.role == "admin").first()
    assert admin is not None, "Admin user must exist in test db"
    return admin


@pytest.fixture(scope="module")
def student_user(db_session):
    student = db_session.query(User).filter(User.role == "student").first()
    assert student is not None, "Student user must exist in test db"
    return student


@pytest.fixture(scope="module")
def lecturer_user(db_session):
    lecturer = db_session.query(User).filter(User.role == "lecturer").first()
    assert lecturer is not None, "Lecturer user must exist in test db"
    return lecturer


# ---------------------------------------------------------------------------
# 1. ADMIN DASHBOARD TESTS
# ---------------------------------------------------------------------------

def test_admin_dashboard_query_budget(db_session, admin_user):
    """Admin dashboard must execute in under 20 queries (baseline was 220 queries)."""
    with QueryCounter() as qc:
        data = get_admin_dashboard_data(admin_user, db_session)
    assert qc.count <= 20, f"Admin dashboard executed {qc.count} queries, exceeding budget of 20"
    assert "metrics" in data
    assert "todays_attendance" in data
    assert "subject_stats" in data
    assert "attendance_trend" in data
    assert "recent_activity" in data
    assert "low_attendance_students" in data


def test_admin_dashboard_metrics_correctness(db_session, admin_user):
    """Verify Admin dashboard aggregates match direct database counts."""
    data = get_admin_dashboard_data(admin_user, db_session)
    expected_students = db_session.query(func.count(User.id)).filter(User.role == "student").scalar()
    expected_lecturers = db_session.query(func.count(User.id)).filter(User.role == "lecturer").scalar()
    expected_subjects = db_session.query(func.count(Subject.id)).scalar()

    assert data["total_students"] == expected_students
    assert data["total_lecturers"] == expected_lecturers
    assert data["total_subjects"] == expected_subjects
    assert data["metrics"]["total_students"] == expected_students


def test_admin_dashboard_trend_continuity(db_session, admin_user):
    """14-day trend must contain exactly 14 dates, monotonically increasing to today."""
    data = get_admin_dashboard_data(admin_user, db_session)
    trend = data["attendance_trend"]
    assert len(trend) == 14
    today = date.today()
    for i, entry in enumerate(trend):
        expected_date = (today - timedelta(days=13 - i)).isoformat()
        assert entry["date"] == expected_date
        assert entry["present"] + entry["absent"] == entry["total"]
        if entry["total"] > 0:
            expected_pct = round((entry["present"] / entry["total"]) * 100, 1)
            assert entry["percentage"] == expected_pct
        else:
            assert entry["percentage"] == 0.0


def test_admin_dashboard_low_attendance_accuracy(db_session, admin_user):
    """All students in low_attendance_students must have percentage < 75.0 and total_classes > 0."""
    data = get_admin_dashboard_data(admin_user, db_session)
    for student in data["low_attendance_students"]:
        assert student["attendance_percentage"] < LOW_ATTENDANCE_THRESHOLD
        assert student["total_classes"] > 0
        assert student["status"] == "Low"
        assert student["classes_needed"] >= 0


# ---------------------------------------------------------------------------
# 2. STUDENT DASHBOARD TESTS
# ---------------------------------------------------------------------------

def test_student_dashboard_query_budget(db_session, student_user):
    """Student dashboard must execute in under 5 queries (baseline was 31 queries)."""
    with QueryCounter() as qc:
        data = student_dashboard(student_user, db_session)
    assert qc.count <= 5, f"Student dashboard executed {qc.count} queries, exceeding budget of 5"
    assert "user" in data
    assert "overall_stats" in data
    assert "subjects" in data
    assert "recent_attendance" in data


def test_student_dashboard_math_correctness(db_session, student_user):
    """Verify Student dashboard subject stats and overall stats add up correctly."""
    data = student_dashboard(student_user, db_session)
    overall = data["overall_stats"]
    assert overall["present"] + overall["absent"] == overall["total_classes"]
    if overall["total_classes"] > 0:
        expected_pct = round((overall["present"] / overall["total_classes"]) * 100, 1)
        assert overall["percentage"] == expected_pct

    for sub in data["subjects"]:
        assert sub["present"] + sub["absent"] == sub["total_classes"]
        if sub["total_classes"] > 0:
            expected_sub_pct = round((sub["present"] / sub["total_classes"]) * 100, 1)
            assert sub["percentage"] == expected_sub_pct

    # Low attendance subjects should accurately match those with < 75%
    for low_sub in data["low_attendance_subjects"]:
        assert low_sub["percentage"] < LOW_ATTENDANCE_THRESHOLD
        assert low_sub["total_classes"] > 0
        assert "classes_needed" in low_sub
        assert low_sub["classes_needed"] >= 0


# ---------------------------------------------------------------------------
# 3. LECTURER DASHBOARD TESTS
# ---------------------------------------------------------------------------

def test_lecturer_dashboard_query_budget(db_session, lecturer_user):
    """Lecturer dashboard must execute in under 12 queries (baseline was 32 queries)."""
    with QueryCounter() as qc:
        data = get_lecturer_dashboard_data(lecturer_user, db_session)
    assert qc.count <= 12, f"Lecturer dashboard executed {qc.count} queries, exceeding budget of 12"
    assert "lecturer" in data
    assert "summary" in data
    assert "subjects" in data
    assert "attendance_overview" in data
    assert "recent_activity" in data


def test_lecturer_dashboard_data_isolation(db_session, lecturer_user):
    """Lecturer must only see assigned subjects."""
    data = get_lecturer_dashboard_data(lecturer_user, db_session)
    assigned_ids = {
        row.subject_id
        for row in db_session.query(LecturerSubject)
        .filter(LecturerSubject.lecturer_id == lecturer_user.id)
        .all()
    }
    for sub in data["subjects"]:
        assert sub["id"] in assigned_ids


def test_lecturer_unique_student_counting(db_session, lecturer_user):
    """Verify total_students is distinct student_id across assigned subjects (no double-counting)."""
    data = get_lecturer_dashboard_data(lecturer_user, db_session)
    assigned_ids = [
        row.subject_id
        for row in db_session.query(LecturerSubject)
        .filter(LecturerSubject.lecturer_id == lecturer_user.id)
        .all()
    ]
    expected_unique = (
        db_session.query(func.count(func.distinct(StudentSubject.student_id)))
        .filter(StudentSubject.subject_id.in_(assigned_ids))
        .scalar()
        or 0
    )
    assert data["summary"]["total_students"] == expected_unique


# ---------------------------------------------------------------------------
# 4. CLASSES NEEDED MATHEMATICAL LOGIC TESTS
# ---------------------------------------------------------------------------

def test_calculate_classes_needed_edge_cases():
    # 0 classes attended -> 0 needed
    assert calculate_classes_needed(0, 0) == 0
    # Already above 75% -> 0 needed
    assert calculate_classes_needed(8, 10) == 0  # 80%
    assert calculate_classes_needed(3, 4) == 0   # 75%
    # Below 75%: 0/1 attended (0%) -> needs 3 more: (0+3)/(1+3) = 3/4 = 75%
    assert calculate_classes_needed(0, 1) == 3
    # 1/2 attended (50%) -> needs (0.75*2 - 1)/(0.25) = (1.5 - 1)/0.25 = 2 -> (1+2)/(2+2) = 3/4 = 75%
    assert calculate_classes_needed(1, 2) == 2
    # 5/10 attended (50%) -> needs (7.5 - 5)/0.25 = 2.5 / 0.25 = 10 -> (5+10)/(10+10) = 15/20 = 75%
    assert calculate_classes_needed(5, 10) == 10


# ---------------------------------------------------------------------------
# 5. RBAC & ENDPOINT ISOLATION TESTS
# ---------------------------------------------------------------------------

def test_rbac_student_cannot_access_admin_dashboard(student_user):
    token = create_access_token(data={"sub": student_user.id, "role": "student"})
    response = client.get("/api/dashboard/admin", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403

    response2 = client.get("/api/admin/dashboard", headers={"Authorization": f"Bearer {token}"})
    assert response2.status_code == 403


def test_rbac_student_cannot_access_lecturer_dashboard(student_user):
    token = create_access_token(data={"sub": student_user.id, "role": "student"})
    response = client.get("/api/dashboard/lecturer", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


def test_rbac_lecturer_cannot_access_admin_dashboard(lecturer_user):
    token = create_access_token(data={"sub": lecturer_user.id, "role": "lecturer"})
    response = client.get("/api/dashboard/admin", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


def test_rbac_lecturer_cannot_access_student_dashboard(lecturer_user):
    token = create_access_token(data={"sub": lecturer_user.id, "role": "lecturer"})
    response = client.get("/api/dashboard/student", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


# ---------------------------------------------------------------------------
# 6. EDGE CASES TESTS
# ---------------------------------------------------------------------------

def test_lecturer_with_no_assigned_subjects(db_session):
    """Lecturer with 0 assigned subjects returns clean zeroed schema without errors."""
    unassigned_lecturer = User(
        id=str(uuid.uuid4()),
        email=f"unassigned.{uuid.uuid4().hex[:6]}@attendx.com",
        password_hash="test_hash",
        full_name="Unassigned Lecturer",
        role="lecturer",
        is_active=True,
    )
    db_session.add(unassigned_lecturer)
    db_session.commit()

    try:
        data = get_lecturer_dashboard_data(unassigned_lecturer, db_session)
        assert data["summary"]["total_subjects"] == 0
        assert data["summary"]["total_students"] == 0
        assert data["summary"]["total_attendance_records"] == 0
        assert data["attendance_overview"]["has_data"] is False
        assert data["subjects"] == []
        assert data["recent_activity"] == []
    finally:
        db_session.delete(unassigned_lecturer)
        db_session.commit()


def test_student_with_no_attendance_or_enrollments(db_session):
    """Student with 0 enrollments and 0 attendance returns valid zero stats."""
    fresh_student = User(
        id=str(uuid.uuid4()),
        email=f"fresh.{uuid.uuid4().hex[:6]}@attendx.com",
        password_hash="test_hash",
        full_name="Fresh Student",
        role="student",
        is_active=True,
    )
    db_session.add(fresh_student)
    db_session.commit()

    try:
        data = student_dashboard(fresh_student, db_session)
        assert data["overall_stats"]["total_classes"] == 0
        assert data["overall_stats"]["present"] == 0
        assert data["overall_stats"]["percentage"] == 0.0
        assert data["subjects"] == []
        assert data["recent_attendance"] == []
        assert data["low_attendance_subjects"] == []
    finally:
        db_session.delete(fresh_student)
        db_session.commit()
