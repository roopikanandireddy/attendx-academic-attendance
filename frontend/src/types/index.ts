export interface User {
  id: string;
  full_name: string;
  email: string;
  role: 'student' | 'admin';
  student_id?: string;
  department?: string;
  year?: number;
  section?: string;
  created_at: string;
  updated_at: string;
}

export interface Subject {
  id: string;
  name: string;
  code: string;
  department: string;
  year: number;
  semester: number;
  created_at: string;
}

export interface AttendanceRecord {
  id: string;
  student_id: string;
  subject_id: string;
  attendance_date: string;
  status: 'present' | 'absent';
  marked_by: string;
  created_at: string;
  student_name?: string;
  student_sid?: string;
  subject_name?: string;
  subject_code?: string;
  marker_name?: string;
}

export interface SubjectStats {
  subject_id: string;
  subject_name: string;
  subject_code: string;
  total_classes: number;
  present: number;
  absent: number;
  percentage: number;
}

export interface StudentListItem {
  id: string;
  full_name: string;
  email: string;
  student_id: string;
  department: string;
  year: number;
  section: string;
  role: string;
  attendance_percentage: number;
  total_classes: number;
  present_classes: number;
  created_at: string;
  updated_at: string;
}

export interface StudentDashboardData {
  user: {
    id: string;
    full_name: string;
    email: string;
    student_id: string;
    department: string;
    year: number;
    section: string;
  };
  overall_stats: {
    total_classes: number;
    present: number;
    absent: number;
    percentage: number;
  };
  subjects: SubjectStats[];
  recent_attendance: {
    id: string;
    subject_name: string;
    subject_code: string;
    attendance_date: string;
    status: string;
  }[];
  low_attendance_subjects: (SubjectStats & { classes_needed: number })[];
}

export interface AdminDashboardData {
  total_students: number;
  total_subjects: number;
  todays_attendance: {
    total: number;
    present: number;
    absent: number;
    percentage: number;
  };
  average_attendance: number;
  recent_attendance: {
    id: string;
    student_name: string;
    student_sid: string;
    subject_name: string;
    subject_code: string;
    attendance_date: string;
    status: string;
  }[];
  low_attendance_students: {
    id: string;
    full_name: string;
    student_id: string;
    department: string;
    year: number;
    section: string;
    attendance_percentage: number;
    total_classes: number;
    present: number;
    classes_needed: number;
  }[];
  subject_stats: {
    subject_id: string;
    subject_name: string;
    subject_code: string;
    total_classes: number;
    present: number;
    absent: number;
    percentage: number;
  }[];
  attendance_trend: {
    date: string;
    total: number;
    present: number;
    absent: number;
    percentage: number;
  }[];
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  full_name: string;
  email: string;
  password: string;
  student_id?: string;
  department?: string;
  year?: number;
  section?: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}
