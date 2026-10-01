import React, { useEffect, useState, useCallback, useMemo } from 'react';
import api from '../../services/api';
import type {
  StudentListItem,
  StudentSummaryMetrics,
  StudentListResponse,
  StudentDetailResponse,
} from '../../types';
import { TableSkeleton } from '../../components/Skeleton';
import EmptyState from '../../components/EmptyState';
import ErrorState from '../../components/ErrorState';
import Modal from '../../components/Modal';
import ConfirmDialog from '../../components/ConfirmDialog';
import {
  Users,
  UserCheck,
  UserX,
  AlertTriangle,
  Search,
  Plus,
  Eye,
  Pencil,
  Power,
  RotateCw,
  X,
  ChevronLeft,
  ChevronRight,
  CalendarCheck,
  BookOpen,
} from 'lucide-react';
import toast from 'react-hot-toast';

export default function AdminStudentsPage() {
  // Data state
  const [students, setStudents] = useState<StudentListItem[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [currentPage, setCurrentPage] = useState(1);
  const [summary, setSummary] = useState<StudentSummaryMetrics | null>(null);

  // Loading & error states
  const [loading, setLoading] = useState(true);
  const [summaryLoading, setSummaryLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'inactive'>('all');
  const [deptFilter, setDeptFilter] = useState('');
  const [yearFilter, setYearFilter] = useState('');
  const [sectionFilter, setSectionFilter] = useState('');
  const [attendanceFilter, setAttendanceFilter] = useState<'all' | 'above_75' | 'below_75'>('all');

  // Modals & action states
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showViewModal, setShowViewModal] = useState(false);
  const [selectedStudentDetail, setSelectedStudentDetail] = useState<StudentDetailResponse | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  // Status toggle confirmation
  const [confirmStudent, setConfirmStudent] = useState<StudentListItem | null>(null);
  const [confirmAction, setConfirmAction] = useState<'disable' | 'enable' | null>(null);
  const [statusActionLoading, setStatusActionLoading] = useState(false);

  // Form states
  const [formLoading, setFormLoading] = useState(false);
  const [formData, setFormData] = useState({
    id: '',
    student_id: '',
    full_name: '',
    email: '',
    password: '',
    department: '',
    year: '1',
    section: 'A',
  });
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});

  // Fetch summary statistics
  const fetchSummary = useCallback(async () => {
    setSummaryLoading(true);
    try {
      const res = await api.get<StudentSummaryMetrics>('/api/admin/students/summary');
      setSummary(res.data);
    } catch {
      // Fallback: don't break main page if summary fails temporarily
    } finally {
      setSummaryLoading(false);
    }
  }, []);

  // Fetch students table data
  const fetchStudents = useCallback(async (isManualRefresh = false) => {
    if (isManualRefresh) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }
    setError(null);

    try {
      const params: Record<string, string | number> = {
        page: currentPage,
        limit: 10,
      };

      if (search.trim()) params.search = search.trim();
      if (statusFilter !== 'all') params.status = statusFilter;
      if (deptFilter.trim()) params.department = deptFilter.trim();
      if (yearFilter.trim()) params.year = yearFilter.trim();
      if (sectionFilter.trim()) params.section = sectionFilter.trim();
      if (attendanceFilter !== 'all') params.attendance = attendanceFilter;

      const res = await api.get<StudentListResponse | StudentListItem[]>('/api/admin/students', { params });

      if (Array.isArray(res.data)) {
        setStudents(res.data);
        setTotalCount(res.data.length);
        setTotalPages(1);
      } else {
        setStudents(res.data.items || []);
        setTotalCount(res.data.total || 0);
        setTotalPages(res.data.pages || 1);
      }
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message || 'Unable to load students.';
      setError(msg);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [currentPage, search, statusFilter, deptFilter, yearFilter, sectionFilter, attendanceFilter]);

  useEffect(() => {
    fetchSummary();
  }, [fetchSummary]);

  useEffect(() => {
    fetchStudents();
  }, [fetchStudents]);

  // Reset page when filters change
  const handleFilterChange = (setter: (val: any) => void, value: any) => {
    setter(value);
    setCurrentPage(1);
  };

  const handleResetFilters = () => {
    setSearch('');
    setStatusFilter('all');
    setDeptFilter('');
    setYearFilter('');
    setSectionFilter('');
    setAttendanceFilter('all');
    setCurrentPage(1);
  };

  const hasActiveFilters = useMemo(() => {
    return (
      Boolean(search.trim()) ||
      statusFilter !== 'all' ||
      Boolean(deptFilter.trim()) ||
      Boolean(yearFilter.trim()) ||
      Boolean(sectionFilter.trim()) ||
      attendanceFilter !== 'all'
    );
  }, [search, statusFilter, deptFilter, yearFilter, sectionFilter, attendanceFilter]);

  // Open Add Student Modal
  const openAddStudentModal = () => {
    setFormData({
      id: '',
      student_id: '',
      full_name: '',
      email: '',
      password: '',
      department: 'CSE',
      year: '1',
      section: 'A',
    });
    setFormErrors({});
    setShowAddModal(true);
  };

  // Open Edit Student Modal
  const openEditStudentModal = (student: StudentListItem) => {
    setFormData({
      id: student.id,
      student_id: student.student_id || '',
      full_name: student.full_name,
      email: student.email,
      password: '',
      department: student.department || 'CSE',
      year: student.year ? student.year.toString() : '1',
      section: student.section || 'A',
    });
    setFormErrors({});
    setShowEditModal(true);
  };

  // Open View Student Details Modal
  const openViewStudentModal = async (studentId: string) => {
    setShowViewModal(true);
    setDetailLoading(true);
    setSelectedStudentDetail(null);
    try {
      const res = await api.get<StudentDetailResponse>(`/api/admin/students/${studentId}`);
      setSelectedStudentDetail(res.data);
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to load student details.');
      setShowViewModal(false);
    } finally {
      setDetailLoading(false);
    }
  };

  // Validate Add Form
  const validateAddForm = () => {
    const errors: Record<string, string> = {};
    if (!formData.student_id.trim()) errors.student_id = 'Student ID is required';
    if (!formData.full_name.trim()) errors.full_name = 'Full name is required';
    if (!formData.email.trim()) {
      errors.email = 'Email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email.trim())) {
      errors.email = 'Valid email is required';
    }
    if (!formData.password) {
      errors.password = 'Password is required';
    } else if (formData.password.length < 6) {
      errors.password = 'Password must be at least 6 characters';
    }
    if (!formData.department.trim()) errors.department = 'Department is required';
    if (!formData.year) errors.year = 'Year is required';
    if (!formData.section.trim()) errors.section = 'Section is required';

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  // Validate Edit Form
  const validateEditForm = () => {
    const errors: Record<string, string> = {};
    if (!formData.full_name.trim()) errors.full_name = 'Full name is required';
    if (!formData.email.trim()) {
      errors.email = 'Email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email.trim())) {
      errors.email = 'Valid email is required';
    }
    if (!formData.department.trim()) errors.department = 'Department is required';
    if (!formData.year) errors.year = 'Year is required';
    if (!formData.section.trim()) errors.section = 'Section is required';

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  // Handle Add Student Submit
  const handleAddStudentSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateAddForm()) return;

    setFormLoading(true);
    try {
      await api.post('/api/admin/students', {
        student_id: formData.student_id.trim(),
        full_name: formData.full_name.trim(),
        email: formData.email.trim().toLowerCase(),
        password: formData.password,
        department: formData.department.trim(),
        year: parseInt(formData.year, 10),
        section: formData.section.trim().toUpperCase(),
      });

      toast.success('Student created successfully.');
      setShowAddModal(false);
      fetchStudents();
      fetchSummary();
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Failed to create student.';
      toast.error(msg);
    } finally {
      setFormLoading(false);
    }
  };

  // Handle Edit Student Submit
  const handleEditStudentSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateEditForm()) return;

    setFormLoading(true);
    try {
      await api.put(`/api/admin/students/${formData.id}`, {
        student_id: formData.student_id.trim() || undefined,
        full_name: formData.full_name.trim(),
        email: formData.email.trim().toLowerCase(),
        department: formData.department.trim(),
        year: parseInt(formData.year, 10),
        section: formData.section.trim().toUpperCase(),
      });

      toast.success('Student updated successfully.');
      setShowEditModal(false);
      fetchStudents();
      fetchSummary();
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Failed to update student.';
      toast.error(msg);
    } finally {
      setFormLoading(false);
    }
  };

  // Handle Status Toggle (Disable/Enable)
  const handleConfirmStatusAction = async () => {
    if (!confirmStudent || !confirmAction) return;

    setStatusActionLoading(true);
    try {
      if (confirmAction === 'disable') {
        await api.post(`/api/admin/students/${confirmStudent.id}/disable`);
        toast.success('Student account disabled.');
      } else {
        await api.post(`/api/admin/students/${confirmStudent.id}/enable`);
        toast.success('Student account enabled.');
      }

      setConfirmStudent(null);
      setConfirmAction(null);
      fetchStudents();
      fetchSummary();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || `Failed to ${confirmAction} student account.`);
    } finally {
      setStatusActionLoading(false);
    }
  };

  return (
    <div className="space-y-6 fade-in">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-surface-200">
        <div>
          <h1 className="text-2xl font-bold text-surface-900 tracking-tight">Student Management</h1>
          <p className="text-sm text-surface-500 mt-0.5">
            Manage student accounts and view attendance information.
          </p>
        </div>
        <div className="flex items-center gap-2.5">
          <button
            onClick={() => {
              fetchStudents(true);
              fetchSummary();
            }}
            disabled={refreshing}
            className="btn btn-secondary btn-sm flex items-center gap-1.5 focus:outline-none focus:ring-2 focus:ring-primary-500/50"
            aria-label="Refresh student list"
          >
            <RotateCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin' : ''}`} />
            <span>{refreshing ? 'Updating...' : 'Refresh'}</span>
          </button>
          <button
            onClick={openAddStudentModal}
            className="btn btn-primary btn-sm flex items-center gap-1.5 shadow-xs"
            aria-label="Add new student"
          >
            <Plus className="w-4 h-4" />
            <span>Add Student</span>
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Students */}
        <div className="card p-4 flex flex-col justify-between border border-surface-200 shadow-xs">
          <div className="flex items-start justify-between mb-3">
            <span className="text-xs font-semibold uppercase tracking-wider text-surface-500">
              Total Students
            </span>
            <div className="w-9 h-9 rounded-xl flex items-center justify-center bg-blue-50 text-blue-700 shadow-xs">
              <Users className="w-4 h-4" aria-hidden="true" />
            </div>
          </div>
          <div>
            <p className="text-2xl font-bold text-surface-900 tracking-tight">
              {summaryLoading ? '...' : summary?.total_students ?? 0}
            </p>
            <p className="text-xs text-surface-400 mt-1">Enrolled student directory</p>
          </div>
        </div>

        {/* Active Students */}
        <div className="card p-4 flex flex-col justify-between border border-surface-200 shadow-xs">
          <div className="flex items-start justify-between mb-3">
            <span className="text-xs font-semibold uppercase tracking-wider text-surface-500">
              Active Students
            </span>
            <div className="w-9 h-9 rounded-xl flex items-center justify-center bg-emerald-50 text-emerald-700 shadow-xs">
              <UserCheck className="w-4 h-4" aria-hidden="true" />
            </div>
          </div>
          <div>
            <p className="text-2xl font-bold text-surface-900 tracking-tight">
              {summaryLoading ? '...' : summary?.active_students ?? 0}
            </p>
            <p className="text-xs text-surface-400 mt-1">Authorized for attendance & portal</p>
          </div>
        </div>

        {/* Inactive Students */}
        <div className="card p-4 flex flex-col justify-between border border-surface-200 shadow-xs">
          <div className="flex items-start justify-between mb-3">
            <span className="text-xs font-semibold uppercase tracking-wider text-surface-500">
              Inactive Students
            </span>
            <div className="w-9 h-9 rounded-xl flex items-center justify-center bg-amber-50 text-amber-700 shadow-xs">
              <UserX className="w-4 h-4" aria-hidden="true" />
            </div>
          </div>
          <div>
            <p className="text-2xl font-bold text-surface-900 tracking-tight">
              {summaryLoading ? '...' : summary?.inactive_students ?? 0}
            </p>
            <p className="text-xs text-surface-400 mt-1">Suspended or disabled accounts</p>
          </div>
        </div>

        {/* Students Below 75% */}
        <div className="card p-4 flex flex-col justify-between border border-surface-200 shadow-xs">
          <div className="flex items-start justify-between mb-3">
            <span className="text-xs font-semibold uppercase tracking-wider text-surface-500">
              Students Below 75%
            </span>
            <div className="w-9 h-9 rounded-xl flex items-center justify-center bg-red-50 text-red-700 shadow-xs">
              <AlertTriangle className="w-4 h-4" aria-hidden="true" />
            </div>
          </div>
          <div>
            <p className="text-2xl font-bold text-surface-900 tracking-tight text-red-600">
              {summaryLoading ? '...' : summary?.below_threshold_students ?? 0}
            </p>
            <p className="text-xs text-surface-400 mt-1">Immediate intervention required</p>
          </div>
        </div>
      </div>

      {/* Search & Filter Toolbar */}
      <div className="card p-4 border border-surface-200 shadow-xs space-y-3">
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-3">
          {/* Search box */}
          <div className="relative md:col-span-2">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-surface-400" />
            <input
              type="text"
              placeholder="Search by ID, name, email..."
              value={search}
              onChange={(e) => handleFilterChange(setSearch, e.target.value)}
              className="input pl-9 text-xs w-full"
              aria-label="Search students"
            />
          </div>

          {/* Status Filter */}
          <div>
            <select
              value={statusFilter}
              onChange={(e) => handleFilterChange(setStatusFilter, e.target.value)}
              className="input text-xs w-full cursor-pointer"
              aria-label="Filter by account status"
            >
              <option value="all">All Statuses</option>
              <option value="active">Active Only</option>
              <option value="inactive">Inactive Only</option>
            </select>
          </div>

          {/* Department Filter */}
          <div>
            <select
              value={deptFilter}
              onChange={(e) => handleFilterChange(setDeptFilter, e.target.value)}
              className="input text-xs w-full cursor-pointer"
              aria-label="Filter by department"
            >
              <option value="">All Departments</option>
              <option value="CSE">CSE</option>
              <option value="ECE">ECE</option>
              <option value="MECH">MECH</option>
              <option value="CIVIL">CIVIL</option>
              <option value="IT">IT</option>
              <option value="EEE">EEE</option>
            </select>
          </div>

          {/* Year Filter */}
          <div>
            <select
              value={yearFilter}
              onChange={(e) => handleFilterChange(setYearFilter, e.target.value)}
              className="input text-xs w-full cursor-pointer"
              aria-label="Filter by academic year"
            >
              <option value="">All Years</option>
              <option value="1">Year 1</option>
              <option value="2">Year 2</option>
              <option value="3">Year 3</option>
              <option value="4">Year 4</option>
            </select>
          </div>

          {/* Attendance Filter */}
          <div>
            <select
              value={attendanceFilter}
              onChange={(e) => handleFilterChange(setAttendanceFilter, e.target.value)}
              className="input text-xs w-full cursor-pointer"
              aria-label="Filter by attendance rate"
            >
              <option value="all">All Attendance</option>
              <option value="above_75">&ge; 75% (Good)</option>
              <option value="below_75">&lt; 75% (Low)</option>
            </select>
          </div>
        </div>

        {/* Section filter & Reset filter row */}
        <div className="flex items-center justify-between pt-2 border-t border-surface-100 text-xs">
          <div className="flex items-center gap-2">
            <span className="text-surface-400 font-medium">Section:</span>
            {['', 'A', 'B', 'C'].map((sec) => (
              <button
                key={sec || 'all'}
                onClick={() => handleFilterChange(setSectionFilter, sec)}
                className={`px-2.5 py-1 rounded-md font-medium transition-colors ${
                  sectionFilter === sec
                    ? 'bg-primary-600 text-white shadow-2xs'
                    : 'bg-surface-100 text-surface-600 hover:bg-surface-200'
                }`}
              >
                {sec ? `Sec ${sec}` : 'All'}
              </button>
            ))}
          </div>

          {hasActiveFilters && (
            <button
              onClick={handleResetFilters}
              className="text-xs text-primary-600 hover:text-primary-800 font-medium flex items-center gap-1"
            >
              <X className="w-3.5 h-3.5" />
              Reset Filters
            </button>
          )}
        </div>
      </div>

      {/* Main Students Table Section */}
      <div className="card border border-surface-200 overflow-hidden shadow-xs">
        {loading ? (
          <div className="p-6">
            <TableSkeleton rows={8} />
          </div>
        ) : error ? (
          <div className="p-6">
            <ErrorState
              title="Unable to load students"
              message={error}
              onRetry={() => fetchStudents(false)}
            />
          </div>
        ) : students.length === 0 ? (
          <div className="py-12 px-6">
            <EmptyState
              icon={<Users className="w-8 h-8 text-surface-400" />}
              title="No students found."
              description={
                hasActiveFilters
                  ? 'No students matched the active filter criteria. Try adjusting or resetting your search filters.'
                  : 'No student accounts currently exist in the database.'
              }
              action={
                hasActiveFilters ? (
                  <button onClick={handleResetFilters} className="btn btn-secondary btn-sm">
                    Clear Filters
                  </button>
                ) : (
                  <button onClick={openAddStudentModal} className="btn btn-primary btn-sm">
                    Add First Student
                  </button>
                )
              }
            />
          </div>
        ) : (
          <div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="bg-surface-50 border-b border-surface-200 text-surface-500 font-semibold uppercase tracking-wider">
                    <th className="py-3 px-4">Student ID</th>
                    <th className="py-3 px-4">Name</th>
                    <th className="py-3 px-4">Email</th>
                    <th className="py-3 px-4">Department</th>
                    <th className="py-3 px-4 text-center">Year</th>
                    <th className="py-3 px-4 text-center">Section</th>
                    <th className="py-3 px-4 text-center">Status</th>
                    <th className="py-3 px-4 text-center">Attendance</th>
                    <th className="py-3 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-surface-100">
                  {students.map((student) => {
                    const isLow = student.attendance_percentage < 75.0 && student.total_classes > 0;
                    return (
                      <tr key={student.id} className="hover:bg-surface-50/80 transition-colors">
                        <td className="py-3 px-4 font-semibold text-surface-900 font-mono">
                          {student.student_id || '—'}
                        </td>
                        <td className="py-3 px-4 font-semibold text-surface-900">
                          {student.full_name}
                        </td>
                        <td className="py-3 px-4 text-surface-500 truncate max-w-[180px]">
                          {student.email}
                        </td>
                        <td className="py-3 px-4 text-surface-600 font-medium">
                          {student.department || '—'}
                        </td>
                        <td className="py-3 px-4 text-center text-surface-600">
                          {student.year ? `Yr ${student.year}` : '—'}
                        </td>
                        <td className="py-3 px-4 text-center text-surface-600">
                          {student.section ? `Sec ${student.section}` : '—'}
                        </td>
                        <td className="py-3 px-4 text-center">
                          <span
                            className={`inline-flex items-center px-2 py-0.5 rounded-full text-[0.68rem] font-bold ${
                              student.status === 'Active' || student.is_active !== false
                                ? 'bg-emerald-100 text-emerald-800'
                                : 'bg-surface-200 text-surface-700'
                            }`}
                          >
                            {student.status || (student.is_active !== false ? 'Active' : 'Inactive')}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-center">
                          <span
                            className={`font-bold ${
                              isLow
                                ? 'text-red-600'
                                : student.total_classes === 0
                                ? 'text-surface-400'
                                : 'text-emerald-700'
                            }`}
                          >
                            {student.total_classes > 0 ? `${student.attendance_percentage}%` : 'N/A'}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-right">
                          <div className="flex items-center justify-end gap-1.5">
                            {/* View Action */}
                            <button
                              onClick={() => openViewStudentModal(student.id)}
                              className="p-1.5 rounded-lg text-surface-500 hover:text-primary-600 hover:bg-primary-50 transition-colors"
                              title="View student details and attendance"
                              aria-label={`View details for ${student.full_name}`}
                            >
                              <Eye className="w-4 h-4" />
                            </button>

                            {/* Edit Action */}
                            <button
                              onClick={() => openEditStudentModal(student)}
                              className="p-1.5 rounded-lg text-surface-500 hover:text-blue-600 hover:bg-blue-50 transition-colors"
                              title="Edit student"
                              aria-label={`Edit ${student.full_name}`}
                            >
                              <Pencil className="w-4 h-4" />
                            </button>

                            {/* Disable / Enable Action */}
                            {student.status === 'Active' || student.is_active !== false ? (
                              <button
                                onClick={() => {
                                  setConfirmStudent(student);
                                  setConfirmAction('disable');
                                }}
                                className="p-1.5 rounded-lg text-surface-400 hover:text-red-600 hover:bg-red-50 transition-colors"
                                title="Disable student account"
                                aria-label={`Disable account for ${student.full_name}`}
                              >
                                <Power className="w-4 h-4" />
                              </button>
                            ) : (
                              <button
                                onClick={() => {
                                  setConfirmStudent(student);
                                  setConfirmAction('enable');
                                }}
                                className="p-1.5 rounded-lg text-surface-400 hover:text-emerald-600 hover:bg-emerald-50 transition-colors"
                                title="Enable student account"
                                aria-label={`Enable account for ${student.full_name}`}
                              >
                                <Power className="w-4 h-4" />
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {/* Pagination Controls */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 px-4 py-3 border-t border-surface-200 bg-surface-50/50 text-xs text-surface-600">
              <div>
                Showing <span className="font-semibold">{(currentPage - 1) * 10 + 1}</span> to{' '}
                <span className="font-semibold">{Math.min(currentPage * 10, totalCount)}</span> of{' '}
                <span className="font-semibold">{totalCount}</span> student records
              </div>

              <div className="flex items-center gap-2 self-center sm:self-auto">
                <button
                  onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                  disabled={currentPage <= 1}
                  className="btn btn-secondary btn-sm px-2.5 py-1 disabled:opacity-40"
                  aria-label="Previous page"
                >
                  <ChevronLeft className="w-3.5 h-3.5" />
                  <span>Previous</span>
                </button>

                <span className="px-3 py-1 font-semibold text-surface-700">
                  Page {currentPage} of {totalPages}
                </span>

                <button
                  onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                  disabled={currentPage >= totalPages}
                  className="btn btn-secondary btn-sm px-2.5 py-1 disabled:opacity-40"
                  aria-label="Next page"
                >
                  <span>Next</span>
                  <ChevronRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Modal: Add Student */}
      <Modal
        isOpen={showAddModal}
        title="Add New Student"
        onClose={() => setShowAddModal(false)}
        maxWidth="max-w-lg"
      >
        <form onSubmit={handleAddStudentSubmit} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-surface-700 mb-1">
                Student ID *
              </label>
              <input
                type="text"
                placeholder="e.g. 2024CS050"
                value={formData.student_id}
                onChange={(e) => setFormData({ ...formData, student_id: e.target.value })}
                className={`input text-xs w-full ${formErrors.student_id ? 'border-red-500' : ''}`}
              />
              {formErrors.student_id && (
                <p className="text-[0.7rem] text-red-500 mt-0.5">{formErrors.student_id}</p>
              )}
            </div>

            <div>
              <label className="block text-xs font-semibold text-surface-700 mb-1">
                Full Name *
              </label>
              <input
                type="text"
                placeholder="e.g. Priya Sharma"
                value={formData.full_name}
                onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                className={`input text-xs w-full ${formErrors.full_name ? 'border-red-500' : ''}`}
              />
              {formErrors.full_name && (
                <p className="text-[0.7rem] text-red-500 mt-0.5">{formErrors.full_name}</p>
              )}
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-surface-700 mb-1">
              Email Address *
            </label>
            <input
              type="email"
              placeholder="e.g. priya.sharma@attendx.com"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              className={`input text-xs w-full ${formErrors.email ? 'border-red-500' : ''}`}
            />
            {formErrors.email && (
              <p className="text-[0.7rem] text-red-500 mt-0.5">{formErrors.email}</p>
            )}
          </div>

          <div>
            <label className="block text-xs font-semibold text-surface-700 mb-1">
              Account Password *
            </label>
            <input
              type="password"
              placeholder="Minimum 6 characters"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              className={`input text-xs w-full ${formErrors.password ? 'border-red-500' : ''}`}
            />
            {formErrors.password && (
              <p className="text-[0.7rem] text-red-500 mt-0.5">{formErrors.password}</p>
            )}
            <p className="text-[0.65rem] text-surface-400 mt-1">
              Password will be encrypted using bcrypt. The student will log in using this password.
            </p>
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-semibold text-surface-700 mb-1">
                Department *
              </label>
              <select
                value={formData.department}
                onChange={(e) => setFormData({ ...formData, department: e.target.value })}
                className="input text-xs w-full"
              >
                <option value="CSE">CSE</option>
                <option value="ECE">ECE</option>
                <option value="MECH">MECH</option>
                <option value="CIVIL">CIVIL</option>
                <option value="IT">IT</option>
                <option value="EEE">EEE</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-surface-700 mb-1">Year *</label>
              <select
                value={formData.year}
                onChange={(e) => setFormData({ ...formData, year: e.target.value })}
                className="input text-xs w-full"
              >
                <option value="1">Year 1</option>
                <option value="2">Year 2</option>
                <option value="3">Year 3</option>
                <option value="4">Year 4</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-surface-700 mb-1">Section *</label>
              <input
                type="text"
                maxLength={4}
                placeholder="A"
                value={formData.section}
                onChange={(e) => setFormData({ ...formData, section: e.target.value.toUpperCase() })}
                className="input text-xs w-full"
              />
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-3 border-t border-surface-100">
            <button
              type="button"
              onClick={() => setShowAddModal(false)}
              className="btn btn-secondary btn-sm"
              disabled={formLoading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-primary btn-sm flex items-center gap-1.5"
              disabled={formLoading}
            >
              {formLoading && <span className="spinner" />}
              <span>Create Student</span>
            </button>
          </div>
        </form>
      </Modal>

      {/* Modal: Edit Student */}
      <Modal
        isOpen={showEditModal}
        title="Edit Student"
        onClose={() => setShowEditModal(false)}
        maxWidth="max-w-lg"
      >
        <form onSubmit={handleEditStudentSubmit} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-surface-700 mb-1">
                Student ID
              </label>
              <input
                type="text"
                value={formData.student_id}
                onChange={(e) => setFormData({ ...formData, student_id: e.target.value })}
                className="input text-xs w-full"
              />
              <p className="text-[0.65rem] text-surface-400 mt-1">Unique student identifier</p>
            </div>

            <div>
              <label className="block text-xs font-semibold text-surface-700 mb-1">
                Full Name *
              </label>
              <input
                type="text"
                value={formData.full_name}
                onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                className={`input text-xs w-full ${formErrors.full_name ? 'border-red-500' : ''}`}
              />
              {formErrors.full_name && (
                <p className="text-[0.7rem] text-red-500 mt-0.5">{formErrors.full_name}</p>
              )}
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-surface-700 mb-1">
              Email Address *
            </label>
            <input
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              className={`input text-xs w-full ${formErrors.email ? 'border-red-500' : ''}`}
            />
            {formErrors.email && (
              <p className="text-[0.7rem] text-red-500 mt-0.5">{formErrors.email}</p>
            )}
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-semibold text-surface-700 mb-1">
                Department *
              </label>
              <select
                value={formData.department}
                onChange={(e) => setFormData({ ...formData, department: e.target.value })}
                className="input text-xs w-full"
              >
                <option value="CSE">CSE</option>
                <option value="ECE">ECE</option>
                <option value="MECH">MECH</option>
                <option value="CIVIL">CIVIL</option>
                <option value="IT">IT</option>
                <option value="EEE">EEE</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-surface-700 mb-1">Year *</label>
              <select
                value={formData.year}
                onChange={(e) => setFormData({ ...formData, year: e.target.value })}
                className="input text-xs w-full"
              >
                <option value="1">Year 1</option>
                <option value="2">Year 2</option>
                <option value="3">Year 3</option>
                <option value="4">Year 4</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-surface-700 mb-1">Section *</label>
              <input
                type="text"
                maxLength={4}
                value={formData.section}
                onChange={(e) => setFormData({ ...formData, section: e.target.value.toUpperCase() })}
                className="input text-xs w-full"
              />
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-3 border-t border-surface-100">
            <button
              type="button"
              onClick={() => setShowEditModal(false)}
              className="btn btn-secondary btn-sm"
              disabled={formLoading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-primary btn-sm flex items-center gap-1.5"
              disabled={formLoading}
            >
              {formLoading && <span className="spinner" />}
              <span>Save Changes</span>
            </button>
          </div>
        </form>
      </Modal>

      {/* Modal: View Student Details */}
      <Modal
        isOpen={showViewModal}
        title="Student Details"
        onClose={() => setShowViewModal(false)}
        maxWidth="max-w-2xl"
      >
        {detailLoading || !selectedStudentDetail ? (
          <div className="py-12 flex justify-center">
            <span className="spinner w-8 h-8 text-primary-600" />
          </div>
        ) : (
          <div className="space-y-6">
            {/* Student Profile Card */}
            <div className="p-4 rounded-xl bg-surface-50 border border-surface-200">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-3">
                <div>
                  <h3 className="text-base font-bold text-surface-900">
                    {selectedStudentDetail.full_name}
                  </h3>
                  <p className="text-xs text-surface-500 font-mono">
                    ID: {selectedStudentDetail.student_id || 'Not assigned'}
                  </p>
                </div>
                <span
                  className={`self-start sm:self-auto inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold ${
                    selectedStudentDetail.status === 'Active' || selectedStudentDetail.is_active
                      ? 'bg-emerald-100 text-emerald-800'
                      : 'bg-red-100 text-red-800'
                  }`}
                >
                  {selectedStudentDetail.status || (selectedStudentDetail.is_active ? 'Active' : 'Inactive')}
                </span>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs pt-2 border-t border-surface-200/60">
                <div>
                  <span className="text-surface-400 block font-medium">Email</span>
                  <span className="font-semibold text-surface-800 truncate block">
                    {selectedStudentDetail.email}
                  </span>
                </div>
                <div>
                  <span className="text-surface-400 block font-medium">Department</span>
                  <span className="font-semibold text-surface-800">
                    {selectedStudentDetail.department || '—'}
                  </span>
                </div>
                <div>
                  <span className="text-surface-400 block font-medium">Academic Year</span>
                  <span className="font-semibold text-surface-800">
                    Year {selectedStudentDetail.year || '—'}
                  </span>
                </div>
                <div>
                  <span className="text-surface-400 block font-medium">Class Section</span>
                  <span className="font-semibold text-surface-800">
                    Section {selectedStudentDetail.section || '—'}
                  </span>
                </div>
              </div>
            </div>

            {/* Attendance Summary */}
            <div className="card p-4 border border-surface-200">
              <div className="flex items-center justify-between mb-3">
                <h4 className="text-xs font-bold uppercase tracking-wider text-surface-600 flex items-center gap-1.5">
                  <CalendarCheck className="w-4 h-4 text-primary-600" />
                  Institutional Attendance Summary
                </h4>
                <span
                  className={`text-sm font-extrabold ${
                    selectedStudentDetail.attendance_summary.percentage >= 75.0
                      ? 'text-emerald-700'
                      : 'text-red-600'
                  }`}
                >
                  {selectedStudentDetail.attendance_summary.total_classes > 0
                    ? `${selectedStudentDetail.attendance_summary.percentage}%`
                    : 'N/A'}
                </span>
              </div>

              <div className="grid grid-cols-3 gap-3 text-center mb-3">
                <div className="p-2.5 rounded-lg bg-surface-50 border border-surface-100">
                  <span className="text-[0.68rem] text-surface-500 uppercase tracking-wider font-semibold block">
                    Total Classes
                  </span>
                  <span className="text-base font-bold text-surface-900 mt-0.5 block">
                    {selectedStudentDetail.attendance_summary.total_classes}
                  </span>
                </div>
                <div className="p-2.5 rounded-lg bg-emerald-50 border border-emerald-100">
                  <span className="text-[0.68rem] text-emerald-700 uppercase tracking-wider font-semibold block">
                    Present
                  </span>
                  <span className="text-base font-bold text-emerald-800 mt-0.5 block">
                    {selectedStudentDetail.attendance_summary.present}
                  </span>
                </div>
                <div className="p-2.5 rounded-lg bg-red-50 border border-red-100">
                  <span className="text-[0.68rem] text-red-700 uppercase tracking-wider font-semibold block">
                    Absent
                  </span>
                  <span className="text-base font-bold text-red-800 mt-0.5 block">
                    {selectedStudentDetail.attendance_summary.absent}
                  </span>
                </div>
              </div>

              <div className="w-full bg-surface-200 rounded-full h-2 overflow-hidden">
                <div
                  className={`h-2 rounded-full transition-all duration-500 ${
                    selectedStudentDetail.attendance_summary.percentage >= 75.0
                      ? 'bg-emerald-500'
                      : 'bg-red-500'
                  }`}
                  style={{
                    width: `${Math.min(100, selectedStudentDetail.attendance_summary.percentage)}%`,
                  }}
                />
              </div>
            </div>

            {/* Subject-Wise Attendance Breakdown */}
            <div>
              <h4 className="text-xs font-bold uppercase tracking-wider text-surface-600 mb-2.5 flex items-center gap-1.5">
                <BookOpen className="w-4 h-4 text-primary-600" />
                Enrolled Subject Breakdown
              </h4>

              {selectedStudentDetail.subjects_attendance.length > 0 ? (
                <div className="border border-surface-200 rounded-xl overflow-hidden">
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="bg-surface-50 border-b border-surface-200 text-surface-500 font-semibold uppercase tracking-wider">
                        <th className="py-2.5 px-3">Subject</th>
                        <th className="py-2.5 px-3">Code</th>
                        <th className="py-2.5 px-3 text-center">Classes</th>
                        <th className="py-2.5 px-3 text-center">Present</th>
                        <th className="py-2.5 px-3 text-center">Absent</th>
                        <th className="py-2.5 px-3 text-right">Attendance %</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-surface-100">
                      {selectedStudentDetail.subjects_attendance.map((sub) => (
                        <tr key={sub.subject_id} className="hover:bg-surface-50">
                          <td className="py-2.5 px-3 font-semibold text-surface-900">
                            {sub.subject_name}
                          </td>
                          <td className="py-2.5 px-3 font-mono text-surface-600">
                            {sub.subject_code}
                          </td>
                          <td className="py-2.5 px-3 text-center text-surface-700">
                            {sub.total_classes}
                          </td>
                          <td className="py-2.5 px-3 text-center text-emerald-700 font-medium">
                            {sub.present}
                          </td>
                          <td className="py-2.5 px-3 text-center text-red-700 font-medium">
                            {sub.absent}
                          </td>
                          <td className="py-2.5 px-3 text-right font-bold">
                            <span
                              className={sub.percentage >= 75.0 ? 'text-emerald-700' : 'text-red-600'}
                            >
                              {sub.total_classes > 0 ? `${sub.percentage}%` : 'N/A'}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="p-6 text-center text-surface-400 border border-surface-200 rounded-xl bg-surface-50/50">
                  <p className="text-xs">No active subject enrollments for this student.</p>
                </div>
              )}
            </div>

            <div className="flex justify-end pt-2">
              <button
                type="button"
                onClick={() => setShowViewModal(false)}
                className="btn btn-secondary btn-sm"
              >
                Close
              </button>
            </div>
          </div>
        )}
      </Modal>

      {/* Confirmation Dialog: Disable Account */}
      <ConfirmDialog
        isOpen={Boolean(confirmStudent && confirmAction === 'disable')}
        title="Disable Student Account"
        message={`Disable this student account (${confirmStudent?.full_name})? The student will not be permitted to authenticate until re-enabled.`}
        confirmLabel="Disable"
        cancelLabel="Cancel"
        variant="danger"
        loading={statusActionLoading}
        onConfirm={handleConfirmStatusAction}
        onCancel={() => {
          setConfirmStudent(null);
          setConfirmAction(null);
        }}
      />

      {/* Confirmation Dialog: Enable Account */}
      <ConfirmDialog
        isOpen={Boolean(confirmStudent && confirmAction === 'enable')}
        title="Enable Student Account"
        message={`Enable this student account (${confirmStudent?.full_name})? The student will be restored to active status and able to log in.`}
        confirmLabel="Enable"
        cancelLabel="Cancel"
        variant="primary"
        loading={statusActionLoading}
        onConfirm={handleConfirmStatusAction}
        onCancel={() => {
          setConfirmStudent(null);
          setConfirmAction(null);
        }}
      />
    </div>
  );
}
