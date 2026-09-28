import { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import type { StudentDashboardData } from '../types';
import { DashboardSkeleton } from '../components/Skeleton';
import ErrorState from '../components/ErrorState';
import {
  Calendar,
  CheckCircle2,
  XCircle,
  TrendingUp,
  AlertTriangle,
  BookOpen,
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
} from 'recharts';

export default function StudentDashboard() {
  const { user } = useAuth();
  const [data, setData] = useState<StudentDashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchDashboard = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await api.get('/api/dashboard/student');
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

  const getGreeting = () => {
    const h = new Date().getHours();
    if (h < 12) return 'Good morning';
    if (h < 17) return 'Good afternoon';
    return 'Good evening';
  };

  const getPercentageColor = (pct: number) => {
    if (pct >= 75) return 'text-success';
    if (pct >= 60) return 'text-warning';
    return 'text-danger';
  };

  const getBarColor = (pct: number) => {
    if (pct >= 75) return '#10b981';
    if (pct >= 60) return '#f59e0b';
    return '#ef4444';
  };

  const statCards = [
    { label: 'Overall Attendance', value: `${data.overall_stats.percentage}%`, icon: TrendingUp, color: 'from-primary-500 to-primary-600', desc: 'All subjects combined' },
    { label: 'Total Classes', value: data.overall_stats.total_classes, icon: Calendar, color: 'from-violet-500 to-violet-600', desc: 'Across all subjects' },
    { label: 'Present', value: data.overall_stats.present, icon: CheckCircle2, color: 'from-emerald-500 to-emerald-600', desc: 'Classes attended' },
    { label: 'Absent', value: data.overall_stats.absent, icon: XCircle, color: 'from-rose-500 to-rose-600', desc: 'Classes missed' },
  ];

  return (
    <div className="space-y-6 fade-in">
      {/* Greeting */}
      <div>
        <h1 className="text-2xl font-bold text-surface-900">
          {getGreeting()}, {user?.full_name?.split(' ')[0]} 👋
        </h1>
        <p className="text-surface-500 text-sm mt-1">Here's your attendance overview</p>
      </div>

      {/* Stats Cards */}
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
            <p className="text-xs text-surface-400 mt-1">{card.desc}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Subject Attendance Chart */}
        <div className="card">
          <h3 className="text-base font-semibold text-surface-800 mb-4 flex items-center gap-2">
            <BookOpen className="w-4 h-4 text-primary-600" />
            Subject Attendance
          </h3>
          {data.subjects.length === 0 ? (
            <p className="text-sm text-surface-400 py-8 text-center">No subjects enrolled yet</p>
          ) : (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={data.subjects} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="subject_code" tick={{ fontSize: 12, fill: '#64748b' }} />
                <YAxis domain={[0, 100]} tick={{ fontSize: 12, fill: '#64748b' }} />
                <Tooltip
                  contentStyle={{ borderRadius: '0.5rem', border: '1px solid #e2e8f0', fontSize: '0.8125rem' }}
                  formatter={(value: any) => [`${value}%`, 'Attendance']}
                />
                <Bar dataKey="percentage" radius={[4, 4, 0, 0]} maxBarSize={40}>
                  {data.subjects.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={getBarColor(entry.percentage)} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Subject Details */}
        <div className="card">
          <h3 className="text-base font-semibold text-surface-800 mb-4">Subject-wise Breakdown</h3>
          {data.subjects.length === 0 ? (
            <p className="text-sm text-surface-400 py-8 text-center">No subjects to show</p>
          ) : (
            <div className="space-y-4">
              {data.subjects.map((sub) => (
                <div key={sub.subject_id} className="flex items-center gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium text-surface-800 truncate">
                        {sub.subject_code} — {sub.subject_name}
                      </span>
                      <span className={`text-sm font-semibold ${getPercentageColor(sub.percentage)}`}>
                        {sub.percentage}%
                      </span>
                    </div>
                    <div className="progress-bar">
                      <div
                        className="progress-fill"
                        style={{
                          width: `${sub.percentage}%`,
                          background: getBarColor(sub.percentage),
                        }}
                      />
                    </div>
                    <p className="text-xs text-surface-400 mt-1">
                      {sub.present}/{sub.total_classes} classes attended
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Attendance */}
        <div className="card">
          <h3 className="text-base font-semibold text-surface-800 mb-4">Recent Attendance</h3>
          {data.recent_attendance.length === 0 ? (
            <p className="text-sm text-surface-400 py-8 text-center">No recent attendance records</p>
          ) : (
            <div className="space-y-2">
              {data.recent_attendance.map((rec) => (
                <div key={rec.id} className="flex items-center justify-between py-2 border-b border-surface-50 last:border-0">
                  <div>
                    <p className="text-sm font-medium text-surface-700">{rec.subject_name}</p>
                    <p className="text-xs text-surface-400">{new Date(rec.attendance_date).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })}</p>
                  </div>
                  <span className={`badge ${rec.status === 'present' ? 'badge-success' : 'badge-danger'}`}>
                    {rec.status === 'present' ? 'Present' : 'Absent'}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Low Attendance Alerts */}
        <div className="card">
          <h3 className="text-base font-semibold text-surface-800 mb-4 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-warning" />
            Attendance Alerts
          </h3>
          {data.low_attendance_subjects.length === 0 ? (
            <div className="py-8 text-center">
              <CheckCircle2 className="w-10 h-10 text-success mx-auto mb-2" />
              <p className="text-sm font-medium text-surface-700">All clear!</p>
              <p className="text-xs text-surface-400">All subjects are above 75% threshold</p>
            </div>
          ) : (
            <div className="space-y-3">
              {data.low_attendance_subjects.map((sub) => (
                <div key={sub.subject_id} className="p-3 rounded-lg bg-amber-50 border border-amber-100">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium text-amber-900">{sub.subject_code}</span>
                    <span className="badge badge-warning">{sub.percentage}%</span>
                  </div>
                  <p className="text-xs text-amber-700">{sub.subject_name}</p>
                  <p className="text-xs text-amber-600 mt-1">
                    {sub.classes_needed > 0
                      ? `Need to attend ${sub.classes_needed} more consecutive classes to reach 75%`
                      : 'Attendance below required threshold'}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
