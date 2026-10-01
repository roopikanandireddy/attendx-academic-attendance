import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import LecturerSidebar from '../components/LecturerSidebar';
import LecturerHeader from '../components/LecturerHeader';

export default function LecturerLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="min-h-screen bg-surface-50">
      {/* Lecturer Sidebar */}
      <LecturerSidebar
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      {/* Main Lecturer Content Container */}
      <div className="lg:ml-64 min-h-screen flex flex-col transition-all duration-200">
        {/* Lecturer Header */}
        <LecturerHeader onOpenSidebar={() => setSidebarOpen(true)} />

        {/* Lecturer Page Content */}
        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl w-full mx-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
