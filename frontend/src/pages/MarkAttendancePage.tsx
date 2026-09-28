import { useEffect, useState } from 'react';
import api from '../services/api';
import type { Subject } from '../types';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorState from '../components/ErrorState';
import { ClipboardCheck, CheckCircle2, XCircle, Loader2, Calendar } from 'lucide-react';
import toast from 'react-hot-toast';

interface StudentRow {
  id: string;
  full_name: string;
  student_id: string;
  status: 'present' | 'absent';
}

export default function MarkAttendancePage() {
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [selectedSubject, setSelectedSubject] = useState('');
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [students, setStudents] = useState<StudentRow[]>([]);
  const [loadingSubjects, setLoadingSubjects] = useState(true);
  const [loadingStudents, setLoadingStudents] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchSubjects = async () => {
      try {
        const res = await api.get('/api/subjects');
        setSubjects(res.data);
      } catch {
        setError('Failed to load subjects');
      } finally {
        setLoadingSubjects(false);
      }
    };
    fetchSubjects();
  }, []);

  const loadStudents = async () => {
    if (!selectedSubject) return;
    setLoadingStudents(true);
    setSubmitted(false);
    try {
      const res = await api.get(`/api/subjects/${selectedSubject}/students`);
      setStudents(res.data.map((s: any) => ({ id: s.id, full_name: s.full_name, student_id: s.student_id, status: 'present' as const })));
    } catch {
      toast.error('Failed to load students');
    } finally {
      setLoadingStudents(false);
    }
  };

  useEffect(() => { if (selectedSubject) loadStudents(); }, [selectedSubject]);

  const toggleStatus = (studentId: string) => {
    setStudents(prev => prev.map(s =>
      s.id === studentId ? { ...s, status: s.status === 'present' ? 'absent' : 'present' } : s
    ));
  };

  const markAll = (status: 'present' | 'absent') => {
    setStudents(prev => prev.map(s => ({ ...s, status })));
  };

  const handleSubmit = async () => {
    if (!selectedSubject || !selectedDate || students.length === 0) return;
    setSubmitting(true);
    try {
      await api.post('/api/attendance', {
        subject_id: selectedSubject,
        attendance_date: selectedDate,
        records: students.map(s => ({ student_id: s.id, status: s.status })),
      });
      toast.success('Attendance marked successfully!');
      setSubmitted(true);
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to submit attendance');
    } finally {
      setSubmitting(false);
    }
  };

  const presentCount = students.filter(s => s.status === 'present').length;
  const absentCount = students.filter(s => s.status === 'absent').length;

  if (loadingSubjects) return <LoadingSpinner text="Loading subjects..." />;
  if (error) return <ErrorState message={error} />;

  return (
    <div className="space-y-6 fade-in">
      <div>
        <h1 className="text-2xl font-bold text-surface-900">Mark Attendance</h1>
        <p className="text-surface-500 text-sm mt-0.5">Select subject and date to mark attendance</p>
      </div>

      {/* Controls */}
      <div className="card">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="label">Subject</label>
            <select value={selectedSubject} onChange={(e) => setSelectedSubject(e.target.value)} className="select">
              <option value="">Select Subject</option>
              {subjects.map(s => <option key={s.id} value={s.id}>{s.code} — {s.name}</option>)}
            </select>
          </div>
          <div>
            <label className="label flex items-center gap-1.5">
              <Calendar className="w-3.5 h-3.5" /> Date
            </label>
            <input type="date" value={selectedDate} onChange={(e) => setSelectedDate(e.target.value)}
              className="input" max={new Date().toISOString().split('T')[0]} />
          </div>
        </div>
      </div>

      {/* Student List */}
      {selectedSubject && (
        loadingStudents ? <LoadingSpinner text="Loading students..." /> :
        students.length === 0 ? (
          <div className="card text-center py-12">
            <ClipboardCheck className="w-10 h-10 text-surface-300 mx-auto mb-3" />
            <p className="text-surface-600 font-medium">No students enrolled</p>
            <p className="text-sm text-surface-400 mt-1">Enroll students in this subject first</p>
          </div>
        ) : submitted ? (
          <div className="card text-center py-12 fade-in">
            <CheckCircle2 className="w-14 h-14 text-success mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-surface-900 mb-2">Attendance Submitted!</h3>
            <p className="text-surface-500 mb-1">{presentCount} present, {absentCount} absent</p>
            <p className="text-sm text-surface-400 mb-6">
              {subjects.find(s => s.id === selectedSubject)?.name} — {new Date(selectedDate).toLocaleDateString()}
            </p>
            <button onClick={() => { setSubmitted(false); setSelectedSubject(''); }}
              className="btn btn-primary">Mark Another</button>
          </div>
        ) : (
          <div className="card">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-4 gap-3">
              <div className="flex items-center gap-4">
                <span className="text-sm font-medium text-surface-600">{students.length} students</span>
                <div className="flex gap-2 text-xs">
                  <span className="badge badge-success">{presentCount} Present</span>
                  <span className="badge badge-danger">{absentCount} Absent</span>
                </div>
              </div>
              <div className="flex gap-2">
                <button onClick={() => markAll('present')} className="btn btn-sm btn-secondary text-success">
                  <CheckCircle2 className="w-3.5 h-3.5" /> All Present
                </button>
                <button onClick={() => markAll('absent')} className="btn btn-sm btn-secondary text-danger">
                  <XCircle className="w-3.5 h-3.5" /> All Absent
                </button>
              </div>
            </div>

            <div className="table-container">
              <table className="table">
                <thead>
                  <tr><th>Student</th><th>Student ID</th><th>Status</th></tr>
                </thead>
                <tbody>
                  {students.map(s => (
                    <tr key={s.id}>
                      <td className="font-medium text-surface-800">{s.full_name}</td>
                      <td className="font-mono text-xs">{s.student_id}</td>
                      <td>
                        <div className="flex gap-2">
                          <button
                            onClick={() => toggleStatus(s.id)}
                            className={`btn btn-sm ${s.status === 'present'
                              ? 'bg-emerald-100 text-emerald-700 border border-emerald-200'
                              : 'btn-secondary'}`}
                          >
                            <CheckCircle2 className="w-3.5 h-3.5" /> Present
                          </button>
                          <button
                            onClick={() => toggleStatus(s.id)}
                            className={`btn btn-sm ${s.status === 'absent'
                              ? 'bg-red-100 text-red-700 border border-red-200'
                              : 'btn-secondary'}`}
                          >
                            <XCircle className="w-3.5 h-3.5" /> Absent
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="flex justify-end mt-4">
              <button onClick={handleSubmit} className="btn btn-primary btn-lg" disabled={submitting}>
                {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <ClipboardCheck className="w-4 h-4" />}
                Submit Attendance
              </button>
            </div>
          </div>
        )
      )}
    </div>
  );
}
