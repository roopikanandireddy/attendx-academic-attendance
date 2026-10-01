# AttendX — Student Attendance Management System

[![FastAPI](https://img.shields.io/badge/FastAPI-0.109.2-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19-61DAFB.svg?logo=react&logoColor=black)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-3178C6.svg?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-CSS-38B2AC.svg?logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Supabase-336791.svg?logo=postgresql&logoColor=white)](https://supabase.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

**AttendX** is an enterprise-grade, multi-role student attendance management web platform designed for higher education institutions. Built on FastAPI, PostgreSQL (Supabase-ready with local SQLite support), React 19, TypeScript, and Tailwind CSS, AttendX provides institutional administrators, faculty lecturers, and students with real-time tracking, granular attendance analytics, automated deficit calculations, role-based security, and event-driven notifications.

---

## Features

### 🎓 Student Portal
- **Login & Authentication**: Secure JWT-based authentication.
- **Personal Dashboard**: High-level attendance percentage badge with color-coded health indicators (Green $\ge$ 75%, Amber 60–74%, Red < 60%).
- **Subject Enrollment**: Interactive modal allowing students to enroll in curriculum catalog subjects.
- **Live Attendance**: Subject-by-subject attendance progress meters with class deficit recovery calculations.
- **Attendance History**: Date-wise attendance logs detailing subject, status, and session timestamp.
- **Notifications**: Real-time bell alerts for attendance marking, welcome events, and low-attendance warnings (<75%).
- **Profile Management**: View and edit personal student profile details.

### 👩‍🏫 Lecturer Portal
- **Login & Authentication**: Dedicated faculty authentication with role enforcement.
- **Lecturer Dashboard**: Quick metrics on assigned subjects, scheduled classes, and average class attendance.
- **Assigned Subjects**: Workspace strictly isolated to curriculum subjects assigned to the faculty member.
- **Session Attendance Marking**: Interactive roster with one-click toggles, bulk actions (*All Present*, *All Absent*), and real-time validation.
- **Attendance Records Explorer**: Searchable and filterable audit log of past sessions by subject, date range, and status.
- **Subject Reports**: Student-by-student attendance percentages, session counts, and deficit indicators with academic CSV export.
- **Notifications & Profile**: In-app notifications and personal profile management.

### 👨‍💼 Admin Portal
- **Executive Dashboard**: High-level KPI metric cards (Total Students, Total Lecturers, Total Subjects, Today's Attendance %, Overall Institution Average).
- **Student Management (CRUD)**: Create, view, update, and search students classified by department, year, and section.
- **Lecturer Management (CRUD)**: Create, view, update, and search faculty profiles with employee IDs.
- **Subject Management (CRUD)**: Add, edit, and organize subjects by code, department, semester, and credits.
- **Lecturer Assignment Engine**: Assign faculty lecturers to curriculum subjects with conflict checks and cascading management.

---

## Technology Stack

### Backend
- **FastAPI**: Asynchronous web framework for high-throughput REST APIs
- **SQLAlchemy 2.0**: Database ORM with support for PostgreSQL (Supabase) and local SQLite
- **PostgreSQL / Supabase**: Production database engine with relational triggers and indexing
- **JWT (Python-Jose)**: Secure stateless authentication tokens
- **Python 3.10+**: Core backend runtime
- **Passlib & Bcrypt**: Password hashing and verification

### Frontend
- **React 19**: Component-based UI library
- **TypeScript**: Static typing across API schemas and UI states
- **Vite**: Ultra-fast build tool and dev server
- **Tailwind CSS**: Modern utility-first styling system
- **Axios**: HTTP client with request/response interceptors
- **Lucide React & Recharts**: Visual icons and interactive analytics charts
- **React Hot Toast**: Notifications and status toasts

---

## Architecture

```
User (Student / Lecturer / Admin)
        ↓
React Frontend (SPA with Role Guards)
        ↓  [REST / JSON over HTTP]
FastAPI REST API (JWT & RBAC Middleware)
        ↓
Business Logic (Attendance Engine, Notification Service, Reporting Service)
        ↓
SQLAlchemy ORM (Data Access Layer)
        ↓
Database Engine (PostgreSQL in Production / SQLite in Development)
```

---

## Project Structure

```
attendx/
├── backend/
│   ├── app/
│   │   ├── api/             # REST API routers (auth, admin, lecturers, students, subjects, attendance, notifications)
│   │   ├── core/            # Config, database engine, security (JWT & bcrypt)
│   │   ├── models/          # SQLAlchemy ORM models (User, Subject, StudentSubject, LecturerSubject, Attendance, Notification)
│   │   ├── schemas/         # Pydantic v2 validation models and request/response contracts
│   │   ├── services/        # Business logic services (NotificationService, LecturerReportService)
│   │   └── main.py          # FastAPI application entry point, middleware, CORS
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

## Setup

### Prerequisites
- **Python 3.10+**
- **Node.js 18+** & `npm`
- **Git**

### Installation Commands

1. **Clone the repository:**
   ```bash
   git clone https://github.com/roopikanandireddy/attendx-academic-attendance.git
   cd attendx-academic-attendance
   ```

2. **Backend Setup:**
   ```bash
   cd backend
   python -m venv .venv
   # Windows:
   .\.venv\Scripts\activate
   # macOS/Linux:
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Frontend Setup:**
   ```bash
   cd ../frontend
   npm install
   ```

---

## ⚙️ Environment Variables

Copy the template files to configure your environment:
- Root: [`.env.example`](file:///.env.example)
- Backend: [`backend/.env.example`](file:///backend/.env.example)
- Frontend: [`frontend/.env.example`](file:///frontend/.env.example)

### Required Environment Variable Names:

| Variable Name | Context | Purpose |
|---|---|---|
| `DATABASE_URL` | Backend | PostgreSQL connection URI (falls back to local SQLite if omitted) |
| `SUPABASE_URL` | Backend | Supabase project URL |
| `SUPABASE_KEY` | Backend | Supabase API key |
| `JWT_SECRET` | Backend | Cryptographic secret key for signing JWT tokens |
| `JWT_ALGORITHM` | Backend | Token signing algorithm (e.g. HS256) |
| `JWT_EXPIRATION_MINUTES`| Backend | Token lifetime in minutes |
| `FRONTEND_URL` | Backend | Allowed CORS origin for frontend client |
| `VITE_API_URL` | Frontend | Target backend API base URL |

> *Note: Never commit actual secret values to version control. Always use environment variables in deployment environments.*

---

## Running Locally

### 1. Seed the Database
```bash
cd backend
python seed.py
```

### 2. Start the Backend API Server
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```
- API Base URL: `http://localhost:8000`
- Interactive OpenAPI Swagger Docs: `http://localhost:8000/docs`

### 3. Start the Frontend Development Server
```bash
cd frontend
npm run dev
```
- Web Application: `http://localhost:5173`

---

## 🔑 Demo Credentials

The database seeding script provisions pre-configured accounts:

| Role | Email | Password | Scope & Characteristics |
|---|---|---|---|
| **System Administrator** | `admin@attendx.com` | `AdminPassword123!` | Full institutional administrative access |
| **Faculty Lecturer** | `dr.alan@lecturer.com` | `LecturerPassword123!` | Assigned to IAI & SE with sample classes |
| **Student (Healthy)** | `john.doe@student.com` | `StudentPassword123!` | Good attendance (>80%) across enrolled courses |
| **Student (At-Risk)** | `alex.kumar@student.com` | `StudentPassword123!` | Low attendance (<75%), triggers alerts & notifications |
| **Student (Alternative)**| `jane.smith@student.com` | `StudentPassword123!` | High attendance CS student |

---

## 🧪 Testing

AttendX includes an automated test pyramid across all system layers.

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

## 🛡️ Security

AttendX incorporates multi-tier defensive controls:
- **JWT Authentication**: Stateless, signed bearer tokens with configurable expiration.
- **Role-Based Access Control (RBAC)**: Strict role guards on all endpoints (`get_current_user`, `get_current_admin`, `get_current_lecturer`).
- **Resource Ownership & IDOR Protection**: Lecturers can only access assigned subjects and students can only access their personal records.
- **Password Hashing**: Industrial-standard `bcrypt` algorithm.
- **SQL Injection Prevention**: Parameterized queries via SQLAlchemy ORM.
- **Environment-Based Secrets**: All sensitive keys loaded exclusively via environment variables.

---

## ☁️ Deployment

Production deployment is handled separately. The repository includes an infrastructure-as-code specification for cloud providers:
- [`render.yaml`](file:///render.yaml): Blueprint configuration for hosting `attendx-api` (FastAPI web service) and `attendx-web` (React static site).
- [`database/schema.sql`](file:///database/schema.sql): PostgreSQL schema ready for Supabase or standard PostgreSQL instances.

---

## 📄 License
This project is licensed under the MIT License. See [LICENSE](file:///LICENSE) for details.
