import { useEffect, useState } from 'react';
import api from '../services/api';
import type { SubjectStats } from '../types';
import LoadingSpinner from '../components/LoadingSpinner';
import EmptyState from '../components/EmptyState';
import ErrorState from '../components/ErrorState';
import EnrollSubjectsModal from '../components/EnrollSubjectsModal';
import { BookOpen, BookPlus, CheckCircle2, XCircle, AlertTriangle } from 'lucide-react';

export default function MySubjectsPage() {
  const [subjects, setSubjects] = useState<SubjectStats[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [enrollModalOpen, setEnrollModalOpen] = useState(false);

  const fetchData = async () => {
    setLoading(true); setError('');
    try {
      const res = await api.get('/api/dashboard/student');
      setSubjects(res.data.subjects);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load subjects');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  const getColor = (pct: number, total: number = 1) => {
    if (total === 0) return { bg: 'bg-surface-300', text: 'text-surface-500', badge: 'badge-secondary' };
    if (pct >= 75) return { bg: 'bg-emerald-500', text: 'text-success', badge: 'badge-success' };
    if (pct >= 60) return { bg: 'bg-amber-500', text: 'text-warning', badge: 'badge-warning' };
    return { bg: 'bg-red-500', text: 'text-danger', badge: 'badge-danger' };
  };

  if (loading) return <LoadingSpinner text="Loading subjects..." />;
  if (error) return <ErrorState message={error} onRetry={fetchData} />;

  return (
    <div className="space-y-6 fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-surface-900">My Subjects</h1>
          <p className="text-surface-500 text-sm mt-0.5">Your enrolled subjects and attendance breakdown</p>
        </div>
        <button
          onClick={() => setEnrollModalOpen(true)}
          className="btn btn-primary flex items-center gap-2 self-start sm:self-auto shadow-sm"
        >
          <BookPlus className="w-4 h-4" />
          Enroll Subjects
        </button>
      </div>

      {subjects.length === 0 ? (
        <EmptyState
          title="No subjects"
          description="You haven't been enrolled in any subjects yet."
          icon={<BookOpen className="w-8 h-8 text-surface-400" />}
          action={
            <button
              onClick={() => setEnrollModalOpen(true)}
              className="btn btn-primary mt-4 inline-flex items-center gap-2"
            >
              <BookPlus className="w-4 h-4" />
              Enroll Subjects
            </button>
          }
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {subjects.map((sub, i) => {
            const color = getColor(sub.percentage, sub.total_classes);
            return (
              <div key={sub.subject_id} className="card card-hover fade-in" style={{ animationDelay: `${i * 0.05}s` }}>
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <span className="badge badge-info font-mono text-xs">{sub.subject_code}</span>
                    <h3 className="text-base font-semibold text-surface-800 mt-1.5">{sub.subject_name}</h3>
                  </div>
                  <div className="text-right">
                    <p className={`text-2xl font-bold ${color.text}`}>{sub.percentage}%</p>
                    {sub.percentage < 75 && sub.total_classes > 0 && (
                      <div className="flex items-center gap-1 mt-1">
                        <AlertTriangle className="w-3 h-3 text-warning" />
                        <span className="text-xs text-warning font-medium">Low</span>
                      </div>
                    )}
                  </div>
                </div>

                <div className="progress-bar mb-3">
                  <div className={`progress-fill ${color.bg}`} style={{ width: `${sub.percentage}%` }} />
                </div>

                <div className="flex justify-between text-xs text-surface-500">
                  <div className="flex items-center gap-1">
                    <CheckCircle2 className="w-3.5 h-3.5 text-success" />
                    <span>{sub.present} present</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <XCircle className="w-3.5 h-3.5 text-danger" />
                    <span>{sub.absent} absent</span>
                  </div>
                  <span>{sub.present} / {sub.total_classes} classes</span>
                </div>
              </div>
            );
          })}
        </div>
      )}

      <EnrollSubjectsModal
        isOpen={enrollModalOpen}
        onClose={() => setEnrollModalOpen(false)}
        onEnrolled={fetchData}
      />
    </div>
  );
}
