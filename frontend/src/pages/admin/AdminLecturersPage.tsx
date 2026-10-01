import React, { useEffect, useState, useCallback } from 'react';
import api from '../../services/api';
import type {
  LecturerListItem,
  LecturerSummaryMetrics,
  LecturerListResponse,
  LecturerDetailResponse,
} from '../../types';
import { TableSkeleton } from '../../components/Skeleton';
import EmptyState from '../../components/EmptyState';
import ErrorState from '../../components/ErrorState';
import Modal from '../../components/Modal';
import ConfirmDialog from '../../components/ConfirmDialog';
import {
  GraduationCap,
  UserCheck,
  UserX,
  BookOpen,
  Search,
  Plus,
  Eye,
  Pencil,
  Power,
  RotateCw,
  X,
  ChevronLeft,
  ChevronRight,
  Mail,
  Building,
  Calendar,
  Layers,
} from 'lucide-react';
import toast from 'react-hot-toast';

const DEPARTMENTS = [
  'Computer Science',
  'Information Technology',
  'Electronics & Communication',
  'Electrical & Electronics',
  'Mechanical Engineering',
  'Civil Engineering',
  'Mathematics',
  'Physics',
];

export default function AdminLecturersPage() {
  // Data state
  const [lecturers, setLecturers] = useState<LecturerListItem[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [currentPage, setCurrentPage] = useState(1);
  const [summary, setSummary] = useState<LecturerSummaryMetrics | null>(null);

  // Loading & error states
  const [loading, setLoading] = useState(true);
  const [summaryLoading, setSummaryLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'inactive'>('all');
  const [deptFilter, setDeptFilter] = useState('');
  const [assignmentFilter, setAssignmentFilter] = useState<'all' | 'assigned' | 'unassigned'>('all');

  // Modals & action states
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showViewModal, setShowViewModal] = useState(false);
  const [selectedLecturerDetail, setSelectedLecturerDetail] = useState<LecturerDetailResponse | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  // Status toggle confirmation
  const [confirmLecturer, setConfirmLecturer] = useState<LecturerListItem | null>(null);
  const [confirmAction, setConfirmAction] = useState<'disable' | 'enable' | null>(null);
  const [statusActionLoading, setStatusActionLoading] = useState(false);

  // Form states
  const [formLoading, setFormLoading] = useState(false);
  const [formData, setFormData] = useState({
    id: '',
    employee_id: '',
    full_name: '',
    email: '',
    password: '',
    department: 'Computer Science',
  });
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});

  // Fetch summary statistics
  const fetchSummary = useCallback(async () => {
    setSummaryLoading(true);
    try {
      const res = await api.get<LecturerSummaryMetrics>('/api/admin/lecturers/summary');
      setSummary(res.data);
    } catch {
      // Don't break page if summary endpoint fails
    } finally {
      setSummaryLoading(false);
    }
  }, []);

  // Fetch lecturers table data
  const fetchLecturers = useCallback(
    async (isManualRefresh = false) => {
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
        if (assignmentFilter !== 'all') params.assignment_status = assignmentFilter;

        const res = await api.get<LecturerListResponse | LecturerListItem[]>('/api/admin/lecturers', { params });

        if (Array.isArray(res.data)) {
          setLecturers(res.data);
          setTotalCount(res.data.length);
          setTotalPages(1);
        } else if (res.data && Array.isArray(res.data.items)) {
          setLecturers(res.data.items);
          setTotalCount(res.data.total ?? 0);
          setTotalPages(res.data.pages ?? 1);
        } else {
          setLecturers([]);
          setTotalCount(0);
          setTotalPages(1);
        }
      } catch (err: any) {
        const errMsg = err?.response?.data?.detail || err?.message || 'Failed to load lecturers.';
        setError(errMsg);
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    },
    [currentPage, search, statusFilter, deptFilter, assignmentFilter]
  );

  useEffect(() => {
    fetchSummary();
  }, [fetchSummary]);

  useEffect(() => {
    fetchLecturers();
  }, [fetchLecturers]);

  // Reset pagination on filter change
  const handleFilterChange = (setter: (val: any) => void, val: any) => {
    setter(val);
    setCurrentPage(1);
  };

  const handleClearFilters = () => {
    setSearch('');
    setStatusFilter('all');
    setDeptFilter('');
    setAssignmentFilter('all');
    setCurrentPage(1);
  };

  const hasActiveFilters = Boolean(
    search.trim() || statusFilter !== 'all' || deptFilter.trim() || assignmentFilter !== 'all'
  );

  // View lecturer details
  const handleViewLecturer = async (id: string) => {
    setShowViewModal(true);
    setDetailLoading(true);
    setSelectedLecturerDetail(null);
    try {
      const res = await api.get<LecturerDetailResponse>(`/api/admin/lecturers/${id}`);
      setSelectedLecturerDetail(res.data);
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Failed to load lecturer details.');
      setShowViewModal(false);
    } finally {
      setDetailLoading(false);
    }
  };

  // Open Edit modal
  const handleOpenEdit = (lecturer: LecturerListItem) => {
    setFormData({
      id: lecturer.id,
      employee_id: lecturer.employee_id,
      full_name: lecturer.full_name,
      email: lecturer.email,
      password: '',
      department: lecturer.department || 'Computer Science',
    });
    setFormErrors({});
    setShowEditModal(true);
  };

  // Open Add modal
  const handleOpenAdd = () => {
    setFormData({
      id: '',
      employee_id: '',
      full_name: '',
      email: '',
      password: '',
      department: 'Computer Science',
    });
    setFormErrors({});
    setShowAddModal(true);
  };

  // Form field validation
  const validateForm = (isEdit = false) => {
    const errors: Record<string, string> = {};
    if (!formData.employee_id.trim()) {
      errors.employee_id = 'Employee ID is required';
    }
    if (!formData.full_name.trim()) {
      errors.full_name = 'Full name is required';
    } else if (formData.full_name.trim().length < 2) {
      errors.full_name = 'Name must be at least 2 characters';
    }
    if (!formData.email.trim()) {
      errors.email = 'Email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email.trim())) {
      errors.email = 'Enter a valid email address';
    }
    if (!formData.department.trim()) {
      errors.department = 'Department is required';
    }
    if (!isEdit) {
      if (!formData.password) {
        errors.password = 'Password is required';
      } else if (formData.password.length < 6) {
        errors.password = 'Password must be at least 6 characters';
      }
    }
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  // Submit Add Lecturer
  const handleCreateLecturer = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateForm(false)) return;

    setFormLoading(true);
    try {
      await api.post('/api/admin/lecturers', {
        employee_id: formData.employee_id.trim(),
        full_name: formData.full_name.trim(),
        email: formData.email.trim().toLowerCase(),
        department: formData.department.trim(),
        password: formData.password,
      });

      toast.success('Lecturer created successfully.');
      setShowAddModal(false);
      fetchLecturers(true);
      fetchSummary();
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      if (err?.response?.status === 409) {
        if (typeof detail === 'string' && detail.toLowerCase().includes('email')) {
          setFormErrors((prev) => ({ ...prev, email: detail }));
        } else if (typeof detail === 'string' && (detail.toLowerCase().includes('employee') || detail.toLowerCase().includes('id'))) {
          setFormErrors((prev) => ({ ...prev, employee_id: detail }));
        } else {
          toast.error(detail || 'A conflict occurred while creating the lecturer.');
        }
      } else {
        toast.error(detail || 'Failed to create lecturer.');
      }
    } finally {
      setFormLoading(false);
    }
  };

  // Submit Edit Lecturer
  const handleUpdateLecturer = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateForm(true)) return;

    setFormLoading(true);
    try {
      await api.put(`/api/admin/lecturers/${formData.id}`, {
        employee_id: formData.employee_id.trim(),
        full_name: formData.full_name.trim(),
        email: formData.email.trim().toLowerCase(),
        department: formData.department.trim(),
      });

      toast.success('Lecturer updated successfully.');
      setShowEditModal(false);
      fetchLecturers(true);
      fetchSummary();
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      if (err?.response?.status === 409) {
        if (typeof detail === 'string' && detail.toLowerCase().includes('email')) {
          setFormErrors((prev) => ({ ...prev, email: detail }));
        } else if (typeof detail === 'string' && (detail.toLowerCase().includes('employee') || detail.toLowerCase().includes('id'))) {
          setFormErrors((prev) => ({ ...prev, employee_id: detail }));
        } else {
          toast.error(detail || 'A conflict occurred while updating.');
        }
      } else {
        toast.error(detail || 'Failed to update lecturer.');
      }
    } finally {
      setFormLoading(false);
    }
  };

  // Confirm Status change (Disable/Enable)
  const handleConfirmStatusChange = async () => {
    if (!confirmLecturer || !confirmAction) return;

    setStatusActionLoading(true);
    try {
      if (confirmAction === 'disable') {
        await api.post(`/api/admin/lecturers/${confirmLecturer.id}/disable`);
        toast.success('Lecturer account disabled.');
      } else {
        await api.post(`/api/admin/lecturers/${confirmLecturer.id}/enable`);
        toast.success('Lecturer account enabled.');
      }

      setConfirmLecturer(null);
      setConfirmAction(null);
      fetchLecturers(true);
      fetchSummary();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || `Failed to ${confirmAction} lecturer.`);
    } finally {
      setStatusActionLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-surface-900 tracking-tight">Lecturer Management</h1>
          <p className="text-surface-500 text-sm mt-0.5">Manage lecturer accounts and teaching assignments.</p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => {
              fetchSummary();
              fetchLecturers(true);
            }}
            disabled={refreshing || loading}
            className="btn btn-secondary flex items-center gap-2"
            title="Refresh lecturer list"
            aria-label="Refresh lecturer list"
          >
            <RotateCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
            <span className="hidden sm:inline">Refresh</span>
          </button>
          <button
            onClick={handleOpenAdd}
            className="btn btn-primary flex items-center gap-2"
            id="add-lecturer-btn"
            aria-label="Add Lecturer"
          >
            <Plus className="w-4 h-4" />
            <span>Add Lecturer</span>
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Lecturers */}
        <div className="bg-white rounded-xl p-5 border border-surface-200 shadow-sm flex items-center gap-4 transition-all hover:shadow-md">
          <div className="w-12 h-12 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center flex-shrink-0">
            <GraduationCap className="w-6 h-6" />
          </div>
          <div>
            <div className="text-sm font-medium text-surface-500">Total Lecturers</div>
            {summaryLoading ? (
              <div className="h-7 w-12 bg-surface-200 animate-pulse rounded mt-1" />
            ) : (
              <div className="text-2xl font-bold text-surface-900">{summary?.total_lecturers ?? 0}</div>
            )}
            <div className="text-xs text-surface-400 mt-0.5">Registered faculty</div>
          </div>
        </div>

        {/* Active Lecturers */}
        <div className="bg-white rounded-xl p-5 border border-surface-200 shadow-sm flex items-center gap-4 transition-all hover:shadow-md">
          <div className="w-12 h-12 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center flex-shrink-0">
            <UserCheck className="w-6 h-6" />
          </div>
          <div>
            <div className="text-sm font-medium text-surface-500">Active Lecturers</div>
            {summaryLoading ? (
              <div className="h-7 w-12 bg-surface-200 animate-pulse rounded mt-1" />
            ) : (
              <div className="text-2xl font-bold text-emerald-600">{summary?.active_lecturers ?? 0}</div>
            )}
            <div className="text-xs text-surface-400 mt-0.5">Permitted to access</div>
          </div>
        </div>

        {/* Inactive Lecturers */}
        <div className="bg-white rounded-xl p-5 border border-surface-200 shadow-sm flex items-center gap-4 transition-all hover:shadow-md">
          <div className="w-12 h-12 rounded-xl bg-rose-50 text-rose-600 flex items-center justify-center flex-shrink-0">
            <UserX className="w-6 h-6" />
          </div>
          <div>
            <div className="text-sm font-medium text-surface-500">Inactive Lecturers</div>
            {summaryLoading ? (
              <div className="h-7 w-12 bg-surface-200 animate-pulse rounded mt-1" />
            ) : (
              <div className="text-2xl font-bold text-rose-600">{summary?.inactive_lecturers ?? 0}</div>
            )}
            <div className="text-xs text-surface-400 mt-0.5">Accounts disabled</div>
          </div>
        </div>

        {/* Lecturers With Assignments */}
        <div className="bg-white rounded-xl p-5 border border-surface-200 shadow-sm flex items-center gap-4 transition-all hover:shadow-md">
          <div className="w-12 h-12 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center flex-shrink-0">
            <BookOpen className="w-6 h-6" />
          </div>
          <div>
            <div className="text-sm font-medium text-surface-500">With Assignments</div>
            {summaryLoading ? (
              <div className="h-7 w-12 bg-surface-200 animate-pulse rounded mt-1" />
            ) : (
              <div className="text-2xl font-bold text-indigo-600">{summary?.lecturers_with_assignments ?? 0}</div>
            )}
            <div className="text-xs text-surface-400 mt-0.5">Teaching active courses</div>
          </div>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white rounded-xl p-4 border border-surface-200 shadow-sm space-y-3">
        <div className="flex flex-col lg:flex-row items-stretch lg:items-center gap-3">
          {/* Search Input */}
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-surface-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search by Employee ID, Name, or Email..."
              value={search}
              onChange={(e) => handleFilterChange(setSearch, e.target.value)}
              className="input pl-10 pr-9 w-full text-sm"
              id="lecturer-search-input"
              aria-label="Search lecturers"
            />
            {search && (
              <button
                onClick={() => handleFilterChange(setSearch, '')}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-surface-400 hover:text-surface-600"
                aria-label="Clear search"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>

          {/* Filters group */}
          <div className="flex flex-wrap items-center gap-2.5">
            {/* Status Filter */}
            <select
              value={statusFilter}
              onChange={(e) => handleFilterChange(setStatusFilter, e.target.value)}
              className="input text-sm py-2 px-3 pr-8 min-w-[120px]"
              aria-label="Filter by Status"
            >
              <option value="all">All Status</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
            </select>

            {/* Department Filter */}
            <select
              value={deptFilter}
              onChange={(e) => handleFilterChange(setDeptFilter, e.target.value)}
              className="input text-sm py-2 px-3 pr-8 min-w-[150px]"
              aria-label="Filter by Department"
            >
              <option value="">All Departments</option>
              {DEPARTMENTS.map((dept) => (
                <option key={dept} value={dept}>
                  {dept}
                </option>
              ))}
            </select>

            {/* Assignment Status Filter */}
            <select
              value={assignmentFilter}
              onChange={(e) => handleFilterChange(setAssignmentFilter, e.target.value)}
              className="input text-sm py-2 px-3 pr-8 min-w-[150px]"
              aria-label="Filter by Assignment Status"
            >
              <option value="all">All Assignments</option>
              <option value="assigned">Assigned</option>
              <option value="unassigned">Unassigned</option>
            </select>

            {/* Clear Filters Button */}
            {hasActiveFilters && (
              <button
                onClick={handleClearFilters}
                className="btn btn-secondary text-xs px-3 py-2 flex items-center gap-1.5 text-surface-600"
                title="Reset all filters"
              >
                <X className="w-3.5 h-3.5" />
                <span>Reset</span>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Lecturers Table */}
      <div className="bg-white rounded-xl border border-surface-200 shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-6">
            <TableSkeleton rows={8} />
          </div>
        ) : error ? (
          <div className="p-6">
            <ErrorState title="Unable to load lecturers" message={error} onRetry={() => fetchLecturers(true)} />
          </div>
        ) : lecturers.length === 0 ? (
          <EmptyState
            icon={<GraduationCap className="w-8 h-8 text-surface-400" />}
            title="No Lecturers Found"
            description={
              hasActiveFilters
                ? 'No lecturers matched the selected filters. Try broadening your search or resetting filters.'
                : 'There are currently no lecturers registered in the system.'
            }
            action={
              <button
                onClick={hasActiveFilters ? handleClearFilters : handleOpenAdd}
                className="btn btn-primary text-sm flex items-center gap-2"
              >
                {hasActiveFilters ? (
                  <>
                    <X className="w-4 h-4" />
                    <span>Clear Filters</span>
                  </>
                ) : (
                  <>
                    <Plus className="w-4 h-4" />
                    <span>Add First Lecturer</span>
                  </>
                )}
              </button>
            }
          />
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm" id="lecturers-table">
                <thead className="bg-surface-50 text-surface-600 font-semibold border-b border-surface-200">
                  <tr>
                    <th scope="col" className="px-5 py-3.5">Employee ID</th>
                    <th scope="col" className="px-5 py-3.5">Name</th>
                    <th scope="col" className="px-5 py-3.5">Email</th>
                    <th scope="col" className="px-5 py-3.5">Department</th>
                    <th scope="col" className="px-5 py-3.5">Status</th>
                    <th scope="col" className="px-5 py-3.5">Assigned Subjects</th>
                    <th scope="col" className="px-5 py-3.5 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-surface-100">
                  {lecturers.map((lecturer) => {
                    const isActive = lecturer.is_active;
                    return (
                      <tr key={lecturer.id} className="hover:bg-surface-50/70 transition-colors">
                        <td className="px-5 py-4 font-mono font-medium text-surface-800">
                          {lecturer.employee_id || '—'}
                        </td>
                        <td className="px-5 py-4 font-medium text-surface-900">
                          <div className="flex items-center gap-2.5">
                            <div className="w-8 h-8 rounded-full bg-primary-50 text-primary-700 flex items-center justify-center font-semibold text-xs flex-shrink-0">
                              {lecturer.full_name
                                .split(' ')
                                .map((n) => n[0])
                                .slice(0, 2)
                                .join('')
                                .toUpperCase()}
                            </div>
                            <span>{lecturer.full_name}</span>
                          </div>
                        </td>
                        <td className="px-5 py-4 text-surface-600">
                          {lecturer.email}
                        </td>
                        <td className="px-5 py-4 text-surface-700">
                          <span className="inline-block px-2.5 py-0.5 rounded-full text-xs font-medium bg-surface-100 text-surface-700 border border-surface-200">
                            {lecturer.department || 'General'}
                          </span>
                        </td>
                        <td className="px-5 py-4">
                          {isActive ? (
                            <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                              Active
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200">
                              <span className="w-1.5 h-1.5 rounded-full bg-rose-500" />
                              Inactive
                            </span>
                          )}
                        </td>
                        <td className="px-5 py-4">
                          {lecturer.assigned_subjects_count > 0 ? (
                            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-indigo-50 text-indigo-700 border border-indigo-200">
                              <BookOpen className="w-3 h-3" />
                              {lecturer.assigned_subjects_count} subjects
                            </span>
                          ) : (
                            <span className="text-surface-400 text-xs italic">
                              Not assigned yet
                            </span>
                          )}
                        </td>
                        <td className="px-5 py-4 text-right">
                          <div className="flex items-center justify-end gap-1.5">
                            <button
                              onClick={() => handleViewLecturer(lecturer.id)}
                              className="p-1.5 text-surface-500 hover:text-primary-600 hover:bg-surface-100 rounded-lg transition-colors"
                              title="View details"
                              aria-label={`View details for ${lecturer.full_name}`}
                            >
                              <Eye className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => handleOpenEdit(lecturer)}
                              className="p-1.5 text-surface-500 hover:text-amber-600 hover:bg-surface-100 rounded-lg transition-colors"
                              title="Edit lecturer"
                              aria-label={`Edit ${lecturer.full_name}`}
                            >
                              <Pencil className="w-4 h-4" />
                            </button>
                            {isActive ? (
                              <button
                                onClick={() => {
                                  setConfirmLecturer(lecturer);
                                  setConfirmAction('disable');
                                }}
                                className="p-1.5 text-surface-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors"
                                title="Disable account"
                                aria-label={`Disable account for ${lecturer.full_name}`}
                              >
                                <Power className="w-4 h-4" />
                              </button>
                            ) : (
                              <button
                                onClick={() => {
                                  setConfirmLecturer(lecturer);
                                  setConfirmAction('enable');
                                }}
                                className="p-1.5 text-surface-400 hover:text-emerald-600 hover:bg-emerald-50 rounded-lg transition-colors"
                                title="Enable account"
                                aria-label={`Enable account for ${lecturer.full_name}`}
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
            <div className="px-5 py-3.5 border-t border-surface-200 bg-surface-50/50 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-surface-600">
              <div>
                Showing <span className="font-semibold text-surface-900">{lecturers.length}</span> of{' '}
                <span className="font-semibold text-surface-900">{totalCount}</span> lecturers
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setCurrentPage((prev) => Math.max(1, prev - 1))}
                  disabled={currentPage <= 1 || loading}
                  className="btn btn-secondary px-2.5 py-1.5 text-xs flex items-center gap-1 disabled:opacity-50"
                  aria-label="Previous page"
                >
                  <ChevronLeft className="w-3.5 h-3.5" />
                  <span>Previous</span>
                </button>
                <span className="px-2 font-medium text-surface-700">
                  Page {currentPage} of {totalPages}
                </span>
                <button
                  onClick={() => setCurrentPage((prev) => Math.min(totalPages, prev + 1))}
                  disabled={currentPage >= totalPages || loading}
                  className="btn btn-secondary px-2.5 py-1.5 text-xs flex items-center gap-1 disabled:opacity-50"
                  aria-label="Next page"
                >
                  <span>Next</span>
                  <ChevronRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          </>
        )}
      </div>

      {/* Add Lecturer Modal */}
      <Modal
        isOpen={showAddModal}
        title="Add New Lecturer"
        onClose={() => !formLoading && setShowAddModal(false)}
        maxWidth="max-w-lg"
      >
        <form onSubmit={handleCreateLecturer} className="space-y-4">
          <div>
            <label className="label" htmlFor="add-employee-id">
              Employee ID <span className="text-danger">*</span>
            </label>
            <input
              id="add-employee-id"
              type="text"
              placeholder="e.g. EMP001"
              value={formData.employee_id}
              onChange={(e) => setFormData({ ...formData, employee_id: e.target.value })}
              className={`input w-full ${formErrors.employee_id ? 'border-danger' : ''}`}
              disabled={formLoading}
            />
            {formErrors.employee_id && (
              <p className="text-danger text-xs mt-1">{formErrors.employee_id}</p>
            )}
          </div>

          <div>
            <label className="label" htmlFor="add-full-name">
              Full Name <span className="text-danger">*</span>
            </label>
            <input
              id="add-full-name"
              type="text"
              placeholder="e.g. Dr. Sarah Connor"
              value={formData.full_name}
              onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
              className={`input w-full ${formErrors.full_name ? 'border-danger' : ''}`}
              disabled={formLoading}
            />
            {formErrors.full_name && (
              <p className="text-danger text-xs mt-1">{formErrors.full_name}</p>
            )}
          </div>

          <div>
            <label className="label" htmlFor="add-email">
              Email Address <span className="text-danger">*</span>
            </label>
            <input
              id="add-email"
              type="email"
              placeholder="e.g. sarah.connor@attendx.com"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              className={`input w-full ${formErrors.email ? 'border-danger' : ''}`}
              disabled={formLoading}
            />
            {formErrors.email && (
              <p className="text-danger text-xs mt-1">{formErrors.email}</p>
            )}
          </div>

          <div>
            <label className="label" htmlFor="add-department">
              Department <span className="text-danger">*</span>
            </label>
            <select
              id="add-department"
              value={formData.department}
              onChange={(e) => setFormData({ ...formData, department: e.target.value })}
              className={`input w-full ${formErrors.department ? 'border-danger' : ''}`}
              disabled={formLoading}
            >
              {DEPARTMENTS.map((dept) => (
                <option key={dept} value={dept}>
                  {dept}
                </option>
              ))}
            </select>
            {formErrors.department && (
              <p className="text-danger text-xs mt-1">{formErrors.department}</p>
            )}
          </div>

          <div>
            <label className="label" htmlFor="add-password">
              Account Password <span className="text-danger">*</span>
            </label>
            <input
              id="add-password"
              type="password"
              placeholder="Minimum 6 characters"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              className={`input w-full ${formErrors.password ? 'border-danger' : ''}`}
              disabled={formLoading}
            />
            {formErrors.password && (
              <p className="text-danger text-xs mt-1">{formErrors.password}</p>
            )}
            <p className="text-surface-400 text-xs mt-1">
              Passwords are automatically hashed using bcrypt. The lecturer will use this to sign in.
            </p>
          </div>

          <div className="flex justify-end gap-3 pt-3 border-t border-surface-100">
            <button
              type="button"
              onClick={() => setShowAddModal(false)}
              className="btn btn-secondary"
              disabled={formLoading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-primary flex items-center gap-2"
              disabled={formLoading}
            >
              {formLoading && <span className="spinner" />}
              <span>Create Lecturer</span>
            </button>
          </div>
        </form>
      </Modal>

      {/* Edit Lecturer Modal */}
      <Modal
        isOpen={showEditModal}
        title="Edit Lecturer Details"
        onClose={() => !formLoading && setShowEditModal(false)}
        maxWidth="max-w-lg"
      >
        <form onSubmit={handleUpdateLecturer} className="space-y-4">
          <div>
            <label className="label" htmlFor="edit-employee-id">
              Employee ID <span className="text-danger">*</span>
            </label>
            <input
              id="edit-employee-id"
              type="text"
              value={formData.employee_id}
              onChange={(e) => setFormData({ ...formData, employee_id: e.target.value })}
              className={`input w-full ${formErrors.employee_id ? 'border-danger' : ''}`}
              disabled={formLoading}
            />
            {formErrors.employee_id && (
              <p className="text-danger text-xs mt-1">{formErrors.employee_id}</p>
            )}
          </div>

          <div>
            <label className="label" htmlFor="edit-full-name">
              Full Name <span className="text-danger">*</span>
            </label>
            <input
              id="edit-full-name"
              type="text"
              value={formData.full_name}
              onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
              className={`input w-full ${formErrors.full_name ? 'border-danger' : ''}`}
              disabled={formLoading}
            />
            {formErrors.full_name && (
              <p className="text-danger text-xs mt-1">{formErrors.full_name}</p>
            )}
          </div>

          <div>
            <label className="label" htmlFor="edit-email">
              Email Address <span className="text-danger">*</span>
            </label>
            <input
              id="edit-email"
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              className={`input w-full ${formErrors.email ? 'border-danger' : ''}`}
              disabled={formLoading}
            />
            {formErrors.email && (
              <p className="text-danger text-xs mt-1">{formErrors.email}</p>
            )}
          </div>

          <div>
            <label className="label" htmlFor="edit-department">
              Department <span className="text-danger">*</span>
            </label>
            <select
              id="edit-department"
              value={formData.department}
              onChange={(e) => setFormData({ ...formData, department: e.target.value })}
              className={`input w-full ${formErrors.department ? 'border-danger' : ''}`}
              disabled={formLoading}
            >
              {DEPARTMENTS.map((dept) => (
                <option key={dept} value={dept}>
                  {dept}
                </option>
              ))}
            </select>
            {formErrors.department && (
              <p className="text-danger text-xs mt-1">{formErrors.department}</p>
            )}
          </div>

          <div className="flex justify-end gap-3 pt-3 border-t border-surface-100">
            <button
              type="button"
              onClick={() => setShowEditModal(false)}
              className="btn btn-secondary"
              disabled={formLoading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-primary flex items-center gap-2"
              disabled={formLoading}
            >
              {formLoading && <span className="spinner" />}
              <span>Save Changes</span>
            </button>
          </div>
        </form>
      </Modal>

      {/* View Lecturer Details Modal */}
      <Modal
        isOpen={showViewModal}
        title="Lecturer Profile & Assignments"
        onClose={() => setShowViewModal(false)}
        maxWidth="max-w-xl"
      >
        {detailLoading ? (
          <div className="p-8 text-center">
            <div className="spinner mx-auto mb-3" />
            <p className="text-surface-500 text-sm">Loading lecturer profile...</p>
          </div>
        ) : selectedLecturerDetail ? (
          <div className="space-y-6">
            {/* Header info */}
            <div className="flex items-start justify-between bg-surface-50 p-4 rounded-xl border border-surface-200">
              <div className="flex items-center gap-3.5">
                <div className="w-12 h-12 rounded-full bg-primary-100 text-primary-700 flex items-center justify-center font-bold text-base">
                  {selectedLecturerDetail.full_name
                    .split(' ')
                    .map((n) => n[0])
                    .slice(0, 2)
                    .join('')
                    .toUpperCase()}
                </div>
                <div>
                  <h3 className="font-semibold text-surface-900 text-base">
                    {selectedLecturerDetail.full_name}
                  </h3>
                  <div className="text-xs text-surface-500 font-mono mt-0.5">
                    Employee ID: {selectedLecturerDetail.employee_id || 'Not set'}
                  </div>
                </div>
              </div>
              <div>
                {selectedLecturerDetail.is_active ? (
                  <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                    <span className="w-2 h-2 rounded-full bg-emerald-500" />
                    Active
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200">
                    <span className="w-2 h-2 rounded-full bg-rose-500" />
                    Inactive
                  </span>
                )}
              </div>
            </div>

            {/* Profile fields */}
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div className="bg-white p-3.5 rounded-lg border border-surface-200">
                <div className="text-xs text-surface-400 flex items-center gap-1.5 mb-1">
                  <Mail className="w-3.5 h-3.5 text-surface-400" />
                  Email Address
                </div>
                <div className="font-medium text-surface-800 break-all">
                  {selectedLecturerDetail.email}
                </div>
              </div>

              <div className="bg-white p-3.5 rounded-lg border border-surface-200">
                <div className="text-xs text-surface-400 flex items-center gap-1.5 mb-1">
                  <Building className="w-3.5 h-3.5 text-surface-400" />
                  Department
                </div>
                <div className="font-medium text-surface-800">
                  {selectedLecturerDetail.department || 'Not specified'}
                </div>
              </div>

              <div className="bg-white p-3.5 rounded-lg border border-surface-200">
                <div className="text-xs text-surface-400 flex items-center gap-1.5 mb-1">
                  <Layers className="w-3.5 h-3.5 text-surface-400" />
                  System Role
                </div>
                <div className="font-medium text-surface-800 capitalize">
                  {selectedLecturerDetail.role}
                </div>
              </div>

              <div className="bg-white p-3.5 rounded-lg border border-surface-200">
                <div className="text-xs text-surface-400 flex items-center gap-1.5 mb-1">
                  <Calendar className="w-3.5 h-3.5 text-surface-400" />
                  Registered Date
                </div>
                <div className="font-medium text-surface-800">
                  {selectedLecturerDetail.created_at
                    ? new Date(selectedLecturerDetail.created_at).toLocaleDateString('en-US', {
                        year: 'numeric',
                        month: 'short',
                        day: 'numeric',
                      })
                    : '—'}
                </div>
              </div>
            </div>

            {/* Assigned Subjects Section */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="font-semibold text-surface-900 text-sm flex items-center gap-2">
                  <BookOpen className="w-4 h-4 text-primary-600" />
                  <span>Assigned Subjects</span>
                </h4>
                <span className="text-xs text-surface-500">
                  {selectedLecturerDetail.assigned_subjects?.length ?? 0} allocated
                </span>
              </div>

              {selectedLecturerDetail.assigned_subjects &&
              selectedLecturerDetail.assigned_subjects.length > 0 ? (
                <div className="border border-surface-200 rounded-lg overflow-hidden">
                  <table className="w-full text-xs text-left">
                    <thead className="bg-surface-50 text-surface-600 border-b border-surface-200">
                      <tr>
                        <th className="px-3 py-2 font-semibold">Subject Code</th>
                        <th className="px-3 py-2 font-semibold">Subject Name</th>
                        <th className="px-3 py-2 font-semibold">Department</th>
                        <th className="px-3 py-2 font-semibold text-right">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-surface-100">
                      {selectedLecturerDetail.assigned_subjects.map((sub) => (
                        <tr key={sub.id}>
                          <td className="px-3 py-2 font-mono font-medium text-surface-800">{sub.code}</td>
                          <td className="px-3 py-2 font-medium text-surface-900">{sub.name}</td>
                          <td className="px-3 py-2 text-surface-600">{sub.department}</td>
                          <td className="px-3 py-2 text-right">
                            <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-50 text-emerald-700">
                              {sub.status || 'Active'}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="bg-surface-50 border border-dashed border-surface-300 rounded-xl p-6 text-center">
                  <BookOpen className="w-8 h-8 text-surface-400 mx-auto mb-2" />
                  <p className="text-sm font-medium text-surface-700">No subjects assigned yet.</p>
                  <p className="text-xs text-surface-400 mt-1 max-w-sm mx-auto">
                    Teaching allocations and subject management will be assigned in later administrative modules.
                  </p>
                </div>
              )}
            </div>

            <div className="flex justify-end pt-3 border-t border-surface-100">
              <button
                type="button"
                onClick={() => setShowViewModal(false)}
                className="btn btn-secondary text-sm"
              >
                Close
              </button>
            </div>
          </div>
        ) : null}
      </Modal>

      {/* Confirmation Dialog for Status Changes */}
      <ConfirmDialog
        isOpen={Boolean(confirmLecturer && confirmAction)}
        title={confirmAction === 'disable' ? 'Disable Lecturer Account' : 'Enable Lecturer Account'}
        message={
          confirmAction === 'disable'
            ? `Disable account for ${confirmLecturer?.full_name}? The lecturer will be immediately prevented from logging into the portal.`
            : `Enable account for ${confirmLecturer?.full_name}? The lecturer will regain authorization to access the portal.`
        }
        confirmLabel={confirmAction === 'disable' ? 'Disable' : 'Enable'}
        cancelLabel="Cancel"
        variant={confirmAction === 'disable' ? 'danger' : 'primary'}
        loading={statusActionLoading}
        onConfirm={handleConfirmStatusChange}
        onCancel={() => {
          setConfirmLecturer(null);
          setConfirmAction(null);
        }}
      />
    </div>
  );
}
