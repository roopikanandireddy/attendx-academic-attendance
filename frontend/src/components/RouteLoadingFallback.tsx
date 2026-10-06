import LoadingSpinner from './LoadingSpinner';
import { DashboardSkeleton, TableSkeleton } from './Skeleton';

interface RouteLoadingFallbackProps {
  variant?: 'dashboard' | 'table' | 'spinner' | 'page';
  text?: string;
}

export default function RouteLoadingFallback({
  variant = 'spinner',
  text = 'Loading...',
}: RouteLoadingFallbackProps) {
  if (variant === 'dashboard') {
    return (
      <div className="w-full p-4 sm:p-6 fade-in animate-pulse">
        <DashboardSkeleton />
      </div>
    );
  }

  if (variant === 'table') {
    return (
      <div className="w-full p-4 sm:p-6 fade-in animate-pulse">
        <TableSkeleton rows={6} />
      </div>
    );
  }

  if (variant === 'page') {
    return (
      <div className="min-h-[70vh] flex items-center justify-center fade-in">
        <LoadingSpinner size="lg" text={text} />
      </div>
    );
  }

  return (
    <div className="min-h-[50vh] flex items-center justify-center fade-in">
      <LoadingSpinner size="md" text={text} />
    </div>
  );
}
