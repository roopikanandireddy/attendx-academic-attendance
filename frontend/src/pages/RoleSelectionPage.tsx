import { Link } from 'react-router-dom';
import {
  GraduationCap,
  BookOpen,
  ShieldCheck,
  ArrowRight,
  CheckCircle2,
  Lock,
  Building2,
  Calendar,
} from 'lucide-react';

interface RoleCardData {
  id: string;
  ctaId: string;
  role: string;
  badge: string;
  title: string;
  description: string;
  cta: string;
  route: string;
  icon: typeof GraduationCap;
  accent: {
    badge: string;
    iconBg: string;
    iconColor: string;
    borderHover: string;
    button: string;
  };
  features: string[];
}

const ROLES: RoleCardData[] = [
  {
    id: 'role-card-student',
    ctaId: 'cta-student',
    role: 'STUDENT',
    badge: 'Student Portal',
    title: 'Student',
    description:
      'Access your attendance, enrolled subjects, history, notifications and profile.',
    cta: 'Continue as Student',
    route: '/login?role=student',
    icon: GraduationCap,
    accent: {
      badge: 'bg-blue-50 text-blue-700 border-blue-200/60',
      iconBg: 'bg-blue-50 border-blue-100',
      iconColor: 'text-blue-600',
      borderHover: 'hover:border-blue-300 hover:shadow-blue-500/5',
      button: 'bg-primary-600 hover:bg-primary-700 text-white shadow-xs',
    },
    features: [
      'Real-time subject-by-subject attendance progress',
      'Deficit recovery calculator with 75% threshold flags',
      'Curriculum course enrollment and schedule logs',
    ],
  },
  {
    id: 'role-card-lecturer',
    ctaId: 'cta-lecturer',
    role: 'LECTURER',
    badge: 'Faculty Portal',
    title: 'Lecturer',
    description:
      'Manage assigned subjects, record attendance and monitor student attendance.',
    cta: 'Continue as Lecturer',
    route: '/login?role=lecturer',
    icon: BookOpen,
    accent: {
      badge: 'bg-indigo-50 text-indigo-700 border-indigo-200/60',
      iconBg: 'bg-indigo-50 border-indigo-100',
      iconColor: 'text-indigo-600',
      borderHover: 'hover:border-indigo-300 hover:shadow-indigo-500/5',
      button: 'bg-indigo-600 hover:bg-indigo-700 text-white shadow-xs',
    },
    features: [
      'Assigned course catalog and enrolled student rosters',
      'One-click session attendance marking with bulk actions',
      'Student attendance audits and official CSV report export',
    ],
  },
  {
    id: 'role-card-admin',
    ctaId: 'cta-admin',
    role: 'ADMIN',
    badge: 'Administration Portal',
    title: 'Admin',
    description:
      'Manage students, lecturers, subjects and academic attendance operations.',
    cta: 'Continue as Admin',
    route: '/login?role=admin',
    icon: ShieldCheck,
    accent: {
      badge: 'bg-purple-50 text-purple-700 border-purple-200/60',
      iconBg: 'bg-purple-50 border-purple-100',
      iconColor: 'text-purple-600',
      borderHover: 'hover:border-purple-300 hover:shadow-purple-500/5',
      button: 'bg-surface-900 hover:bg-surface-800 text-white shadow-xs',
    },
    features: [
      'Centralized student & faculty profile management (CRUD)',
      'Subject catalog creation and faculty assignment engine',
      'Institutional attendance analytics and departmental oversight',
    ],
  },
];

