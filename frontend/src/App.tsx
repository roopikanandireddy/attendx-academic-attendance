import { lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AuthProvider, useAuth } from './context/AuthContext';
import LoadingSpinner from './components/LoadingSpinner';
import UnauthorizedState from './components/UnauthorizedState';
import RouteErrorBoundary from './components/RouteErrorBoundary';
import RouteLoadingFallback from './components/RouteLoadingFallback';

import {
  ClipboardCheck,
  BarChart3,
  BookOpen,
} from 'lucide-react';

// Lazy Layouts
const DashboardLayout = lazy(() => import('./layouts/DashboardLayout'));
const AdminLayout = lazy(() => import('./layouts/AdminLayout'));
const LecturerLayout = lazy(() => import('./layouts/LecturerLayout'));

// Lazy Public Auth Pages
const LoginPage = lazy(() => import('./pages/LoginPage'));
const RegisterPage = lazy(() => import('./pages/RegisterPage'));
const AccountActivationPage = lazy(() => import('./pages/AccountActivationPage'));
const ForgotPasswordPage = lazy(() => import('./pages/ForgotPasswordPage'));
const ResetPasswordPage = lazy(() => import('./pages/ResetPasswordPage'));
const RoleSelectionPage = lazy(() => import('./pages/RoleSelectionPage'));

// Lazy Student Pages
const StudentDashboard = lazy(() => import('./pages/StudentDashboard'));
const ProfilePage = lazy(() => import('./pages/ProfilePage'));
const MySubjectsPage = lazy(() => import('./pages/MySubjectsPage'));
const MyAttendancePage = lazy(() => import('./pages/MyAttendancePage'));
const AttendanceRecordsPage = lazy(() => import('./pages/AttendanceRecordsPage'));
const NotificationsPage = lazy(() => import('./pages/NotificationsPage'));

// Lazy Admin Pages
const AdminDashboardPage = lazy(() => import('./pages/admin/AdminDashboardPage'));
const AdminStudentsPage = lazy(() => import('./pages/admin/AdminStudentsPage'));
const AdminLecturersPage = lazy(() => import('./pages/admin/AdminLecturersPage'));
const AdminSubjectsPage = lazy(() => import('./pages/admin/AdminSubjectsPage'));
const AdminAssignmentsPage = lazy(() => import('./pages/admin/AdminAssignmentsPage'));
const AdminSectionPlaceholder = lazy(() => import('./pages/admin/AdminSectionPlaceholder'));

