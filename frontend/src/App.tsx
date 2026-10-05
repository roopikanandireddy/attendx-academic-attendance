import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AuthProvider, useAuth } from './context/AuthContext';
import DashboardLayout from './layouts/DashboardLayout';
import AdminLayout from './layouts/AdminLayout';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import AccountActivationPage from './pages/AccountActivationPage';
import ForgotPasswordPage from './pages/ForgotPasswordPage';
import ResetPasswordPage from './pages/ResetPasswordPage';
import StudentDashboard from './pages/StudentDashboard';
import ProfilePage from './pages/ProfilePage';
import MySubjectsPage from './pages/MySubjectsPage';
import MyAttendancePage from './pages/MyAttendancePage';
import AttendanceRecordsPage from './pages/AttendanceRecordsPage';
import LoadingSpinner from './components/LoadingSpinner';
import UnauthorizedState from './components/UnauthorizedState';
import NotificationsPage from './pages/NotificationsPage';
import RoleSelectionPage from './pages/RoleSelectionPage';

// Admin Foundation Pages
import AdminDashboardPage from './pages/admin/AdminDashboardPage';
import AdminStudentsPage from './pages/admin/AdminStudentsPage';
import AdminLecturersPage from './pages/admin/AdminLecturersPage';
import AdminSubjectsPage from './pages/admin/AdminSubjectsPage';
import AdminAssignmentsPage from './pages/admin/AdminAssignmentsPage';
import AdminSectionPlaceholder from './pages/admin/AdminSectionPlaceholder';

import LecturerLayout from './layouts/LecturerLayout';
import LecturerDashboardPage from './pages/lecturer/LecturerDashboardPage';
import LecturerAttendancePage from './pages/lecturer/LecturerAttendancePage';
import LecturerRecordsReportsPage from './pages/lecturer/LecturerRecordsReportsPage';
import LecturerSectionPlaceholder from './pages/lecturer/LecturerSectionPlaceholder';

import {
  ClipboardCheck,
  BarChart3,
  BookOpen,
} from 'lucide-react';

function AdminRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <LoadingSpinner size="lg" text="Verifying admin credentials..." />;
  if (!user) return <Navigate to="/login" replace />;
  if (user.role !== 'admin') {
    return <UnauthorizedState message="You don't have permission to access the Admin Portal." />;
  }
  return <>{children}</>;
}

function LecturerRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <LoadingSpinner size="lg" text="Verifying lecturer credentials..." />;
  if (!user) return <Navigate to="/login" replace />;
  if (user.role !== 'lecturer') {
    return <UnauthorizedState message="You don't have permission to access the Lecturer Portal." />;
  }
  return <>{children}</>;
}

function StudentRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <LoadingSpinner size="lg" text="Loading AttendX..." />;
  if (!user) return <Navigate to="/login" replace />;
  if (user.role !== 'student') {
    if (user.role === 'admin') return <Navigate to="/admin/dashboard" replace />;
    if (user.role === 'lecturer') return <Navigate to="/lecturer/dashboard" replace />;
    return <UnauthorizedState message="You don't have permission to access the Student Portal." />;
  }
  return <>{children}</>;
}

