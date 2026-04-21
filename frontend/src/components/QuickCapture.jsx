import React, { useState } from 'react';
import { Plus, Zap } from 'lucide-react';

export default function QuickCapture({ onCapture, placeholder = 'Capture anything...', autoFocus = false }) {
  const [content, setContent] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!content.trim()) return;
    setLoading(true);
    try {
      await onCapture(content.trim());
      setContent('');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex gap-2">
      <div className="flex-1 relative">
        <Zap className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-charlie-400" />
        <input
          type="text"
          value={content}
          onChange={(e) => setContent(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          autoFocus={autoFocus}
          className="w-full pl-10 pr-4 py-3 bg-white border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-charlie-300 focus:border-charlie-400 transition-shadow"
          disabled={loading}
        />
      </div>
      <button
        type="submit"
        disabled={loading || !content.trim()}
        className="px-4 py-3 bg-charlie-600 text-white rounded-xl text-sm font-medium hover:bg-charlie-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
      >
        <Plus className="w-4 h-4" />
        Capture
      </button>
    </form>
  );
}
