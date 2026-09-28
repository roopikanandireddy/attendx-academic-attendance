import { AlertTriangle } from 'lucide-react';

interface ErrorStateProps {
  title?: string;
  message: string;
  onRetry?: () => void;
}

export default function ErrorState({ title = 'Something went wrong', message, onRetry }: ErrorStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4 text-center fade-in">
      <div className="w-16 h-16 rounded-2xl bg-red-50 flex items-center justify-center mb-4">
        <AlertTriangle className="w-8 h-8 text-danger" />
      </div>
      <h3 className="text-lg font-semibold text-surface-800 mb-1">{title}</h3>
      <p className="text-sm text-surface-500 max-w-sm mb-6">{message}</p>
      {onRetry && (
        <button onClick={onRetry} className="btn btn-primary btn-sm">
          Try Again
        </button>
      )}
    </div>
  );
}