function RootRoute() {
  const { user, loading } = useAuth();
  if (loading) return <LoadingSpinner size="lg" text="Loading AttendX..." />;
  if (user) {
    if (user.role === 'admin') return <Navigate to="/admin/dashboard" replace />;
    if (user.role === 'lecturer') return <Navigate to="/lecturer/dashboard" replace />;
    return <Navigate to="/dashboard" replace />;
  }
  return <RoleSelectionPage />;
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Toaster
          position="top-right"
          toastOptions={{
            duration: 3000,
            style: { fontSize: '0.875rem', borderRadius: '0.5rem', padding: '0.75rem 1rem' },
          }}
        />
        <Routes>
          {/* Root role-selection landing page for visitors / dashboard redirect for authenticated users */}
          <Route path="/" element={<RootRoute />} />

          {/* Public authentication routes */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/activate-account" element={<AccountActivationPage />} />
          <Route path="/forgot-password" element={<ForgotPasswordPage />} />
          <Route path="/reset-password" element={<ResetPasswordPage />} />

          {/* Role-specific login route aliases */}
          <Route path="/student/login" element={<Navigate to="/login?role=student" replace />} />
          <Route path="/lecturer/login" element={<Navigate to="/login?role=lecturer" replace />} />
          <Route path="/admin/login" element={<Navigate to="/login?role=admin" replace />} />

          {/* Registration route aliases */}
          <Route path="/student/register" element={<Navigate to="/register" replace />} />
          <Route path="/lecturer/register" element={<Navigate to="/register" replace />} />
          <Route path="/admin/register" element={<Navigate to="/register" replace />} />

          {/* Dashboard route aliases */}
          <Route path="/student/dashboard" element={<Navigate to="/dashboard" replace />} />

          {/* Student routes — 100% preserved */}
          <Route element={<DashboardLayout />}>
            <Route path="/dashboard" element={<StudentRoute><StudentDashboard /></StudentRoute>} />
            <Route path="/my-subjects" element={<StudentRoute><MySubjectsPage /></StudentRoute>} />
            <Route path="/my-attendance" element={<StudentRoute><MyAttendancePage /></StudentRoute>} />
            <Route path="/attendance-history" element={<StudentRoute><AttendanceRecordsPage /></StudentRoute>} />
            <Route path="/notifications" element={<StudentRoute><NotificationsPage /></StudentRoute>} />
            <Route path="/profile" element={<StudentRoute><ProfilePage /></StudentRoute>} />
          </Route>

          {/* Admin routes — Module A1 Foundation */}
          <Route
            element={
              <AdminRoute>
                <AdminLayout />
              </AdminRoute>
            }
          >
            <Route path="/admin/dashboard" element={<AdminDashboardPage />} />
            <Route path="/admin/students" element={<AdminStudentsPage />} />
            <Route path="/admin/lecturers" element={<AdminLecturersPage />} />
            <Route path="/admin/subjects" element={<AdminSubjectsPage />} />
            <Route path="/admin/assignments" element={<AdminAssignmentsPage />} />
            <Route
              path="/admin/attendance"
              element={
                <AdminSectionPlaceholder
                  title="Attendance"
                  category="Attendance"
                  description="Review and verify attendance records across departments."
                  icon={ClipboardCheck}
                  plannedFeatures={[
                    'Daily attendance session records',
                    'Attendance status verification and adjustments',
                    'Multi-department attendance review',
                    'Automated low attendance warning flags',
                  ]}
                />
              }
            />
            <Route
              path="/admin/reports"
              element={
                <AdminSectionPlaceholder
                  title="Reports"
                  category="Attendance"
                  description="Generate institutional attendance summaries and analytics."
                  icon={BarChart3}
                  plannedFeatures={[
                    'Institutional attendance percentage breakdown',
                    'Departmental comparison metrics',
                    'Exportable attendance audit sheets',
                    'Low-attendance student intervention logs',
                  ]}
                />
              }
            />
            <Route path="/admin/notifications" element={<NotificationsPage />} />
            <Route path="/admin/profile" element={<ProfilePage />} />
          </Route>

          {/* Lecturer routes — Module L1 Foundation */}
          <Route
            element={
              <LecturerRoute>
                <LecturerLayout />
              </LecturerRoute>
            }
          >
            <Route path="/lecturer/dashboard" element={<LecturerDashboardPage />} />
            <Route
              path="/lecturer/subjects"
              element={
                <LecturerSectionPlaceholder
                  title="My Subjects"
                  category="Teaching Workspace"
                  description="View courses and student rosters assigned to your faculty profile."
                  icon={BookOpen}
                  plannedFeatures={[
                    'Assigned course list with department and semester breakdown',
                    'Enrolled student roster viewing with student IDs',
                    'Subject-level attendance summary aggregates',
                    'Roster export and student details inspection',
                  ]}
                />
              }
            />
            <Route
              path="/lecturer/attendance"
              element={<LecturerAttendancePage />}
            />
            <Route
              path="/lecturer/reports"
              element={<LecturerRecordsReportsPage />}
            />
            <Route
              path="/lecturer/records"
              element={<Navigate to="/lecturer/reports" replace />}
            />
            <Route path="/lecturer/notifications" element={<NotificationsPage />} />
            <Route path="/lecturer/profile" element={<ProfilePage />} />
          </Route>

          {/* Catch all */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
