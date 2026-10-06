import { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import api, { isRequestCancelled } from '../../services/api';
import type { AdminDashboardData } from '../../types';
import { DashboardSkeleton } from '../../components/Skeleton';
import ErrorState from '../../components/ErrorState';
import {
  Users,
  GraduationCap,
  BookOpen,
  CalendarCheck,
  TrendingUp,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Layers,
  ClipboardCheck,
  BarChart3,
  UserPlus,
  BookPlus,
  ArrowRight,
  RotateCw,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';

export default function AdminDashboardPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [data, setData] = useState<AdminDashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const fetchDashboardData = useCallback(async (isManualRefresh = false, signal?: AbortSignal) => {
    if (isManualRefresh) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }
    setError(null);

    try {
      // Use existing API service with authentication interceptor
      const res = await api.get<AdminDashboardData>('/api/admin/dashboard', { signal });
      setData(res.data);
    } catch (err: any) {
      if (isRequestCancelled(err)) return;
      const msg =
        err.response?.data?.detail ||
        err.message ||
        'Unable to load dashboard data. Please try again.';
      setError(msg);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    fetchDashboardData(false, controller.signal);
    return () => {
      controller.abort();
    };
  }, [fetchDashboardData]);

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 17) return 'Good afternoon';
    return 'Good evening';
  };

  if (loading) {
    return <DashboardSkeleton />;
  }

  if (error || !data) {
    return (
      <div className="space-y-6">
        <ErrorState
          title="Unable to load dashboard data"
          message={error || 'An unexpected error occurred while communicating with the server.'}
          onRetry={() => fetchDashboardData(false)}
        />
      </div>
    );
  }

  // Summary card definitions matching Section 2 requirements
  const summaryCards = [
    {
      title: 'Total Students',
      value: data.total_students,
      subtext: 'Active student accounts',
      icon: Users,
      color: 'from-blue-600 to-blue-700',
      bgColor: 'bg-blue-50 text-blue-700',
    },
    {
      title: 'Total Lecturers',
      value: data.total_lecturers,
      subtext: 'Active faculty members',
      icon: GraduationCap,
      color: 'from-indigo-600 to-indigo-700',
      bgColor: 'bg-indigo-50 text-indigo-700',
    },
    {
      title: 'Total Subjects',
      value: data.total_subjects,
      subtext: 'Curriculum course subjects',
      icon: BookOpen,
      color: 'from-emerald-600 to-emerald-700',
      bgColor: 'bg-emerald-50 text-emerald-700',
    },
    {
      title: "Today's Attendance",
      value: data.todays_attendance.total > 0 ? `${data.todays_attendance.percentage}%` : '—',
      subtext:
        data.todays_attendance.total > 0
          ? `${data.todays_attendance.present}/${data.todays_attendance.total} sessions present`
          : 'No sessions recorded today',
      icon: CalendarCheck,
      color: 'from-amber-600 to-amber-700',
      bgColor: 'bg-amber-50 text-amber-700',
    },
    {
      title: 'Average Attendance',
      value: `${data.average_attendance}%`,
      subtext: 'Overall institutional attendance rate',
      icon: TrendingUp,
      color: 'from-violet-600 to-violet-700',
      bgColor: 'bg-violet-50 text-violet-700',
    },
  ];

  // Quick action definitions matching Section 7 requirements
  const quickActions = [
    { label: 'Add Student', icon: UserPlus, to: '/admin/students', color: 'bg-blue-50 text-blue-700 hover:bg-blue-100' },
    { label: 'Add Lecturer', icon: GraduationCap, to: '/admin/lecturers', color: 'bg-indigo-50 text-indigo-700 hover:bg-indigo-100' },
    { label: 'Add Subject', icon: BookPlus, to: '/admin/subjects', color: 'bg-emerald-50 text-emerald-700 hover:bg-emerald-100' },
    { label: 'Assign Lecturer', icon: Layers, to: '/admin/assignments', color: 'bg-cyan-50 text-cyan-700 hover:bg-cyan-100' },
    { label: 'View Attendance', icon: ClipboardCheck, to: '/admin/attendance', color: 'bg-amber-50 text-amber-700 hover:bg-amber-100' },
    { label: 'View Reports', icon: BarChart3, to: '/admin/reports', color: 'bg-violet-50 text-violet-700 hover:bg-violet-100' },
  ];

  const statsList = data.attendance_overview || data.subject_stats || [];
  const chartData = statsList.map((s) => ({
    name: s.subject_code || s.subject_name,
    fullName: s.subject_name,
    percentage: s.percentage,
    present: s.present,
    absent: s.absent,
    total: s.total_classes,
  }));

  return (
    <div className="space-y-6 fade-in">
      {/* Top Header Section */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-2 border-b border-surface-200">
        <div>
          <h1 className="text-2xl font-bold text-surface-900 tracking-tight">
            {getGreeting()}, {user?.full_name || 'Administrator'}
          </h1>
          <p className="text-sm text-surface-500 mt-0.5">
            Here's your attendance management overview
          </p>
        </div>
        <div className="flex items-center gap-2 self-start sm:self-auto">
          <button
            onClick={() => fetchDashboardData(true)}
            disabled={refreshing}
            className="btn btn-secondary btn-sm flex items-center gap-1.5 focus:outline-none focus:ring-2 focus:ring-primary-500/50"
            aria-label="Refresh dashboard data"
          >
            <RotateCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin' : ''}`} />
            <span>{refreshing ? 'Updating...' : 'Refresh'}</span>
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        {summaryCards.map((card, i) => (
          <div
            key={i}
            className="card card-hover p-4 flex flex-col justify-between border border-surface-200 shadow-xs"
          >
            <div className="flex items-start justify-between mb-3">
              <span className="text-xs font-semibold uppercase tracking-wider text-surface-500">
                {card.title}
              </span>
              <div
                className={`w-9 h-9 rounded-xl flex items-center justify-center ${card.bgColor} shadow-xs`}
              >
                <card.icon className="w-4 h-4" aria-hidden="true" />
              </div>
            </div>
            <div>
              <p className="text-2xl font-bold text-surface-900 tracking-tight">
                {card.value}
              </p>
              <p className="text-xs text-surface-400 mt-1 truncate">
                {card.subtext}
              </p>
            </div>
          </div>
        ))}
      </div>

      {/* Today's Attendance Overview & Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Today's Attendance Overview */}
        <div className="card border border-surface-200 p-5 lg:col-span-1 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-base font-bold text-surface-900">
                Today's Attendance Overview
              </h3>
              <span className="badge badge-primary text-xs">
                {new Date().toLocaleDateString(undefined, {
                  month: 'short',
                  day: 'numeric',
                })}
              </span>
            </div>
            {data.todays_attendance.total > 0 ? (
              <div className="space-y-4">
                <div className="flex items-center justify-between p-3 rounded-xl bg-surface-50 border border-surface-100">
                  <span className="text-xs text-surface-600 font-medium">Total Sessions</span>
                  <span className="text-sm font-bold text-surface-900">
                    {data.todays_attendance.total}
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-100">
                    <p className="text-[0.68rem] text-emerald-700 font-semibold uppercase tracking-wider">
                      Present
                    </p>
                    <p className="text-lg font-bold text-emerald-800 mt-0.5">
                      {data.todays_attendance.present}
                    </p>
                  </div>
                  <div className="p-3 rounded-xl bg-red-50 border border-red-100">
                    <p className="text-[0.68rem] text-red-700 font-semibold uppercase tracking-wider">
                      Absent
                    </p>
                    <p className="text-lg font-bold text-red-800 mt-0.5">
                      {data.todays_attendance.absent}
                    </p>
                  </div>
                </div>
                <div>
                  <div className="flex items-center justify-between text-xs mb-1.5">
                    <span className="text-surface-500 font-medium">Attendance Rate</span>
                    <span className="font-bold text-surface-800">
                      {data.todays_attendance.percentage}%
                    </span>
                  </div>
                  <div className="w-full bg-surface-200 rounded-full h-2 overflow-hidden">
                    <div
                      className="bg-emerald-500 h-2 rounded-full transition-all duration-500"
                      style={{ width: `${Math.min(100, data.todays_attendance.percentage)}%` }}
                    />
                  </div>
                </div>
              </div>
            ) : (
              <div className="py-8 text-center text-surface-400">
                <CalendarCheck className="w-10 h-10 mx-auto mb-2 text-surface-300" aria-hidden="true" />
                <p className="text-sm font-medium text-surface-600">
                  No attendance recorded today.
                </p>
                <p className="text-xs text-surface-400 mt-1 max-w-xs mx-auto">
                  Attendance logged by administrators or faculty today will appear here in real-time.
                </p>
              </div>
            )}
          </div>
          <div className="pt-3 mt-4 border-t border-surface-100 flex items-center justify-between">
            <span className="text-xs text-surface-400">Manage logs</span>
            <button
              onClick={() => navigate('/admin/attendance')}
              className="text-xs font-semibold text-primary-600 hover:text-primary-800 flex items-center gap-1"
            >
              Attendance Records
              <ArrowRight className="w-3 h-3" />
            </button>
          </div>
        </div>

        {/* Quick Actions Panel */}
        <div className="card border border-surface-200 p-5 lg:col-span-2 flex flex-col justify-between">
          <div>
            <h3 className="text-base font-bold text-surface-900 mb-1">
              Quick Administrative Actions
            </h3>
            <p className="text-xs text-surface-500 mb-4">
              Direct shortcuts to university management modules
            </p>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              {quickActions.map((action) => (
                <button
                  key={action.label}
                  onClick={() => navigate(action.to)}
                  className={`flex items-center gap-2.5 p-3 rounded-xl border border-surface-200/80 ${action.color} text-left font-medium text-xs transition-all duration-200 hover:shadow-xs group focus:outline-none focus:ring-2 focus:ring-primary-500/50`}
                >
                  <action.icon className="w-4 h-4 flex-shrink-0 group-hover:scale-110 transition-transform duration-200" aria-hidden="true" />
                  <span className="truncate">{action.label}</span>
                </button>
              ))}
            </div>
          </div>
          <div className="pt-3 mt-4 border-t border-surface-100 flex items-center justify-between text-xs text-surface-400">
            <span>All buttons route to established protected pages</span>
            <span className="font-medium text-surface-600">AttendX Admin Shell</span>
          </div>
        </div>
      </div>

      {/* Attendance Overview Chart */}
      <div className="card border border-surface-200 p-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4">
          <div>
            <h3 className="text-base font-bold text-surface-900">
              Subject Attendance Overview
            </h3>
            <p className="text-xs text-surface-500">
              Real-time attendance performance per academic curriculum course
            </p>
          </div>
          <span className="text-xs text-surface-400 bg-surface-100 px-2.5 py-1 rounded-md">
            {chartData.length} Subjects Tracked
          </span>
        </div>

        {chartData.length > 0 ? (
          <div className="w-full h-72 sm:h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={chartData}
                margin={{ top: 10, right: 10, left: -20, bottom: 20 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                <XAxis
                  dataKey="name"
                  tick={{ fontSize: 11, fill: '#64748b' }}
                  interval={0}
                  angle={-15}
                  textAnchor="end"
                />
                <YAxis
                  tick={{ fontSize: 11, fill: '#64748b' }}
                  domain={[0, 100]}
                  unit="%"
                />
                <Tooltip
                  formatter={(value: any, name: any) => [
                    `${value}%`,
                    name === 'percentage' ? 'Attendance Rate' : name,
                  ]}
                  labelFormatter={(label) => {
                    const item = chartData.find((c) => c.name === label);
                    return item ? `${item.fullName} (${label})` : label;
                  }}
                  contentStyle={{
                    backgroundColor: '#ffffff',
                    border: '1px solid #e2e8f0',
                    borderRadius: '0.75rem',
                    fontSize: '0.75rem',
                    boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
                  }}
                />
                <Legend
                  wrapperStyle={{ fontSize: '0.75rem', paddingTop: '10px' }}
                />
                <Bar
                  dataKey="percentage"
                  name="Attendance %"
                  fill="#2563eb"
                  radius={[6, 6, 0, 0]}
                  maxBarSize={45}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <div className="py-12 text-center text-surface-400">
            <BookOpen className="w-10 h-10 mx-auto mb-2 text-surface-300" aria-hidden="true" />
            <p className="text-sm font-medium text-surface-600">
              No subject attendance data available yet.
            </p>
            <p className="text-xs text-surface-400 mt-1">
              Course subjects and student attendance logs will populate this chart automatically.
            </p>
          </div>
        )}
      </div>

      {/* Two Column Section: Low Attendance Students & Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Low Attendance Students (< 75%) */}
        <div className="card border border-surface-200 p-5 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-danger" />
                <h3 className="text-base font-bold text-surface-900">
                  Low Attendance Students
                </h3>
              </div>
              <span className="badge badge-danger text-xs font-semibold">
                Threshold: &lt; 75%
              </span>
            </div>
            <p className="text-xs text-surface-500 mb-4">
              Students requiring immediate academic attendance intervention
            </p>

            {data.low_attendance_students.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-surface-100 text-surface-400 uppercase tracking-wider font-semibold">
                      <th className="pb-2.5">Student ID</th>
                      <th className="pb-2.5">Student Name</th>
                      <th className="pb-2.5">Subject</th>
                      <th className="pb-2.5 text-center">Attendance %</th>
                      <th className="pb-2.5 text-right">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-surface-50">
                    {data.low_attendance_students.slice(0, 7).map((student) => (
                      <tr key={student.id} className="hover:bg-surface-50/80 transition-colors">
                        <td className="py-2.5 font-medium text-surface-700">
                          {student.student_id || student.id.slice(0, 8)}
                        </td>
                        <td className="py-2.5 font-semibold text-surface-900 truncate max-w-[130px]">
                          {student.full_name}
                        </td>
                        <td className="py-2.5 text-surface-500">
                          {student.subject || 'Overall'}
                        </td>
                        <td className="py-2.5 text-center">
                          <span className="font-bold text-red-600">
                            {student.attendance_percentage}%
                          </span>
                        </td>
                        <td className="py-2.5 text-right">
                          <span className="px-2 py-0.5 rounded-full text-[0.68rem] font-bold bg-red-100 text-red-700">
                            Low
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="py-10 text-center text-surface-400">
                <CheckCircle2 className="w-10 h-10 mx-auto mb-2 text-emerald-500" aria-hidden="true" />
                <p className="text-sm font-semibold text-surface-800">
                  All students are currently above the attendance threshold.
                </p>
                <p className="text-xs text-surface-400 mt-1">
                  No students have attendance below 75%.
                </p>
              </div>
            )}
          </div>
          {data.low_attendance_students.length > 7 && (
            <div className="pt-3 mt-4 border-t border-surface-100 text-center">
              <span className="text-xs text-surface-400">
                Showing 7 of {data.low_attendance_students.length} students below threshold
              </span>
            </div>
          )}
        </div>

        {/* Recent Activity Section */}
        <div className="card border border-surface-200 p-5 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4 text-primary-600" />
                <h3 className="text-base font-bold text-surface-900">
                  Recent Activity
                </h3>
              </div>
              <span className="text-xs text-surface-400 font-medium">
                Live Audit Stream
              </span>
            </div>
            <p className="text-xs text-surface-500 mb-4">
              Real institutional transactions recorded in database
            </p>

            {data.recent_activity && data.recent_activity.length > 0 ? (
              <div className="space-y-3">
                {data.recent_activity.slice(0, 6).map((item) => (
                  <div
                    key={item.id}
                    className="flex items-start gap-3 p-2.5 rounded-xl hover:bg-surface-50 transition-colors border border-transparent hover:border-surface-100"
                  >
                    <div
                      className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 text-xs font-bold ${
                        item.type === 'attendance'
                          ? item.status === 'present'
                            ? 'bg-emerald-100 text-emerald-700'
                            : 'bg-red-100 text-red-700'
                          : 'bg-blue-100 text-blue-700'
                      }`}
                    >
                      {item.type === 'attendance' ? (
                        <ClipboardCheck className="w-4 h-4" />
                      ) : (
                        <Users className="w-4 h-4" />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-semibold text-surface-800 truncate">
                        {item.title}
                      </p>
                      <p className="text-[0.7rem] text-surface-500 truncate mt-0.5">
                        {item.description}
                      </p>
                    </div>
                    <span className="text-[0.65rem] text-surface-400 flex-shrink-0">
                      {new Date(item.timestamp).toLocaleTimeString([], {
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="py-10 text-center text-surface-400">
                <Clock className="w-10 h-10 mx-auto mb-2 text-surface-300" aria-hidden="true" />
                <p className="text-sm font-semibold text-surface-700">
                  No recent system activity recorded.
                </p>
                <p className="text-xs text-surface-400 mt-1 max-w-xs mx-auto">
                  Recent attendance submissions and enrollments will appear here automatically.
                </p>
              </div>
            )}
          </div>
          <div className="pt-3 mt-4 border-t border-surface-100 flex items-center justify-between text-xs text-surface-400">
            <span>Verified database activity stream</span>
            <span>Real-time</span>
          </div>
        </div>
      </div>
    </div>
  );
}
