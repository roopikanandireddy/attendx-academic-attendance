import { useEffect, useState } from 'react';
import api from '../services/api';
import LoadingSpinner from '../components/LoadingSpinner';
import EmptyState from '../components/EmptyState';
import ErrorState from '../components/ErrorState';
import { ClipboardCheck, CheckCircle2, XCircle } from 'lucide-react';
import {
  PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip,
} from 'recharts';

export default function MyAttendancePage() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchData = async () => {
    setLoading(true); setError('');
    try {
      const res = await api.get('/api/dashboard/student');
      setData(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  if (loading) return <LoadingSpinner text="Loading attendance..." />;
  if (error) return <ErrorState message={error} onRetry={fetchData} />;
  if (!data) return null;

  const { overall_stats, subjects, recent_attendance } = data;
  const COLORS = ['#10b981', '#ef4444'];
  const pieData = [
    { name: 'Present', value: overall_stats.present },
    { name: 'Absent', value: overall_stats.absent },
  ];

  return (
    <div className="space-y-6 fade-in">
      <div>
        <h1 className="text-2xl font-bold text-surface-900">My Attendance</h1>
        <p className="text-surface-500 text-sm mt-0.5">Detailed view of your attendance</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Overall Summary */}
        <div className="card text-center">
          <h3 className="text-sm font-medium text-surface-500 mb-4">Overall Attendance</h3>
          {overall_stats.total_classes === 0 ? (
            <p className="text-surface-400 text-sm py-8">No attendance data yet</p>
          ) : (
            <>
              <div className={`text-5xl font-bold mb-2 ${
                overall_stats.percentage >= 75 ? 'text-success' :
                overall_stats.percentage >= 60 ? 'text-warning' : 'text-danger'
              }`}>
                {overall_stats.percentage}%
              </div>
              <p className="text-sm text-surface-500 mb-4">
                {overall_stats.present} of {overall_stats.total_classes} classes
              </p>
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie data={pieData} cx="50%" cy="50%" innerRadius={50} outerRadius={75}
                    paddingAngle={4} dataKey="value">
                    {pieData.map((_, i) => <Cell key={i} fill={COLORS[i]} />)}
                  </Pie>
                  <Legend />
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </>
          )}
        </div>

        {/* Subject Table */}
        <div className="card lg:col-span-2">
          <h3 className="text-base font-semibold text-surface-800 mb-4">Subject-wise Attendance</h3>
          {subjects.length === 0 ? (
            <EmptyState title="No subjects" description="No subjects enrolled." />
          ) : (
            <div className="table-container">
              <table className="table">
                <thead>
                  <tr><th>Subject</th><th>Present</th><th>Total</th><th>Attendance</th></tr>
                </thead>
                <tbody>
                  {subjects.map((s: any) => (
                    <tr key={s.subject_id}>
                      <td>
                        <div>
                          <p className="font-medium text-surface-800">{s.subject_name}</p>
                          <p className="text-xs text-surface-400 font-mono">{s.subject_code}</p>
                        </div>
                      </td>
                      <td className="text-success font-semibold">{s.present}</td>
                      <td>{s.total_classes}</td>
                      <td>
                        <div className="flex items-center gap-2">
                          <div className="progress-bar w-16">
                            <div className="progress-fill" style={{
                              width: `${s.percentage}%`,
                              background: s.percentage >= 75 ? '#10b981' : s.percentage >= 60 ? '#f59e0b' : '#ef4444',
                            }} />
                          </div>
                          <span className={`text-sm font-semibold ${
                            s.percentage >= 75 ? 'text-success' : s.percentage >= 60 ? 'text-warning' : 'text-danger'
                          }`}>{s.percentage}%</span>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Recent History */}
      <div className="card">
        <h3 className="text-base font-semibold text-surface-800 mb-4">Recent History</h3>
        {recent_attendance.length === 0 ? (
          <EmptyState title="No records" description="No attendance records found." icon={<ClipboardCheck className="w-8 h-8 text-surface-400" />} />
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {recent_attendance.map((rec: any) => (
              <div key={rec.id} className={`p-3 rounded-lg border ${
                rec.status === 'present' ? 'bg-emerald-50 border-emerald-100' : 'bg-red-50 border-red-100'
              }`}>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm font-medium text-surface-800">{rec.subject_code}</span>
                  {rec.status === 'present'
                    ? <CheckCircle2 className="w-4 h-4 text-success" />
                    : <XCircle className="w-4 h-4 text-danger" />
                  }
                </div>
                <p className="text-xs text-surface-500">{rec.subject_name}</p>
                <p className="text-xs text-surface-400 mt-1">
                  {new Date(rec.attendance_date).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
