-- AttendX Database Schema
-- Supabase PostgreSQL

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE users (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'student' CHECK (role IN ('student', 'lecturer', 'admin')),
    student_id VARCHAR(50) UNIQUE,
    employee_id VARCHAR(50) UNIQUE,
    department VARCHAR(100),
    year INTEGER CHECK (year >= 1 AND year <= 6),
    section VARCHAR(10),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    account_status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE' CHECK (account_status IN ('ACTIVE', 'PENDING_ACTIVATION', 'SUSPENDED', 'INVITED', 'DISABLED')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Subjects table
CREATE TABLE subjects (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50) NOT NULL UNIQUE,
    department VARCHAR(100) NOT NULL,
    year INTEGER NOT NULL CHECK (year >= 1 AND year <= 6),
    semester INTEGER NOT NULL CHECK (semester >= 1 AND semester <= 12),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Student-Subject enrollment
CREATE TABLE student_subjects (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    student_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subject_id VARCHAR(36) NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(student_id, subject_id)
);

-- Lecturer-Subject teaching assignment
CREATE TABLE lecturer_subjects (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    lecturer_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subject_id VARCHAR(36) NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(lecturer_id, subject_id)
);

-- Attendance records
CREATE TABLE attendance (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    student_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subject_id VARCHAR(36) NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    attendance_date DATE NOT NULL,
    status VARCHAR(10) NOT NULL CHECK (status IN ('present', 'absent')),
    marked_by VARCHAR(36) NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(student_id, subject_id, attendance_date)
);

-- Notifications table
CREATE TABLE notifications (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    type VARCHAR(50) NOT NULL CHECK (type IN ('attendance', 'low_attendance', 'enrollment', 'system', 'reminder')),
    related_entity_type VARCHAR(50),
    related_entity_id VARCHAR(255),
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Account activation and security tokens table
CREATE TABLE account_activation_tokens (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(64) NOT NULL,
    token_type VARCHAR(20) NOT NULL DEFAULT 'activation' CHECK (token_type IN ('activation', 'password_reset')),
    expires_at TIMESTAMPTZ NOT NULL,
    used_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_account_status ON users(account_status);
CREATE INDEX idx_users_department ON users(department);
CREATE INDEX idx_users_student_id ON users(student_id);
CREATE INDEX idx_users_employee_id ON users(employee_id);
CREATE INDEX idx_account_tokens_token_hash ON account_activation_tokens(token_hash);
CREATE INDEX idx_account_tokens_user_id ON account_activation_tokens(user_id);
CREATE INDEX idx_subjects_code ON subjects(code);
CREATE INDEX idx_subjects_department ON subjects(department);
CREATE INDEX idx_subjects_year ON subjects(year);
CREATE INDEX idx_student_subjects_student ON student_subjects(student_id);
CREATE INDEX idx_student_subjects_subject ON student_subjects(subject_id);
CREATE INDEX idx_attendance_student ON attendance(student_id);
CREATE INDEX idx_attendance_subject ON attendance(subject_id);
CREATE INDEX idx_attendance_date ON attendance(attendance_date);
CREATE INDEX idx_attendance_student_subject ON attendance(student_id, subject_id);
CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_is_read ON notifications(is_read);
CREATE INDEX idx_notifications_created_at ON notifications(created_at);
CREATE INDEX idx_notifications_user_unread ON notifications(user_id, is_read);

-- Updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to users table
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Seed initial subject catalog (6 required batch subjects)
INSERT INTO subjects (id, name, code, department, year, semester) VALUES
    ('a0000000-0000-0000-0000-000000000001', 'Introduction to Artificial Intelligence', 'IAI', 'Computer Science', 3, 5),
    ('a0000000-0000-0000-0000-000000000002', 'Software Engineering', 'SE', 'Computer Science', 3, 5),
    ('a0000000-0000-0000-0000-000000000003', 'Intelligent Control Systems', 'ISC', 'Computer Science', 3, 5),
    ('a0000000-0000-0000-0000-000000000004', 'Business Economics & Financial Analysis', 'BEFA', 'Computer Science', 3, 5),
    ('a0000000-0000-0000-0000-000000000005', 'Environmental Science', 'ES', 'Computer Science', 3, 5),
    ('a0000000-0000-0000-0000-000000000006', 'Advanced Engineering Laboratory-3', 'AE-3 LAB', 'Computer Science', 3, 5)
ON CONFLICT (code) DO NOTHING;

