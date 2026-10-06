import React, { useEffect, useState, useCallback } from 'react';
import api, { isRequestCancelled } from '../../services/api';
import type {
  LecturerAssignmentItem,
  AssignmentSummaryMetrics,
  AssignmentListResponse,
  LecturerListItem,
  Subject,
} from '../../types';
import { TableSkeleton } from '../../components/Skeleton';
import EmptyState from '../../components/EmptyState';
import ErrorState from '../../components/ErrorState';
import Modal from '../../components/Modal';
import ConfirmDialog from '../../components/ConfirmDialog';
import {
  Layers,
  GraduationCap,
  BookOpen,
  AlertTriangle,
  Search,
  Plus,
  RotateCw,
  X,
  ChevronLeft,
  ChevronRight,
  Trash2,
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

export default function AdminAssignmentsPage() {
  // Data state
  const [assignments, setAssignments] = useState<LecturerAssignmentItem[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [currentPage, setCurrentPage] = useState(1);
  const [summary, setSummary] = useState<AssignmentSummaryMetrics | null>(null);

  // Loading & error states
  const [loading, setLoading] = useState(true);
  const [summaryLoading, setSummaryLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [search, setSearch] = useState('');
  const [deptFilter, setDeptFilter] = useState('');

  // Modals & Action states
  const [showAddModal, setShowAddModal] = useState(false);
  const [formLoading, setFormLoading] = useState(false);

  // Dropdown lists
  const [lecturersList, setLecturersList] = useState<LecturerListItem[]>([]);
  const [subjectsList, setSubjectsList] = useState<Subject[]>([]);
  const [dropdownsLoading, setDropdownsLoading] = useState(false);

  const [selectedLecturerId, setSelectedLecturerId] = useState('');
  const [selectedSubjectId, setSelectedSubjectId] = useState('');

  // Delete confirmation
  const [deleteItem, setDeleteItem] = useState<LecturerAssignmentItem | null>(null);
  const [deleteLoading, setDeleteLoading] = useState(false);

  // Fetch summary statistics
  const fetchSummary = useCallback(async (signal?: AbortSignal) => {
    setSummaryLoading(true);
    try {
      const res = await api.get<AssignmentSummaryMetrics>('/api/admin/assignments/summary', { signal });
      setSummary(res.data);
    } catch (err: unknown) {
      if (isRequestCancelled(err)) return;
      // Don't break page on summary failure
    } finally {
      setSummaryLoading(false);
    }
  }, []);

  // Fetch assignments table data
  const fetchAssignments = useCallback(
    async (isManualRefresh = false, signal?: AbortSignal) => {
      if (isManualRefresh) setRefreshing(true);
      else setLoading(true);
      setError(null);

      try {
        const params: Record<string, string | number> = {
          page: currentPage,
          limit: 10,
        };

        if (search.trim()) params.search = search.trim();
        if (deptFilter.trim()) params.department = deptFilter.trim();

        const res = await api.get<AssignmentListResponse>('/api/admin/assignments', { params, signal });

        if (res.data && Array.isArray(res.data.items)) {
          setAssignments(res.data.items);
          setTotalCount(res.data.total ?? 0);
          setTotalPages(res.data.pages ?? 1);
        } else {
          setAssignments([]);
          setTotalCount(0);
          setTotalPages(1);
        }
      } catch (err: any) {
        if (isRequestCancelled(err)) return;
        const errMsg = err?.response?.data?.detail || err?.message || 'Failed to load assignments.';
        setError(errMsg);
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    },
    [currentPage, search, deptFilter]
  );

  useEffect(() => {
    const controller = new AbortController();
    fetchSummary(controller.signal);
    return () => {
      controller.abort();
    };
  }, [fetchSummary]);

  useEffect(() => {
    const controller = new AbortController();
    fetchAssignments(false, controller.signal);
    return () => {
      controller.abort();
    };
  }, [fetchAssignments]);

  // Load dropdown lists for New Assignment modal
  const loadDropdowns = async () => {
    setDropdownsLoading(true);
    try {
      const [lecRes, subRes] = await Promise.all([
        api.get('/api/admin/lecturers?status=active&limit=100'),
        api.get('/api/subjects'),
      ]);

      const lecs = Array.isArray(lecRes.data) ? lecRes.data : lecRes.data.items || [];
      const subs = Array.isArray(subRes.data) ? subRes.data : subRes.data.items || [];

      setLecturersList(lecs);
      setSubjectsList(subs);

      if (lecs.length > 0) setSelectedLecturerId(lecs[0].id);
      if (subs.length > 0) setSelectedSubjectId(subs[0].id);
    } catch (err: unknown) {
      if (isRequestCancelled(err)) return;
      toast.error('Failed to load faculty or course lists.');
    } finally {
      setDropdownsLoading(false);
    }
  };

  const handleOpenAdd = () => {
    setShowAddModal(true);
    loadDropdowns();
  };

  const handleFilterChange = (setter: (val: any) => void, val: any) => {
    setter(val);
    setCurrentPage(1);
  };

  const handleClearFilters = () => {
    setSearch('');
    setDeptFilter('');
    setCurrentPage(1);
  };

  const hasActiveFilters = Boolean(search.trim() || deptFilter.trim());

  // Submit New Assignment
  const handleCreateAssignment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedLecturerId || !selectedSubjectId) {
      toast.error('Please select both a faculty member and a subject.');
      return;
    }

    setFormLoading(true);
    try {
      await api.post('/api/admin/assignments', {
        lecturer_id: selectedLecturerId,
        subject_id: selectedSubjectId,
      });

      toast.success('Teaching assignment created successfully.');
      setShowAddModal(false);
      fetchAssignments(true);
      fetchSummary();
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      toast.error(detail || 'Failed to create assignment.');
    } finally {
      setFormLoading(false);
    }
  };

  // Delete Assignment
  const handleDeleteAssignment = async () => {
    if (!deleteItem) return;

    setDeleteLoading(true);
    try {
      await api.delete(`/api/admin/assignments/${deleteItem.id}`);
      toast.success('Teaching assignment removed.');
      setDeleteItem(null);
      fetchAssignments(true);
      fetchSummary();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Failed to remove assignment.');
    } finally {
      setDeleteLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-surface-900 tracking-tight">Teaching Assignments</h1>
          <p className="text-surface-500 text-sm mt-0.5">Allocate faculty members to curriculum courses and manage teaching loads.</p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => {
              fetchSummary();
              fetchAssignments(true);
            }}
            disabled={refreshing || loading}
            className="btn btn-secondary flex items-center gap-2"
            title="Refresh assignment list"
            aria-label="Refresh assignment list"
          >
            <RotateCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
            <span className="hidden sm:inline">Refresh</span>
          </button>
          <button
            onClick={handleOpenAdd}
            className="btn btn-primary flex items-center gap-2"
            id="new-assignment-btn"
            aria-label="New Assignment"
          >
            <Plus className="w-4 h-4" />
            <span>New Assignment</span>
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Assignments */}
        <div className="bg-white rounded-xl p-5 border border-surface-200 shadow-sm flex items-center gap-4 transition-all hover:shadow-md">
          <div className="w-12 h-12 rounded-xl bg-cyan-50 text-cyan-600 flex items-center justify-center flex-shrink-0">
            <Layers className="w-6 h-6" />
          </div>
          <div>
            <div className="text-sm font-medium text-surface-500">Total Allocations</div>
            {summaryLoading ? (
              <div className="h-7 w-12 bg-surface-200 animate-pulse rounded mt-1" />
            ) : (
              <div className="text-2xl font-bold text-surface-900">{summary?.total_assignments ?? 0}</div>
            )}
            <div className="text-xs text-surface-400 mt-0.5">Faculty-course links</div>
          </div>
        </div>

        {/* Assigned Faculty */}
        <div className="bg-white rounded-xl p-5 border border-surface-200 shadow-sm flex items-center gap-4 transition-all hover:shadow-md">
          <div className="w-12 h-12 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center flex-shrink-0">
            <GraduationCap className="w-6 h-6" />
          </div>
          <div>
            <div className="text-sm font-medium text-surface-500">Assigned Faculty</div>
            {summaryLoading ? (
              <div className="h-7 w-12 bg-surface-200 animate-pulse rounded mt-1" />
            ) : (
              <div className="text-2xl font-bold text-indigo-600">{summary?.assigned_lecturers ?? 0}</div>
            )}
            <div className="text-xs text-surface-400 mt-0.5">Active teaching faculty</div>
          </div>
        </div>

        {/* Covered Courses */}
        <div className="bg-white rounded-xl p-5 border border-surface-200 shadow-sm flex items-center gap-4 transition-all hover:shadow-md">
          <div className="w-12 h-12 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center flex-shrink-0">
            <BookOpen className="w-6 h-6" />
          </div>
          <div>
            <div className="text-sm font-medium text-surface-500">Covered Courses</div>
            {summaryLoading ? (
              <div className="h-7 w-12 bg-surface-200 animate-pulse rounded mt-1" />
            ) : (
              <div className="text-2xl font-bold text-emerald-600">{summary?.assigned_subjects ?? 0}</div>
            )}
            <div className="text-xs text-surface-400 mt-0.5">With faculty mapped</div>
          </div>
        </div>

        {/* Unassigned Courses */}
        <div className="bg-white rounded-xl p-5 border border-surface-200 shadow-sm flex items-center gap-4 transition-all hover:shadow-md">
          <div className="w-12 h-12 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center flex-shrink-0">
            <AlertTriangle className="w-6 h-6" />
          </div>
          <div>
            <div className="text-sm font-medium text-surface-500">Unassigned Courses</div>
            {summaryLoading ? (
              <div className="h-7 w-12 bg-surface-200 animate-pulse rounded mt-1" />
            ) : (
              <div className="text-2xl font-bold text-amber-600">{summary?.unassigned_subjects ?? 0}</div>
            )}
            <div className="text-xs text-surface-400 mt-0.5">Awaiting allocation</div>
          </div>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white rounded-xl p-4 border border-surface-200 shadow-sm space-y-3">
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
          {/* Search Input */}
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-surface-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search by Faculty Name, Employee ID, or Course Code..."
              value={search}
              onChange={(e) => handleFilterChange(setSearch, e.target.value)}
              className="input pl-10 pr-9 w-full text-sm"
              id="assignment-search-input"
              aria-label="Search assignments"
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

          {/* Department Filter */}
          <select
            value={deptFilter}
            onChange={(e) => handleFilterChange(setDeptFilter, e.target.value)}
            className="input text-sm py-2 px-3 pr-8 min-w-[160px]"
            aria-label="Filter by Department"
          >
            <option value="">All Departments</option>
            {DEPARTMENTS.map((dept) => (
              <option key={dept} value={dept}>
                {dept}
              </option>
            ))}
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

      {/* Assignments Table */}
      <div className="bg-white rounded-xl border border-surface-200 shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-6">
            <TableSkeleton rows={8} />
          </div>
        ) : error ? (
          <div className="p-6">
            <ErrorState title="Unable to load assignments" message={error} onRetry={() => fetchAssignments(true)} />
          </div>
        ) : assignments.length === 0 ? (
          <EmptyState
            icon={<Layers className="w-8 h-8 text-surface-400" />}
            title="No Teaching Assignments Found"
            description={
              hasActiveFilters
                ? 'No teaching assignments matched the search or filter criteria.'
                : 'No faculty members are currently assigned to any courses.'
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
                    <span>Create First Assignment</span>
                  </>
                )}
              </button>
            }
          />
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm" id="assignments-table">
                <thead className="bg-surface-50 text-surface-600 font-semibold border-b border-surface-200">
                  <tr>
                    <th scope="col" className="px-5 py-3.5">Faculty Member</th>
                    <th scope="col" className="px-5 py-3.5">Employee ID</th>
                    <th scope="col" className="px-5 py-3.5">Assigned Course</th>
                    <th scope="col" className="px-5 py-3.5">Course Department</th>
                    <th scope="col" className="px-5 py-3.5">Curriculum Level</th>
                    <th scope="col" className="px-5 py-3.5 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-surface-100">
                  {assignments.map((item) => (
                    <tr key={item.id} className="hover:bg-surface-50/70 transition-colors">
                      <td className="px-5 py-4 font-medium text-surface-900">
                        <div className="flex items-center gap-2.5">
                          <div className="w-8 h-8 rounded-full bg-indigo-50 text-indigo-700 flex items-center justify-center font-semibold text-xs flex-shrink-0">
                            {item.lecturer_name
                              .split(' ')
                              .map((n) => n[0])
                              .slice(0, 2)
                              .join('')
                              .toUpperCase()}
                          </div>
                          <div>
                            <div>{item.lecturer_name}</div>
                            <div className="text-xs text-surface-400">{item.lecturer_email}</div>
                          </div>
                        </div>
                      </td>
                      <td className="px-5 py-4 font-mono font-medium text-surface-700">
                        {item.lecturer_employee_id || '—'}
                      </td>
                      <td className="px-5 py-4">
                        <div className="font-semibold text-primary-700 font-mono text-xs">{item.subject_code}</div>
                        <div className="text-surface-900 text-xs font-medium">{item.subject_name}</div>
                      </td>
                      <td className="px-5 py-4 text-surface-700">
                        <span className="inline-block px-2.5 py-0.5 rounded-full text-xs font-medium bg-surface-100 text-surface-700 border border-surface-200">
                          {item.subject_department}
                        </span>
                      </td>
                      <td className="px-5 py-4 text-surface-600 text-xs">
                        Year {item.subject_year} • Sem {item.subject_semester}
                      </td>
                      <td className="px-5 py-4 text-right">
                        <button
                          onClick={() => setDeleteItem(item)}
                          className="p-1.5 text-surface-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors"
                          title="Remove assignment"
                          aria-label={`Remove assignment for ${item.lecturer_name} on ${item.subject_code}`}
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination Controls */}
            <div className="px-5 py-3.5 border-t border-surface-200 bg-surface-50/50 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-surface-600">
              <div>
                Showing <span className="font-semibold text-surface-900">{assignments.length}</span> of{' '}
                <span className="font-semibold text-surface-900">{totalCount}</span> assignments
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

      {/* New Assignment Modal */}
      <Modal
        isOpen={showAddModal}
        title="Create Teaching Assignment"
        onClose={() => !formLoading && setShowAddModal(false)}
        maxWidth="max-w-lg"
      >
        <form onSubmit={handleCreateAssignment} className="space-y-4">
          <div>
            <label className="label" htmlFor="assign-lecturer-select">
              Select Faculty Member <span className="text-danger">*</span>
            </label>
            {dropdownsLoading ? (
              <div className="p-3 text-xs text-surface-500">Loading faculty members...</div>
            ) : lecturersList.length === 0 ? (
              <p className="text-xs text-amber-600 bg-amber-50 p-2.5 rounded-lg border border-amber-200">
                No active faculty members available. Please create or enable a lecturer account first.
              </p>
            ) : (
              <select
                id="assign-lecturer-select"
                value={selectedLecturerId}
                onChange={(e) => setSelectedLecturerId(e.target.value)}
                className="input w-full text-sm"
                disabled={formLoading}
              >
                {lecturersList.map((lec) => (
                  <option key={lec.id} value={lec.id}>
                    {lec.full_name} ({lec.employee_id || 'No ID'}) — {lec.department}
                  </option>
                ))}
              </select>
            )}
          </div>

          <div>
            <label className="label" htmlFor="assign-subject-select">
              Select Curriculum Course <span className="text-danger">*</span>
            </label>
            {dropdownsLoading ? (
              <div className="p-3 text-xs text-surface-500">Loading courses...</div>
            ) : subjectsList.length === 0 ? (
              <p className="text-xs text-amber-600 bg-amber-50 p-2.5 rounded-lg border border-amber-200">
                No courses available in catalog.
              </p>
            ) : (
              <select
                id="assign-subject-select"
                value={selectedSubjectId}
                onChange={(e) => setSelectedSubjectId(e.target.value)}
                className="input w-full text-sm"
                disabled={formLoading}
              >
                {subjectsList.map((sub) => (
                  <option key={sub.id} value={sub.id}>
                    {sub.code} — {sub.name} ({sub.department})
                  </option>
                ))}
              </select>
            )}
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
              disabled={formLoading || lecturersList.length === 0 || subjectsList.length === 0}
            >
              {formLoading && <span className="spinner" />}
              <span>Allocate Course</span>
            </button>
          </div>
        </form>
      </Modal>

      {/* Confirm Remove Assignment Dialog */}
      <ConfirmDialog
        isOpen={Boolean(deleteItem)}
        title="Remove Teaching Assignment"
        message={`Are you sure you want to remove the assignment for ${deleteItem?.lecturer_name} on ${deleteItem?.subject_code} — ${deleteItem?.subject_name}? The lecturer will no longer have teaching allocation for this course.`}
        confirmLabel="Remove Assignment"
        cancelLabel="Cancel"
        variant="danger"
        loading={deleteLoading}
        onConfirm={handleDeleteAssignment}
        onCancel={() => setDeleteItem(null)}
      />
    </div>
  );
}
