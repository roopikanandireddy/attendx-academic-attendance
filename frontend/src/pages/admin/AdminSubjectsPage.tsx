import React, { useEffect, useState, useCallback } from 'react';
import api, { isRequestCancelled } from '../../services/api';
import type {
  SubjectListItem,
  SubjectSummaryMetrics,
  SubjectListResponse,
  SubjectDetailResponse,
  LecturerListItem,
} from '../../types';
import { TableSkeleton } from '../../components/Skeleton';
import EmptyState from '../../components/EmptyState';
import ErrorState from '../../components/ErrorState';
import Modal from '../../components/Modal';
import ConfirmDialog from '../../components/ConfirmDialog';
import {
  BookOpen,
  UserCheck,
  Users,
  Search,
  Plus,
  Eye,
  Pencil,
  Trash2,
  RotateCw,
  X,
  ChevronLeft,
  ChevronRight,
  UserPlus,
  UserMinus,
  GraduationCap,
  Layers,
  Calendar,
  Building,
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

export default function AdminSubjectsPage() {
  // Data state
  const [subjects, setSubjects] = useState<SubjectListItem[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [currentPage, setCurrentPage] = useState(1);
  const [summary, setSummary] = useState<SubjectSummaryMetrics | null>(null);

  // Loading & error states
  const [loading, setLoading] = useState(true);
  const [summaryLoading, setSummaryLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [search, setSearch] = useState('');
  const [deptFilter, setDeptFilter] = useState('');
  const [yearFilter, setYearFilter] = useState('');
  const [semesterFilter, setSemesterFilter] = useState('');
  const [assignmentFilter, setAssignmentFilter] = useState<'all' | 'assigned' | 'unassigned'>('all');

  // Modals
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showViewModal, setShowViewModal] = useState(false);
  const [showAssignModal, setShowAssignModal] = useState(false);
  const [selectedSubjectDetail, setSelectedSubjectDetail] = useState<SubjectDetailResponse | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  // Faculty pool for assignment modal
  const [availableLecturers, setAvailableLecturers] = useState<LecturerListItem[]>([]);
  const [lecturersLoading, setLecturersLoading] = useState(false);
  const [selectedLecturerId, setSelectedLecturerId] = useState('');
  const [subjectForAssignment, setSubjectForAssignment] = useState<SubjectListItem | null>(null);

  // Delete confirmation
  const [deleteSubjectItem, setDeleteSubjectItem] = useState<SubjectListItem | null>(null);
  const [deleteLoading, setDeleteLoading] = useState(false);

  // Form states
  const [formLoading, setFormLoading] = useState(false);
  const [formData, setFormData] = useState({
    id: '',
    code: '',
    name: '',
    department: 'Computer Science',
    year: '1',
    semester: '1',
  });
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});

  // Active view modal tab
  const [viewTab, setViewTab] = useState<'info' | 'faculty' | 'students'>('info');

  // Fetch summary metrics
  const fetchSummary = useCallback(async (signal?: AbortSignal) => {
    setSummaryLoading(true);
    try {
      const res = await api.get<SubjectSummaryMetrics>('/api/admin/subjects/summary', { signal });
      setSummary(res.data);
    } catch (err: unknown) {
      if (isRequestCancelled(err)) return;
      // Don't break page on summary failure
    } finally {
      setSummaryLoading(false);
    }
  }, []);

  // Fetch subjects table data
  const fetchSubjects = useCallback(
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
        if (yearFilter.trim()) params.year = yearFilter.trim();
        if (semesterFilter.trim()) params.semester = semesterFilter.trim();
        if (assignmentFilter !== 'all') params.assignment_status = assignmentFilter;

        const res = await api.get<SubjectListResponse>('/api/admin/subjects', { params, signal });

        if (res.data && Array.isArray(res.data.items)) {
          setSubjects(res.data.items);
          setTotalCount(res.data.total ?? 0);
          setTotalPages(res.data.pages ?? 1);
        } else {
          setSubjects([]);
          setTotalCount(0);
          setTotalPages(1);
        }
      } catch (err: any) {
        if (isRequestCancelled(err)) return;
        const errMsg = err?.response?.data?.detail || err?.message || 'Failed to load subjects.';
        setError(errMsg);
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    },
    [currentPage, search, deptFilter, yearFilter, semesterFilter, assignmentFilter]
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
    fetchSubjects(false, controller.signal);
    return () => {
      controller.abort();
    };
  }, [fetchSubjects]);

  // Load active lecturers for assignment dropdown
  const loadLecturers = async () => {
    setLecturersLoading(true);
    try {
      const res = await api.get('/api/admin/lecturers?status=active&limit=100');
      const items = Array.isArray(res.data) ? res.data : res.data.items || [];
      setAvailableLecturers(items);
      if (items.length > 0) {
        setSelectedLecturerId(items[0].id);
      }
    } catch (err: unknown) {
      if (isRequestCancelled(err)) return;
      toast.error('Failed to load active lecturers list.');
    } finally {
      setLecturersLoading(false);
    }
  };

  const handleFilterChange = (setter: (val: any) => void, val: any) => {
    setter(val);
    setCurrentPage(1);
  };

  const handleClearFilters = () => {
    setSearch('');
    setDeptFilter('');
    setYearFilter('');
    setSemesterFilter('');
    setAssignmentFilter('all');
    setCurrentPage(1);
  };

  const hasActiveFilters = Boolean(
    search.trim() || deptFilter.trim() || yearFilter.trim() || semesterFilter.trim() || assignmentFilter !== 'all'
  );

  // View subject full details
  const handleViewSubject = async (id: string) => {
    setShowViewModal(true);
    setDetailLoading(true);
    setSelectedSubjectDetail(null);
    setViewTab('info');
    try {
      const res = await api.get<SubjectDetailResponse>(`/api/admin/subjects/${id}`);
      setSelectedSubjectDetail(res.data);
    } catch (err: any) {
      if (isRequestCancelled(err)) return;
      toast.error(err?.response?.data?.detail || 'Failed to load subject details.');
      setShowViewModal(false);
    } finally {
      setDetailLoading(false);
    }
  };

  // Open Edit modal
  const handleOpenEdit = (subject: SubjectListItem) => {
    setFormData({
      id: subject.id,
      code: subject.code,
      name: subject.name,
      department: subject.department,
      year: String(subject.year),
      semester: String(subject.semester),
    });
    setFormErrors({});
    setShowEditModal(true);
  };

  // Open Add modal
  const handleOpenAdd = () => {
    setFormData({
      id: '',
      code: '',
      name: '',
      department: 'Computer Science',
      year: '1',
      semester: '1',
    });
    setFormErrors({});
    setShowAddModal(true);
  };

  // Open Assign Faculty modal
  const handleOpenAssign = (subject: SubjectListItem) => {
    setSubjectForAssignment(subject);
    setShowAssignModal(true);
    loadLecturers();
  };

  // Form validation
  const validateForm = () => {
    const errors: Record<string, string> = {};
    if (!formData.code.trim()) {
      errors.code = 'Subject code is required';
    } else if (formData.code.trim().length < 2) {
      errors.code = 'Code must be at least 2 characters';
    }
    if (!formData.name.trim()) {
      errors.name = 'Subject name is required';
    } else if (formData.name.trim().length < 2) {
      errors.name = 'Name must be at least 2 characters';
    }
    if (!formData.department.trim()) {
      errors.department = 'Department is required';
    }
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  // Submit Add Subject
  const handleCreateSubject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateForm()) return;

    setFormLoading(true);
    try {
      await api.post('/api/admin/subjects', {
        code: formData.code.trim().toUpperCase(),
        name: formData.name.trim(),
        department: formData.department.trim(),
        year: parseInt(formData.year, 10),
        semester: parseInt(formData.semester, 10),
      });

      toast.success('Subject created successfully.');
      setShowAddModal(false);
      fetchSubjects(true);
      fetchSummary();
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      if (err?.response?.status === 409) {
        setFormErrors((prev) => ({ ...prev, code: detail || 'Subject code already exists' }));
      } else {
        toast.error(detail || 'Failed to create subject.');
      }
    } finally {
      setFormLoading(false);
    }
  };

  // Submit Edit Subject
  const handleUpdateSubject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateForm()) return;

    setFormLoading(true);
    try {
      await api.put(`/api/admin/subjects/${formData.id}`, {
        code: formData.code.trim().toUpperCase(),
        name: formData.name.trim(),
        department: formData.department.trim(),
        year: parseInt(formData.year, 10),
        semester: parseInt(formData.semester, 10),
      });

      toast.success('Subject updated successfully.');
      setShowEditModal(false);
      fetchSubjects(true);
      fetchSummary();
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      if (err?.response?.status === 409) {
        setFormErrors((prev) => ({ ...prev, code: detail || 'Subject code already exists' }));
      } else {
        toast.error(detail || 'Failed to update subject.');
      }
    } finally {
      setFormLoading(false);
    }
  };

  // Submit Assign Faculty
  const handleAssignFaculty = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!subjectForAssignment || !selectedLecturerId) return;

    setFormLoading(true);
    try {
      await api.post('/api/admin/assignments', {
        subject_id: subjectForAssignment.id,
        lecturer_id: selectedLecturerId,
      });

      toast.success('Faculty member assigned successfully.');
      setShowAssignModal(false);
      fetchSubjects(true);
      fetchSummary();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Failed to assign faculty member.');
    } finally {
      setFormLoading(false);
    }
  };

  // Remove Faculty Assignment
  const handleUnassignFaculty = async (subjectId: string, lecturerId: string) => {
    try {
      await api.delete(`/api/admin/subjects/${subjectId}/lecturers/${lecturerId}`);
      toast.success('Faculty unassigned successfully.');
      if (selectedSubjectDetail) {
        handleViewSubject(subjectId);
      }
      fetchSubjects(true);
      fetchSummary();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Failed to unassign faculty.');
    }
  };

  // Delete Subject
  const handleDeleteSubject = async () => {
    if (!deleteSubjectItem) return;

    setDeleteLoading(true);
    try {
      await api.delete(`/api/admin/subjects/${deleteSubjectItem.id}`);
      toast.success('Subject deleted successfully.');
      setDeleteSubjectItem(null);
      fetchSubjects(true);
      fetchSummary();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Failed to delete subject.');
    } finally {
      setDeleteLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-surface-900 tracking-tight">Subject Management</h1>
          <p className="text-surface-500 text-sm mt-0.5">Curriculum courses, department offerings, and course catalog.</p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => {
              fetchSummary();
              fetchSubjects(true);
            }}
            disabled={refreshing || loading}
            className="btn btn-secondary flex items-center gap-2"
            title="Refresh subjects list"
            aria-label="Refresh subjects list"
          >
            <RotateCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
            <span className="hidden sm:inline">Refresh</span>
          </button>
          <button
            onClick={handleOpenAdd}
            className="btn btn-primary flex items-center gap-2"
            id="add-subject-btn"
            aria-label="Add Subject"
          >
            <Plus className="w-4 h-4" />
            <span>Add Subject</span>
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Subjects */}
        <div className="bg-white rounded-xl p-5 border border-surface-200 shadow-sm flex items-center gap-4 transition-all hover:shadow-md">
          <div className="w-12 h-12 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center flex-shrink-0">
            <BookOpen className="w-6 h-6" />
          </div>
          <div>
            <div className="text-sm font-medium text-surface-500">Total Subjects</div>
            {summaryLoading ? (
              <div className="h-7 w-12 bg-surface-200 animate-pulse rounded mt-1" />
            ) : (
              <div className="text-2xl font-bold text-surface-900">{summary?.total_subjects ?? 0}</div>
            )}
            <div className="text-xs text-surface-400 mt-0.5">Catalog curriculum</div>
          </div>
        </div>

        {/* Assigned Subjects */}
        <div className="bg-white rounded-xl p-5 border border-surface-200 shadow-sm flex items-center gap-4 transition-all hover:shadow-md">
          <div className="w-12 h-12 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center flex-shrink-0">
            <UserCheck className="w-6 h-6" />
          </div>
          <div>
            <div className="text-sm font-medium text-surface-500">Assigned Courses</div>
            {summaryLoading ? (
              <div className="h-7 w-12 bg-surface-200 animate-pulse rounded mt-1" />
            ) : (
              <div className="text-2xl font-bold text-emerald-600">{summary?.assigned_subjects ?? 0}</div>
            )}
            <div className="text-xs text-surface-400 mt-0.5">With faculty allocated</div>
          </div>
        </div>

        {/* Unassigned Subjects */}
        <div className="bg-white rounded-xl p-5 border border-surface-200 shadow-sm flex items-center gap-4 transition-all hover:shadow-md">
          <div className="w-12 h-12 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center flex-shrink-0">
            <Layers className="w-6 h-6" />
          </div>
          <div>
            <div className="text-sm font-medium text-surface-500">Unassigned Courses</div>
            {summaryLoading ? (
              <div className="h-7 w-12 bg-surface-200 animate-pulse rounded mt-1" />
            ) : (
              <div className="text-2xl font-bold text-amber-600">{summary?.unassigned_subjects ?? 0}</div>
            )}
            <div className="text-xs text-surface-400 mt-0.5">Need faculty mapping</div>
          </div>
        </div>

        {/* Total Enrollments */}
        <div className="bg-white rounded-xl p-5 border border-surface-200 shadow-sm flex items-center gap-4 transition-all hover:shadow-md">
          <div className="w-12 h-12 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center flex-shrink-0">
            <Users className="w-6 h-6" />
          </div>
          <div>
            <div className="text-sm font-medium text-surface-500">Total Enrollments</div>
            {summaryLoading ? (
              <div className="h-7 w-12 bg-surface-200 animate-pulse rounded mt-1" />
            ) : (
              <div className="text-2xl font-bold text-purple-600">{summary?.total_enrollments ?? 0}</div>
            )}
            <div className="text-xs text-surface-400 mt-0.5">Student course seats</div>
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
              placeholder="Search by Subject Code or Course Name..."
              value={search}
              onChange={(e) => handleFilterChange(setSearch, e.target.value)}
              className="input pl-10 pr-9 w-full text-sm"
              id="subject-search-input"
              aria-label="Search subjects"
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

            {/* Year Filter */}
            <select
              value={yearFilter}
              onChange={(e) => handleFilterChange(setYearFilter, e.target.value)}
              className="input text-sm py-2 px-3 pr-8 min-w-[110px]"
              aria-label="Filter by Year"
            >
              <option value="">All Years</option>
              <option value="1">Year 1</option>
              <option value="2">Year 2</option>
              <option value="3">Year 3</option>
              <option value="4">Year 4</option>
            </select>

            {/* Semester Filter */}
            <select
              value={semesterFilter}
              onChange={(e) => handleFilterChange(setSemesterFilter, e.target.value)}
              className="input text-sm py-2 px-3 pr-8 min-w-[110px]"
              aria-label="Filter by Semester"
            >
              <option value="">All Semesters</option>
              {[1, 2, 3, 4, 5, 6, 7, 8].map((s) => (
                <option key={s} value={String(s)}>
                  Sem {s}
                </option>
              ))}
            </select>

            {/* Assignment Status Filter */}
            <select
              value={assignmentFilter}
              onChange={(e) => handleFilterChange(setAssignmentFilter, e.target.value)}
              className="input text-sm py-2 px-3 pr-8 min-w-[140px]"
              aria-label="Filter by Faculty Assignment"
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

      {/* Subjects Table */}
      <div className="bg-white rounded-xl border border-surface-200 shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-6">
            <TableSkeleton rows={8} />
          </div>
        ) : error ? (
          <div className="p-6">
            <ErrorState title="Unable to load subjects" message={error} onRetry={() => fetchSubjects(true)} />
          </div>
        ) : subjects.length === 0 ? (
          <EmptyState
            icon={<BookOpen className="w-8 h-8 text-surface-400" />}
            title="No Subjects Found"
            description={
              hasActiveFilters
                ? 'No subjects matched the selected filters. Try broadening your search or resetting filters.'
                : 'There are currently no subjects registered in the course catalog.'
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
                    <span>Add First Subject</span>
                  </>
                )}
              </button>
            }
          />
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm" id="subjects-table">
                <thead className="bg-surface-50 text-surface-600 font-semibold border-b border-surface-200">
                  <tr>
                    <th scope="col" className="px-5 py-3.5">Code</th>
                    <th scope="col" className="px-5 py-3.5">Course Name</th>
                    <th scope="col" className="px-5 py-3.5">Department</th>
                    <th scope="col" className="px-5 py-3.5">Year / Sem</th>
                    <th scope="col" className="px-5 py-3.5">Assigned Faculty</th>
                    <th scope="col" className="px-5 py-3.5">Enrollments</th>
                    <th scope="col" className="px-5 py-3.5 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-surface-100">
                  {subjects.map((sub) => {
                    const hasLecturer = sub.assigned_lecturers && sub.assigned_lecturers.length > 0;
                    return (
                      <tr key={sub.id} className="hover:bg-surface-50/70 transition-colors">
                        <td className="px-5 py-4 font-mono font-semibold text-primary-700">
                          {sub.code}
                        </td>
                        <td className="px-5 py-4 font-medium text-surface-900">
                          {sub.name}
                        </td>
                        <td className="px-5 py-4 text-surface-700">
                          <span className="inline-block px-2.5 py-0.5 rounded-full text-xs font-medium bg-surface-100 text-surface-700 border border-surface-200">
                            {sub.department}
                          </span>
                        </td>
                        <td className="px-5 py-4 text-surface-600 text-xs">
                          <span className="font-medium text-surface-800">Year {sub.year}</span> • Sem {sub.semester}
                        </td>
                        <td className="px-5 py-4">
                          {hasLecturer ? (
                            <div className="flex flex-wrap gap-1.5">
                              {sub.assigned_lecturers.map((lec) => (
                                <span
                                  key={lec.id}
                                  className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200"
                                >
                                  <GraduationCap className="w-3 h-3" />
                                  <span>{lec.full_name}</span>
                                </span>
                              ))}
                            </div>
                          ) : (
                            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-50 text-amber-700 border border-amber-200">
                              <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
                              Unassigned
                            </span>
                          )}
                        </td>
                        <td className="px-5 py-4">
                          <span className="inline-flex items-center gap-1 text-xs text-surface-600 bg-surface-100 px-2 py-0.5 rounded-md font-medium">
                            <Users className="w-3 h-3 text-surface-400" />
                            {sub.enrolled_students_count} students
                          </span>
                        </td>
                        <td className="px-5 py-4 text-right">
                          <div className="flex items-center justify-end gap-1.5">
                            <button
                              onClick={() => handleViewSubject(sub.id)}
                              className="p-1.5 text-surface-500 hover:text-primary-600 hover:bg-surface-100 rounded-lg transition-colors"
                              title="View details"
                              aria-label={`View details for ${sub.name}`}
                            >
                              <Eye className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => handleOpenAssign(sub)}
                              className="p-1.5 text-surface-500 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors"
                              title="Assign faculty"
                              aria-label={`Assign faculty to ${sub.name}`}
                            >
                              <UserPlus className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => handleOpenEdit(sub)}
                              className="p-1.5 text-surface-500 hover:text-amber-600 hover:bg-surface-100 rounded-lg transition-colors"
                              title="Edit subject"
                              aria-label={`Edit ${sub.name}`}
                            >
                              <Pencil className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => setDeleteSubjectItem(sub)}
                              className="p-1.5 text-surface-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors"
                              title="Delete subject"
                              aria-label={`Delete ${sub.name}`}
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
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
                Showing <span className="font-semibold text-surface-900">{subjects.length}</span> of{' '}
                <span className="font-semibold text-surface-900">{totalCount}</span> subjects
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

      {/* Add Subject Modal */}
      <Modal
        isOpen={showAddModal}
        title="Add New Subject"
        onClose={() => !formLoading && setShowAddModal(false)}
        maxWidth="max-w-lg"
      >
        <form onSubmit={handleCreateSubject} className="space-y-4">
          <div>
            <label className="label" htmlFor="add-subject-code">
              Subject Code <span className="text-danger">*</span>
            </label>
            <input
              id="add-subject-code"
              type="text"
              placeholder="e.g. CS301"
              value={formData.code}
              onChange={(e) => setFormData({ ...formData, code: e.target.value.toUpperCase() })}
              className={`input w-full font-mono uppercase ${formErrors.code ? 'border-danger' : ''}`}
              disabled={formLoading}
            />
            {formErrors.code && <p className="text-danger text-xs mt-1">{formErrors.code}</p>}
          </div>

          <div>
            <label className="label" htmlFor="add-subject-name">
              Course Name <span className="text-danger">*</span>
            </label>
            <input
              id="add-subject-name"
              type="text"
              placeholder="e.g. Data Structures & Algorithms"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className={`input w-full ${formErrors.name ? 'border-danger' : ''}`}
              disabled={formLoading}
            />
            {formErrors.name && <p className="text-danger text-xs mt-1">{formErrors.name}</p>}
          </div>

          <div>
            <label className="label" htmlFor="add-department">
              Department <span className="text-danger">*</span>
            </label>
            <select
              id="add-department"
              value={formData.department}
              onChange={(e) => setFormData({ ...formData, department: e.target.value })}
              className="input w-full"
              disabled={formLoading}
            >
              {DEPARTMENTS.map((dept) => (
                <option key={dept} value={dept}>
                  {dept}
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label" htmlFor="add-year">Academic Year</label>
              <select
                id="add-year"
                value={formData.year}
                onChange={(e) => setFormData({ ...formData, year: e.target.value })}
                className="input w-full"
                disabled={formLoading}
              >
                <option value="1">Year 1</option>
                <option value="2">Year 2</option>
                <option value="3">Year 3</option>
                <option value="4">Year 4</option>
              </select>
            </div>
            <div>
              <label className="label" htmlFor="add-semester">Semester</label>
              <select
                id="add-semester"
                value={formData.semester}
                onChange={(e) => setFormData({ ...formData, semester: e.target.value })}
                className="input w-full"
                disabled={formLoading}
              >
                {[1, 2, 3, 4, 5, 6, 7, 8].map((s) => (
                  <option key={s} value={String(s)}>
                    Semester {s}
                  </option>
                ))}
              </select>
            </div>
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
              <span>Create Subject</span>
            </button>
          </div>
        </form>
      </Modal>

      {/* Edit Subject Modal */}
      <Modal
        isOpen={showEditModal}
        title="Edit Subject"
        onClose={() => !formLoading && setShowEditModal(false)}
        maxWidth="max-w-lg"
      >
        <form onSubmit={handleUpdateSubject} className="space-y-4">
          <div>
            <label className="label" htmlFor="edit-subject-code">
              Subject Code <span className="text-danger">*</span>
            </label>
            <input
              id="edit-subject-code"
              type="text"
              value={formData.code}
              onChange={(e) => setFormData({ ...formData, code: e.target.value.toUpperCase() })}
              className={`input w-full font-mono uppercase ${formErrors.code ? 'border-danger' : ''}`}
              disabled={formLoading}
            />
            {formErrors.code && <p className="text-danger text-xs mt-1">{formErrors.code}</p>}
          </div>

          <div>
            <label className="label" htmlFor="edit-subject-name">
              Course Name <span className="text-danger">*</span>
            </label>
            <input
              id="edit-subject-name"
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className={`input w-full ${formErrors.name ? 'border-danger' : ''}`}
              disabled={formLoading}
            />
            {formErrors.name && <p className="text-danger text-xs mt-1">{formErrors.name}</p>}
          </div>

          <div>
            <label className="label" htmlFor="edit-department">
              Department <span className="text-danger">*</span>
            </label>
            <select
              id="edit-department"
              value={formData.department}
              onChange={(e) => setFormData({ ...formData, department: e.target.value })}
              className="input w-full"
              disabled={formLoading}
            >
              {DEPARTMENTS.map((dept) => (
                <option key={dept} value={dept}>
                  {dept}
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label" htmlFor="edit-year">Academic Year</label>
              <select
                id="edit-year"
                value={formData.year}
                onChange={(e) => setFormData({ ...formData, year: e.target.value })}
                className="input w-full"
                disabled={formLoading}
              >
                <option value="1">Year 1</option>
                <option value="2">Year 2</option>
                <option value="3">Year 3</option>
                <option value="4">Year 4</option>
              </select>
            </div>
            <div>
              <label className="label" htmlFor="edit-semester">Semester</label>
              <select
                id="edit-semester"
                value={formData.semester}
                onChange={(e) => setFormData({ ...formData, semester: e.target.value })}
                className="input w-full"
                disabled={formLoading}
              >
                {[1, 2, 3, 4, 5, 6, 7, 8].map((s) => (
                  <option key={s} value={String(s)}>
                    Semester {s}
                  </option>
                ))}
              </select>
            </div>
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

      {/* Assign Faculty Modal */}
      <Modal
        isOpen={showAssignModal}
        title="Assign Faculty Member"
        onClose={() => !formLoading && setShowAssignModal(false)}
        maxWidth="max-w-md"
      >
        <form onSubmit={handleAssignFaculty} className="space-y-4">
          <div className="bg-surface-50 p-3 rounded-lg border border-surface-200 text-xs">
            <div className="font-semibold text-surface-900">{subjectForAssignment?.code}</div>
            <div className="text-surface-600">{subjectForAssignment?.name}</div>
          </div>

          <div>
            <label className="label" htmlFor="select-lecturer">
              Select Faculty Member <span className="text-danger">*</span>
            </label>
            {lecturersLoading ? (
              <div className="p-3 text-xs text-surface-500">Loading active lecturers...</div>
            ) : availableLecturers.length === 0 ? (
              <p className="text-xs text-amber-600 bg-amber-50 p-2.5 rounded-lg border border-amber-200">
                No active faculty members available. Please add or enable lecturers first.
              </p>
            ) : (
              <select
                id="select-lecturer"
                value={selectedLecturerId}
                onChange={(e) => setSelectedLecturerId(e.target.value)}
                className="input w-full text-sm"
                disabled={formLoading}
              >
                {availableLecturers.map((lec) => (
                  <option key={lec.id} value={lec.id}>
                    {lec.full_name} ({lec.employee_id || 'No ID'}) — {lec.department}
                  </option>
                ))}
              </select>
            )}
          </div>

          <div className="flex justify-end gap-3 pt-3 border-t border-surface-100">
            <button
              type="button"
              onClick={() => setShowAssignModal(false)}
              className="btn btn-secondary"
              disabled={formLoading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-primary flex items-center gap-2"
              disabled={formLoading || availableLecturers.length === 0}
            >
              {formLoading && <span className="spinner" />}
              <span>Assign Faculty</span>
            </button>
          </div>
        </form>
      </Modal>

      {/* View Subject Full Details Modal */}
      <Modal
        isOpen={showViewModal}
        title="Course Overview & Allocations"
        onClose={() => setShowViewModal(false)}
        maxWidth="max-w-2xl"
      >
        {detailLoading ? (
          <div className="p-8 text-center">
            <div className="spinner mx-auto mb-3" />
            <p className="text-surface-500 text-sm">Loading course details...</p>
          </div>
        ) : selectedSubjectDetail ? (
          <div className="space-y-5">
            {/* Header info */}
            <div className="flex items-start justify-between bg-surface-50 p-4 rounded-xl border border-surface-200">
              <div className="flex items-center gap-3.5">
                <div className="w-12 h-12 rounded-xl bg-primary-100 text-primary-700 flex items-center justify-center font-bold text-base font-mono">
                  {selectedSubjectDetail.code.slice(0, 4)}
                </div>
                <div>
                  <h3 className="font-semibold text-surface-900 text-base">
                    {selectedSubjectDetail.name}
                  </h3>
                  <div className="text-xs text-surface-500 font-mono mt-0.5">
                    Course Code: <span className="font-semibold text-primary-700">{selectedSubjectDetail.code}</span>
                  </div>
                </div>
              </div>
              <span className="inline-block px-3 py-1 rounded-full text-xs font-semibold bg-surface-100 text-surface-700 border border-surface-200">
                {selectedSubjectDetail.department}
              </span>
            </div>

            {/* Navigation Tabs */}
            <div className="flex border-b border-surface-200 text-xs font-medium">
              <button
                onClick={() => setViewTab('info')}
                className={`pb-2.5 px-4 border-b-2 transition-colors ${
                  viewTab === 'info'
                    ? 'border-primary-600 text-primary-600 font-semibold'
                    : 'border-transparent text-surface-500 hover:text-surface-700'
                }`}
              >
                Course Info
              </button>
              <button
                onClick={() => setViewTab('faculty')}
                className={`pb-2.5 px-4 border-b-2 transition-colors flex items-center gap-1.5 ${
                  viewTab === 'faculty'
                    ? 'border-primary-600 text-primary-600 font-semibold'
                    : 'border-transparent text-surface-500 hover:text-surface-700'
                }`}
              >
                <span>Assigned Faculty</span>
                <span className="px-1.5 py-0.2 rounded-full bg-surface-100 text-[10px]">
                  {selectedSubjectDetail.assigned_lecturers_count}
                </span>
              </button>
              <button
                onClick={() => setViewTab('students')}
                className={`pb-2.5 px-4 border-b-2 transition-colors flex items-center gap-1.5 ${
                  viewTab === 'students'
                    ? 'border-primary-600 text-primary-600 font-semibold'
                    : 'border-transparent text-surface-500 hover:text-surface-700'
                }`}
              >
                <span>Enrolled Students</span>
                <span className="px-1.5 py-0.2 rounded-full bg-surface-100 text-[10px]">
                  {selectedSubjectDetail.enrolled_students_count}
                </span>
              </button>
            </div>

            {/* Tab 1: Course Info */}
            {viewTab === 'info' && (
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div className="bg-white p-3.5 rounded-lg border border-surface-200">
                  <div className="text-xs text-surface-400 flex items-center gap-1.5 mb-1">
                    <Building className="w-3.5 h-3.5 text-surface-400" />
                    Department
                  </div>
                  <div className="font-medium text-surface-800">{selectedSubjectDetail.department}</div>
                </div>
                <div className="bg-white p-3.5 rounded-lg border border-surface-200">
                  <div className="text-xs text-surface-400 flex items-center gap-1.5 mb-1">
                    <Calendar className="w-3.5 h-3.5 text-surface-400" />
                    Academic Level
                  </div>
                  <div className="font-medium text-surface-800">
                    Year {selectedSubjectDetail.year} • Semester {selectedSubjectDetail.semester}
                  </div>
                </div>
                <div className="bg-white p-3.5 rounded-lg border border-surface-200">
                  <div className="text-xs text-surface-400 flex items-center gap-1.5 mb-1">
                    <GraduationCap className="w-3.5 h-3.5 text-surface-400" />
                    Assigned Faculty
                  </div>
                  <div className="font-medium text-surface-800">
                    {selectedSubjectDetail.assigned_lecturers_count} faculty allocated
                  </div>
                </div>
                <div className="bg-white p-3.5 rounded-lg border border-surface-200">
                  <div className="text-xs text-surface-400 flex items-center gap-1.5 mb-1">
                    <Users className="w-3.5 h-3.5 text-surface-400" />
                    Enrolled Students
                  </div>
                  <div className="font-medium text-surface-800">
                    {selectedSubjectDetail.enrolled_students_count} active students
                  </div>
                </div>
              </div>
            )}

            {/* Tab 2: Assigned Faculty */}
            {viewTab === 'faculty' && (
              <div className="space-y-3">
                {selectedSubjectDetail.assigned_lecturers && selectedSubjectDetail.assigned_lecturers.length > 0 ? (
                  <div className="border border-surface-200 rounded-lg overflow-hidden">
                    <table className="w-full text-xs text-left">
                      <thead className="bg-surface-50 text-surface-600 border-b border-surface-200">
                        <tr>
                          <th className="px-4 py-2 font-semibold">Faculty Name</th>
                          <th className="px-4 py-2 font-semibold">Employee ID</th>
                          <th className="px-4 py-2 font-semibold">Department</th>
                          <th className="px-4 py-2 font-semibold text-right">Action</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-surface-100">
                        {selectedSubjectDetail.assigned_lecturers.map((lec) => (
                          <tr key={lec.id}>
                            <td className="px-4 py-2.5 font-medium text-surface-900">{lec.full_name}</td>
                            <td className="px-4 py-2.5 font-mono text-surface-600">{lec.employee_id || '—'}</td>
                            <td className="px-4 py-2.5 text-surface-600">{lec.department || 'General'}</td>
                            <td className="px-4 py-2.5 text-right">
                              <button
                                onClick={() => handleUnassignFaculty(selectedSubjectDetail.id, lec.id)}
                                className="text-rose-600 hover:text-rose-800 font-medium text-xs inline-flex items-center gap-1"
                              >
                                <UserMinus className="w-3.5 h-3.5" />
                                <span>Remove</span>
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div className="bg-surface-50 border border-dashed border-surface-300 rounded-xl p-6 text-center">
                    <GraduationCap className="w-8 h-8 text-surface-400 mx-auto mb-2" />
                    <p className="text-sm font-medium text-surface-700">No faculty assigned to this course yet.</p>
                    <button
                      onClick={() => {
                        setShowViewModal(false);
                        const match = subjects.find((s) => s.id === selectedSubjectDetail.id);
                        if (match) handleOpenAssign(match);
                      }}
                      className="btn btn-primary text-xs mt-3"
                    >
                      Assign Faculty Now
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* Tab 3: Enrolled Students */}
            {viewTab === 'students' && (
              <div className="space-y-3">
                {selectedSubjectDetail.enrolled_students && selectedSubjectDetail.enrolled_students.length > 0 ? (
                  <div className="border border-surface-200 rounded-lg overflow-hidden max-h-60 overflow-y-auto">
                    <table className="w-full text-xs text-left">
                      <thead className="bg-surface-50 text-surface-600 border-b border-surface-200 sticky top-0">
                        <tr>
                          <th className="px-4 py-2 font-semibold">Student ID</th>
                          <th className="px-4 py-2 font-semibold">Full Name</th>
                          <th className="px-4 py-2 font-semibold">Department</th>
                          <th className="px-4 py-2 font-semibold">Section</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-surface-100">
                        {selectedSubjectDetail.enrolled_students.map((st) => (
                          <tr key={st.id}>
                            <td className="px-4 py-2 font-mono font-medium text-surface-800">{st.student_id || '—'}</td>
                            <td className="px-4 py-2 font-medium text-surface-900">{st.full_name}</td>
                            <td className="px-4 py-2 text-surface-600">{st.department || '—'}</td>
                            <td className="px-4 py-2 text-surface-600">Sec {st.section || 'A'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div className="bg-surface-50 border border-dashed border-surface-300 rounded-xl p-6 text-center">
                    <Users className="w-8 h-8 text-surface-400 mx-auto mb-2" />
                    <p className="text-sm font-medium text-surface-700">No students enrolled in this course yet.</p>
                  </div>
                )}
              </div>
            )}

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

      {/* Confirm Subject Delete Dialog */}
      <ConfirmDialog
        isOpen={Boolean(deleteSubjectItem)}
        title="Delete Subject"
        message={`Are you sure you want to delete ${deleteSubjectItem?.code} — ${deleteSubjectItem?.name}? This will remove all associated student enrollments and faculty teaching assignments.`}
        confirmLabel="Delete Subject"
        cancelLabel="Cancel"
        variant="danger"
        loading={deleteLoading}
        onConfirm={handleDeleteSubject}
        onCancel={() => setDeleteSubjectItem(null)}
      />
    </div>
  );
}