// Lazy Lecturer Pages
const LecturerDashboardPage = lazy(() => import('./pages/lecturer/LecturerDashboardPage'));
const LecturerAttendancePage = lazy(() => import('./pages/lecturer/LecturerAttendancePage'));
const LecturerRecordsReportsPage = lazy(() => import('./pages/lecturer/LecturerRecordsReportsPage'));
const LecturerSectionPlaceholder = lazy(() => import('./pages/lecturer/LecturerSectionPlaceholder'));

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
  return (
    <Suspense fallback={<RouteLoadingFallback variant="page" text="Loading AttendX..." />}>
      <RoleSelectionPage />
    </Suspense>
  );
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
        <RouteErrorBoundary>
          <Routes>
            {/* Root role-selection landing page for visitors / dashboard redirect for authenticated users */}
            <Route path="/" element={<RootRoute />} />

            {/* Public authentication routes */}
            <Route
              path="/login"
              element={
                <Suspense fallback={<RouteLoadingFallback variant="page" text="Loading login..." />}>
                  <LoginPage />
                </Suspense>
              }
            />
            <Route
              path="/register"
              element={
                <Suspense fallback={<RouteLoadingFallback variant="page" text="Loading registration..." />}>
                  <RegisterPage />
                </Suspense>
              }
            />
            <Route
              path="/activate-account"
              element={
                <Suspense fallback={<RouteLoadingFallback variant="page" text="Loading account activation..." />}>
                  <AccountActivationPage />
                </Suspense>
              }
            />
            <Route
              path="/forgot-password"
              element={
                <Suspense fallback={<RouteLoadingFallback variant="page" text="Loading password recovery..." />}>
                  <ForgotPasswordPage />
                </Suspense>
              }
            />
            <Route
              path="/reset-password"
              element={
                <Suspense fallback={<RouteLoadingFallback variant="page" text="Loading password reset..." />}>
                  <ResetPasswordPage />
                </Suspense>
              }
            />

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
            <Route
              element={
                <StudentRoute>
                  <Suspense fallback={<RouteLoadingFallback variant="page" text="Loading Student Workspace..." />}>
                    <DashboardLayout />
                  </Suspense>
                </StudentRoute>
              }
            >
              <Route
                path="/dashboard"
                element={
                  <Suspense fallback={<RouteLoadingFallback variant="dashboard" text="Loading Dashboard..." />}>
                    <StudentDashboard />
                  </Suspense>
                }
              />
              <Route
                path="/my-subjects"
                element={
                  <Suspense fallback={<RouteLoadingFallback variant="table" text="Loading Subjects..." />}>
                    <MySubjectsPage />
                  </Suspense>
                }
              />
              <Route
                path="/my-attendance"
                element={
                  <Suspense fallback={<RouteLoadingFallback variant="dashboard" text="Loading Attendance..." />}>
                    <MyAttendancePage />
                  </Suspense>
                }
              />
              <Route
                path="/attendance-history"
                element={
                  <Suspense fallback={<RouteLoadingFallback variant="table" text="Loading Attendance Records..." />}>
                    <AttendanceRecordsPage />
                  </Suspense>
                }
              />
              <Route
                path="/notifications"
                element={
                  <Suspense fallback={<RouteLoadingFallback variant="page" text="Loading Notifications..." />}>
                    <NotificationsPage />
                  </Suspense>
                }
              />
              <Route
                path="/profile"
                element={
                  <Suspense fallback={<RouteLoadingFallback variant="page" text="Loading Profile..." />}>
                    <ProfilePage />
                  </Suspense>
                }
              />
            </Route>

            {/* Admin routes — Module A1 Foundation */}
            <Route
              element={
                <AdminRoute>
                  <Suspense fallback={<RouteLoadingFallback variant="page" text="Loading Admin Portal..." />}>
                    <AdminLayout />
                  </Suspense>
                </AdminRoute>
              }
            >
              <Route
                path="/admin/dashboard"
                element={
                  <Suspense fallback={<RouteLoadingFallback variant="dashboard" text="Loading Admin Dashboard..." />}>
                    <AdminDashboardPage />
                  </Suspense>
                }
              />
              <Route
                path="/admin/students"
                element={
                  <Suspense fallback={<RouteLoadingFallback variant="table" text="Loading Student Management..." />}>
                    <AdminStudentsPage />
                  </Suspense>
                }
              />
              <Route
                path="/admin/lecturers"
                element={
                  <Suspense fallback={<RouteLoadingFallback variant="table" text="Loading Faculty Management..." />}>
                    <AdminLecturersPage />
                  </Suspense>
                }
              />
              <Route
                path="/admin/subjects"
                element={
                  <Suspense fallback={<RouteLoadingFallback variant="table" text="Loading Subject Catalog..." />}>
                    <AdminSubjectsPage />
                  </Suspense>
                }
              />
              <Route
                path="/admin/assignments"
                element={
                  <Suspense fallback={<RouteLoadingFallback variant="table" text="Loading Faculty Assignments..." />}>
                    <AdminAssignmentsPage />
                  </Suspense>
                }
              />
              <Route
                path="/admin/attendance"
                element={
                  <Suspense fallback={<RouteLoadingFallback variant="table" text="Loading Attendance Review..." />}>
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
                  </Suspense>
                }
              />
              <Route
                path="/admin/reports"
                element={
                  <Suspense fallback={<RouteLoadingFallback variant="dashboard" text="Loading Reports..." />}>
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
                  </Suspense>
                }
              />
              <Route
                path="/admin/notifications"
                element={
                  <Suspense fallback={<RouteLoadingFallback variant="page" text="Loading Notifications..." />}>
                    <NotificationsPage />
                  </Suspense>
                }
              />
              <Route
                path="/admin/profile"
                element={
                  <Suspense fallback={<RouteLoadingFallback variant="page" text="Loading Profile..." />}>
                    <ProfilePage />
                  </Suspense>
                }
              />
            </Route>

            {/* Lecturer routes — Module L1 Foundation */}
            <Route
              element={
                <LecturerRoute>
                  <Suspense fallback={<RouteLoadingFallback variant="page" text="Loading Lecturer Portal..." />}>
                    <LecturerLayout />
                  </Suspense>
                </LecturerRoute>
              }
            >
              <Route
                path="/lecturer/dashboard"
                element={
                  <Suspense fallback={<RouteLoadingFallback variant="dashboard" text="Loading Lecturer Dashboard..." />}>
                    <LecturerDashboardPage />
                  </Suspense>
                }
              />
              <Route
                path="/lecturer/subjects"
                element={
                  <Suspense fallback={<RouteLoadingFallback variant="table" text="Loading Assigned Subjects..." />}>
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
                  </Suspense>
                }
              />
              <Route
                path="/lecturer/attendance"
                element={
                  <Suspense fallback={<RouteLoadingFallback variant="table" text="Loading Attendance Session..." />}>
                    <LecturerAttendancePage />
                  </Suspense>
                }
              />
              <Route
                path="/lecturer/reports"
                element={
                  <Suspense fallback={<RouteLoadingFallback variant="table" text="Loading Records & Reports..." />}>
                    <LecturerRecordsReportsPage />
                  </Suspense>
                }
              />
              <Route
                path="/lecturer/records"
                element={<Navigate to="/lecturer/reports" replace />}
              />
              <Route
                path="/lecturer/notifications"
                element={
                  <Suspense fallback={<RouteLoadingFallback variant="page" text="Loading Notifications..." />}>
                    <NotificationsPage />
                  </Suspense>
                }
              />
              <Route
                path="/lecturer/profile"
                element={
                  <Suspense fallback={<RouteLoadingFallback variant="page" text="Loading Profile..." />}>
                    <ProfilePage />
                  </Suspense>
                }
              />
            </Route>

            {/* Catch all */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </RouteErrorBoundary>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
