import React, { useState, useEffect } from 'react';
import { X } from 'lucide-react';
import { projectsApi } from '../services/api';

export default function TaskFormModal({ task, onSave, onClose }) {
  const isEdit = !!task;
  const [form, setForm] = useState({
    title: task?.title || '',
    description: task?.description || '',
    status: task?.status || 'next',
    priority: task?.priority || 'medium',
    context: task?.context || '',
    project_id: task?.project_id || '',
    estimated_time: task?.estimated_time || '',
    due_date: task?.due_date?.slice(0, 16) || '',
    tags: task?.tags || '',
    recurrence: task?.recurrence || 'none',
    reminder_at: task?.reminder_at?.slice(0, 16) || '',
  });
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    projectsApi.list().then(setProjects).catch(() => {});
  }, []);

  const handleChange = (field) => (e) => setForm({ ...form, [field]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const data = {
        ...form,
        estimated_time: form.estimated_time ? parseInt(form.estimated_time) : null,
        due_date: form.due_date || null,
        project_id: form.project_id || null,
        context: form.context || null,
        description: form.description || null,
        tags: form.tags || null,
        recurrence: form.recurrence || 'none',
        reminder_at: form.reminder_at || null,
      };
      await onSave(data, task?.id);
      onClose();
    } finally {
      setLoading(false);
    }
  };

  const inputClass = "w-full px-3 py-2 border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-700 dark:text-gray-100 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-charlie-300";
  const labelClass = "block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100 dark:border-gray-700">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">{isEdit ? 'Edit Task' : 'New Task'}</h2>
          <button onClick={onClose} className="p-1 text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="px-6 py-4 space-y-3">
          <div>
            <label className={labelClass}>Title *</label>
            <input type="text" value={form.title} onChange={handleChange('title')} required className={inputClass} />
          </div>

          <div>
            <label className={labelClass}>Description</label>
            <textarea value={form.description} onChange={handleChange('description')} rows={2} className={inputClass} />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className={labelClass}>Status</label>
              <select value={form.status} onChange={handleChange('status')} className={inputClass}>
                <option value="next">Next</option>
                <option value="in_progress">In Progress</option>
                <option value="waiting">Waiting</option>
                <option value="someday">Someday</option>
              </select>
            </div>
            <div>
              <label className={labelClass}>Priority</label>
              <select value={form.priority} onChange={handleChange('priority')} className={inputClass}>
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="critical">Critical</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className={labelClass}>Context</label>
              <input type="text" value={form.context} onChange={handleChange('context')} placeholder="@work, @home..." className={inputClass} />
            </div>
            <div>
              <label className={labelClass}>Estimated Time (min)</label>
              <input type="number" value={form.estimated_time} onChange={handleChange('estimated_time')} min="0" className={inputClass} />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className={labelClass}>Project</label>
              <select value={form.project_id} onChange={handleChange('project_id')} className={inputClass}>
                <option value="">No project</option>
                {projects.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
              </select>
            </div>
            <div>
              <label className={labelClass}>Due Date</label>
              <input type="datetime-local" value={form.due_date} onChange={handleChange('due_date')} className={inputClass} />
            </div>
          </div>

          {/* New fields: Tags, Recurrence, Reminder */}
          <div>
            <label className={labelClass}>Tags (comma-separated)</label>
            <input type="text" value={form.tags} onChange={handleChange('tags')} placeholder="urgent, research, followup..." className={inputClass} />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className={labelClass}>Recurrence</label>
              <select value={form.recurrence} onChange={handleChange('recurrence')} className={inputClass}>
                <option value="none">None</option>
                <option value="daily">Daily</option>
                <option value="weekly">Weekly</option>
                <option value="monthly">Monthly</option>
              </select>
            </div>
            <div>
              <label className={labelClass}>Reminder</label>
              <input type="datetime-local" value={form.reminder_at} onChange={handleChange('reminder_at')} className={inputClass} />
            </div>
          </div>

          <button type="submit" disabled={loading}
            className="w-full py-2.5 bg-charlie-600 text-white rounded-lg text-sm font-medium hover:bg-charlie-700 disabled:opacity-50 transition-colors mt-2">
            {loading ? 'Saving...' : isEdit ? 'Update Task' : 'Create Task'}
          </button>
        </form>
      </div>
    </div>
  );
}
