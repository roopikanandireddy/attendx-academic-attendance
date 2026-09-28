import { X } from 'lucide-react';

interface ModalProps {
  isOpen: boolean;
  title: string;
  onClose: () => void;
  children: React.ReactNode;
  maxWidth?: string;
}

export default function Modal({ isOpen, title, onClose, children, maxWidth = 'max-w-lg' }: ModalProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="fixed inset-0 bg-black/40 backdrop-blur-sm" onClick={onClose} />
      <div className={`relative bg-white rounded-xl shadow-2xl ${maxWidth} w-full max-h-[90vh] overflow-y-auto fade-in`}>
        <div className="sticky top-0 bg-white px-6 py-4 border-b border-surface-100 flex items-center justify-between rounded-t-xl z-10">
          <h2 className="text-lg font-semibold text-surface-900">{title}</h2>
          <button onClick={onClose} className="text-surface-400 hover:text-surface-600 transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>
        <div className="p-6">{children}</div>
      </div>
    </div>
  );
}
