import { useEffect, useState } from 'react';
import api from '../services/api';
import type { Subject } from '../types';
import { TableSkeleton } from '../components/Skeleton';
import EmptyState from '../components/EmptyState';
import ErrorState from '../components/ErrorState';
import Modal from '../components/Modal';
import ConfirmDialog from '../components/ConfirmDialog';
import { Search, Plus, Pencil, Trash2, BookOpen, Loader2 } from 'lucide-react';
import toast from 'react-hot-toast';

export default function SubjectsPage() {
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [filterDept, setFilterDept] = useState('');
  const [filterYear, setFilterYear] = useState('');
  const [filterSem, setFilterSem] = useState('');

  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing] = useState<Subject | null>(null);
  const [formLoading, setFormLoading] = useState(false);
  const [form, setForm] = useState({ name: '', code: '', department: '', year: '', semester: '' });
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});

  const [deleteSubject, setDeleteSubject] = useState<Subject | null>(null);
  const [deleteLoading, setDeleteLoading] = useState(false);

  const fetchSubjects = async () => {
    setLoading(true); setError('');
    try {
      const params: Record<string, string> = {};
      if (search) params.search = search;
      if (filterDept) params.department = filterDept;
      if (filterYear) params.year = filterYear;
      if (filterSem) params.semester = filterSem;
      const res = await api.get('/api/subjects', { params });
      setSubjects(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load subjects');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchSubjects(); }, [search, filterDept, filterYear, filterSem]);

  const resetForm = () => {
    setForm({ name: '', code: '', department: '', year: '', semester: '' });
    setFormErrors({});
    setEditing(null);
  };

  const openAdd = () => { resetForm(); setShowModal(true); };
  const openEdit = (s: Subject) => {
    setEditing(s);
    setForm({ name: s.name, code: s.code, department: s.department, year: s.year.toString(), semester: s.semester.toString() });
    setFormErrors({});
    setShowModal(true);
  };

  const validateForm = () => {
    const errs: Record<string, string> = {};
    if (!form.name.trim()) errs.name = 'Required';
    if (!form.code.trim()) errs.code = 'Required';
    if (!form.department.trim()) errs.department = 'Required';
    if (!form.year) errs.year = 'Required';
    if (!form.semester) errs.semester = 'Required';
    setFormErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateForm()) return;
    setFormLoading(true);
    try {
      const payload = { name: form.name.trim(), code: form.code.trim().toUpperCase(), department: form.department.trim(), year: parseInt(form.year), semester: parseInt(form.semester) };
      if (editing) {
        await api.put(`/api/subjects/${editing.id}`, payload);
        toast.success('Subject updated');
      } else {
        await api.post('/api/subjects', payload);
        toast.success('Subject added');
      }
      setShowModal(false);
      fetchSubjects();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Operation failed');
    } finally {
      setFormLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!deleteSubject) return;
    setDeleteLoading(true);
    try {
      await api.delete(`/api/subjects/${deleteSubject.id}`);
      toast.success('Subject deleted');
      setDeleteSubject(null);
      fetchSubjects();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Delete failed');
    } finally {
      setDeleteLoading(false);
    }
  };

  const departments = [...new Set(subjects.map(s => s.department))];

  if (error) return <ErrorState message={error} onRetry={fetchSubjects} />;

  return (
    <div className="space-y-6 fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-surface-900">Subjects</h1>
          <p className="text-surface-500 text-sm mt-0.5">Manage course subjects</p>
        </div>
        <button onClick={openAdd} className="btn btn-primary">
          <Plus className="w-4 h-4" /> Add Subject
        </button>
      </div>

      <div className="card">
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-surface-400" />
            <input value={search} onChange={(e) => setSearch(e.target.value)}
              className="input pl-10" placeholder="Search subjects..." />
          </div>
          <select value={filterDept} onChange={(e) => setFilterDept(e.target.value)} className="select sm:w-40">
            <option value="">All Departments</option>
            {departments.map(d => <option key={d} value={d}>{d}</option>)}
          </select>
          <select value={filterYear} onChange={(e) => setFilterYear(e.target.value)} className="select sm:w-28">
            <option value="">All Years</option>
            {[1,2,3,4,5,6].map(y => <option key={y} value={y}>Year {y}</option>)}
          </select>
          <select value={filterSem} onChange={(e) => setFilterSem(e.target.value)} className="select sm:w-36">
            <option value="">All Semesters</option>
            {[1,2,3,4,5,6,7,8].map(s => <option key={s} value={s}>Semester {s}</option>)}
          </select>
        </div>
      </div>

      {loading ? <TableSkeleton /> : subjects.length === 0 ? (
        <EmptyState title="No subjects found" description="Add your first subject."
          icon={<BookOpen className="w-8 h-8 text-surface-400" />}
          action={<button onClick={openAdd} className="btn btn-primary btn-sm"><Plus className="w-4 h-4" /> Add Subject</button>} />
      ) : (
        <div className="table-container">
          <table className="table">
            <thead>
              <tr><th>Code</th><th>Name</th><th>Department</th><th>Year</th><th>Semester</th><th>Actions</th></tr>
            </thead>
            <tbody>
              {subjects.map(s => (
                <tr key={s.id}>
                  <td><span className="badge badge-info font-mono">{s.code}</span></td>
                  <td className="font-medium text-surface-800">{s.name}</td>
                  <td>{s.department}</td>
                  <td>{s.year}</td>
                  <td>{s.semester}</td>
                  <td>
                    <div className="flex gap-1">
                      <button onClick={() => openEdit(s)} className="btn btn-ghost btn-sm" aria-label="Edit"><Pencil className="w-3.5 h-3.5" /></button>
                      <button onClick={() => setDeleteSubject(s)} className="btn btn-ghost btn-sm text-danger" aria-label="Delete"><Trash2 className="w-3.5 h-3.5" /></button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <Modal isOpen={showModal} title={editing ? 'Edit Subject' : 'Add Subject'} onClose={() => setShowModal(false)}>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">Subject Name *</label>
              <input value={form.name} onChange={(e) => setForm({...form, name: e.target.value})}
                className={`input ${formErrors.name ? 'input-error' : ''}`} placeholder="Data Structures" />
              {formErrors.name && <p className="text-xs text-danger mt-1">{formErrors.name}</p>}
            </div>
            <div>
              <label className="label">Subject Code *</label>
              <input value={form.code} onChange={(e) => setForm({...form, code: e.target.value})}
                className={`input ${formErrors.code ? 'input-error' : ''}`} placeholder="CS201" />
              {formErrors.code && <p className="text-xs text-danger mt-1">{formErrors.code}</p>}
            </div>
          </div>
          <div>
            <label className="label">Department *</label>
            <input value={form.department} onChange={(e) => setForm({...form, department: e.target.value})}
              className={`input ${formErrors.department ? 'input-error' : ''}`} placeholder="Computer Science" />
            {formErrors.department && <p className="text-xs text-danger mt-1">{formErrors.department}</p>}
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">Year *</label>
              <select value={form.year} onChange={(e) => setForm({...form, year: e.target.value})}
                className={`select ${formErrors.year ? 'input-error' : ''}`}>
                <option value="">Select Year</option>
                {[1,2,3,4,5,6].map(y => <option key={y} value={y}>Year {y}</option>)}
              </select>
              {formErrors.year && <p className="text-xs text-danger mt-1">{formErrors.year}</p>}
            </div>
            <div>
              <label className="label">Semester *</label>
              <select value={form.semester} onChange={(e) => setForm({...form, semester: e.target.value})}
                className={`select ${formErrors.semester ? 'input-error' : ''}`}>
                <option value="">Select Semester</option>
                {[1,2,3,4,5,6,7,8,9,10,11,12].map(s => <option key={s} value={s}>Semester {s}</option>)}
              </select>
              {formErrors.semester && <p className="text-xs text-danger mt-1">{formErrors.semester}</p>}
            </div>
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={() => setShowModal(false)} className="btn btn-secondary">Cancel</button>
            <button type="submit" className="btn btn-primary" disabled={formLoading}>
              {formLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : (editing ? 'Update' : 'Add Subject')}
            </button>
          </div>
        </form>
      </Modal>

      <ConfirmDialog isOpen={!!deleteSubject} title="Delete Subject"
        message={`Delete ${deleteSubject?.name} (${deleteSubject?.code})? All related attendance records will be removed.`}
        confirmLabel="Delete" loading={deleteLoading} onConfirm={handleDelete} onCancel={() => setDeleteSubject(null)} />
    </div>
  );
}
