import { useEffect, useState, useCallback, useMemo } from 'react';
import api from '../../services/api';
import type {
  LecturerAssignedSubjectItem,
  LecturerAttendanceSessionResponse,
} from '../../types';
import LoadingSpinner from '../../components/LoadingSpinner';
import EmptyState from '../../components/EmptyState';
import ErrorState from '../../components/ErrorState';
import toast from 'react-hot-toast';
import {
  ClipboardCheck,
  CheckCircle2,
  XCircle,
  Calendar,
  BookOpen,
  Users,
  Search,
  RotateCw,
  Save,
  Check,
  X,
  Info,
  Sparkles,
} from 'lucide-react';

export default function LecturerAttendancePage() {
  const [subjects, setSubjects] = useState<LecturerAssignedSubjectItem[]>([]);
  const [selectedSubjectId, setSelectedSubjectId] = useState<string>('');
  const [selectedDate, setSelectedDate] = useState<string>(
    new Date().toISOString().split('T')[0]
  );
  const [sessionData, setSessionData] = useState<LecturerAttendanceSessionResponse | null>(null);
  const [studentStatuses, setStudentStatuses] = useState<Record<string, 'present' | 'absent'>>({});
  
  const [loadingSubjects, setLoadingSubjects] = useState(true);
  const [loadingSession, setLoadingSession] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'present' | 'absent' | 'unmarked'>('all');

  const todayStr = useMemo(() => new Date().toISOString().split('T')[0], []);

  // 1. Fetch assigned subjects for current lecturer
  const fetchAssignedSubjects = useCallback(async () => {
    setLoadingSubjects(true);
    setError(null);
    try {
      const res = await api.get<LecturerAssignedSubjectItem[]>('/api/lecturer/subjects');
      setSubjects(res.data);
      if (res.data.length > 0 && !selectedSubjectId) {
        setSelectedSubjectId(res.data[0].id);
      }
    } catch (err: any) {
      setError(
        err.response?.data?.detail ||
          'Failed to load your assigned subjects. Please try again.'
      );
    } finally {
      setLoadingSubjects(false);
    }
  }, [selectedSubjectId]);

  useEffect(() => {
    fetchAssignedSubjects();
  }, [fetchAssignedSubjects]);

  // 2. Fetch session roster and existing attendance
  const fetchSession = useCallback(async () => {
    if (!selectedSubjectId || !selectedDate) return;
    setLoadingSession(true);
    try {
      const res = await api.get<LecturerAttendanceSessionResponse>(
        `/api/lecturer/attendance/session`,
        {
          params: {
            subject_id: selectedSubjectId,
            attendance_date: selectedDate,
          },
        }
      );
      setSessionData(res.data);

      // Pre-fill statuses from existing session records
      const initialMap: Record<string, 'present' | 'absent'> = {};
      res.data.students.forEach((s) => {
        if (s.status === 'present' || s.status === 'absent') {
          initialMap[s.student_id] = s.status;
        }
      });
      setStudentStatuses(initialMap);
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to load class roster for this session');
    } finally {
      setLoadingSession(false);
    }
  }, [selectedSubjectId, selectedDate]);

  useEffect(() => {
    if (selectedSubjectId && selectedDate) {
      fetchSession();
    }
  }, [fetchSession, selectedSubjectId, selectedDate]);

  // 3. Mark individual student status
  const handleSetStatus = (studentId: string, status: 'present' | 'absent') => {
    setStudentStatuses((prev) => ({
      ...prev,
      [studentId]: status,
    }));
  };

  // 4. Batch marking controls
  const handleMarkAll = (status: 'present' | 'absent') => {
    if (!sessionData) return;
    const updated: Record<string, 'present' | 'absent'> = { ...studentStatuses };
    sessionData.students.forEach((s) => {
      updated[s.student_id] = status;
    });
    setStudentStatuses(updated);
  };

  const handleClearAll = () => {
    setStudentStatuses({});
  };

  // 5. Submit attendance session to database
  const handleSubmitAttendance = async () => {
    if (!selectedSubjectId || !selectedDate || !sessionData) return;

    const records = Object.entries(studentStatuses).map(([student_id, status]) => ({
      student_id,
      status,
    }));

    if (records.length === 0) {
      toast.error('Please mark at least one student before saving.');
      return;
    }

    setSaving(true);
    try {
      const payload = {
        subject_id: selectedSubjectId,
        attendance_date: selectedDate,
        records,
      };

      const res = await api.post('/api/lecturer/attendance', payload);
      toast.success(
        `Attendance saved: ${res.data.present_count} present, ${res.data.absent_count} absent.`
      );
      // Reload session from database to reflect saved state
      await fetchSession();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to submit attendance session.');
    } finally {
      setSaving(false);
    }
  };

  // Summary counts
  const totalEnrolled = sessionData?.total_students || 0;
  const currentPresentCount = useMemo(
    () => Object.values(studentStatuses).filter((s) => s === 'present').length,
    [studentStatuses]
  );
  const currentAbsentCount = useMemo(
    () => Object.values(studentStatuses).filter((s) => s === 'absent').length,
    [studentStatuses]
  );
  const currentUnmarkedCount = Math.max(
    0,
    totalEnrolled - (currentPresentCount + currentAbsentCount)
  );

  const activeSubject = useMemo(
    () => subjects.find((s) => s.id === selectedSubjectId),
    [subjects, selectedSubjectId]
  );

  // Filtered students roster
  const filteredStudents = useMemo(() => {
    if (!sessionData) return [];
    return sessionData.students.filter((st) => {
      // Search query
      const matchesSearch =
        searchQuery.trim() === '' ||
        st.full_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (st.student_sid && st.student_sid.toLowerCase().includes(searchQuery.toLowerCase()));

      // Status filter
      const currentSt = studentStatuses[st.student_id];
      let matchesStatus = true;
      if (statusFilter === 'present') matchesStatus = currentSt === 'present';
      else if (statusFilter === 'absent') matchesStatus = currentSt === 'absent';
      else if (statusFilter === 'unmarked') matchesStatus = !currentSt;

      return matchesSearch && matchesStatus;
    });
  }, [sessionData, searchQuery, statusFilter, studentStatuses]);

  if (loadingSubjects) {
    return <LoadingSpinner text="Loading your assigned courses..." />;
  }

  if (error) {
    return <ErrorState message={error} onRetry={fetchAssignedSubjects} />;
  }

  if (subjects.length === 0) {
    return (
      <div className="card p-8 border border-surface-200 max-w-4xl mx-auto">
        <EmptyState
          title="No Subjects Assigned"
          description="You do not currently have any teaching subjects assigned to your faculty profile. Once an administrator assigns courses to you, you will be able to take attendance here."
          icon={<BookOpen className="w-10 h-10 text-surface-400" />}
        />
      </div>
    );
  }

  return (
    <div className="space-y-6 fade-in max-w-6xl mx-auto pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="badge badge-primary text-xs flex items-center gap-1">
              <ClipboardCheck className="w-3.5 h-3.5" />
              Module L3
            </span>
            <h1 className="text-2xl font-bold text-surface-900 tracking-tight">
              Class Attendance
            </h1>
          </div>
          <p className="text-surface-500 text-sm mt-0.5">
            Select an assigned course and session date to record or update student attendance.
          </p>
        </div>

        <button
          onClick={fetchSession}
          disabled={loadingSession || !selectedSubjectId}
          className="btn btn-secondary text-xs flex items-center gap-1.5 self-start sm:self-auto"
          title="Refresh current session data"
          aria-label="Refresh session roster"
        >
          <RotateCw className={`w-3.5 h-3.5 ${loadingSession ? 'animate-spin' : ''}`} />
          <span>Reload Session</span>
        </button>
      </div>

      {/* Session Controls: Subject & Date Selector */}
      <div className="card p-5 border border-surface-200 shadow-xs">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="label flex items-center justify-between text-xs font-semibold text-surface-700">
              <span className="flex items-center gap-1.5">
                <BookOpen className="w-3.5 h-3.5 text-indigo-600" />
                Teaching Subject
              </span>
              {activeSubject && (
                <span className="text-[0.7rem] text-surface-500 font-normal">
                  Year {activeSubject.year} · Sem {activeSubject.semester}
                </span>
              )}
            </label>
            <select
              value={selectedSubjectId}
              onChange={(e) => setSelectedSubjectId(e.target.value)}
              className="select w-full mt-1 font-medium"
              aria-label="Select teaching subject"
            >
              {subjects.map((sub) => (
                <option key={sub.id} value={sub.id}>
                  {sub.code} — {sub.name} ({sub.enrolled_students_count} students)
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="label flex items-center justify-between text-xs font-semibold text-surface-700">
              <span className="flex items-center gap-1.5">
                <Calendar className="w-3.5 h-3.5 text-indigo-600" />
                Session Date
              </span>
              <span className="text-[0.7rem] text-surface-400 font-normal">
                Max: Today ({todayStr})
              </span>
            </label>
            <input
              type="date"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              max={todayStr}
              className="input w-full mt-1 font-mono text-sm"
              aria-label="Select session date"
            />
          </div>
        </div>

        {/* Existing Session Alert Pill */}
        {sessionData && (
          <div className="mt-4 pt-3 border-t border-surface-100 flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              {sessionData.has_existing_records ? (
                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                  Existing Attendance Session Recorded
                </span>
              ) : (
                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200">
                  <Sparkles className="w-3.5 h-3.5 text-blue-600" />
                  New Session — Not Yet Recorded
                </span>
              )}
              <span className="text-xs text-surface-500">
                {sessionData.has_existing_records
                  ? 'Saving will update records in place without creating duplicates.'
                  : 'Mark students and click Save Attendance below.'}
              </span>
            </div>

            <div className="flex items-center gap-2 text-xs text-surface-500">
              <Users className="w-3.5 h-3.5" />
              <span>{totalEnrolled} students enrolled in {sessionData.subject_code}</span>
            </div>
          </div>
        )}
      </div>

      {/* Roster & Marking Area */}
      {loadingSession ? (
        <div className="card p-12 text-center border border-surface-200">
          <LoadingSpinner text="Loading session roster..." />
        </div>
      ) : !sessionData || sessionData.students.length === 0 ? (
        <div className="card p-10 text-center border border-surface-200">
          <EmptyState
            title="No Students Enrolled"
            description="There are currently no students enrolled in this course. You can only mark attendance once students are enrolled."
            icon={<Users className="w-10 h-10 text-surface-300" />}
          />
        </div>
      ) : (
        <div className="card p-5 border border-surface-200 shadow-xs space-y-4">
          {/* Quick Stats Bar & Batch Actions */}
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-4 border-b border-surface-100">
            {/* Tally badges */}
            <div className="flex flex-wrap items-center gap-2">
              <div className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-surface-100 text-surface-800 text-xs font-semibold">
                <span>Total:</span>
                <span className="font-bold">{totalEnrolled}</span>
              </div>
              <div className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-emerald-50 text-emerald-700 border border-emerald-200 text-xs font-semibold">
                <Check className="w-3.5 h-3.5" />
                <span>Present:</span>
                <span className="font-bold">{currentPresentCount}</span>
              </div>
              <div className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-rose-50 text-rose-700 border border-rose-200 text-xs font-semibold">
                <X className="w-3.5 h-3.5" />
                <span>Absent:</span>
                <span className="font-bold">{currentAbsentCount}</span>
              </div>
              {currentUnmarkedCount > 0 && (
                <div className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-amber-50 text-amber-700 border border-amber-200 text-xs font-semibold">
                  <Info className="w-3.5 h-3.5" />
                  <span>Unmarked:</span>
                  <span className="font-bold">{currentUnmarkedCount}</span>
                </div>
              )}
            </div>

            {/* Batch marking controls */}
            <div className="flex flex-wrap items-center gap-2">
              <button
                type="button"
                onClick={() => handleMarkAll('present')}
                className="btn btn-sm bg-emerald-50 hover:bg-emerald-100 text-emerald-700 border border-emerald-200 flex items-center gap-1.5"
                title="Mark all enrolled students as present"
              >
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                <span>Mark All Present</span>
              </button>
              <button
                type="button"
                onClick={() => handleMarkAll('absent')}
                className="btn btn-sm bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 flex items-center gap-1.5"
                title="Mark all enrolled students as absent"
              >
                <XCircle className="w-3.5 h-3.5 text-rose-600" />
                <span>Mark All Absent</span>
              </button>
              <button
                type="button"
                onClick={handleClearAll}
                className="btn btn-sm btn-secondary text-surface-500 hover:text-surface-700 text-xs"
                title="Clear all marked selections"
              >
                Clear
              </button>
            </div>
          </div>

          {/* Search & Filter Toolbar */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="relative flex-1 max-w-sm">
              <Search className="w-4 h-4 text-surface-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Search student by name or ID..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="input pl-9 text-xs w-full"
                aria-label="Search student roster"
              />
            </div>

            <div className="flex items-center gap-1 text-xs">
              <span className="text-surface-400 text-[0.7rem] uppercase font-semibold mr-1">Filter:</span>
              {(['all', 'present', 'absent', 'unmarked'] as const).map((filterKey) => (
                <button
                  key={filterKey}
                  onClick={() => setStatusFilter(filterKey)}
                  className={`px-2.5 py-1 rounded-md text-xs font-semibold capitalize transition-colors ${
                    statusFilter === filterKey
                      ? 'bg-surface-800 text-white shadow-xs'
                      : 'bg-surface-100 text-surface-600 hover:bg-surface-200'
                  }`}
                >
                  {filterKey}
                </button>
              ))}
            </div>
          </div>

          {/* Student Roster Table */}
          <div className="overflow-x-auto border border-surface-200 rounded-xl">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-surface-50 border-b border-surface-200 text-surface-600 font-semibold">
                  <th className="py-3 px-4 w-12 text-center">#</th>
                  <th className="py-3 px-4">Student</th>
                  <th className="py-3 px-4">Student Roll / ID</th>
                  <th className="py-3 px-4">Department</th>
                  <th className="py-3 px-4 text-center w-56">Attendance Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-surface-100 bg-white">
                {filteredStudents.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="py-8 text-center text-surface-400 text-xs">
                      No students matching your search criteria.
                    </td>
                  </tr>
                ) : (
                  filteredStudents.map((student, idx) => {
                    const currentStatus = studentStatuses[student.student_id];
                    return (
                      <tr
                        key={student.student_id}
                        className={`hover:bg-surface-50/70 transition-colors ${
                          currentStatus === 'present'
                            ? 'bg-emerald-50/20'
                            : currentStatus === 'absent'
                            ? 'bg-rose-50/20'
                            : ''
                        }`}
                      >
                        <td className="py-3 px-4 text-center font-mono text-surface-400 text-[0.75rem]">
                          {idx + 1}
                        </td>
                        <td className="py-3 px-4">
                          <div className="flex items-center gap-2.5">
                            <div className="w-7 h-7 rounded-full bg-indigo-100 text-indigo-700 flex items-center justify-center font-bold text-[0.7rem] flex-shrink-0">
                              {student.full_name.charAt(0).toUpperCase()}
                            </div>
                            <span className="font-semibold text-surface-900 text-sm">
                              {student.full_name}
                            </span>
                          </div>
                        </td>
                        <td className="py-3 px-4 font-mono text-surface-700 font-medium">
                          {student.student_sid || '—'}
                        </td>
                        <td className="py-3 px-4 text-surface-500">
                          {student.department || 'Computer Science'}
                        </td>
                        <td className="py-3 px-4 text-center">
                          <div className="inline-flex rounded-lg border border-surface-200 p-0.5 bg-surface-50 shadow-2xs">
                            <button
                              type="button"
                              onClick={() => handleSetStatus(student.student_id, 'present')}
                              className={`px-3 py-1 rounded-md text-xs font-semibold flex items-center gap-1.5 transition-all ${
                                currentStatus === 'present'
                                  ? 'bg-emerald-600 text-white shadow-xs font-bold'
                                  : 'text-surface-600 hover:text-emerald-700 hover:bg-emerald-50'
                              }`}
                              aria-pressed={currentStatus === 'present'}
                            >
                              <Check className="w-3.5 h-3.5" />
                              <span>Present</span>
                            </button>
                            <button
                              type="button"
                              onClick={() => handleSetStatus(student.student_id, 'absent')}
                              className={`px-3 py-1 rounded-md text-xs font-semibold flex items-center gap-1.5 transition-all ${
                                currentStatus === 'absent'
                                  ? 'bg-rose-600 text-white shadow-xs font-bold'
                                  : 'text-surface-600 hover:text-rose-700 hover:bg-rose-50'
                              }`}
                              aria-pressed={currentStatus === 'absent'}
                            >
                              <X className="w-3.5 h-3.5" />
                              <span>Absent</span>
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>

          {/* Action Footer */}
          <div className="pt-4 border-t border-surface-100 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="text-xs text-surface-500">
              <span>Ready to submit for </span>
              <strong className="text-surface-800">{activeSubject?.code}</strong>
              <span> on </span>
              <strong className="text-surface-800">{selectedDate}</strong>
              <span> ({currentPresentCount + currentAbsentCount} of {totalEnrolled} marked).</span>
            </div>

            <button
              type="button"
              onClick={handleSubmitAttendance}
              disabled={saving || currentPresentCount + currentAbsentCount === 0}
              className="btn btn-primary flex items-center gap-2 self-end sm:self-auto shadow-sm disabled:opacity-50"
            >
              <Save className={`w-4 h-4 ${saving ? 'animate-spin' : ''}`} />
              <span>{sessionData.has_existing_records ? 'Update Attendance' : 'Save Attendance'}</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
