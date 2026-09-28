import { useEffect, useState } from 'react';
import api from '../services/api';
import type { StudentListItem } from '../types';
import { TableSkeleton } from '../components/Skeleton';
import EmptyState from '../components/EmptyState';
import ErrorState from '../components/ErrorState';
import Modal from '../components/Modal';
import ConfirmDialog from '../components/ConfirmDialog';
import { Search, Plus, Pencil, Trash2, Users, Loader2 } from 'lucide-react';
import toast from 'react-hot-toast';

export default function StudentsPage() {
  const [students, setStudents] = useState<StudentListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [filterDept, setFilterDept] = useState('');
  const [filterYear, setFilterYear] = useState('');
  const [filterSection, setFilterSection] = useState('');

  // Modal state
  const [showModal, setShowModal] = useState(false);
  const [editingStudent, setEditingStudent] = useState<StudentListItem | null>(null);
  const [formLoading, setFormLoading] = useState(false);
  const [form, setForm] = useState({
    full_name: '', email: '', password: '', student_id: '', department: '', year: '', section: '',
  });
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});

  // Delete state
  const [deleteStudent, setDeleteStudent] = useState<StudentListItem | null>(null);
  const [deleteLoading, setDeleteLoading] = useState(false);

  const fetchStudents = async () => {
    setLoading(true); setError('');
    try {
      const params: Record<string, string> = {};
      if (search) params.search = search;
      if (filterDept) params.department = filterDept;
      if (filterYear) params.year = filterYear;
      if (filterSection) params.section = filterSection;
      const res = await api.get('/api/students', { params });
      setStudents(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load students');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchStudents(); }, [search, filterDept, filterYear, filterSection]);

  const resetForm = () => {
    setForm({ full_name: '', email: '', password: '', student_id: '', department: '', year: '', section: '' });
    setFormErrors({});
    setEditingStudent(null);
  };

  const openAddModal = () => { resetForm(); setShowModal(true); };
  const openEditModal = (s: StudentListItem) => {
    setEditingStudent(s);
    setForm({
      full_name: s.full_name, email: s.email, password: '', student_id: s.student_id || '',
      department: s.department || '', year: s.year?.toString() || '', section: s.section || '',
    });
    setFormErrors({});
    setShowModal(true);
  };

  const validateForm = () => {
    const errs: Record<string, string> = {};
    if (!form.full_name.trim()) errs.full_name = 'Required';
    if (!form.email.trim()) errs.email = 'Required';
    if (!editingStudent && !form.password) errs.password = 'Required';
    if (form.password && form.password.length < 6) errs.password = 'Min 6 characters';
    if (!form.student_id.trim()) errs.student_id = 'Required';
    if (!form.department.trim()) errs.department = 'Required';
    if (!form.year) errs.year = 'Required';
    if (!form.section.trim()) errs.section = 'Required';
    setFormErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateForm()) return;
    setFormLoading(true);
    try {
      if (editingStudent) {
        await api.put(`/api/students/${editingStudent.id}`, {
          full_name: form.full_name.trim(),
          email: form.email.trim(),
          student_id: form.student_id.trim(),
          department: form.department.trim(),
          year: parseInt(form.year),
          section: form.section.trim(),
        });
        toast.success('Student updated');
      } else {
        await api.post('/api/students', {
          full_name: form.full_name.trim(),
          email: form.email.trim(),
          password: form.password,
          student_id: form.student_id.trim(),
          department: form.department.trim(),
          year: parseInt(form.year),
          section: form.section.trim(),
        });
        toast.success('Student added');
      }
      setShowModal(false);
      fetchStudents();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Operation failed');
    } finally {
      setFormLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!deleteStudent) return;
    setDeleteLoading(true);
    try {
      await api.delete(`/api/students/${deleteStudent.id}`);
      toast.success('Student deleted');
      setDeleteStudent(null);
      fetchStudents();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Delete failed');
    } finally {
      setDeleteLoading(false);
    }
  };

  const departments = [...new Set(students.map(s => s.department).filter(Boolean))];
  const sections = [...new Set(students.map(s => s.section).filter(Boolean))];

  if (error) return <ErrorState message={error} onRetry={fetchStudents} />;

  return (
    <div className="space-y-6 fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-surface-900">Students</h1>
          <p className="text-surface-500 text-sm mt-0.5">Manage student records</p>
        </div>
        <button onClick={openAddModal} className="btn btn-primary">
          <Plus className="w-4 h-4" /> Add Student
        </button>
      </div>

      {/* Filters */}
      <div className="card">
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-surface-400" />
            <input value={search} onChange={(e) => setSearch(e.target.value)}
              className="input pl-10" placeholder="Search by name, email, or ID..." />
          </div>
          <select value={filterDept} onChange={(e) => setFilterDept(e.target.value)} className="select sm:w-40">
            <option value="">All Departments</option>
            {departments.map(d => <option key={d} value={d}>{d}</option>)}
          </select>
          <select value={filterYear} onChange={(e) => setFilterYear(e.target.value)} className="select sm:w-28">
            <option value="">All Years</option>
            {[1,2,3,4,5,6].map(y => <option key={y} value={y}>Year {y}</option>)}
          </select>
          <select value={filterSection} onChange={(e) => setFilterSection(e.target.value)} className="select sm:w-32">
            <option value="">All Sections</option>
            {sections.map(s => <option key={s} value={s}>Section {s}</option>)}
          </select>
        </div>
      </div>

      {/* Table */}
      {loading ? <TableSkeleton /> : students.length === 0 ? (
        <EmptyState title="No students found" description="Add your first student or adjust your filters."
          icon={<Users className="w-8 h-8 text-surface-400" />}
          action={<button onClick={openAddModal} className="btn btn-primary btn-sm"><Plus className="w-4 h-4" /> Add Student</button>} />
      ) : (
        <div className="table-container">
          <table className="table">
            <thead>
              <tr>
                <th>Student</th>
                <th>Student ID</th>
                <th>Department</th>
                <th>Year / Section</th>
                <th>Attendance</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {students.map(s => (
                <tr key={s.id}>
                  <td>
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary-400 to-primary-600 flex items-center justify-center text-white text-xs font-semibold flex-shrink-0">
                        {s.full_name.charAt(0)}
                      </div>
                      <div className="min-w-0">
                        <p className="text-sm font-medium text-surface-800 truncate">{s.full_name}</p>
                        <p className="text-xs text-surface-400 truncate">{s.email}</p>
                      </div>
                    </div>
                  </td>
                  <td className="font-mono text-xs">{s.student_id}</td>
                  <td>{s.department}</td>
                  <td>{s.year} / {s.section}</td>
                  <td>
                    <div className="flex items-center gap-2">
                      <div className="progress-bar w-16">
                        <div className="progress-fill" style={{
                          width: `${s.attendance_percentage}%`,
                          background: s.attendance_percentage >= 75 ? '#10b981' : s.attendance_percentage >= 60 ? '#f59e0b' : '#ef4444',
                        }} />
                      </div>
                      <span className={`text-sm font-semibold ${
                        s.attendance_percentage >= 75 ? 'text-success' : s.attendance_percentage >= 60 ? 'text-warning' : 'text-danger'
                      }`}>{s.attendance_percentage}%</span>
                    </div>
                  </td>
                  <td>
                    <div className="flex gap-1">
                      <button onClick={() => openEditModal(s)} className="btn btn-ghost btn-sm" aria-label="Edit student">
                        <Pencil className="w-3.5 h-3.5" />
                      </button>
                      <button onClick={() => setDeleteStudent(s)} className="btn btn-ghost btn-sm text-danger" aria-label="Delete student">
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Add/Edit Modal */}
      <Modal isOpen={showModal} title={editingStudent ? 'Edit Student' : 'Add Student'} onClose={() => setShowModal(false)}>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="label">Full Name *</label>
            <input value={form.full_name} onChange={(e) => setForm({...form, full_name: e.target.value})}
              className={`input ${formErrors.full_name ? 'input-error' : ''}`} placeholder="John Doe" />
            {formErrors.full_name && <p className="text-xs text-danger mt-1">{formErrors.full_name}</p>}
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">Email *</label>
              <input type="email" value={form.email} onChange={(e) => setForm({...form, email: e.target.value})}
                className={`input ${formErrors.email ? 'input-error' : ''}`} placeholder="student@example.com" />
              {formErrors.email && <p className="text-xs text-danger mt-1">{formErrors.email}</p>}
            </div>
            <div>
              <label className="label">{editingStudent ? 'Password (leave blank to keep)' : 'Password *'}</label>
              <input type="password" value={form.password} onChange={(e) => setForm({...form, password: e.target.value})}
                className={`input ${formErrors.password ? 'input-error' : ''}`} placeholder="Min 6 characters" />
              {formErrors.password && <p className="text-xs text-danger mt-1">{formErrors.password}</p>}
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">Student ID *</label>
              <input value={form.student_id} onChange={(e) => setForm({...form, student_id: e.target.value})}
                className={`input ${formErrors.student_id ? 'input-error' : ''}`} placeholder="2024CS001" />
              {formErrors.student_id && <p className="text-xs text-danger mt-1">{formErrors.student_id}</p>}
            </div>
            <div>
              <label className="label">Department *</label>
              <input value={form.department} onChange={(e) => setForm({...form, department: e.target.value})}
                className={`input ${formErrors.department ? 'input-error' : ''}`} placeholder="Computer Science" />
              {formErrors.department && <p className="text-xs text-danger mt-1">{formErrors.department}</p>}
            </div>
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
              <label className="label">Section *</label>
              <input value={form.section} onChange={(e) => setForm({...form, section: e.target.value})}
                className={`input ${formErrors.section ? 'input-error' : ''}`} placeholder="A" />
              {formErrors.section && <p className="text-xs text-danger mt-1">{formErrors.section}</p>}
            </div>
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={() => setShowModal(false)} className="btn btn-secondary">Cancel</button>
            <button type="submit" className="btn btn-primary" disabled={formLoading}>
              {formLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : (editingStudent ? 'Update' : 'Add Student')}
            </button>
          </div>
        </form>
      </Modal>

      {/* Delete Confirm */}
      <ConfirmDialog
        isOpen={!!deleteStudent}
        title="Delete Student"
        message={`Are you sure you want to delete ${deleteStudent?.full_name}? This will remove all their attendance records.`}
        confirmLabel="Delete"
        loading={deleteLoading}
        onConfirm={handleDelete}
        onCancel={() => setDeleteStudent(null)}
      />
    </div>
  );
}
