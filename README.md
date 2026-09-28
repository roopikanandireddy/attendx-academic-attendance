# AttendX — Student Attendance Management System

[![FastAPI](https://img.shields.io/badge/FastAPI-0.109.2-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg?logo=react&logoColor=black)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-3178C6.svg?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-CSS-38B2AC.svg?logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Supabase-336791.svg?logo=postgresql&logoColor=white)](https://supabase.com)

**AttendX** is a modern, production-grade student attendance management web application built with FastAPI, PostgreSQL/Supabase, React, and Tailwind CSS. It empowers educational institutions to record, manage, monitor, and analyze attendance with automated metrics, low-attendance alerts, and role-based access control.

---

## 🚀 Key Features

### 👨‍💼 Administrator Portal
- **Executive Dashboard**: High-level KPI metric cards (Total Students, Total Subjects, Today's Attendance %, Overall Institution Average).
- **Interactive Analytics**: 14-day attendance trend lines, daily present/absent distribution donuts, and subject performance bar charts.
- **Student Management (CRUD)**: Add, edit, delete, search, and filter students by department, year, and section.
- **Subject Management (CRUD)**: Add, edit, delete, and filter subjects with codes, departments, semesters, and years.
- **Attendance Marking**: Interactive session marker with one-click toggles, bulk actions (*All Present*, *All Absent*), and real-time counters.
- **Attendance Records & Auditing**: Filterable attendance logs with inline status updates and deletion capabilities.
- **Low Attendance Alerts**: Immediate notification banner for any student falling below the critical 75% attendance threshold, with calculated classes needed to recover.

### 🎓 Student Portal
- **Personalized Dashboard**: Overall attendance percentage badge, total classes attended vs. missed, and recent session timeline.
- **Subject Breakdown**: Progress meters for every enrolled subject with visual health color codes (Green $\ge$ 75%, Amber 60–74%, Red < 60%).
- **Attendance History**: Date-wise attendance logs detailing subject, status, and class date.
- **Profile Management**: View and edit personal profile information.

### 🛡️ Security & Architecture
- **JWT Authentication**: Secure Bearer tokens with configurable expiration and encrypted secrets.
- **Role-Based Access Control (RBAC)**: Strict backend authorization guards (`get_current_admin` / `get_current_user`) ensuring students cannot access administrative endpoints.
- **Password Hashing**: Industry-standard `bcrypt` password hashing via Passlib.
- **SQLAlchemy ORM**: Database-agnostic layer supporting Supabase PostgreSQL in production and local SQLite in development.

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| **Frontend** | React 18, Vite, TypeScript, Tailwind CSS, Lucide Icons, Recharts, React Router v6, Axios, React Hot Toast |
| **Backend** | Python 3.10+, FastAPI, Pydantic v2, SQLAlchemy 2.0, Passlib (Bcrypt), Python-Jose |
| **Database** | Supabase PostgreSQL / Local SQLite |
| **Deployment** | Render (`render.yaml`), Dockerfile |

---

## 📁 Project Structure

```
attendx/
├── backend/
│   ├── app/
│   │   ├── api/             # REST API routers (auth, students, subjects, attendance, dashboard)
│   │   ├── core/            # Config, database engine, security (JWT & bcrypt)
│   │   ├── models/          # SQLAlchemy ORM models (User, Subject, StudentSubject, Attendance)
│   │   ├── schemas/         # Pydantic validation schemas
│   │   └── main.py          # FastAPI application entry point & CORS configuration
│   ├── requirements.txt     # Pinned Python dependencies
│   ├── seed.py              # Database seeding script with realistic demo data
│   └── Dockerfile           # Production container specification
├── frontend/
│   ├── src/
│   │   ├── components/      # Reusable UI components (Modal, ConfirmDialog, Skeletons, Sidebar)
│   │   ├── context/         # AuthContext with persistent login session
│   │   ├── layouts/         # DashboardLayout with responsive sidebar & topbar
│   │   ├── pages/           # Admin & Student dashboards, CRUD views, attendance markers
│   │   ├── services/        # Axios API client with JWT interceptor
│   │   ├── types/           # TypeScript interfaces
│   │   ├── App.tsx          # Route definitions & RBAC guards
│   │   └── index.css        # Tailwind design tokens, typography, & custom components
│   ├── package.json
│   └── vite.config.ts       # Vite configuration with API dev proxy
├── database/
│   └── schema.sql           # Complete Supabase PostgreSQL schema with indexes & triggers
├── render.yaml              # Render Blueprint deployment configuration
└── README.md
```

---

## ⚡ Quick Start (Local Setup)

### 1. Prerequisites
- **Python 3.10+**
- **Node.js 18+** & `npm`
- **Git**

### 2. Backend Setup
```bash
# Navigate to backend directory
cd backend

# (Optional) Create and activate virtual environment
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the database seeding script (creates tables & initial accounts)
python seed.py

# Start FastAPI dev server
uvicorn app.main:app --reload --port 8000
```
Backend will be live at: **`http://localhost:8000`**  
Interactive Swagger API docs at: **`http://localhost:8000/docs`**

### 3. Frontend Setup
```bash
# In a new terminal, navigate to frontend directory
cd frontend

# Install npm dependencies
npm install

# Start Vite dev server
npm run dev
```
Frontend will be live at: **`http://localhost:5173`**

---

## 🔑 Demo Credentials

The database seeding script (`backend/seed.py`) provisions the following test accounts:

| Role | Email | Password | Details |
|---|---|---|---|
| **Admin** | `admin@attendx.com` | `AdminPassword123!` | System Administrator (Full Access) |
| **Student** | `john.doe@student.com` | `StudentPassword123!` | High attendance student (~86%) |
| **Student** | `alex.kumar@student.com` | `StudentPassword123!` | Low attendance student (~60%, triggers alerts) |
| **Student** | `jane.smith@student.com` | `StudentPassword123!` | Enrolled in CS subjects (~95%) |

---

## 🌐 API Overview

| Method | Endpoint | Access | Description |
|---|---|---|---|
| `POST` | `/api/auth/register` | Public | Register student account |
| `POST` | `/api/auth/login` | Public | Authenticate user & issue JWT |
| `GET` | `/api/auth/me` | Authenticated | Get current authenticated profile |
| `PUT` | `/api/auth/profile` | Authenticated | Update user profile |
| `GET` | `/api/dashboard/admin` | Admin | Overall metrics, trends, low attendance list |
| `GET` | `/api/dashboard/student` | Student | Personal attendance stats, subject breakdown |
| `GET` | `/api/students` | Admin | List students with search and filters |
| `POST` | `/api/students` | Admin | Create student account |
| `PUT` | `/api/students/{id}` | Admin | Update student details |
| `DELETE` | `/api/students/{id}` | Admin | Delete student |
| `GET` | `/api/subjects` | Authenticated | List all course subjects |
| `POST` | `/api/subjects` | Admin | Create subject |
| `PUT` | `/api/subjects/{id}` | Admin | Update subject |
| `DELETE` | `/api/subjects/{id}` | Admin | Delete subject |
| `GET` | `/api/subjects/{id}/students` | Admin | List students enrolled in subject |
| `POST` | `/api/attendance` | Admin | Bulk mark attendance for session |
| `GET` | `/api/attendance` | Authenticated | Query attendance records (filtered) |
| `PUT` | `/api/attendance/{id}` | Admin | Update single attendance record status |
| `DELETE` | `/api/attendance/{id}` | Admin | Delete single attendance record |

---

## ☁️ Deployment Guide

### Deploying to Render & Supabase

1. **Database Setup (Supabase)**:
   - Create a free project on [Supabase](https://supabase.com).
   - Go to the **SQL Editor** in Supabase and run the contents of [`database/schema.sql`](file:///c:/Administrator/projects/attendx/database/schema.sql).
   - Copy your PostgreSQL connection string from **Project Settings > Database > Connection String (URI)**.

2. **Automated Deployment (Render Blueprint)**:
   - Push your repository to GitHub.
   - On [Render](https://render.com), click **New + > Blueprint**.
   - Connect your GitHub repository. Render will automatically detect [`render.yaml`](file:///c:/Administrator/projects/attendx/render.yaml) and configure:
     - `attendx-api`: Python Web Service with `uvicorn app.main:app`.
     - `attendx-web`: Static Site building `npm run build`.
   - Set the following environment variables in Render:
     - `DATABASE_URL`: Your Supabase connection string.
     - `FRONTEND_URL`: Your Render frontend URL (e.g. `https://attendx-web.onrender.com`).
     - `VITE_API_URL`: Your Render backend API URL (e.g. `https://attendx-api.onrender.com`).
   - Click **Apply** to deploy!

---

## 📄 License
This project is licensed under the MIT License.
