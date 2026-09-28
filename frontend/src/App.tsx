import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AuthProvider, useAuth } from './context/AuthContext';
import DashboardLayout from './layouts/DashboardLayout';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import StudentDashboard from './pages/StudentDashboard';
import AdminDashboard from './pages/AdminDashboard';
import StudentsPage from './pages/StudentsPage';
import SubjectsPage from './pages/SubjectsPage';
import MarkAttendancePage from './pages/MarkAttendancePage';
import AttendanceRecordsPage from './pages/AttendanceRecordsPage';
import ReportsPage from './pages/ReportsPage';
import ProfilePage from './pages/ProfilePage';
import MySubjectsPage from './pages/MySubjectsPage';
import MyAttendancePage from './pages/MyAttendancePage';
import LoadingSpinner from './components/LoadingSpinner';

function AdminRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <LoadingSpinner size="lg" />;
  if (!user) return <Navigate to="/login" replace />;
  if (user.role !== 'admin') return <Navigate to="/dashboard" replace />;
  return <>{children}</>;
}

function StudentRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <LoadingSpinner size="lg" />;
  if (!user) return <Navigate to="/login" replace />;
  if (user.role !== 'student') return <Navigate to="/admin/dashboard" replace />;
  return <>{children}</>;
}

function RootRedirect() {
  const { user, loading } = useAuth();
  if (loading) return <LoadingSpinner size="lg" />;
  if (!user) return <Navigate to="/login" replace />;
  return <Navigate to={user.role === 'admin' ? '/admin/dashboard' : '/dashboard'} replace />;
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
          {/* Public routes */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />

          {/* Root redirect */}
          <Route path="/" element={<RootRedirect />} />

          {/* Student routes */}
          <Route element={<DashboardLayout />}>
            <Route path="/dashboard" element={<StudentRoute><StudentDashboard /></StudentRoute>} />
            <Route path="/my-subjects" element={<StudentRoute><MySubjectsPage /></StudentRoute>} />
            <Route path="/my-attendance" element={<StudentRoute><MyAttendancePage /></StudentRoute>} />
            <Route path="/attendance-history" element={<StudentRoute><AttendanceRecordsPage /></StudentRoute>} />
            <Route path="/profile" element={<ProfilePage />} />

            {/* Admin routes */}
            <Route path="/admin/dashboard" element={<AdminRoute><AdminDashboard /></AdminRoute>} />
            <Route path="/admin/students" element={<AdminRoute><StudentsPage /></AdminRoute>} />
            <Route path="/admin/subjects" element={<AdminRoute><SubjectsPage /></AdminRoute>} />
            <Route path="/admin/mark-attendance" element={<AdminRoute><MarkAttendancePage /></AdminRoute>} />
            <Route path="/admin/attendance-records" element={<AdminRoute><AttendanceRecordsPage /></AdminRoute>} />
            <Route path="/admin/reports" element={<AdminRoute><ReportsPage /></AdminRoute>} />
          </Route>

          {/* Catch all */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
