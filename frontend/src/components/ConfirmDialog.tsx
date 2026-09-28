import { AlertTriangle, X } from 'lucide-react';

interface ConfirmDialogProps {
  isOpen: boolean;
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  variant?: 'danger' | 'primary';
  loading?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

export default function ConfirmDialog({
  isOpen,
  title,
  message,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  variant = 'danger',
  loading = false,
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="fixed inset-0 bg-black/40 backdrop-blur-sm" onClick={onCancel} />
      <div className="relative bg-white rounded-xl shadow-2xl max-w-md w-full p-6 fade-in">
        <button onClick={onCancel} className="absolute top-4 right-4 text-surface-400 hover:text-surface-600">
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-start gap-4 mb-6">
          <div className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 ${
            variant === 'danger' ? 'bg-red-50' : 'bg-primary-50'
          }`}>
            <AlertTriangle className={`w-5 h-5 ${variant === 'danger' ? 'text-danger' : 'text-primary-600'}`} />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-surface-900 mb-1">{title}</h3>
            <p className="text-sm text-surface-500">{message}</p>
          </div>
        </div>

        <div className="flex justify-end gap-3">
          <button onClick={onCancel} className="btn btn-secondary" disabled={loading}>
            {cancelLabel}
          </button>
          <button
            onClick={onConfirm}
            className={`btn ${variant === 'danger' ? 'btn-danger' : 'btn-primary'}`}
            disabled={loading}
          >
            {loading && <span className="spinner" />}
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
