import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import { User, Mail, Hash, Building, Calendar, BookOpen, Loader2, CheckCircle2 } from 'lucide-react';
import toast from 'react-hot-toast';

export default function ProfilePage() {
  const { user, updateUser } = useAuth();
  const [editing, setEditing] = useState(false);
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({
    full_name: user?.full_name || '',
    department: user?.department || '',
    year: user?.year?.toString() || '',
    section: user?.section || '',
  });

  const handleSave = async () => {
    setLoading(true);
    try {
      const res = await api.put('/api/auth/profile', {
        full_name: form.full_name.trim(),
        department: form.department.trim(),
        year: form.year ? parseInt(form.year) : null,
        section: form.section.trim(),
      });
      updateUser(res.data);
      setEditing(false);
      toast.success('Profile updated!');
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Update failed');
    } finally {
      setLoading(false);
    }
  };

  const infoRow = (icon: React.ReactNode, label: string, value: string | undefined, editable = false, field = '') => (
    <div className="flex items-start gap-4 py-4 border-b border-surface-50 last:border-0">
      <div className="w-10 h-10 rounded-xl bg-surface-100 flex items-center justify-center flex-shrink-0">
        {icon}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-xs font-medium text-surface-400 uppercase tracking-wider">{label}</p>
        {editing && editable ? (
          <input
            value={(form as any)[field] || ''}
            onChange={(e) => setForm({ ...form, [field]: e.target.value })}
            className="input mt-1"
          />
        ) : (
          <p className="text-sm font-medium text-surface-800 mt-0.5">{value || '—'}</p>
        )}
      </div>
    </div>
  );

  return (
    <div className="max-w-2xl mx-auto space-y-6 fade-in">
      <div>
        <h1 className="text-2xl font-bold text-surface-900">Profile</h1>
        <p className="text-surface-500 text-sm mt-0.5">Your account information</p>
      </div>

      {/* Avatar Card */}
      <div className="card text-center py-8">
        <div className="w-20 h-20 rounded-full bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center text-white text-2xl font-bold mx-auto mb-4 shadow-lg shadow-primary-200">
          {user?.full_name?.charAt(0).toUpperCase()}
        </div>
        <h2 className="text-xl font-semibold text-surface-900">{user?.full_name}</h2>
        <p className="text-surface-500 text-sm mt-0.5">{user?.email}</p>
        <span className={`badge mt-2 ${
          user?.role === 'admin' ? 'badge-info' : user?.role === 'lecturer' ? 'badge-primary' : 'badge-success'
        }`}>
          {user?.role === 'admin' ? 'Administrator' : user?.role === 'lecturer' ? 'Lecturer' : 'Student'}
        </span>
      </div>

      {/* Details */}
      <div className="card">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-base font-semibold text-surface-800">Personal Information</h3>
          {!editing ? (
            <button onClick={() => setEditing(true)} className="btn btn-secondary btn-sm">Edit Profile</button>
          ) : (
            <div className="flex gap-2">
              <button onClick={() => setEditing(false)} className="btn btn-secondary btn-sm">Cancel</button>
              <button onClick={handleSave} className="btn btn-primary btn-sm" disabled={loading}>
                {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <CheckCircle2 className="w-3.5 h-3.5" />}
                Save
              </button>
            </div>
          )}
        </div>

        {infoRow(<User className="w-4 h-4 text-surface-500" />, 'Full Name', user?.full_name, true, 'full_name')}
        {infoRow(<Mail className="w-4 h-4 text-surface-500" />, 'Email', user?.email)}
        {user?.student_id && infoRow(<Hash className="w-4 h-4 text-surface-500" />, 'Student ID', user.student_id)}
        {user?.employee_id && infoRow(<Hash className="w-4 h-4 text-surface-500" />, 'Employee ID', user.employee_id)}
        {infoRow(<Building className="w-4 h-4 text-surface-500" />, 'Department', user?.department, true, 'department')}
        {user?.role === 'student' && infoRow(<Calendar className="w-4 h-4 text-surface-500" />, 'Year', user?.year?.toString(), true, 'year')}
        {user?.role === 'student' && infoRow(<BookOpen className="w-4 h-4 text-surface-500" />, 'Section', user?.section, true, 'section')}
      </div>

      <div className="card">
        <h3 className="text-base font-semibold text-surface-800 mb-2">Account Details</h3>
        <div className="text-sm text-surface-500 space-y-1">
          <p>Account created: {user?.created_at ? new Date(user.created_at).toLocaleDateString() : '—'}</p>
          <p>Last updated: {user?.updated_at ? new Date(user.updated_at).toLocaleDateString() : '—'}</p>
        </div>
      </div>
    </div>
  );
}
