import { useEffect, useState } from 'react';
import api from '../services/api';
import type { AdminDashboardData } from '../types';
import { DashboardSkeleton } from '../components/Skeleton';
import ErrorState from '../components/ErrorState';
import { useNavigate } from 'react-router-dom';
import {
  Users, BookOpen, CalendarCheck, TrendingUp, UserPlus, BookPlus, ClipboardCheck, AlertTriangle,
} from 'lucide-react';
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, PieChart, Pie, Cell, Legend,
} from 'recharts';

export default function AdminDashboard() {
  const [data, setData] = useState<AdminDashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const fetchDashboard = async () => {
    setLoading(true); setError('');
    try {
      const res = await api.get('/api/dashboard/admin');
      setData(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchDashboard(); }, []);

  if (loading) return <DashboardSkeleton />;
  if (error) return <ErrorState message={error} onRetry={fetchDashboard} />;
  if (!data) return null;

  const COLORS = ['#10b981', '#ef4444'];

  const statCards = [
    { label: 'Total Students', value: data.total_students, icon: Users, color: 'from-primary-500 to-primary-600' },
    { label: 'Total Subjects', value: data.total_subjects, icon: BookOpen, color: 'from-violet-500 to-violet-600' },
    { label: "Today's Attendance", value: `${data.todays_attendance.percentage}%`, icon: CalendarCheck, color: 'from-emerald-500 to-emerald-600', sub: `${data.todays_attendance.present}/${data.todays_attendance.total} present` },
    { label: 'Average Attendance', value: `${data.average_attendance}%`, icon: TrendingUp, color: 'from-amber-500 to-amber-600' },
  ];

  const quickActions = [
    { label: 'Add Student', icon: UserPlus, to: '/admin/students', color: 'bg-primary-50 text-primary-700' },
    { label: 'Add Subject', icon: BookPlus, to: '/admin/subjects', color: 'bg-violet-50 text-violet-700' },
    { label: 'Mark Attendance', icon: ClipboardCheck, to: '/admin/mark-attendance', color: 'bg-emerald-50 text-emerald-700' },
  ];

  const pieData = [
    { name: 'Present', value: data.todays_attendance.present },
    { name: 'Absent', value: data.todays_attendance.absent },
  ];

  return (
    <div className="space-y-6 fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div>
          <h1 className="text-2xl font-bold text-surface-900">Admin Dashboard</h1>
          <p className="text-surface-500 text-sm mt-0.5">Overview of attendance management</p>
        </div>
        <div className="flex gap-2">
          {quickActions.map((action) => (
            <button key={action.label} onClick={() => navigate(action.to)}
              className={`btn btn-sm ${action.color} hover:opacity-90 transition-opacity`}>
              <action.icon className="w-4 h-4" />
              <span className="hidden sm:inline">{action.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((card, i) => (
          <div key={i} className="card card-hover fade-in" style={{ animationDelay: `${i * 0.05}s` }}>
            <div className="flex items-start justify-between mb-3">
              <p className="text-sm font-medium text-surface-500">{card.label}</p>
              <div className={`w-9 h-9 rounded-xl bg-gradient-to-br ${card.color} flex items-center justify-center`}>
                <card.icon className="w-4 h-4 text-white" />
              </div>
            </div>
            <p className="text-2xl font-bold text-surface-900">{card.value}</p>
            {card.sub && <p className="text-xs text-surface-400 mt-1">{card.sub}</p>}
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Attendance Trend */}
        <div className="card lg:col-span-2">
          <h3 className="text-base font-semibold text-surface-800 mb-4">Attendance Trend (Last 14 Days)</h3>
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={data.attendance_trend} margin={{ top: 0, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#94a3b8' }}
                tickFormatter={(v) => new Date(v).toLocaleDateString('en', { month: 'short', day: 'numeric' })} />
              <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} />
              <Tooltip contentStyle={{ borderRadius: '0.5rem', border: '1px solid #e2e8f0', fontSize: '0.8125rem' }} />
              <Line type="monotone" dataKey="present" stroke="#10b981" strokeWidth={2} dot={{ r: 3 }} name="Present" />
              <Line type="monotone" dataKey="absent" stroke="#ef4444" strokeWidth={2} dot={{ r: 3 }} name="Absent" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Today's Pie */}
        <div className="card">
          <h3 className="text-base font-semibold text-surface-800 mb-4">Today's Breakdown</h3>
          {data.todays_attendance.total === 0 ? (
            <p className="text-sm text-surface-400 py-8 text-center">No attendance marked today</p>
          ) : (
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie data={pieData} cx="50%" cy="50%" innerRadius={60} outerRadius={90}
                  paddingAngle={4} dataKey="value" label={({ name, percent }) => `${name} ${((percent ?? 0) * 100).toFixed(0)}%`}
                  labelLine={false}>
                  {pieData.map((_, i) => <Cell key={`cell-${i}`} fill={COLORS[i]} />)}
                </Pie>
                <Legend />
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Subject Stats */}
        <div className="card">
          <h3 className="text-base font-semibold text-surface-800 mb-4">Subject Attendance</h3>
          {data.subject_stats.length === 0 ? (
            <p className="text-sm text-surface-400 py-8 text-center">No subjects yet</p>
          ) : (
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={data.subject_stats} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="subject_code" tick={{ fontSize: 11, fill: '#94a3b8' }} />
                <YAxis domain={[0, 100]} tick={{ fontSize: 11, fill: '#94a3b8' }} />
                <Tooltip contentStyle={{ borderRadius: '0.5rem', border: '1px solid #e2e8f0', fontSize: '0.8125rem' }} />
                <Bar dataKey="percentage" fill="#3b82f6" radius={[4, 4, 0, 0]} maxBarSize={36} name="Attendance %" />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Recent Attendance */}
        <div className="card">
          <h3 className="text-base font-semibold text-surface-800 mb-4">Recent Attendance</h3>
          {data.recent_attendance.length === 0 ? (
            <p className="text-sm text-surface-400 py-8 text-center">No records yet</p>
          ) : (
            <div className="space-y-2 max-h-[280px] overflow-y-auto">
              {data.recent_attendance.map((rec) => (
                <div key={rec.id} className="flex items-center justify-between py-2 border-b border-surface-50 last:border-0">
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium text-surface-700 truncate">{rec.student_name}</p>
                    <p className="text-xs text-surface-400">{rec.subject_code} • {new Date(rec.attendance_date).toLocaleDateString()}</p>
                  </div>
                  <span className={`badge ${rec.status === 'present' ? 'badge-success' : 'badge-danger'}`}>
                    {rec.status === 'present' ? 'Present' : 'Absent'}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Low Attendance Students */}
      {data.low_attendance_students.length > 0 && (
        <div className="card">
          <h3 className="text-base font-semibold text-surface-800 mb-4 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-warning" />
            Low Attendance Students (Below 75%)
          </h3>
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Student</th>
                  <th>Department</th>
                  <th>Year/Section</th>
                  <th>Attendance</th>
                  <th>Classes Needed</th>
                </tr>
              </thead>
              <tbody>
                {data.low_attendance_students.map((s) => (
                  <tr key={s.id}>
                    <td>
                      <div>
                        <p className="font-medium text-surface-800">{s.full_name}</p>
                        <p className="text-xs text-surface-400">{s.student_id}</p>
                      </div>
                    </td>
                    <td>{s.department}</td>
                    <td>{s.year} / {s.section}</td>
                    <td>
                      <span className={`font-semibold ${s.attendance_percentage < 60 ? 'text-danger' : 'text-warning'}`}>
                        {s.attendance_percentage}%
                      </span>
                    </td>
                    <td>{s.classes_needed}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
