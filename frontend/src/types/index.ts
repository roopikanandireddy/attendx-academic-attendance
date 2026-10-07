export type UserRole = 'student' | 'lecturer' | 'admin';

export interface User {
  id: string;
  full_name: string;
  email: string;
  role: UserRole;
  student_id?: string;
  employee_id?: string;
  department?: string;
  year?: number;
  section?: string;
  is_active?: boolean;
  account_status?: string;
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
  is_active?: boolean;
  account_status?: string;
  status?: string;
  attendance_percentage: number;
  total_classes: number;
  present_classes: number;
  absent_classes?: number;
  created_at: string;
  updated_at: string;
}

export interface StudentSummaryMetrics {
  total_students: number;
  active_students: number;
  inactive_students: number;
  below_threshold_students: number;
}

export interface StudentListResponse {
  items: StudentListItem[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

export interface StudentDetailResponse {
  id: string;
  student_id: string;
  full_name: string;
  email: string;
  role: string;
  department: string;
  year: number;
  section: string;
  is_active: boolean;
  account_status?: string;
  status: string;
  created_at?: string;
  updated_at?: string;
  attendance_summary: {
    total_classes: number;
    present: number;
    absent: number;
    percentage: number;
  };
  subjects_attendance: {
    subject_id: string;
    subject_name: string;
    subject_code: string;
    department: string;
    year: number;
    semester: number;
    total_classes: number;
    present: number;
    absent: number;
    percentage: number;
  }[];
  enrollments: {
    id: string;
    subject_id: string;
    created_at?: string;
  }[];
}

export interface LecturerListItem {
  id: string;
  employee_id: string;
  full_name: string;
  email: string;
  department: string;
  role: string;
  is_active: boolean;
  account_status?: string;
  status: string;
  assigned_subjects_count: number;
  created_at: string;
  updated_at: string;
}

export interface LecturerSummaryMetrics {
  total_lecturers: number;
  active_lecturers: number;
  inactive_lecturers: number;
  lecturers_with_assignments: number;
}

export interface LecturerListResponse {
  items: LecturerListItem[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

export interface LecturerAssignedSubject {
  id: string;
  name: string;
  code: string;
  department: string;
  status?: string;
}

export interface LecturerDetailResponse {
  id: string;
  employee_id: string;
  full_name: string;
  email: string;
  department: string;
  role: string;
  is_active: boolean;
  status: string;
  created_at?: string;
  updated_at?: string;
  assigned_subjects_count: number;
  assigned_subjects: LecturerAssignedSubject[];
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

export interface RecentActivityItem {
  id: string;
  title: string;
  description: string;
  type: 'attendance' | 'enrollment' | 'system';
  status?: string;
  timestamp: string;
}

export interface AdminDashboardData {
  total_students: number;
  total_lecturers: number;
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
    subject?: string;
    attendance_percentage: number;
    total_classes: number;
    present: number;
    status?: string;
    classes_needed: number;
  }[];
  subject_stats: SubjectStats[];
  attendance_overview?: SubjectStats[];
  attendance_trend: {
    date: string;
    total: number;
    present: number;
    absent: number;
    percentage: number;
  }[];
  recent_activity?: RecentActivityItem[];
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

export type NotificationType = 'attendance' | 'low_attendance' | 'enrollment' | 'system' | 'reminder';

export interface NotificationItem {
  id: string;
  user_id: string;
  title: string;
  message: string;
  type: NotificationType;
  related_entity_type?: string | null;
  related_entity_id?: string | null;
  is_read: boolean;
  created_at: string;
}

export interface UnreadCountResponse {
  count: number;
}

export interface SubjectSummaryMetrics {
  total_subjects: number;
  assigned_subjects: number;
  unassigned_subjects: number;
  total_enrollments: number;
}

export interface AssignedLecturerInfo {
  id: string;
  full_name: string;
  email: string;
  employee_id?: string;
  department?: string;
  assignment_id?: string;
}

export interface EnrolledStudentInfo {
  id: string;
  full_name: string;
  email: string;
  student_id?: string;
  department?: string;
  year?: number;
  section?: string;
  enrollment_id: string;
}

export interface SubjectListItem {
  id: string;
  name: string;
  code: string;
  department: string;
  year: number;
  semester: number;
  assigned_lecturers: AssignedLecturerInfo[];
  assigned_lecturers_count: number;
  enrolled_students_count: number;
  created_at: string;
}

export interface SubjectListResponse {
  items: SubjectListItem[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

export interface SubjectDetailResponse {
  id: string;
  name: string;
  code: string;
  department: string;
  year: number;
  semester: number;
  assigned_lecturers: AssignedLecturerInfo[];
  assigned_lecturers_count: number;
  enrolled_students: EnrolledStudentInfo[];
  enrolled_students_count: number;
  created_at: string;
}

export interface AssignmentSummaryMetrics {
  total_assignments: number;
  assigned_lecturers: number;
  assigned_subjects: number;
  unassigned_subjects: number;
}

export interface LecturerAssignmentItem {
  id: string;
  lecturer_id: string;
  subject_id: string;
  lecturer_name: string;
  lecturer_email: string;
  lecturer_employee_id?: string;
  lecturer_department?: string;
  subject_name: string;
  subject_code: string;
  subject_department: string;
  subject_year: number;
  subject_semester: number;
  created_at: string;
}

export interface AssignmentListResponse {
  items: LecturerAssignmentItem[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

export interface LecturerDashboardProfile {
  id: string;
  name?: string;
  full_name: string;
  email: string;
  employee_id?: string;
  department?: string;
  role: string;
}

export interface LecturerDashboardMetrics {
  total_subjects: number;
  total_students: number;
  total_attendance_records: number;
  attendance_records?: number;
  average_attendance: number;
}

export interface LecturerDashboardSubject {
  id: string;
  name: string;
  code: string;
  department: string;
  year: number;
  semester: number;
  enrolled_students: number;
  total_classes: number;
  present: number;
  absent: number;
  attendance_percentage: number;
  has_attendance: boolean;
}

export interface LecturerAttendanceOverview {
  total_classes: number;
  present: number;
  absent: number;
  percentage: number;
  has_data: boolean;
}

export interface LecturerRecentActivityItem {
  id: string;
  student_name: string;
  student_sid?: string;
  subject_name: string;
  subject_code: string;
  attendance_date: string;
  status: string;
  created_at?: string;
}

export interface LecturerDashboardData {
  lecturer: LecturerDashboardProfile;
  summary: LecturerDashboardMetrics;
  subjects: LecturerDashboardSubject[];
  attendance_overview: LecturerAttendanceOverview;
  recent_activity: LecturerRecentActivityItem[];
  unread_notifications_count: number;
}

export interface LecturerAssignedSubjectItem {
  id: string;
  name: string;
  code: string;
  department: string;
  year: number;
  semester: number;
  enrolled_students_count: number;
}

export interface LecturerSessionStudentItem {
  student_id: string;
  full_name: string;
  student_sid?: string;
  department?: string;
  status?: 'present' | 'absent' | null;
  attendance_id?: string | null;
}

export interface LecturerAttendanceSessionResponse {
  subject_id: string;
  subject_code: string;
  subject_name: string;
  department: string;
  attendance_date: string;
  has_existing_records: boolean;
  total_students: number;
  present_count: number;
  absent_count: number;
  unmarked_count: number;
  students: LecturerSessionStudentItem[];
}

export interface LecturerAttendanceBulkResult {
  message: string;
  subject_id: string;
  subject_code: string;
  attendance_date: string;
  total_processed: number;
  created_count: number;
  updated_count: number;
  present_count: number;
  absent_count: number;
}

export interface LecturerRecordsSummary {
  total_students: number;
  total_records: number;
  present_count: number;
  absent_count: number;
  attendance_percentage: number;
}

export interface LecturerRecordItem {
  id: string;
  student_id: string;
  student_name: string;
  student_sid?: string;
  student_department?: string;
  subject_id: string;
  subject_name: string;
  subject_code: string;
  attendance_date: string;
  status: 'present' | 'absent';
  marked_by: string;
  created_at?: string;
}

export interface LecturerRecordsResponse {
  summary: LecturerRecordsSummary;
  records: LecturerRecordItem[];
  page: number;
  limit: number;
  total: number;
  total_pages: number;
}

export interface LecturerStudentSessionItem {
  id: string;
  attendance_date: string;
  subject_id: string;
  subject_name: string;
  subject_code: string;
  status: 'present' | 'absent';
  created_at?: string;
}

export interface LecturerStudentSubjectBreakdown {
  subject_id: string;
  subject_name: string;
  subject_code: string;
  total_classes: number;
  present: number;
  absent: number;
  percentage: number;
}

export interface LecturerStudentReportResponse {
  student_id: string;
  student_name: string;
  student_sid?: string;
  email: string;
  department?: string;
  year?: number;
  section?: string;
  total_classes: number;
  present: number;
  absent: number;
  percentage: number;
  subject_breakdown: LecturerStudentSubjectBreakdown[];
  history: LecturerStudentSessionItem[];
}

export interface LecturerSubjectStudentBreakdown {
  student_id: string;
  student_name: string;
  student_sid?: string;
  email: string;
  department?: string;
  year?: number;
  section?: string;
  total_classes: number;
  present: number;
  absent: number;
  percentage: number;
}

export interface LecturerSubjectDailySession {
  attendance_date: string;
  total_students: number;
  present: number;
  absent: number;
  percentage: number;
}

export interface LecturerSubjectReportResponse {
  subject_id: string;
  subject_name: string;
  subject_code: string;
  department: string;
  year: number;
  semester: number;
  total_students: number;
  total_records: number;
  total_sessions: number;
  present: number;
  absent: number;
  percentage: number;
  students: LecturerSubjectStudentBreakdown[];
  sessions: LecturerSubjectDailySession[];
}

export interface EmailDeliveryInfo {
  success: boolean;
  status: string;
  error_code?: string | null;
  message: string;
}
