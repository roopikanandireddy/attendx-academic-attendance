import { useState, useEffect } from 'react';
import api, { isRequestCancelled } from '../services/api';
import type { Subject } from '../types';
import Modal from './Modal';
import LoadingSpinner from './LoadingSpinner';
import ErrorState from './ErrorState';
import toast from 'react-hot-toast';

interface EnrollSubjectsModalProps {
  isOpen: boolean;
  onClose: () => void;
  onEnrolled: () => void;
}

const PREFERRED_ORDER = ['IAI', 'SE', 'ISC', 'BEFA', 'ES', 'AE-3 LAB'];

export default function EnrollSubjectsModal({
  isOpen,
  onClose,
  onEnrolled,
}: EnrollSubjectsModalProps) {
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [enrolledIds, setEnrolledIds] = useState<Set<string>>(new Set());
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  // Fetch subjects from the database via FastAPI when modal opens
  useEffect(() => {
    if (!isOpen) return;

    const controller = new AbortController();
    setLoading(true);
    setError('');

    Promise.all([
      api.get<Subject[]>('/api/subjects', { signal: controller.signal }),
      api.get<string[]>('/api/subjects/my-enrollments', { signal: controller.signal }),
    ])
      .then(([subjectsRes, enrollmentsRes]) => {
        // Sort subjects in the catalog order
        const sorted = [...subjectsRes.data].sort((a, b) => {
          const idxA = PREFERRED_ORDER.indexOf(a.code);
          const idxB = PREFERRED_ORDER.indexOf(b.code);
          if (idxA !== -1 && idxB !== -1) return idxA - idxB;
          if (idxA !== -1) return -1;
          if (idxB !== -1) return 1;
          return a.code.localeCompare(b.code);
        });

        setSubjects(sorted);

        const currentEnrolled = new Set<string>(enrollmentsRes.data || []);
        setEnrolledIds(currentEnrolled);
        // Pre-select already enrolled subjects so student sees them checked
        setSelectedIds(new Set(currentEnrolled));
      })
      .catch((err: any) => {
        if (isRequestCancelled(err)) return;
        setError(err.response?.data?.detail || 'Failed to load subject catalog');
      })
      .finally(() => {
        setLoading(false);
      });

    return () => {
      controller.abort();
    };
  }, [isOpen]);

  const toggleSubject = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const handleEnroll = async () => {
    if (selectedIds.size === 0) {
      toast.error('Please select at least one subject to enroll');
      return;
    }

    setSubmitting(true);
    try {
      const res = await api.post('/api/subjects/enroll-batch', {
        subject_ids: Array.from(selectedIds),
      });

      const added = res.data.enrolled_count ?? 0;
      if (added > 0) {
        toast.success(`Successfully enrolled in ${added} subject${added > 1 ? 's' : ''}!`);
      } else {
        toast.success('Subject enrollments up to date!');
      }

      onEnrolled();
      onClose();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to enroll in subjects');
    } finally {
      setSubmitting(false);
    }
  };

  const selectedCount = selectedIds.size;

  return (
    <Modal isOpen={isOpen} title="Enroll in Subjects" onClose={onClose} maxWidth="max-w-xl">
      <div className="space-y-5">
        <div>
          <p className="text-sm text-surface-600">Select the subjects you want to enroll in.</p>
        </div>

        {loading ? (
          <div className="py-8">
            <LoadingSpinner text="Fetching subject catalog from database..." />
          </div>
        ) : error ? (
          <ErrorState message={error} onRetry={() => {}} />
        ) : (
          <div className="space-y-2.5 max-h-[50vh] overflow-y-auto pr-1">
            {subjects.map((sub) => {
              const isSelected = selectedIds.has(sub.id);
              const isEnrolled = enrolledIds.has(sub.id);

              return (
                <label
                  key={sub.id}
                  className={`flex items-start gap-3.5 p-3.5 rounded-xl border transition-all cursor-pointer ${
                    isSelected
                      ? 'border-primary-500 bg-primary-50/50 shadow-xs'
                      : 'border-surface-200 hover:border-surface-300 hover:bg-surface-50/60'
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={isSelected}
                    onChange={() => toggleSubject(sub.id)}
                    className="mt-0.5 h-4 w-4 rounded border-surface-300 text-primary-600 focus:ring-primary-500 cursor-pointer accent-primary-600"
                  />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-surface-900 text-sm tracking-tight">
                        {sub.code}
                      </span>
                      {isEnrolled && (
                        <span className="badge badge-success text-[10px] py-0.5 px-2 font-medium">
                          Enrolled
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-surface-600 mt-0.5 leading-snug">{sub.name}</p>
                  </div>
                </label>
              );
            })}
          </div>
        )}

        {/* Footer actions */}
        <div className="pt-3 border-t border-surface-100 flex items-center justify-between">
          <div className="text-sm font-medium text-surface-700">
            Selected: <span className="font-semibold text-primary-600">{selectedCount} subjects</span>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={onClose}
              disabled={submitting}
              className="btn btn-secondary text-sm px-4 py-2"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleEnroll}
              disabled={loading || submitting || selectedCount === 0}
              className="btn btn-primary text-sm px-4 py-2 flex items-center gap-1.5 shadow-sm"
            >
              {submitting ? 'Enrolling...' : 'Enroll Subjects'}
            </button>
          </div>
        </div>
      </div>
    </Modal>
  );
}