export default function RoleSelectionPage() {
  return (
    <div id="role-selection-root" className="min-h-screen bg-surface-50 flex flex-col text-surface-900">
      {/* Top Academic Header */}
      <header className="bg-white border-b border-surface-200 sticky top-0 z-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          {/* Institution / Brand Logo */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-600 to-primary-700 flex items-center justify-center text-white shadow-xs">
              <GraduationCap className="w-5 h-5" aria-hidden="true" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xl font-bold text-surface-900 tracking-tight leading-none">AttendX</span>
                <span className="hidden sm:inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold tracking-wide uppercase bg-surface-100 text-surface-600 border border-surface-200">
                  Institutional
                </span>
              </div>
              <p className="text-xs text-surface-500 font-medium">Academic Attendance Management System</p>
            </div>
          </div>

          {/* Institutional Status & Secondary Link */}
          <nav aria-label="Portal Navigation" className="flex items-center gap-3 sm:gap-4">
            <div className="hidden md:flex items-center gap-2 text-xs text-surface-500 font-medium bg-surface-50 px-3 py-1.5 rounded-lg border border-surface-200/80">
              <Building2 className="w-3.5 h-3.5 text-surface-400" aria-hidden="true" />
              <span>Academic Year 2026–2027</span>
              <span className="text-surface-300">•</span>
              <Calendar className="w-3.5 h-3.5 text-surface-400" aria-hidden="true" />
              <span>Semester 1</span>
            </div>

            <Link
              to="/login"
              className="text-xs sm:text-sm font-medium text-primary-600 hover:text-primary-700 px-3 py-1.5 rounded-lg hover:bg-primary-50 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500"
            >
              Direct Sign In
            </Link>
          </nav>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-10 sm:py-16 flex flex-col justify-center">
        {/* Hero Section */}
        <section className="text-center max-w-3xl mx-auto mb-10 sm:mb-14">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-primary-50 text-primary-700 border border-primary-200/60 mb-4">
            <Building2 className="w-3.5 h-3.5" aria-hidden="true" />
            <span>Academic Attendance Management System</span>
          </div>
          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold text-surface-900 tracking-tight leading-tight">
            AttendX — Academic Attendance Management System
          </h1>
          <p className="mt-3 text-lg sm:text-xl text-surface-600 font-medium">
            Unified Attendance Tracking for Students, Lecturers, and Administrators
          </p>
          <p className="mt-2 text-sm text-surface-500 max-w-2xl mx-auto">
            AttendX provides automated attendance recording, course enrollment tracking, 75% attendance threshold monitoring, and comprehensive institutional reporting with secure role-based access. Select your institutional portal below to continue.
          </p>
        </section>

        {/* Role Cards Grid */}
        <section aria-label="Role selection cards" className="w-full">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 lg:gap-8 max-w-6xl mx-auto">
            {ROLES.map((card) => {
              const Icon = card.icon;
              return (
                <article
                  key={card.role}
                  id={card.id}
                  className={`bg-white rounded-2xl border border-surface-200 p-6 sm:p-7 flex flex-col justify-between transition-all duration-200 ${card.accent.borderHover} hover:shadow-lg focus-within:ring-2 focus-within:ring-primary-500/50`}
                >
                  <div>
                    {/* Role header: Icon & Role Tag */}
                    <div className="flex items-center justify-between gap-3 mb-5">
                      <div
                        className={`w-12 h-12 rounded-xl flex items-center justify-center border ${card.accent.iconBg} ${card.accent.iconColor}`}
                      >
                        <Icon className="w-6 h-6" aria-hidden="true" />
                      </div>
                      <span
                        className={`inline-flex items-center px-2.5 py-1 rounded-md text-xs font-semibold tracking-wider uppercase border ${card.accent.badge}`}
                      >
                        {card.role}
                      </span>
                    </div>

                    {/* Role Title */}
                    <h2 className="text-xl font-bold text-surface-900 tracking-tight mb-2">
                      {card.title}
                    </h2>

                    {/* Standard Exact Role Description */}
                    <p className="text-sm text-surface-600 leading-relaxed min-h-[4rem]">
                      {card.description}
                    </p>

                    {/* Key Capabilities List */}
                    <div className="mt-5 pt-5 border-t border-surface-100">
                      <p className="text-[11px] font-semibold text-surface-400 uppercase tracking-wider mb-2.5">
                        Key Capabilities
                      </p>
                      <ul className="space-y-2 text-xs text-surface-600" aria-label={`${card.title} capabilities`}>
                        {card.features.map((feature, idx) => (
                          <li key={idx} className="flex items-start gap-2">
                            <CheckCircle2
                              className="w-4 h-4 text-emerald-500 shrink-0 mt-0.5"
                              aria-hidden="true"
                            />
                            <span className="leading-snug">{feature}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>

                  {/* CTA Action */}
                  <div className="mt-7 pt-5 border-t border-surface-100">
                    <Link
                      to={card.route}
                      id={card.ctaId}
                      className={`btn w-full btn-lg font-medium flex items-center justify-center gap-2 group transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-primary-500 ${card.accent.button}`}
                      aria-label={`${card.cta} - Open ${card.title} Login`}
                    >
                      <span>{card.cta}</span>
                      <ArrowRight
                        className="w-4 h-4 transition-transform duration-200 group-hover:translate-x-0.5"
                        aria-hidden="true"
                      />
                    </Link>
                  </div>
                </article>
              );
            })}
          </div>
        </section>

        {/* Security & Academic Integrity Footnote */}
        <section className="mt-12 sm:mt-16 max-w-2xl mx-auto w-full text-center">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-white border border-surface-200 text-xs text-surface-500 shadow-2xs">
            <Lock className="w-3.5 h-3.5 text-surface-400" aria-hidden="true" />
            <span>Secure Role-Based Access Control • Institutional Data Protection</span>
          </div>
          <p className="mt-3 text-xs text-surface-400">
            AttendX enforces role permissions, audit logging, and course enrollment validation across all academic sessions.
          </p>
        </section>
      </main>

      {/* Institutional Academic Footer */}
      <footer className="bg-white border-t border-surface-200 py-6">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-surface-500">
          <div className="flex items-center gap-2">
            <GraduationCap className="w-4 h-4 text-primary-600" aria-hidden="true" />
            <span className="font-semibold text-surface-700">AttendX</span>
            <span>— Academic Attendance Management System</span>
          </div>

          <div className="flex items-center gap-6">
            <span>© {new Date().getFullYear()} AttendX. All rights reserved.</span>
            <span className="text-surface-300">•</span>
            <span className="text-surface-400">v1.2.0 Production</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
