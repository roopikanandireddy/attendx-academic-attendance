import { useEffect, useState } from 'react';
import api from '../services/api';
import type { AdminDashboardData } from '../types';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorState from '../components/ErrorState';
import { BarChart3 } from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend,
} from 'recharts';

export default function ReportsPage() {
  const [data, setData] = useState<AdminDashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchData = async () => {
    setLoading(true); setError('');
    try {
      const res = await api.get('/api/dashboard/admin');
      setData(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  if (loading) return <LoadingSpinner text="Generating reports..." />;
  if (error) return <ErrorState message={error} onRetry={fetchData} />;
  if (!data) return null;

  const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#ec4899'];

  const totalPresent = data.subject_stats.reduce((sum, s) => sum + s.present, 0);
  const totalAbsent = data.subject_stats.reduce((sum, s) => sum + s.absent, 0);
  const overallPie = [
    { name: 'Present', value: totalPresent },
    { name: 'Absent', value: totalAbsent },
  ];

  return (
    <div className="space-y-6 fade-in">
      <div>
        <h1 className="text-2xl font-bold text-surface-900 flex items-center gap-2">
          <BarChart3 className="w-6 h-6 text-primary-600" />
          Reports
        </h1>
        <p className="text-surface-500 text-sm mt-0.5">Attendance analytics and insights</p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="card">
          <p className="text-xs font-medium text-surface-400 uppercase tracking-wider">Total Students</p>
          <p className="text-2xl font-bold text-surface-900 mt-1">{data.total_students}</p>
        </div>
        <div className="card">
          <p className="text-xs font-medium text-surface-400 uppercase tracking-wider">Total Subjects</p>
          <p className="text-2xl font-bold text-surface-900 mt-1">{data.total_subjects}</p>
        </div>
        <div className="card">
          <p className="text-xs font-medium text-surface-400 uppercase tracking-wider">Avg Attendance</p>
          <p className="text-2xl font-bold text-primary-600 mt-1">{data.average_attendance}%</p>
        </div>
        <div className="card">
          <p className="text-xs font-medium text-surface-400 uppercase tracking-wider">Low Attendance</p>
          <p className="text-2xl font-bold text-danger mt-1">{data.low_attendance_students.length}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Subject Performance */}
        <div className="card">
          <h3 className="text-base font-semibold text-surface-800 mb-4">Subject-wise Performance</h3>
          {data.subject_stats.length === 0 ? (
            <p className="text-sm text-surface-400 py-8 text-center">No data available</p>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={data.subject_stats} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="subject_code" tick={{ fontSize: 11, fill: '#94a3b8' }} />
                <YAxis domain={[0, 100]} tick={{ fontSize: 11, fill: '#94a3b8' }} />
                <Tooltip contentStyle={{ borderRadius: '0.5rem', border: '1px solid #e2e8f0', fontSize: '0.8125rem' }}
                  formatter={(value: any) => [`${value}%`, 'Attendance']} />
                <Bar dataKey="percentage" radius={[4, 4, 0, 0]} maxBarSize={40}>
                  {data.subject_stats.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Overall Distribution */}
        <div className="card">
          <h3 className="text-base font-semibold text-surface-800 mb-4">Overall Attendance Distribution</h3>
          {totalPresent + totalAbsent === 0 ? (
            <p className="text-sm text-surface-400 py-8 text-center">No data available</p>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie data={overallPie} cx="50%" cy="50%" innerRadius={60} outerRadius={100}
                  paddingAngle={4} dataKey="value"
                  label={({ name, percent }) => `${name} ${((percent ?? 0) * 100).toFixed(1)}%`}>
                  {overallPie.map((_, i) => <Cell key={i} fill={['#10b981', '#ef4444'][i]} />)}
                </Pie>
                <Legend />
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Subject Details Table */}
      <div className="card">
        <h3 className="text-base font-semibold text-surface-800 mb-4">Detailed Subject Statistics</h3>
        {data.subject_stats.length === 0 ? (
          <p className="text-sm text-surface-400 py-4 text-center">No subjects</p>
        ) : (
          <div className="table-container">
            <table className="table">
              <thead>
                <tr><th>Code</th><th>Subject</th><th>Total Classes</th><th>Present</th><th>Absent</th><th>Percentage</th></tr>
              </thead>
              <tbody>
                {data.subject_stats.map((s) => (
                  <tr key={s.subject_id}>
                    <td><span className="badge badge-info font-mono">{s.subject_code}</span></td>
                    <td className="font-medium text-surface-800">{s.subject_name}</td>
                    <td>{s.total_classes}</td>
                    <td className="text-success font-medium">{s.present}</td>
                    <td className="text-danger font-medium">{s.absent}</td>
                    <td>
                      <div className="flex items-center gap-2">
                        <div className="progress-bar w-16">
                          <div className="progress-fill" style={{
                            width: `${s.percentage}%`,
                            background: s.percentage >= 75 ? '#10b981' : s.percentage >= 60 ? '#f59e0b' : '#ef4444',
                          }} />
                        </div>
                        <span className="text-sm font-semibold">{s.percentage}%</span>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Low Attendance */}
      {data.low_attendance_students.length > 0 && (
        <div className="card">
          <h3 className="text-base font-semibold text-surface-800 mb-4">Students Below 75% Threshold</h3>
          <div className="table-container">
            <table className="table">
              <thead>
                <tr><th>Student</th><th>ID</th><th>Department</th><th>Attendance</th><th>Action Needed</th></tr>
              </thead>
              <tbody>
                {data.low_attendance_students.map(s => (
                  <tr key={s.id}>
                    <td className="font-medium text-surface-800">{s.full_name}</td>
                    <td className="font-mono text-xs">{s.student_id}</td>
                    <td>{s.department}</td>
                    <td>
                      <span className={`font-semibold ${s.attendance_percentage < 60 ? 'text-danger' : 'text-warning'}`}>
                        {s.attendance_percentage}%
                      </span>
                    </td>
                    <td className="text-sm text-surface-500">
                      Attend {s.classes_needed} more classes
                    </td>
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
