import { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import api, { isRequestCancelled } from '../../services/api';
import type { LecturerDashboardData } from '../../types';
import { DashboardSkeleton } from '../../components/Skeleton';
import EmptyState from '../../components/EmptyState';
import ErrorState from '../../components/ErrorState';
import {
  BookOpen,
  Users,
  ClipboardCheck,
  TrendingUp,
  ShieldCheck,
  Building,
  User,
  RotateCw,
  Bell,
  Clock,
  ArrowRight,
  Sparkles,
  FileCheck2,
  Calendar,
  CheckCircle2,
  XCircle,
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts';

export default function LecturerDashboardPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [data, setData] = useState<LecturerDashboardData | null>(null);
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
      const res = await api.get<LecturerDashboardData>('/api/lecturer/dashboard', { signal });
      setData(res.data);
    } catch (err: any) {
      if (isRequestCancelled(err)) {
        return;
      }
      if (err.response?.status === 401) {
        setError('Your session has expired. Please sign in again.');
      } else if (err.response?.status === 403) {
        setError('You do not have permission to view this dashboard.');
      } else if (err.response?.status >= 500) {
        setError('Unable to load your dashboard right now. Please try again later.');
      } else if (!err.response) {
        setError('Unable to connect to AttendX. Please check your network connection.');
      } else {
        setError(err.response?.data?.detail || 'Unable to load dashboard data.');
      }
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
      <div className="space-y-6 max-w-6xl mx-auto">
        <ErrorState
          title="Unable to load dashboard data"
          message={error || 'An unexpected error occurred while communicating with the server.'}
          onRetry={() => fetchDashboardData(false)}
        />
      </div>
    );
  }

  const { lecturer, summary, subjects, attendance_overview, recent_activity, unread_notifications_count } = data;

  // Real summary metrics for the cards
  const summaryCards = [
    {
      id: 'metric-subjects',
      title: 'Assigned Subjects',
      value: summary.total_subjects,
      subtext: summary.total_subjects === 1 ? '1 course assignment' : `${summary.total_subjects} course assignments`,
      icon: BookOpen,
      iconBg: 'bg-indigo-50 text-indigo-600',
    },
    {
      id: 'metric-students',
      title: 'Total Students',
      value: summary.total_students,
      subtext: 'Unique students across subjects',
      icon: Users,
      iconBg: 'bg-blue-50 text-blue-600',
    },
    {
      id: 'metric-attendance',
      title: 'Attendance Records',
      value: summary.total_attendance_records,
      subtext: attendance_overview.has_data
        ? `${attendance_overview.present} present · ${attendance_overview.absent} absent`
        : 'No records registered yet',
      icon: ClipboardCheck,
      iconBg: 'bg-emerald-50 text-emerald-600',
    },
    {
      id: 'metric-rate',
      title: 'Overall Attendance Rate',
      value: attendance_overview.has_data ? `${summary.average_attendance}%` : '—',
      subtext: attendance_overview.has_data
        ? summary.average_attendance >= 75
          ? 'Meets institutional benchmark (≥75%)'
          : 'Below 75% target threshold'
        : 'Pending session recording',
      icon: TrendingUp,
      iconBg: summary.average_attendance >= 75 ? 'bg-emerald-50 text-emerald-600' : 'bg-amber-50 text-amber-600',
    },
  ];

  // Prepare chart data from real subjects data (only if attendance exists)
  const chartData = subjects
    .filter((s) => s.has_attendance)
    .map((s) => ({
      name: s.code,
      attendanceRate: s.attendance_percentage,
      present: s.present,
      absent: s.absent,
      total: s.total_classes,
    }));

  return (
    <div className="space-y-6 fade-in max-w-6xl mx-auto pb-10">
      {/* 1. Header / Welcome Banner with Lecturer Identity */}
      <div className="card bg-gradient-to-r from-surface-900 via-surface-800 to-indigo-950 text-white p-6 sm:p-8 border-0 shadow-lg relative overflow-hidden">
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-2">
              <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-500/20 text-indigo-300 border border-indigo-400/30">
                <Sparkles className="w-3.5 h-3.5" />
                Faculty Portal
              </span>
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[0.7rem] font-medium bg-emerald-500/20 text-emerald-300 border border-emerald-400/30">
                <ShieldCheck className="w-3 h-3" />
                {lecturer.department || 'Faculty Member'}
              </span>
              {unread_notifications_count > 0 && (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[0.7rem] font-medium bg-amber-500/20 text-amber-300 border border-amber-400/30">
                  <Bell className="w-3 h-3" />
                  {unread_notifications_count} New Notice{unread_notifications_count > 1 ? 's' : ''}
                </span>
              )}
            </div>

            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight">
              {getGreeting()}, {lecturer.full_name || user?.full_name || 'Faculty Member'} 👋
            </h1>

            <p className="text-surface-300 text-sm max-w-2xl leading-relaxed">
              Welcome to your AttendX faculty workspace. Monitor your assigned courses, review student attendance rates,
              and stay synchronized with institutional academic records.
            </p>
          </div>

          <div className="flex items-center gap-3 self-start md:self-auto">
            <button
              onClick={() => fetchDashboardData(true)}
              disabled={refreshing}
              className="btn bg-white/10 hover:bg-white/20 text-white border border-white/15 backdrop-blur-xs flex items-center gap-2 transition-all shadow-sm disabled:opacity-50"
              title="Refresh dashboard metrics"
              aria-label="Refresh dashboard data"
            >
              <RotateCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
              <span className="hidden sm:inline">{refreshing ? 'Updating...' : 'Refresh'}</span>
            </button>
            <button
              onClick={() => navigate('/lecturer/profile')}
              className="btn bg-white/10 hover:bg-white/20 text-white border border-white/15 backdrop-blur-xs flex items-center gap-2 transition-all shadow-sm"
              aria-label="View faculty profile"
            >
              <User className="w-4 h-4" />
              <span>Profile</span>
            </button>
          </div>
        </div>
      </div>

      {/* 2. Lecturer Quick Context Bar */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div className="bg-white rounded-xl border border-surface-200 px-4 py-3 flex items-center gap-3 shadow-xs">
          <div className="w-9 h-9 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center flex-shrink-0">
            <User className="w-5 h-5" />
          </div>
          <div className="min-w-0">
            <span className="text-[0.7rem] uppercase tracking-wider font-semibold text-surface-400 block">Faculty Member</span>
            <span className="text-sm font-bold text-surface-900 truncate block">{lecturer.full_name}</span>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-surface-200 px-4 py-3 flex items-center gap-3 shadow-xs">
          <div className="w-9 h-9 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center flex-shrink-0">
            <Building className="w-5 h-5" />
          </div>
          <div className="min-w-0">
            <span className="text-[0.7rem] uppercase tracking-wider font-semibold text-surface-400 block">Department</span>
            <span className="text-sm font-bold text-surface-900 truncate block">{lecturer.department || 'Not Specified'}</span>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-surface-200 px-4 py-3 flex items-center gap-3 shadow-xs">
          <div className="w-9 h-9 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center flex-shrink-0">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div className="min-w-0">
            <span className="text-[0.7rem] uppercase tracking-wider font-semibold text-surface-400 block">Staff Identifier</span>
            <span className="text-sm font-bold text-surface-900 truncate block">{lecturer.employee_id || 'Faculty Staff'}</span>
          </div>
        </div>
      </div>

      {/* 3. Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {summaryCards.map((card) => {
          const Icon = card.icon;
          return (
            <div key={card.id} className="card p-5 border border-surface-200 shadow-xs flex flex-col justify-between">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-semibold uppercase tracking-wider text-surface-500">
                  {card.title}
                </span>
                <div className={`w-10 h-10 rounded-xl ${card.iconBg} flex items-center justify-center flex-shrink-0`}>
                  <Icon className="w-5 h-5" />
                </div>
              </div>
              <div>
                <div className="text-2xl sm:text-3xl font-bold text-surface-900 tracking-tight">
                  {card.value}
                </div>
                <p className="text-xs text-surface-500 mt-1 leading-snug">
                  {card.subtext}
                </p>
              </div>
            </div>
          );
        })}
      </div>

      {/* 4. Assigned Subjects Section */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <BookOpen className="w-4 h-4 text-indigo-600" />
            <h2 className="text-base font-bold text-surface-900">Assigned Subjects</h2>
            <span className="text-xs text-surface-500 font-medium">({subjects.length})</span>
          </div>
          <span className="text-xs text-surface-400">Institutional teaching assignments</span>
        </div>

        {subjects.length === 0 ? (
          <div className="card p-8 border border-surface-200">
            <EmptyState
              title="No subjects assigned yet"
              description="An administrator has not assigned any teaching courses to your faculty account yet. Once assigned, your subjects will appear here."
              icon={<BookOpen className="w-8 h-8 text-surface-400" />}
            />
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {subjects.map((subject) => (
              <div
                key={subject.id}
                className="card card-hover p-5 border border-surface-200 flex flex-col justify-between group"
              >
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <span className="px-2.5 py-1 rounded-md text-xs font-bold bg-indigo-50 text-indigo-700 border border-indigo-100 font-mono">
                      {subject.code}
                    </span>
                    <span className="text-[0.72rem] text-surface-500 font-medium">
                      Year {subject.year} · Sem {subject.semester}
                    </span>
                  </div>

                  <h3 className="text-base font-bold text-surface-900 group-hover:text-indigo-600 transition-colors line-clamp-2">
                    {subject.name}
                  </h3>
                  <p className="text-xs text-surface-500 mt-1">{subject.department}</p>

                  <div className="mt-4 pt-3 border-t border-surface-100 grid grid-cols-2 gap-2 text-xs">
                    <div>
                      <span className="text-surface-400 block text-[0.68rem] uppercase font-semibold">Students</span>
                      <span className="font-semibold text-surface-800 flex items-center gap-1 mt-0.5">
                        <Users className="w-3.5 h-3.5 text-surface-400" />
                        {subject.enrolled_students} Enrolled
                      </span>
                    </div>
                    <div>
                      <span className="text-surface-400 block text-[0.68rem] uppercase font-semibold">Attendance</span>
                      {subject.has_attendance ? (
                        <span className={`font-semibold flex items-center gap-1 mt-0.5 ${
                          subject.attendance_percentage >= 75 ? 'text-emerald-600' : 'text-amber-600'
                        }`}>
                          <TrendingUp className="w-3.5 h-3.5" />
                          {subject.attendance_percentage}%
                        </span>
                      ) : (
                        <span className="text-surface-400 italic mt-0.5 block">No sessions</span>
                      )}
                    </div>
                  </div>
                </div>

                <div className="mt-4 pt-3 border-t border-surface-100 flex items-center justify-between">
                  <span className="text-[0.72rem] text-surface-500">
                    {subject.has_attendance
                      ? `${subject.present} present / ${subject.total_classes} records`
                      : '0 sessions recorded'}
                  </span>
                  <button
                    onClick={() => navigate('/lecturer/subjects')}
                    className="text-xs font-semibold text-indigo-600 hover:text-indigo-700 flex items-center gap-1 transition-colors"
                    aria-label={`View details for ${subject.code}`}
                  >
                    <span>View Roster</span>
                    <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 5. Attendance Overview & Subject-Wise Attendance Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Subject-Wise Attendance Analysis & Chart */}
        <div className="lg:col-span-7 card p-5 border border-surface-200">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-base font-bold text-surface-900">Subject Attendance Performance</h3>
              <p className="text-xs text-surface-500 mt-0.5">Attendance rates across your assigned subjects</p>
            </div>
            {attendance_overview.has_data && (
              <span className="badge badge-secondary text-xs">
                {subjects.filter((s) => s.has_attendance).length} of {subjects.length} active
              </span>
            )}
          </div>

          {!attendance_overview.has_data ? (
            <EmptyState
              title="No attendance records available"
              description="No student attendance sessions have been logged for your assigned courses yet. Performance analytics will visualize here once attendance is recorded."
              icon={<TrendingUp className="w-8 h-8 text-surface-400" />}
            />
          ) : (
            <div className="space-y-5">
              {/* Optional Recharts bar chart */}
              {chartData.length > 0 && (
                <div className="h-48 w-full pt-2">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                      <XAxis dataKey="name" tick={{ fontSize: 12, fill: '#64748b' }} axisLine={false} tickLine={false} />
                      <YAxis
                        domain={[0, 100]}
                        tick={{ fontSize: 11, fill: '#64748b' }}
                        axisLine={false}
                        tickLine={false}
                        tickFormatter={(v) => `${v}%`}
                      />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: '#0f172a',
                          borderRadius: '8px',
                          border: 'none',
                          color: '#fff',
                          fontSize: '12px',
                        }}
                        formatter={(value: any) => [`${value}%`, 'Attendance Rate']}
                      />
                      <Bar dataKey="attendanceRate" fill="#4f46e5" radius={[4, 4, 0, 0]} maxBarSize={40} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}

              {/* Subject Breakdown Table */}
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="border-b border-surface-200 text-surface-500">
                      <th className="py-2 font-semibold">Subject</th>
                      <th className="py-2 font-semibold text-center">Enrolled</th>
                      <th className="py-2 font-semibold text-center">Present</th>
                      <th className="py-2 font-semibold text-center">Absent</th>
                      <th className="py-2 font-semibold text-right">Attendance</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-surface-100">
                    {subjects.map((sub) => (
                      <tr key={sub.id} className="hover:bg-surface-50/50">
                        <td className="py-2.5">
                          <span className="font-bold text-surface-900 block font-mono">{sub.code}</span>
                          <span className="text-[0.7rem] text-surface-500 truncate max-w-[160px] block">
                            {sub.name}
                          </span>
                        </td>
                        <td className="py-2.5 text-center text-surface-700">{sub.enrolled_students}</td>
                        <td className="py-2.5 text-center text-emerald-600 font-semibold">{sub.present}</td>
                        <td className="py-2.5 text-center text-rose-500 font-semibold">{sub.absent}</td>
                        <td className="py-2.5 text-right font-bold">
                          {sub.has_attendance ? (
                            <span className={sub.attendance_percentage >= 75 ? 'text-emerald-600' : 'text-amber-600'}>
                              {sub.attendance_percentage}%
                            </span>
                          ) : (
                            <span className="text-surface-400 font-normal italic">No data</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Attendance Overview Distribution & Faculty Actions */}
        <div className="lg:col-span-5 space-y-4">
          <div className="card p-5 border border-surface-200">
            <h3 className="text-base font-bold text-surface-900 mb-1">Attendance Distribution</h3>
            <p className="text-xs text-surface-500 mb-4">Faculty session verification breakdown</p>

            {attendance_overview.has_data ? (
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between text-xs mb-1.5 font-medium">
                    <span className="text-surface-600">Overall Rate</span>
                    <span className="text-surface-900 font-bold">{attendance_overview.percentage}%</span>
                  </div>
                  <div className="w-full h-2.5 rounded-full bg-surface-100 overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${
                        attendance_overview.percentage >= 75 ? 'bg-emerald-500' : 'bg-amber-500'
                      }`}
                      style={{ width: `${Math.min(100, Math.max(0, attendance_overview.percentage))}%` }}
                    />
                  </div>
                  <span className="text-[0.68rem] text-surface-400 mt-1 block">
                    Institutional target threshold: 75%
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-3 pt-2 border-t border-surface-100">
                  <div className="p-3 rounded-lg bg-emerald-50/60 border border-emerald-100">
                    <div className="flex items-center gap-1.5 text-emerald-700 mb-1">
                      <CheckCircle2 className="w-4 h-4" />
                      <span className="text-xs font-bold uppercase tracking-wider">Present</span>
                    </div>
                    <span className="text-xl font-bold text-emerald-800">{attendance_overview.present}</span>
                    <span className="text-[0.7rem] text-emerald-600 block mt-0.5">
                      {attendance_overview.total_classes > 0
                        ? `${Math.round((attendance_overview.present / attendance_overview.total_classes) * 100)}% of records`
                        : ''}
                    </span>
                  </div>

                  <div className="p-3 rounded-lg bg-rose-50/60 border border-rose-100">
                    <div className="flex items-center gap-1.5 text-rose-700 mb-1">
                      <XCircle className="w-4 h-4" />
                      <span className="text-xs font-bold uppercase tracking-wider">Absent</span>
                    </div>
                    <span className="text-xl font-bold text-rose-800">{attendance_overview.absent}</span>
                    <span className="text-[0.7rem] text-rose-600 block mt-0.5">
                      {attendance_overview.total_classes > 0
                        ? `${Math.round((attendance_overview.absent / attendance_overview.total_classes) * 100)}% of records`
                        : ''}
                    </span>
                  </div>
                </div>
              </div>
            ) : (
              <div className="py-6 text-center text-xs text-surface-500">
                <Calendar className="w-8 h-8 text-surface-300 mx-auto mb-2" />
                <p className="font-semibold text-surface-700">No session metrics</p>
                <p className="mt-1 max-w-[200px] mx-auto text-surface-400">
                  Attendance percentages will calculate automatically once classes are marked.
                </p>
              </div>
            )}
          </div>

          {/* Quick Navigation Card */}
          <div className="card p-5 border border-surface-200">
            <h4 className="text-xs font-bold uppercase tracking-wider text-surface-400 mb-3">
              Faculty Workflows
            </h4>
            <div className="space-y-2">
              <button
                onClick={() => navigate('/lecturer/subjects')}
                className="w-full text-left p-3 rounded-lg border border-surface-200 hover:border-indigo-300 hover:bg-indigo-50/30 transition-all flex items-center justify-between group"
              >
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-md bg-indigo-50 text-indigo-600 flex items-center justify-center">
                    <BookOpen className="w-4 h-4" />
                  </div>
                  <div>
                    <span className="text-xs font-bold text-surface-900 group-hover:text-indigo-600 transition-colors block">
                      Course Rosters
                    </span>
                    <span className="text-[0.7rem] text-surface-500">View enrolled students list</span>
                  </div>
                </div>
                <ArrowRight className="w-4 h-4 text-surface-400 group-hover:text-indigo-600 group-hover:translate-x-0.5 transition-all" />
              </button>

              <button
                onClick={() => navigate('/lecturer/attendance')}
                className="w-full text-left p-3 rounded-lg border border-surface-200 hover:border-indigo-300 hover:bg-indigo-50/30 transition-all flex items-center justify-between group"
              >
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-md bg-purple-50 text-purple-600 flex items-center justify-center">
                    <ClipboardCheck className="w-4 h-4" />
                  </div>
                  <div>
                    <span className="text-xs font-bold text-surface-900 group-hover:text-indigo-600 transition-colors block">
                      Mark Attendance
                    </span>
                    <span className="text-[0.7rem] text-surface-500">Record or update class attendance</span>
                  </div>
                </div>
                <ArrowRight className="w-4 h-4 text-surface-400 group-hover:text-indigo-600 group-hover:translate-x-0.5 transition-all" />
              </button>

              <button
                onClick={() => navigate('/lecturer/reports')}
                className="w-full text-left p-3 rounded-lg border border-surface-200 hover:border-indigo-300 hover:bg-indigo-50/30 transition-all flex items-center justify-between group"
              >
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-md bg-blue-50 text-blue-600 flex items-center justify-center">
                    <FileCheck2 className="w-4 h-4" />
                  </div>
                  <div>
                    <span className="text-xs font-bold text-surface-900 group-hover:text-indigo-600 transition-colors block">
                      Records & Reports
                    </span>
                    <span className="text-[0.7rem] text-surface-500">Module L4 · Compliance Audits</span>
                  </div>
                </div>
                <span className="badge badge-secondary text-[0.65rem] px-1.5 py-0.5">Coming Soon</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* 6. Recent Activity Section */}
      <div className="card p-5 border border-surface-200">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-indigo-600" />
            <h3 className="text-base font-bold text-surface-900">Recent Attendance Activity</h3>
          </div>
          <span className="text-xs text-surface-400">Class session activity log</span>
        </div>

        {recent_activity.length === 0 ? (
          <EmptyState
            title="No recent attendance activity"
            description="Student attendance records marked for your assigned courses will appear chronologically in this activity stream."
            icon={<Clock className="w-8 h-8 text-surface-400" />}
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-surface-200 text-surface-500">
                  <th className="py-2.5 font-semibold">Student</th>
                  <th className="py-2.5 font-semibold">Subject</th>
                  <th className="py-2.5 font-semibold">Date</th>
                  <th className="py-2.5 font-semibold text-center">Status</th>
                  <th className="py-2.5 font-semibold text-right">Recorded</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-surface-100">
                {recent_activity.map((item) => (
                  <tr key={item.id} className="hover:bg-surface-50/50 transition-colors">
                    <td className="py-2.5">
                      <span className="font-semibold text-surface-900 block">{item.student_name}</span>
                      {item.student_sid && (
                        <span className="text-[0.68rem] text-surface-400 block">{item.student_sid}</span>
                      )}
                    </td>
                    <td className="py-2.5">
                      <span className="font-semibold text-surface-800 font-mono block">{item.subject_code}</span>
                      <span className="text-[0.68rem] text-surface-500 truncate max-w-[180px] block">{item.subject_name}</span>
                    </td>
                    <td className="py-2.5 text-surface-600 font-mono text-[0.75rem]">
                      {item.attendance_date}
                    </td>
                    <td className="py-2.5 text-center">
                      <span
                        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[0.68rem] font-semibold ${
                          item.status === 'present'
                            ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                            : 'bg-rose-50 text-rose-700 border border-rose-200'
                        }`}
                      >
                        {item.status === 'present' ? (
                          <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                        ) : (
                          <XCircle className="w-3 h-3 text-rose-600" />
                        )}
                        {item.status.toUpperCase()}
                      </span>
                    </td>
                    <td className="py-2.5 text-right text-surface-400 text-[0.68rem]">
                      {item.created_at ? new Date(item.created_at).toLocaleDateString() : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
