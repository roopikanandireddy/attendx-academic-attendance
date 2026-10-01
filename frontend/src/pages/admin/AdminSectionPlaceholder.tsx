import { useNavigate } from 'react-router-dom';
import type { LucideIcon } from 'lucide-react';
import { ArrowLeft, ShieldCheck, Layers } from 'lucide-react';

interface AdminSectionPlaceholderProps {
  title: string;
  category: string;
  description: string;
  icon: LucideIcon;
  plannedFeatures: string[];
}

export default function AdminSectionPlaceholder({
  title,
  category,
  description,
  icon: Icon,
  plannedFeatures,
}: AdminSectionPlaceholderProps) {
  const navigate = useNavigate();

  return (
    <div className="space-y-6 fade-in max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-semibold text-primary-600 uppercase tracking-wider">
              {category}
            </span>
            <span className="text-surface-300">•</span>
            <span className="badge badge-info text-[0.68rem] px-2 py-0.5">
              Module A1 Shell
            </span>
          </div>
          <h2 className="text-2xl font-bold text-surface-900 tracking-tight">{title}</h2>
          <p className="text-sm text-surface-500 mt-0.5">{description}</p>
        </div>
        <button
          onClick={() => navigate('/admin/dashboard')}
          className="btn btn-secondary btn-sm self-start sm:self-auto flex items-center gap-1.5"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Dashboard
        </button>
      </div>

      {/* Main Container */}
      <div className="card border border-surface-200 shadow-sm p-6 sm:p-8 text-center sm:text-left">
        <div className="flex flex-col sm:flex-row items-center sm:items-start gap-5 mb-6">
          <div className="w-14 h-14 rounded-2xl bg-primary-50 text-primary-600 border border-primary-100 flex items-center justify-center flex-shrink-0 shadow-xs">
            <Icon className="w-7 h-7" aria-hidden="true" />
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-bold text-surface-900">
              {title} Management Foundation
            </h3>
            <p className="text-sm text-surface-500 mt-1 leading-relaxed">
              This route is protected and active under the AttendX Admin Foundation. Core management workflows,
              interactive data tables, and batch actions are scheduled for implementation in dedicated modules.
            </p>
          </div>
        </div>

        {/* Feature roadmap preview */}
        <div className="bg-surface-50 rounded-xl p-4 sm:p-5 border border-surface-200/60 mb-6">
          <div className="flex items-center gap-2 mb-3">
            <Layers className="w-4 h-4 text-primary-600" />
            <h4 className="text-xs font-bold uppercase tracking-wider text-surface-700">
              Scheduled Capabilities for this Section
            </h4>
          </div>
          <ul className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 text-xs text-surface-600">
            {plannedFeatures.map((feat, idx) => (
              <li key={idx} className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-primary-500 flex-shrink-0" />
                <span>{feat}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Security badge footer */}
        <div className="pt-4 border-t border-surface-100 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-surface-400">
          <div className="flex items-center gap-1.5">
            <ShieldCheck className="w-4 h-4 text-emerald-500" />
            <span>Role-Based Access Control verified: <strong>admin</strong> access only</span>
          </div>
          <span>AttendX Architecture Standard</span>
        </div>
      </div>
    </div>
  );
}
