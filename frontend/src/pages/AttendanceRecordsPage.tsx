import { useEffect, useState, useCallback } from 'react';
import api, { isRequestCancelled } from '../services/api';
import { useAuth } from '../context/AuthContext';
import type { Subject, AttendanceRecord } from '../types';
import { TableSkeleton } from '../components/Skeleton';
import EmptyState from '../components/EmptyState';
import ErrorState from '../components/ErrorState';
import ConfirmDialog from '../components/ConfirmDialog';
import { History, Pencil, Trash2, Filter } from 'lucide-react';
import toast from 'react-hot-toast';

export default function AttendanceRecordsPage() {
  const { user } = useAuth();
  const isAdmin = user?.role === 'admin';

  const [records, setRecords] = useState<AttendanceRecord[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [subjects, setSubjects] = useState<Subject[]>([]);

  const [filterSubject, setFilterSubject] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [filterDateFrom, setFilterDateFrom] = useState('');
  const [filterDateTo, setFilterDateTo] = useState('');
  const [page, setPage] = useState(1);

  const [deleteRecord, setDeleteRecord] = useState<AttendanceRecord | null>(null);
  const [deleteLoading, setDeleteLoading] = useState(false);

  const [editRecord, setEditRecord] = useState<AttendanceRecord | null>(null);
  const [editStatus, setEditStatus] = useState('');
  const [editLoading, setEditLoading] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    api.get('/api/subjects', { signal: controller.signal })
      .then(res => setSubjects(res.data))
      .catch(err => {
        if (isRequestCancelled(err)) return;
      });
    return () => {
      controller.abort();
    };
  }, []);

  const fetchRecords = useCallback(async (signal?: AbortSignal) => {
    setLoading(true); setError('');
    try {
      const params: Record<string, string | number> = { page, limit: 30 };
      if (filterSubject) params.subject_id = filterSubject;
      if (filterStatus) params.status = filterStatus;
      if (filterDateFrom) params.date_from = filterDateFrom;
      if (filterDateTo) params.date_to = filterDateTo;
      const res = await api.get('/api/attendance', { params, signal });
      setRecords(res.data.records);
      setTotal(res.data.total);
    } catch (err: any) {
      if (isRequestCancelled(err)) return;
      setError(err.response?.data?.detail || 'Failed to load records');
    } finally {
      setLoading(false);
    }
  }, [filterSubject, filterStatus, filterDateFrom, filterDateTo, page]);

  useEffect(() => {
    const controller = new AbortController();
    fetchRecords(controller.signal);
    return () => {
      controller.abort();
    };
  }, [fetchRecords]);

  const handleEdit = async () => {
    if (!editRecord) return;
    setEditLoading(true);
    try {
      await api.put(`/api/attendance/${editRecord.id}`, { status: editStatus });
      toast.success('Record updated');
      setEditRecord(null);
      fetchRecords();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Update failed');
    } finally {
      setEditLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!deleteRecord) return;
    setDeleteLoading(true);
    try {
      await api.delete(`/api/attendance/${deleteRecord.id}`);
      toast.success('Record deleted');
      setDeleteRecord(null);
      fetchRecords();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Delete failed');
    } finally {
      setDeleteLoading(false);
    }
  };

  if (error) return <ErrorState message={error} onRetry={fetchRecords} />;

  return (
    <div className="space-y-6 fade-in">
      <div>
        <h1 className="text-2xl font-bold text-surface-900">
          {isAdmin ? 'Attendance Records' : 'Attendance History'}
        </h1>
        <p className="text-surface-500 text-sm mt-0.5">
          {isAdmin ? 'View and manage all attendance records' : 'View your attendance history'}
        </p>
      </div>

      {/* Filters */}
      <div className="card">
        <div className="flex items-center gap-2 mb-3">
          <Filter className="w-4 h-4 text-surface-400" />
          <span className="text-sm font-medium text-surface-600">Filters</span>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          <select value={filterSubject} onChange={(e) => { setFilterSubject(e.target.value); setPage(1); }} className="select">
            <option value="">All Subjects</option>
            {subjects.map(s => <option key={s.id} value={s.id}>{s.code} — {s.name}</option>)}
          </select>
          <select value={filterStatus} onChange={(e) => { setFilterStatus(e.target.value); setPage(1); }} className="select">
            <option value="">All Status</option>
            <option value="present">Present</option>
            <option value="absent">Absent</option>
          </select>
          <input type="date" value={filterDateFrom} onChange={(e) => { setFilterDateFrom(e.target.value); setPage(1); }}
            className="input" placeholder="From Date" />
          <input type="date" value={filterDateTo} onChange={(e) => { setFilterDateTo(e.target.value); setPage(1); }}
            className="input" placeholder="To Date" />
        </div>
      </div>

      {/* Records */}
      {loading ? <TableSkeleton /> : records.length === 0 ? (
        <EmptyState title="No records found" description="No attendance records match your filters."
          icon={<History className="w-8 h-8 text-surface-400" />} />
      ) : (
        <>
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Date</th>
                  {isAdmin && <th>Student</th>}
                  <th>Subject</th>
                  <th>Status</th>
                  <th>Marked By</th>
                  {isAdmin && <th>Actions</th>}
                </tr>
              </thead>
              <tbody>
                {records.map(r => (
                  <tr key={r.id}>
                    <td className="whitespace-nowrap">
                      {new Date(r.attendance_date).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' })}
                    </td>
                    {isAdmin && (
                      <td>
                        <div>
                          <p className="text-sm font-medium text-surface-800">{r.student_name}</p>
                          <p className="text-xs text-surface-400">{r.student_sid}</p>
                        </div>
                      </td>
                    )}
                    <td>
                      <span className="badge badge-info font-mono text-xs">{r.subject_code}</span>
                      <span className="ml-2 text-sm">{r.subject_name}</span>
                    </td>
                    <td>
                      <span className={`badge ${r.status === 'present' ? 'badge-success' : 'badge-danger'}`}>
                        {r.status === 'present' ? 'Present' : 'Absent'}
                      </span>
                    </td>
                    <td className="text-sm text-surface-500">{r.marker_name}</td>
                    {isAdmin && (
                      <td>
                        <div className="flex gap-1">
                          <button onClick={() => { setEditRecord(r); setEditStatus(r.status === 'present' ? 'absent' : 'present'); }}
                            className="btn btn-ghost btn-sm" aria-label="Edit"><Pencil className="w-3.5 h-3.5" /></button>
                          <button onClick={() => setDeleteRecord(r)}
                            className="btn btn-ghost btn-sm text-danger" aria-label="Delete"><Trash2 className="w-3.5 h-3.5" /></button>
                        </div>
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {total > 30 && (
            <div className="flex justify-center gap-2">
              <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page <= 1} className="btn btn-secondary btn-sm">Previous</button>
              <span className="flex items-center text-sm text-surface-500">Page {page} of {Math.ceil(total / 30)}</span>
              <button onClick={() => setPage(p => p + 1)} disabled={page >= Math.ceil(total / 30)} className="btn btn-secondary btn-sm">Next</button>
            </div>
          )}
        </>
      )}

      {/* Edit Confirm */}
      <ConfirmDialog
        isOpen={!!editRecord}
        title="Update Attendance"
        message={`Change status of ${editRecord?.student_name}'s attendance on ${editRecord ? new Date(editRecord.attendance_date).toLocaleDateString() : ''} to "${editStatus}"?`}
        confirmLabel="Update"
        variant="primary"
        loading={editLoading}
        onConfirm={handleEdit}
        onCancel={() => setEditRecord(null)}
      />

      {/* Delete Confirm */}
      <ConfirmDialog
        isOpen={!!deleteRecord}
        title="Delete Record"
        message={`Delete attendance record for ${deleteRecord?.student_name} on ${deleteRecord ? new Date(deleteRecord.attendance_date).toLocaleDateString() : ''}?`}
        confirmLabel="Delete"
        loading={deleteLoading}
        onConfirm={handleDelete}
        onCancel={() => setDeleteRecord(null)}
      />
    </div>
  );
}
