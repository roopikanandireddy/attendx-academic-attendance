# AttendX — Student Attendance Management System

[![FastAPI](https://img.shields.io/badge/FastAPI-0.109.2-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19-61DAFB.svg?logo=react&logoColor=black)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-3178C6.svg?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-CSS-38B2AC.svg?logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Supabase-336791.svg?logo=postgresql&logoColor=white)](https://supabase.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**AttendX** is an enterprise-grade, multi-role student attendance management web platform designed for higher education institutions. Built on FastAPI, PostgreSQL (Supabase-ready with local SQLite support), React 19, TypeScript, and Tailwind CSS, AttendX provides institutional administrators, faculty lecturers, and students with real-time tracking, granular attendance analytics, automated deficit calculations, role-based security, and event-driven notifications.

---

## 🏛️ System Architecture & Roles

AttendX implements strict **Role-Based Access Control (RBAC)** across three distinct persona portals:

```
                            ┌──────────────────────────────────┐
                            │      AttendX Gateway & Auth       │
                            │  JWT HS256 + Bcrypt + RBAC Guard │
                            └────────────────┬─────────────────┘
                                             │
               ┌─────────────────────────────┼─────────────────────────────┐
               ▼                             ▼                             ▼
    ┌────────────────────┐        ┌────────────────────┐        ┌────────────────────┐
    │ Administrator      │        │ Lecturer           │        │ Student            │
    │ Portal             │        │ Portal             │        │ Portal             │
    ├────────────────────┤        ├────────────────────┤        ├────────────────────┤
    │ • KPI Analytics    │        │ • Teaching Roster  │        │ • Live Attendance  │
    │ • Student CRUD     │        │ • Session Marker   │        │ • Subject Health   │
    │ • Lecturer CRUD    │        │ • Real-time Logs   │        │ • Deficit Formula  │
    │ • Subject Catalog  │        │ • Subject Reports  │        │ • History Logs     │
    │ • Teaching Assign. │        │ • CSV/Excel Export │        │ • Event Alerts     │
    └────────────────────┘        └────────────────────┘        └────────────────────┘
```

---

## 🚀 Key Modules & Capabilities

### 👨‍💼 1. Administrator Portal (Modules A1–A5)
- **Executive Metrics & KPIs**: Total student headcount, active faculty lecturers, curriculum subjects, today's attendance rate, and campus-wide average.
- **Student Directory Management**: Full CRUD operations for student records, department filtering, academic year/section classification, and search.
- **Lecturer Directory Management**: Full CRUD operations for faculty profiles with unique employee IDs and department mappings.
- **Curriculum Catalog**: Add, modify, and manage subject records with course codes, semester credit mappings, and departments.
- **Teaching Assignment Engine**: Assign faculty lecturers to specific curriculum subjects with duplicate prevention and cascade management.

### 👩‍🏫 2. Lecturer Portal (Modules L1–L4)
- **Lecturer Workspace**: Dedicated faculty dashboard isolating classes and metrics strictly to subjects assigned to the logged-in lecturer.
- **Session Attendance Marker**: Interactive session roster with fast one-click toggles, bulk actions (*All Present*, *All Absent*), and real-time validation.
- **Attendance Records Explorer**: Searchable, filterable audit log of past sessions by subject, date range, and attendance status.
- **Granular Subject Reports**: In-depth analytics per subject with student-by-student attendance percentages, session counts, and deficit tracking.
- **Data Export**: Standard academic CSV export formatted for institutional compliance and record archiving.

### 🎓 3. Student Portal
- **Real-Time Attendance Overview**: Institutional attendance percentage badge with color-coded health indicators (Green $\ge$ 75%, Amber 60–74%, Red < 60%).
- **Subject-by-Subject Breakdown**: Progress meters for enrolled subjects showing attended classes vs. total classes held.
- **Recovery Deficit Calculation**: Mathematical determination of consecutive classes needed to return above the mandatory 75% threshold.
- **Interactive Enrollment**: Batch subject enrollment modal allowing students to register for active semester catalog subjects.
- **Personal Profile**: Account inspection and self-service profile details management.

### 🔔 4. Notification Engine (Module I2)
- **Real-Time Header Bell**: Notification bell in topbars across all portals displaying unread badges with real-time polling/refresh.
- **Event-Driven Dispatch**:
  - Welcome notification on registration.
  - Enrollment confirmation upon subject registration.
  - Attendance update notifications on session marking.
  - Critical low-attendance alert whenever attendance drops below 75%.
- **Lifecycle Management**: Mark individual alerts as read, bulk mark-all-as-read, and strict user notification isolation.

### 🛡️ 5. Security & IDOR Protection (Module I4)
- **Token Security**: Cryptographically signed JWT access tokens (HS256) with strict subject claims and expiration handling.
- **Horizontal & Vertical IDOR Guards**: Explicit authorization checks verifying that lecturers can only access assigned subjects and students can only access their own records.
- **SQL Injection Prevention**: 100% parameterized queries via SQLAlchemy 2.0 ORM.
- **Sanitized Error Responses**: Production error handlers suppressing stack traces and SQL queries from client responses.

---

## 🛠️ Technology Stack

| Layer | Technology | Description |
|---|---|---|
| **Frontend** | React 19, TypeScript, Vite, Tailwind CSS | Fast SPA with typed state and modern component architecture |
| **Icons & UI** | Lucide React, Recharts, React Hot Toast | Responsive charts, accessible icons, toast notifications |
| **Backend** | Python 3.10+, FastAPI, Pydantic v2 | High-performance asynchronous REST API framework |
| **ORM / Data** | SQLAlchemy 2.0, PostgreSQL / SQLite | Dual-mode database compatibility (Supabase / local dev) |
| **Security** | Passlib (Bcrypt), Python-Jose | Industrial-standard password hashing and JWT issuance |
| **Testing** | Pytest, Httpx, Custom E2E Test Runners | 5-level test automation covering Unit, System, Module, and UAT |

---

## 📁 Repository Structure

```
attendx/
├── backend/
│   ├── app/
│   │   ├── api/             # REST API routers (auth, admin, lecturers, students, subjects, attendance, notifications)
│   │   ├── core/            # Configuration, database engine, security (JWT & bcrypt)
│   │   ├── models/          # SQLAlchemy ORM models (User, Subject, StudentSubject, LecturerSubject, Attendance, Notification)
│   │   ├── schemas/         # Pydantic v2 validation models and request/response contracts
│   │   ├── services/        # Business logic services (NotificationService, LecturerReportService)
│   │   └── main.py          # FastAPI application entry point, middleware, CORS
│   ├── attendx_dev.db       # Seeded local development SQLite database
│   ├── requirements.txt     # Pinned Python dependencies
│   ├── seed.py              # Database seeding script with realistic multi-role demo data
│   ├── test_qa_units.py     # Level 2 Unit Testing Suite (39 checks)
│   ├── test_qa_master.py    # Master QA Multi-Level Testing Suite (80 checks)
│   ├── verify_module_i5.py  # Comprehensive E2E Regression Verification Suite (128 checks)
│   └── Dockerfile           # Production container specification
├── frontend/
│   ├── src/
│   │   ├── components/      # Reusable UI components (Sidebar, Topbar, Modals, NotificationBell, Roster)
│   │   ├── context/         # AuthContext with session persistence and RBAC state
│   │   ├── layouts/         # Role-specific layouts (AdminLayout, LecturerLayout, DashboardLayout)
│   │   ├── pages/           # View controllers (Admin, Lecturer, and Student views)
│   │   │   ├── admin/       # Admin Dashboard, Student/Lecturer/Subject/Assignment managers
│   │   │   └── lecturer/    # Lecturer Dashboard, Class Marker, Records, Reports
│   │   ├── services/        # Axios API client, interceptors, typed endpoints
│   │   ├── types/           # Shared TypeScript interfaces
│   │   ├── App.tsx          # Master routing switch with ProtectedRoute RBAC guards
│   │   └── index.css        # Tailwind utility and theme definitions
│   ├── package.json         # Frontend dependencies and build scripts
│   └── vite.config.ts       # Vite build setup with API proxy
├── database/
│   └── schema.sql           # Complete Supabase PostgreSQL schema with triggers, indexes, and initial catalog
├── .env.example             # Environment configuration template
├── render.yaml              # Render deployment blueprint
└── README.md
```

---

## ⚡ Local Development Setup

### 1. Prerequisites
- **Python 3.10+**
- **Node.js 18+** & `npm`
- **Git**

### 2. Backend Setup
```bash
# Navigate to the backend directory
cd backend

# Create and activate virtual environment
python -m venv .venv
# On Windows:
.\.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Seed the database with sample users, catalog subjects, and attendance
python seed.py

# Launch FastAPI development server
uvicorn app.main:app --reload --port 8000
```
- API Base URL: `http://localhost:8000`
- Interactive OpenAPI Docs: `http://localhost:8000/docs`

### 3. Frontend Setup
```bash
# In a separate terminal, navigate to the frontend directory
cd frontend

# Install dependencies
npm install

# Start Vite development server
npm run dev
```
- Web Application: `http://localhost:5173`

---

## 🔑 Demo Credentials

The database seeding script provisions pre-configured accounts across all roles:

| Role | Email | Password | Scope & Characteristics |
|---|---|---|---|
| **System Administrator** | `admin@attendx.com` | `AdminPassword123!` | Full institutional administrative access |
| **Faculty Lecturer** | `dr.alan@lecturer.com` | `LecturerPassword123!` | Assigned to IAI & SE with sample classes |
| **Student (Healthy)** | `john.doe@student.com` | `StudentPassword123!` | Good attendance (>80%) across enrolled courses |
| **Student (At-Risk)** | `alex.kumar@student.com` | `StudentPassword123!` | Low attendance (<75%), triggers alerts & notifications |
| **Student (Alternative)**| `jane.smith@student.com` | `StudentPassword123!` | High attendance CS student |

---

## 🧪 Quality Assurance & Test Suites

AttendX features an automated test pyramid across all system layers.

### Run Level 2 Unit Testing Suite (39 Checks)
Tests security primitives, attendance formulas, schema validation, notification dispatch, and DB uniqueness constraints:
```bash
cd backend
python test_qa_units.py
```

### Run Master QA Suite (80 Checks)
Executes System Testing (Level 1), Module Testing (Level 3), Integration Testing (Level 4), UAT (Level 5), and Negative Test Cases:
```bash
cd backend
python test_qa_master.py
```

### Run Comprehensive E2E Regression Suite (128 Checks)
Runs full end-to-end integration workflows, concurrency tests, and latency benchmarks (<500ms):
```bash
cd backend
python verify_module_i5.py
```

### Frontend Typecheck & Build
```bash
cd frontend
npm run lint
npm run build
```

---

## 🌐 API Endpoint Matrix

| Method | Endpoint | Role Guard | Description |
|---|---|---|---|
| `POST` | `/api/auth/register` | Public | Register new student account |
| `POST` | `/api/auth/login` | Public | Authenticate user & issue JWT |
| `GET` | `/api/auth/me` | Authenticated | Fetch authenticated user profile |
| `PUT` | `/api/auth/profile` | Authenticated | Update user profile |
| `GET` | `/api/dashboard/admin` | Admin | Institutional metrics, trends, low attendance table |
| `GET` | `/api/dashboard/lecturer` | Lecturer | Lecturer-specific metrics and assigned subjects |
| `GET` | `/api/dashboard/student` | Student | Personal attendance stats and subject breakdown |
| `GET` | `/api/admin/students` | Admin | Filterable, paginated student management |
| `POST` | `/api/admin/students` | Admin | Create student record |
| `GET` | `/api/admin/lecturers` | Admin | Filterable, paginated lecturer management |
| `POST` | `/api/admin/lecturers` | Admin | Create lecturer record |
| `GET` | `/api/admin/assignments` | Admin | List lecturer subject assignments |
| `POST` | `/api/admin/assignments` | Admin | Assign lecturer to subject |
| `GET` | `/api/lecturer/subjects` | Lecturer | List subjects assigned to logged-in lecturer |
| `GET` | `/api/lecturer/attendance/session` | Lecturer | Get class roster for specific date & subject |
| `POST` | `/api/lecturer/attendance/mark` | Lecturer | Bulk submit attendance session records |
| `GET` | `/api/lecturer/records` | Lecturer | Query attendance records with status filters |
| `GET` | `/api/lecturer/reports/{id}` | Lecturer | Granular subject attendance report |
| `GET` | `/api/lecturer/reports/{id}/export` | Lecturer | Academic CSV export of subject attendance |
| `GET` | `/api/subjects` | Authenticated | List all active catalog subjects |
| `GET` | `/api/subjects/my-enrollments` | Student | List subjects currently enrolled by student |
| `POST` | `/api/subjects/enroll-batch` | Student | Batch enroll student into subjects |
| `GET` | `/api/attendance` | Authenticated | Query personal or institutional attendance |
| `GET` | `/api/notifications` | Authenticated | List user notifications (newest first) |
| `GET` | `/api/notifications/unread-count` | Authenticated | Get total unread notifications count |
| `PUT` | `/api/notifications/{id}/read` | Authenticated | Mark single notification as read |
| `PUT` | `/api/notifications/read-all` | Authenticated | Mark all notifications as read |

---

## ☁️ Deployment Guide

### Deploying to Render & Supabase

1. **Database Setup (Supabase)**:
   - Create a project on [Supabase](https://supabase.com).
   - In the **SQL Editor**, execute [`database/schema.sql`](file:///c:/Administrator/projects/attendx/database/schema.sql).
   - Obtain the connection URI from **Project Settings > Database > Connection String (URI)**.

2. **Automated Blueprint Deployment (Render)**:
   - Push your repository to GitHub.
   - In [Render](https://render.com), choose **New + > Blueprint**.
   - Select your repository. Render will automatically detect [`render.yaml`](file:///c:/Administrator/projects/attendx/render.yaml) and provision:
     - `attendx-api`: Python 3.10+ web service with `uvicorn app.main:app`.
     - `attendx-web`: Static web app building `npm run build`.
   - Configure environment variables:
     - `DATABASE_URL`: Your Supabase PostgreSQL connection string.
     - `JWT_SECRET`: Secure random string (min 32 characters).
     - `FRONTEND_URL`: URL of the deployed frontend static site.
     - `VITE_API_URL`: URL of the deployed backend service.
   - Click **Apply** to deploy.

---

## 📄 License
This project is licensed under the MIT License. See [LICENSE](file:///c:/Administrator/projects/attendx/LICENSE) for details.
