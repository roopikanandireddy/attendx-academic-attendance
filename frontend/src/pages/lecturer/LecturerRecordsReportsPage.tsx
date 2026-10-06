import { useEffect, useState, useCallback } from 'react';
import api, { isRequestCancelled } from '../../services/api';
import type {
  LecturerAssignedSubjectItem,
  LecturerRecordsResponse,
  LecturerStudentReportResponse,
  LecturerSubjectReportResponse,
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
  Download,
  Filter,
  Percent,
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
  ChevronLeft,
  ChevronRight,
  Eye,
  X,
  FileSpreadsheet,
  AlertTriangle,
} from 'lucide-react';

export default function LecturerRecordsReportsPage() {
  // 1. Subjects state
  const [subjects, setSubjects] = useState<LecturerAssignedSubjectItem[]>([]);
  const [loadingSubjects, setLoadingSubjects] = useState(true);

  // 2. Active Tab state: 'records' | 'subject_report'
  const [activeTab, setActiveTab] = useState<'records' | 'subject_report'>('records');

  // 3. Filter states
  const [selectedSubjectId, setSelectedSubjectId] = useState<string>('');
  const [dateFrom, setDateFrom] = useState<string>('');
  const [dateTo, setDateTo] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'present' | 'absent'>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');

  // 4. Records list state & pagination
  const [recordsData, setRecordsData] = useState<LecturerRecordsResponse | null>(null);
  const [loadingRecords, setLoadingRecords] = useState(false);
  const [recordsError, setRecordsError] = useState<string | null>(null);
  const [page, setPage] = useState<number>(1);
  const [limit, setLimit] = useState<number>(20);
  const [sortBy, setSortBy] = useState<string>('date');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  // 5. Subject Report state
  const [subjectReportData, setSubjectReportData] = useState<LecturerSubjectReportResponse | null>(null);
  const [loadingSubjectReport, setLoadingSubjectReport] = useState(false);
  const [subjectReportError, setSubjectReportError] = useState<string | null>(null);

  // 6. Student Report Modal state
  const [inspectStudentId, setInspectStudentId] = useState<string | null>(null);
  const [studentReportData, setStudentReportData] = useState<LecturerStudentReportResponse | null>(null);
  const [loadingStudentReport, setLoadingStudentReport] = useState(false);
  const [studentReportError, setStudentReportError] = useState<string | null>(null);

  // 7. Exporting state
  const [isExporting, setIsExporting] = useState(false);

  // Fetch assigned subjects
  const fetchAssignedSubjects = useCallback(async (signal?: AbortSignal) => {
    setLoadingSubjects(true);
    try {
      const res = await api.get<LecturerAssignedSubjectItem[]>('/api/lecturer/subjects', { signal });
      setSubjects(res.data);
    } catch (err: any) {
      if (isRequestCancelled(err)) return;
      toast.error(err.response?.data?.detail || 'Failed to load assigned subjects');
    } finally {
      setLoadingSubjects(false);
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    fetchAssignedSubjects(controller.signal);
    return () => {
      controller.abort();
    };
  }, [fetchAssignedSubjects]);

  // Fetch records
  const fetchRecords = useCallback(async (signal?: AbortSignal) => {
    setLoadingRecords(true);
    setRecordsError(null);
    try {
      const params: Record<string, any> = {
        page,
        limit,
        sort_by: sortBy,
        sort_order: sortOrder,
      };

      if (selectedSubjectId) params.subject_id = selectedSubjectId;
      if (dateFrom) params.date_from = dateFrom;
      if (dateTo) params.date_to = dateTo;
      if (statusFilter !== 'all') params.status = statusFilter;
      if (searchQuery.trim()) params.search = searchQuery.trim();

      const res = await api.get<LecturerRecordsResponse>('/api/lecturer/records', { params, signal });
      setRecordsData(res.data);
    } catch (err: any) {
      if (isRequestCancelled(err)) return;
      setRecordsError(err.response?.data?.detail || 'Failed to load attendance records');
    } finally {
      setLoadingRecords(false);
    }
  }, [selectedSubjectId, dateFrom, dateTo, statusFilter, searchQuery, page, limit, sortBy, sortOrder]);

  useEffect(() => {
    const controller = new AbortController();
    fetchRecords(controller.signal);
    return () => {
      controller.abort();
    };
  }, [fetchRecords]);

  // Fetch subject-level report
  const fetchSubjectReport = useCallback(async (signal?: AbortSignal) => {
    if (!selectedSubjectId) {
      setSubjectReportData(null);
      return;
    }
    setLoadingSubjectReport(true);
    setSubjectReportError(null);
    try {
      const params: Record<string, any> = {};
      if (dateFrom) params.date_from = dateFrom;
      if (dateTo) params.date_to = dateTo;

      const res = await api.get<LecturerSubjectReportResponse>(
        `/api/lecturer/reports/subject/${selectedSubjectId}`,
        { params, signal }
      );
      setSubjectReportData(res.data);
    } catch (err: any) {
      if (isRequestCancelled(err)) return;
      setSubjectReportError(err.response?.data?.detail || 'Failed to load subject report');
    } finally {
      setLoadingSubjectReport(false);
    }
  }, [selectedSubjectId, dateFrom, dateTo]);

  useEffect(() => {
    if (activeTab === 'subject_report' && selectedSubjectId) {
      const controller = new AbortController();
      fetchSubjectReport(controller.signal);
      return () => {
        controller.abort();
      };
    }
  }, [activeTab, selectedSubjectId, fetchSubjectReport]);

  // Open student inspection modal
  const handleOpenStudentReport = async (studentId: string) => {
    setInspectStudentId(studentId);
    setLoadingStudentReport(true);
    setStudentReportError(null);
    setStudentReportData(null);
    try {
      const params: Record<string, any> = {};
      if (selectedSubjectId) params.subject_id = selectedSubjectId;
      const res = await api.get<LecturerStudentReportResponse>(
        `/api/lecturer/reports/student/${studentId}`,
        { params }
      );
      setStudentReportData(res.data);
    } catch (err: any) {
      if (isRequestCancelled(err)) return;
      setStudentReportError(err.response?.data?.detail || 'Failed to load student attendance history');
    } finally {
      setLoadingStudentReport(false);
    }
  };

  const handleCloseStudentReport = () => {
    setInspectStudentId(null);
    setStudentReportData(null);
    setStudentReportError(null);
  };

  // Reset all filters
  const handleResetFilters = () => {
    setSelectedSubjectId('');
    setDateFrom('');
    setDateTo('');
    setStatusFilter('all');
    setSearchQuery('');
    setPage(1);
    setSortBy('date');
    setSortOrder('desc');
  };

  // Sorting helper
  const handleSort = (field: string) => {
    if (sortBy === field) {
      setSortOrder((prev) => (prev === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortBy(field);
      setSortOrder('asc');
    }
    setPage(1);
  };

  // Export CSV handler
  const handleExportCSV = async (exportType: 'records' | 'subject' | 'student', studentIdToExport?: string) => {
    setIsExporting(true);
    const toastId = toast.loading('Generating academic CSV export...');
    try {
      const params: Record<string, any> = { export_type: exportType };
      if (selectedSubjectId) params.subject_id = selectedSubjectId;
      if (dateFrom) params.date_from = dateFrom;
      if (dateTo) params.date_to = dateTo;
      if (statusFilter !== 'all') params.status = statusFilter;
      if (searchQuery.trim()) params.search = searchQuery.trim();
      if (studentIdToExport) params.student_id = studentIdToExport;

      const response = await api.get('/api/lecturer/reports/export', {
        params,
        responseType: 'blob',
      });

      // Extract filename from header if present
      let filename = `attendx_${exportType}_export_${new Date().toISOString().split('T')[0]}.csv`;
      const disposition = response.headers['content-disposition'];
      if (disposition && disposition.indexOf('filename=') !== -1) {
        const matches = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/.exec(disposition);
        if (matches != null && matches[1]) {
          filename = matches[1].replace(/['"]/g, '');
        }
      }

      // Trigger download
      const blob = new Blob([response.data], { type: 'text/csv;charset=utf-8;' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.parentNode?.removeChild(link);
      window.URL.revokeObjectURL(url);

      toast.success('Report exported successfully', { id: toastId });
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to export report CSV', { id: toastId });
    } finally {
      setIsExporting(false);
    }
  };

  // Format date helper
  const formatDate = (dateStr: string) => {
    try {
      const d = new Date(dateStr + 'T00:00:00');
      return d.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
      });
    } catch {
      return dateStr;
    }
  };

  const summary = recordsData?.summary;

  return (
    <div className="space-y-6">
      {/* 1. Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-2 border-b border-surface-200">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-50 text-indigo-700 border border-indigo-200">
              Module L4
            </span>
            <span className="text-xs font-medium text-surface-400">Faculty Records & Reports</span>
          </div>
          <h1 className="text-2xl font-bold text-surface-900 tracking-tight">
            Attendance Records & Reports
          </h1>
          <p className="text-sm text-surface-500 mt-0.5">
            Query class session logs, analyze student attendance rates, and export official registers.
          </p>
        </div>

        {/* Global actions */}
        <div className="flex items-center gap-2.5 flex-wrap">
          <button
            onClick={() => {
              if (activeTab === 'records') fetchRecords();
              else fetchSubjectReport();
            }}
            disabled={loadingRecords || loadingSubjectReport}
            className="btn btn-secondary btn-sm"
            title="Refresh current data view"
          >
            <RotateCw
              className={`w-4 h-4 text-surface-600 ${
                loadingRecords || loadingSubjectReport ? 'animate-spin' : ''
              }`}
            />
            <span className="hidden sm:inline">Refresh</span>
          </button>

          {activeTab === 'records' ? (
            <button
              onClick={() => handleExportCSV('records')}
              disabled={isExporting || (recordsData?.total || 0) === 0}
              className="btn btn-primary btn-sm flex items-center gap-1.5 shadow-sm"
              title="Export filtered records to academic CSV"
            >
              <Download className="w-4 h-4" />
              <span>Export Records CSV</span>
            </button>
          ) : (
            <button
              onClick={() => handleExportCSV('subject')}
              disabled={isExporting || !selectedSubjectId}
              className="btn btn-primary btn-sm flex items-center gap-1.5 shadow-sm"
              title="Export subject roster summary to academic CSV"
            >
              <FileSpreadsheet className="w-4 h-4" />
              <span>Export Roster CSV</span>
            </button>
          )}
        </div>
      </div>

      {/* 2. Filter Bar */}
      <div className="card p-4 sm:p-5 shadow-xs border-surface-200 bg-white">
        <div className="flex items-center justify-between gap-2 mb-3 pb-2.5 border-b border-surface-100">
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-surface-500">
            <Filter className="w-3.5 h-3.5 text-primary-600" />
            <span>Search & Filter Criteria</span>
          </div>
          <button
            onClick={handleResetFilters}
            className="text-xs font-semibold text-primary-600 hover:text-primary-800 transition-colors focus:outline-none"
          >
            Reset Filters
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3.5">
          {/* Subject Filter */}
          <div className="space-y-1">
            <label className="label text-xs font-semibold text-surface-700">Subject</label>
            <div className="relative">
              <select
                value={selectedSubjectId}
                onChange={(e) => {
                  setSelectedSubjectId(e.target.value);
                  setPage(1);
                }}
                disabled={loadingSubjects || subjects.length === 0}
                className="input text-xs py-2 pr-8 appearance-none bg-surface-50/50 hover:bg-white transition-colors"
              >
                <option value="">All Assigned Subjects ({subjects.length})</option>
                {subjects.map((sub) => (
                  <option key={sub.id} value={sub.id}>
                    {sub.code} — {sub.name}
                  </option>
                ))}
              </select>
              <BookOpen className="w-4 h-4 text-surface-400 absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
            </div>
            {subjects.length === 0 && !loadingSubjects && (
              <p className="text-[0.7rem] text-surface-400">No subjects assigned.</p>
            )}
          </div>

          {/* Date From */}
          <div className="space-y-1">
            <label className="label text-xs font-semibold text-surface-700">Date From</label>
            <div className="relative">
              <input
                type="date"
                value={dateFrom}
                max={dateTo || undefined}
                onChange={(e) => {
                  setDateFrom(e.target.value);
                  setPage(1);
                }}
                className="input text-xs py-2 pr-8 bg-surface-50/50 hover:bg-white transition-colors"
              />
              <Calendar className="w-4 h-4 text-surface-400 absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
            </div>
          </div>

          {/* Date To */}
          <div className="space-y-1">
            <label className="label text-xs font-semibold text-surface-700">Date To</label>
            <div className="relative">
              <input
                type="date"
                value={dateTo}
                min={dateFrom || undefined}
                onChange={(e) => {
                  setDateTo(e.target.value);
                  setPage(1);
                }}
                className="input text-xs py-2 pr-8 bg-surface-50/50 hover:bg-white transition-colors"
              />
              <Calendar className="w-4 h-4 text-surface-400 absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
            </div>
          </div>

          {/* Attendance Status */}
          <div className="space-y-1">
            <label className="label text-xs font-semibold text-surface-700">Status</label>
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value as 'all' | 'present' | 'absent');
                setPage(1);
              }}
              className="input text-xs py-2 bg-surface-50/50 hover:bg-white transition-colors"
            >
              <option value="all">All Statuses</option>
              <option value="present">Present Only</option>
              <option value="absent">Absent Only</option>
            </select>
          </div>

          {/* Student Search */}
          <div className="space-y-1">
            <label className="label text-xs font-semibold text-surface-700">Student Search</label>
            <div className="relative">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => {
                  setSearchQuery(e.target.value);
                  setPage(1);
                }}
                placeholder="Name or roll no..."
                className="input text-xs py-2 pl-8 pr-7 bg-surface-50/50 hover:bg-white transition-colors"
              />
              <Search className="w-3.5 h-3.5 text-surface-400 absolute left-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery('')}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-surface-400 hover:text-surface-600"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* 3. Summary Statistics Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3.5">
        {/* Total Students */}
        <div className="card p-4 flex items-center gap-3.5 bg-white shadow-xs">
          <div className="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center flex-shrink-0">
            <Users className="w-5 h-5" />
          </div>
          <div className="min-w-0">
            <p className="text-xs font-medium text-surface-500 truncate">Total Students</p>
            <p className="text-xl font-bold text-surface-900">
              {summary ? summary.total_students : '—'}
            </p>
          </div>
        </div>

        {/* Total Attendance Records */}
        <div className="card p-4 flex items-center gap-3.5 bg-white shadow-xs">
          <div className="w-10 h-10 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center flex-shrink-0">
            <ClipboardCheck className="w-5 h-5" />
          </div>
          <div className="min-w-0">
            <p className="text-xs font-medium text-surface-500 truncate">Total Records</p>
            <p className="text-xl font-bold text-surface-900">
              {summary ? summary.total_records : '—'}
            </p>
          </div>
        </div>

        {/* Present Count */}
        <div className="card p-4 flex items-center gap-3.5 bg-white shadow-xs">
          <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center flex-shrink-0">
            <CheckCircle2 className="w-5 h-5" />
          </div>
          <div className="min-w-0">
            <p className="text-xs font-medium text-surface-500 truncate">Present</p>
            <p className="text-xl font-bold text-emerald-700">
              {summary ? summary.present_count : '—'}
            </p>
          </div>
        </div>

        {/* Absent Count */}
        <div className="card p-4 flex items-center gap-3.5 bg-white shadow-xs">
          <div className="w-10 h-10 rounded-xl bg-rose-50 text-rose-600 flex items-center justify-center flex-shrink-0">
            <XCircle className="w-5 h-5" />
          </div>
          <div className="min-w-0">
            <p className="text-xs font-medium text-surface-500 truncate">Absent</p>
            <p className="text-xl font-bold text-rose-700">
              {summary ? summary.absent_count : '—'}
            </p>
          </div>
        </div>

        {/* Overall Percentage */}
        <div className="card p-4 flex items-center gap-3.5 bg-white shadow-xs col-span-2 sm:col-span-1">
          <div
            className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 ${
              (summary?.attendance_percentage || 0) >= 75
                ? 'bg-emerald-50 text-emerald-600'
                : 'bg-amber-50 text-amber-600'
            }`}
          >
            <Percent className="w-5 h-5" />
          </div>
          <div className="min-w-0">
            <p className="text-xs font-medium text-surface-500 truncate">Attendance %</p>
            <p
              className={`text-xl font-bold ${
                (summary?.attendance_percentage || 0) >= 75
                  ? 'text-emerald-700'
                  : 'text-amber-700'
              }`}
            >
              {summary ? `${summary.attendance_percentage.toFixed(1)}%` : '—'}
            </p>
          </div>
        </div>
      </div>

      {/* 4. Tab Navigation */}
      <div className="flex border-b border-surface-200">
        <button
          onClick={() => setActiveTab('records')}
          className={`flex items-center gap-2 py-3 px-5 text-sm font-semibold border-b-2 transition-colors ${
            activeTab === 'records'
              ? 'border-primary-600 text-primary-700'
              : 'border-transparent text-surface-500 hover:text-surface-800'
          }`}
        >
          <ClipboardCheck className="w-4 h-4" />
          <span>Attendance Records Table</span>
          {recordsData && (
            <span className="ml-1 px-2 py-0.5 rounded-full text-xs bg-surface-100 text-surface-600">
              {recordsData.total}
            </span>
          )}
        </button>

        <button
          onClick={() => {
            setActiveTab('subject_report');
            if (!selectedSubjectId && subjects.length > 0) {
              setSelectedSubjectId(subjects[0].id);
            }
          }}
          className={`flex items-center gap-2 py-3 px-5 text-sm font-semibold border-b-2 transition-colors ${
            activeTab === 'subject_report'
              ? 'border-primary-600 text-primary-700'
              : 'border-transparent text-surface-500 hover:text-surface-800'
          }`}
        >
          <BookOpen className="w-4 h-4" />
          <span>Subject Report & Roster</span>
        </button>
      </div>

      {/* 5. TAB 1: Attendance Records View */}
      {activeTab === 'records' && (
        <div className="card p-0 overflow-hidden shadow-xs border-surface-200">
          {loadingRecords ? (
            <div className="py-20">
              <LoadingSpinner size="lg" text="Loading filtered attendance records..." />
            </div>
          ) : recordsError ? (
            <div className="p-8">
              <ErrorState message={recordsError} onRetry={fetchRecords} />
            </div>
          ) : recordsData && recordsData.records.length === 0 ? (
            <div className="p-12">
              <EmptyState
                title="No attendance records found"
                description={
                  subjects.length === 0
                    ? 'No subjects are currently assigned to your faculty profile.'
                    : 'No attendance records match the selected filters. Try broadening your date range or adjusting filters.'
                }
                action={
                  <button onClick={handleResetFilters} className="btn btn-secondary btn-sm">
                    Reset All Filters
                  </button>
                }
              />
            </div>
          ) : recordsData ? (
            <>
              {/* Responsive table */}
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse min-w-[700px]">
                  <thead>
                    <tr className="bg-surface-50 text-[0.72rem] font-bold text-surface-500 uppercase tracking-wider border-b border-surface-200">
                      <th
                        className="py-3 px-4 cursor-pointer hover:bg-surface-100/80 transition-colors select-none"
                        onClick={() => handleSort('date')}
                      >
                        <div className="flex items-center gap-1.5">
                          <span>Date</span>
                          {sortBy === 'date' ? (
                            sortOrder === 'asc' ? <ArrowUp className="w-3.5 h-3.5" /> : <ArrowDown className="w-3.5 h-3.5" />
                          ) : (
                            <ArrowUpDown className="w-3 h-3 text-surface-400" />
                          )}
                        </div>
                      </th>
                      <th
                        className="py-3 px-4 cursor-pointer hover:bg-surface-100/80 transition-colors select-none"
                        onClick={() => handleSort('subject_code')}
                      >
                        <div className="flex items-center gap-1.5">
                          <span>Subject</span>
                          {sortBy === 'subject_code' && (
                            sortOrder === 'asc' ? <ArrowUp className="w-3.5 h-3.5" /> : <ArrowDown className="w-3.5 h-3.5" />
                          )}
                        </div>
                      </th>
                      <th
                        className="py-3 px-4 cursor-pointer hover:bg-surface-100/80 transition-colors select-none"
                        onClick={() => handleSort('student_name')}
                      >
                        <div className="flex items-center gap-1.5">
                          <span>Student</span>
                          {sortBy === 'student_name' && (
                            sortOrder === 'asc' ? <ArrowUp className="w-3.5 h-3.5" /> : <ArrowDown className="w-3.5 h-3.5" />
                          )}
                        </div>
                      </th>
                      <th
                        className="py-3 px-4 cursor-pointer hover:bg-surface-100/80 transition-colors select-none"
                        onClick={() => handleSort('student_sid')}
                      >
                        <div className="flex items-center gap-1.5">
                          <span>Roll Number</span>
                          {sortBy === 'student_sid' && (
                            sortOrder === 'asc' ? <ArrowUp className="w-3.5 h-3.5" /> : <ArrowDown className="w-3.5 h-3.5" />
                          )}
                        </div>
                      </th>
                      <th
                        className="py-3 px-4 cursor-pointer hover:bg-surface-100/80 transition-colors select-none"
                        onClick={() => handleSort('status')}
                      >
                        <div className="flex items-center gap-1.5">
                          <span>Status</span>
                          {sortBy === 'status' && (
                            sortOrder === 'asc' ? <ArrowUp className="w-3.5 h-3.5" /> : <ArrowDown className="w-3.5 h-3.5" />
                          )}
                        </div>
                      </th>
                      <th className="py-3 px-4 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-surface-100 text-sm">
                    {recordsData.records.map((r) => (
                      <tr key={r.id} className="hover:bg-surface-50/70 transition-colors">
                        <td className="py-3 px-4 font-medium text-surface-800 whitespace-nowrap">
                          {formatDate(r.attendance_date)}
                        </td>
                        <td className="py-3 px-4 whitespace-nowrap">
                          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-surface-100 text-surface-700 mr-1.5">
                            {r.subject_code}
                          </span>
                          <span className="text-xs text-surface-600 truncate max-w-[180px] inline-block align-bottom">
                            {r.subject_name}
                          </span>
                        </td>
                        <td className="py-3 px-4 font-semibold text-surface-900 whitespace-nowrap">
                          {r.student_name}
                        </td>
                        <td className="py-3 px-4 text-xs font-mono text-surface-600 whitespace-nowrap">
                          {r.student_sid || '—'}
                        </td>
                        <td className="py-3 px-4 whitespace-nowrap">
                          {r.status === 'present' ? (
                            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                              <CheckCircle2 className="w-3 h-3" />
                              Present
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200">
                              <XCircle className="w-3 h-3" />
                              Absent
                            </span>
                          )}
                        </td>
                        <td className="py-3 px-4 text-right whitespace-nowrap">
                          <button
                            onClick={() => handleOpenStudentReport(r.student_id)}
                            className="inline-flex items-center gap-1 text-xs font-semibold text-primary-600 hover:text-primary-800 bg-primary-50/60 hover:bg-primary-100/70 px-2.5 py-1 rounded-md transition-colors"
                            title="Inspect individual student attendance report"
                          >
                            <Eye className="w-3.5 h-3.5" />
                            <span>Report</span>
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Pagination bar */}
              <div className="px-4 py-3 border-t border-surface-200 bg-surface-50/50 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-surface-600">
                <div className="flex items-center gap-2">
                  <span>
                    Showing{' '}
                    <span className="font-semibold text-surface-900">
                      {(page - 1) * limit + 1}
                    </span>{' '}
                    to{' '}
                    <span className="font-semibold text-surface-900">
                      {Math.min(page * limit, recordsData.total)}
                    </span>{' '}
                    of{' '}
                    <span className="font-semibold text-surface-900">
                      {recordsData.total}
                    </span>{' '}
                    records
                  </span>

                  <span className="text-surface-300">•</span>

                  <div className="flex items-center gap-1">
                    <span>Show</span>
                    <select
                      value={limit}
                      onChange={(e) => {
                        setLimit(Number(e.target.value));
                        setPage(1);
                      }}
                      className="border border-surface-200 rounded px-1.5 py-0.5 bg-white text-xs"
                    >
                      <option value={10}>10</option>
                      <option value={20}>20</option>
                      <option value={50}>50</option>
                    </select>
                  </div>
                </div>

                <div className="flex items-center gap-1">
                  <button
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page <= 1}
                    className="p-1.5 rounded-md border border-surface-200 bg-white hover:bg-surface-100 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                    aria-label="Previous page"
                  >
                    <ChevronLeft className="w-4 h-4" />
                  </button>
                  <span className="px-2 font-medium">
                    Page {page} of {recordsData.total_pages}
                  </span>
                  <button
                    onClick={() => setPage((p) => Math.min(recordsData.total_pages, p + 1))}
                    disabled={page >= recordsData.total_pages}
                    className="p-1.5 rounded-md border border-surface-200 bg-white hover:bg-surface-100 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                    aria-label="Next page"
                  >
                    <ChevronRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </>
          ) : null}
        </div>
      )}

      {/* 6. TAB 2: Subject Report View */}
      {activeTab === 'subject_report' && (
        <div className="space-y-6">
          {!selectedSubjectId ? (
            <div className="card p-12 text-center">
              <EmptyState
                title="Select a subject to inspect report"
                description="Please select one of your assigned subjects from the filter bar above to view its comprehensive attendance statistics and roster breakdown."
              />
            </div>
          ) : loadingSubjectReport ? (
            <div className="card py-20">
              <LoadingSpinner size="lg" text="Generating subject attendance report..." />
            </div>
          ) : subjectReportError ? (
            <div className="card p-8">
              <ErrorState message={subjectReportError} onRetry={fetchSubjectReport} />
            </div>
          ) : subjectReportData ? (
            <>
              {/* Subject Hero KPI Card */}
              <div className="card p-5 bg-gradient-to-r from-surface-900 to-indigo-950 text-white shadow-md">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="px-2 py-0.5 rounded text-xs font-bold bg-white/20 text-white">
                        {subjectReportData.subject_code}
                      </span>
                      <span className="text-xs text-white/70">
                        {subjectReportData.department} • Semester {subjectReportData.semester}
                      </span>
                    </div>
                    <h2 className="text-xl font-bold tracking-tight text-white">
                      {subjectReportData.subject_name}
                    </h2>
                    <p className="text-xs text-white/70 mt-1">
                      {dateFrom || dateTo
                        ? `Filtered from ${dateFrom || 'start'} to ${dateTo || 'present'}`
                        : 'Cumulative all-time subject records'}
                    </p>
                  </div>

                  <div className="flex items-center gap-6">
                    <div className="text-center">
                      <p className="text-xs text-white/60">Enrolled</p>
                      <p className="text-2xl font-bold text-white">
                        {subjectReportData.total_students}
                      </p>
                    </div>
                    <div className="text-center">
                      <p className="text-xs text-white/60">Sessions</p>
                      <p className="text-2xl font-bold text-white">
                        {subjectReportData.total_sessions}
                      </p>
                    </div>
                    <div className="text-center">
                      <p className="text-xs text-white/60">Total Logs</p>
                      <p className="text-2xl font-bold text-white">
                        {subjectReportData.total_records}
                      </p>
                    </div>
                    <div className="text-center pl-3 border-l border-white/20">
                      <p className="text-xs text-white/60">Attendance</p>
                      <p
                        className={`text-2xl font-extrabold ${
                          subjectReportData.percentage >= 75
                            ? 'text-emerald-400'
                            : 'text-amber-400'
                        }`}
                      >
                        {subjectReportData.percentage.toFixed(1)}%
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Student Roster Breakdown Table */}
              <div className="card p-0 overflow-hidden shadow-xs border-surface-200">
                <div className="p-4 bg-surface-50 border-b border-surface-200 flex items-center justify-between">
                  <div>
                    <h3 className="text-sm font-bold text-surface-900">Enrolled Student Roster</h3>
                    <p className="text-xs text-surface-500">
                      Student-by-student attendance breakdown for this subject
                    </p>
                  </div>
                  <span className="text-xs font-semibold text-surface-600 bg-white px-2.5 py-1 rounded border border-surface-200">
                    {subjectReportData.students.length} Enrolled Students
                  </span>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-left border-collapse min-w-[650px]">
                    <thead>
                      <tr className="bg-surface-50/70 text-[0.72rem] font-bold text-surface-500 uppercase tracking-wider border-b border-surface-200">
                        <th className="py-2.5 px-4">Roll Number</th>
                        <th className="py-2.5 px-4">Student Name</th>
                        <th className="py-2.5 px-4 text-center">Classes</th>
                        <th className="py-2.5 px-4 text-center">Present</th>
                        <th className="py-2.5 px-4 text-center">Absent</th>
                        <th className="py-2.5 px-4">Attendance %</th>
                        <th className="py-2.5 px-4 text-right">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-surface-100 text-sm">
                      {subjectReportData.students.map((stu) => {
                        const isLow = stu.total_classes > 0 && stu.percentage < 75;
                        return (
                          <tr key={stu.student_id} className="hover:bg-surface-50/70 transition-colors">
                            <td className="py-3 px-4 font-mono text-xs text-surface-600 whitespace-nowrap">
                              {stu.student_sid || '—'}
                            </td>
                            <td className="py-3 px-4 whitespace-nowrap">
                              <p className="font-semibold text-surface-900">{stu.student_name}</p>
                              <p className="text-[0.7rem] text-surface-400">{stu.email}</p>
                            </td>
                            <td className="py-3 px-4 text-center font-medium text-surface-700">
                              {stu.total_classes}
                            </td>
                            <td className="py-3 px-4 text-center font-medium text-emerald-700">
                              {stu.present}
                            </td>
                            <td className="py-3 px-4 text-center font-medium text-rose-700">
                              {stu.absent}
                            </td>
                            <td className="py-3 px-4 whitespace-nowrap">
                              <div className="flex items-center gap-2">
                                <span
                                  className={`text-xs font-bold px-2 py-0.5 rounded-full ${
                                    isLow
                                      ? 'bg-rose-50 text-rose-700 border border-rose-200'
                                      : 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                                  }`}
                                >
                                  {stu.percentage.toFixed(1)}%
                                </span>
                                {isLow && (
                                  <span
                                    title="Attendance is below standard 75% threshold"
                                    className="text-rose-600"
                                  >
                                    <AlertTriangle className="w-3.5 h-3.5" />
                                  </span>
                                )}
                              </div>
                            </td>
                            <td className="py-3 px-4 text-right whitespace-nowrap">
                              <button
                                onClick={() => handleOpenStudentReport(stu.student_id)}
                                className="inline-flex items-center gap-1 text-xs font-semibold text-primary-600 hover:text-primary-800 bg-primary-50/60 hover:bg-primary-100/70 px-2.5 py-1 rounded-md transition-colors"
                              >
                                <Eye className="w-3.5 h-3.5" />
                                <span>Inspect</span>
                              </button>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Daily Session Breakdown Table */}
              <div className="card p-0 overflow-hidden shadow-xs border-surface-200">
                <div className="p-4 bg-surface-50 border-b border-surface-200">
                  <h3 className="text-sm font-bold text-surface-900">Session-by-Session History</h3>
                  <p className="text-xs text-surface-500">
                    Daily class attendance tallies for this subject
                  </p>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-left border-collapse min-w-[500px]">
                    <thead>
                      <tr className="bg-surface-50/70 text-[0.72rem] font-bold text-surface-500 uppercase tracking-wider border-b border-surface-200">
                        <th className="py-2.5 px-4">Date</th>
                        <th className="py-2.5 px-4 text-center">Students Marked</th>
                        <th className="py-2.5 px-4 text-center">Present</th>
                        <th className="py-2.5 px-4 text-center">Absent</th>
                        <th className="py-2.5 px-4 text-right">Daily Attendance %</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-surface-100 text-sm">
                      {subjectReportData.sessions.map((sess) => (
                        <tr key={sess.attendance_date} className="hover:bg-surface-50/70 transition-colors">
                          <td className="py-2.5 px-4 font-medium text-surface-800 whitespace-nowrap">
                            {formatDate(sess.attendance_date)}
                          </td>
                          <td className="py-2.5 px-4 text-center text-surface-700">
                            {sess.total_students}
                          </td>
                          <td className="py-2.5 px-4 text-center font-medium text-emerald-700">
                            {sess.present}
                          </td>
                          <td className="py-2.5 px-4 text-center font-medium text-rose-700">
                            {sess.absent}
                          </td>
                          <td className="py-2.5 px-4 text-right whitespace-nowrap">
                            <span
                              className={`text-xs font-bold px-2 py-0.5 rounded-full ${
                                sess.percentage >= 75
                                  ? 'bg-emerald-50 text-emerald-700'
                                  : 'bg-amber-50 text-amber-700'
                              }`}
                            >
                              {sess.percentage.toFixed(1)}%
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          ) : null}
        </div>
      )}

      {/* 7. Student Inspection Modal */}
      {inspectStudentId && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs animate-fade-in"
          role="dialog"
          aria-modal="true"
          aria-labelledby="student-modal-title"
        >
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-2xl max-h-[90vh] flex flex-col overflow-hidden border border-surface-200">
            {/* Modal Header */}
            <div className="px-6 py-4 border-b border-surface-100 flex items-center justify-between bg-surface-50/50">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-lg bg-indigo-100 text-indigo-700 flex items-center justify-center font-bold text-xs">
                  {studentReportData?.student_name?.charAt(0).toUpperCase() || 'S'}
                </div>
                <div>
                  <h3 id="student-modal-title" className="text-base font-bold text-surface-900 leading-tight">
                    {studentReportData ? studentReportData.student_name : 'Loading Student...'}
                  </h3>
                  <p className="text-xs text-surface-500">
                    {studentReportData?.student_sid
                      ? `Roll No: ${studentReportData.student_sid} • `
                      : ''}
                    {studentReportData?.department || 'Student Roster'}
                  </p>
                </div>
              </div>
              <button
                onClick={handleCloseStudentReport}
                className="text-surface-400 hover:text-surface-700 p-1.5 rounded-lg hover:bg-surface-100 transition-colors"
                aria-label="Close modal"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 overflow-y-auto space-y-5 flex-1">
              {loadingStudentReport ? (
                <div className="py-12">
                  <LoadingSpinner size="md" text="Loading student attendance history..." />
                </div>
              ) : studentReportError ? (
                <ErrorState message={studentReportError} />
              ) : studentReportData ? (
                <>
                  {/* Summary Metric Strip */}
                  <div className="grid grid-cols-4 gap-3 bg-surface-50 p-3.5 rounded-xl border border-surface-200/80 text-center">
                    <div>
                      <p className="text-[0.68rem] uppercase font-bold text-surface-500">Total Classes</p>
                      <p className="text-lg font-bold text-surface-900">{studentReportData.total_classes}</p>
                    </div>
                    <div>
                      <p className="text-[0.68rem] uppercase font-bold text-emerald-600">Present</p>
                      <p className="text-lg font-bold text-emerald-700">{studentReportData.present}</p>
                    </div>
                    <div>
                      <p className="text-[0.68rem] uppercase font-bold text-rose-600">Absent</p>
                      <p className="text-lg font-bold text-rose-700">{studentReportData.absent}</p>
                    </div>
                    <div>
                      <p className="text-[0.68rem] uppercase font-bold text-surface-500">Attendance %</p>
                      <p
                        className={`text-lg font-extrabold ${
                          studentReportData.percentage >= 75 ? 'text-emerald-700' : 'text-rose-700'
                        }`}
                      >
                        {studentReportData.percentage.toFixed(1)}%
                      </p>
                    </div>
                  </div>

                  {studentReportData.percentage < 75 && studentReportData.total_classes > 0 && (
                    <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg flex items-center gap-2.5 text-xs text-rose-800">
                      <AlertTriangle className="w-4 h-4 text-rose-600 flex-shrink-0" />
                      <span>
                        Low attendance warning: Student is currently below the academic threshold of 75%.
                      </span>
                    </div>
                  )}

                  {/* Subject Breakdown */}
                  {studentReportData.subject_breakdown.length > 0 && (
                    <div className="space-y-2">
                      <h4 className="text-xs font-bold uppercase tracking-wider text-surface-500">
                        Subject Breakdown
                      </h4>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                        {studentReportData.subject_breakdown.map((sb) => (
                          <div
                            key={sb.subject_id}
                            className="p-3 bg-white border border-surface-200 rounded-lg text-xs space-y-1"
                          >
                            <div className="flex items-center justify-between">
                              <span className="font-semibold text-surface-800 truncate">
                                {sb.subject_code} — {sb.subject_name}
                              </span>
                              <span
                                className={`font-bold px-1.5 py-0.5 rounded text-[0.65rem] ${
                                  sb.percentage >= 75
                                    ? 'bg-emerald-50 text-emerald-700'
                                    : 'bg-rose-50 text-rose-700'
                                }`}
                              >
                                {sb.percentage.toFixed(1)}%
                              </span>
                            </div>
                            <p className="text-surface-500 text-[0.7rem]">
                              {sb.present} of {sb.total_classes} classes attended ({sb.absent} absent)
                            </p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Chronological Session History */}
                  <div className="space-y-2">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-surface-500">
                      Chronological Session Logs ({studentReportData.history.length})
                    </h4>
                    <div className="border border-surface-200 rounded-lg overflow-hidden max-h-60 overflow-y-auto">
                      <table className="w-full text-left text-xs">
                        <thead className="bg-surface-50 text-[0.7rem] uppercase font-bold text-surface-500 sticky top-0 border-b border-surface-200">
                          <tr>
                            <th className="py-2 px-3">Date</th>
                            <th className="py-2 px-3">Subject</th>
                            <th className="py-2 px-3 text-right">Status</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-surface-100">
                          {studentReportData.history.map((h) => (
                            <tr key={h.id} className="hover:bg-surface-50/60">
                              <td className="py-2 px-3 font-medium text-surface-800">
                                {formatDate(h.attendance_date)}
                              </td>
                              <td className="py-2 px-3 text-surface-600">
                                {h.subject_code}
                              </td>
                              <td className="py-2 px-3 text-right">
                                {h.status === 'present' ? (
                                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[0.65rem] font-semibold bg-emerald-50 text-emerald-700">
                                    <CheckCircle2 className="w-2.5 h-2.5" />
                                    Present
                                  </span>
                                ) : (
                                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[0.65rem] font-semibold bg-rose-50 text-rose-700">
                                    <XCircle className="w-2.5 h-2.5" />
                                    Absent
                                  </span>
                                )}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </>
              ) : null}
            </div>

            {/* Modal Footer */}
            <div className="px-6 py-3.5 border-t border-surface-100 bg-surface-50/50 flex items-center justify-between">
              <button
                onClick={() => studentReportData && handleExportCSV('student', studentReportData.student_id)}
                disabled={!studentReportData || isExporting}
                className="btn btn-secondary btn-sm flex items-center gap-1.5"
              >
                <Download className="w-3.5 h-3.5" />
                <span>Export Student CSV</span>
              </button>

              <button
                onClick={handleCloseStudentReport}
                className="btn btn-secondary btn-sm"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
