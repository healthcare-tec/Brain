import React, { useState, useEffect, useCallback } from 'react';
import { FolderKanban, Plus, X, Trash2, Edit2 } from 'lucide-react';
import { projectsApi } from '../services/api';
import clsx from 'clsx';

const STATUS_COLORS = {
  active: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300',
  on_hold: 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300',
  completed: 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300',
  archived: 'bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400',
};

export default function ProjectsPage() {
  const [projects, setProjects] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [editProject, setEditProject] = useState(null);
  const [form, setForm] = useState({ name: '', description: '', area: '', status: 'active' });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const loadProjects = useCallback(async () => {
    setLoading(true);
    try { setProjects(await projectsApi.list()); } catch (err) { console.error(err); } finally { setLoading(false); }
  }, []);

  useEffect(() => { loadProjects(); }, [loadProjects]);

  const openCreate = () => { setEditProject(null); setForm({ name: '', description: '', area: '', status: 'active' }); setShowForm(true); };
  const openEdit = (p) => { setEditProject(p); setForm({ name: p.name, description: p.description || '', area: p.area || '', status: p.status }); setShowForm(true); };

  const handleSubmit = async (e) => {
    e.preventDefault(); setSaving(true);
    try {
      const data = { ...form, description: form.description || null, area: form.area || null };
      if (editProject) await projectsApi.update(editProject.id, data); else await projectsApi.create(data);
      setShowForm(false); await loadProjects();
    } finally { setSaving(false); }
  };

  const handleDelete = async (id) => { if (!confirm('Delete this project?')) return; await projectsApi.delete(id); await loadProjects(); };

  const inputClass = "w-full px-3 py-2 border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-700 dark:text-gray-100 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-charlie-300";

  return (
    <div className="max-w-4xl mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-xl bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center">
          <FolderKanban className="w-5 h-5 text-purple-600 dark:text-purple-400" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Projects</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400">Project Dashboard — track outcomes</p>
        </div>
        <button onClick={openCreate}
          className="ml-auto px-4 py-2 bg-charlie-600 text-white rounded-xl text-sm font-medium hover:bg-charlie-700 transition-colors flex items-center gap-2">
          <Plus className="w-4 h-4" /> New Project
        </button>
      </div>

      {loading ? (
        <div className="text-center py-12 text-gray-400 dark:text-gray-500">Loading...</div>
      ) : projects.length === 0 ? (
        <div className="text-center py-12">
          <FolderKanban className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" />
          <p className="text-gray-500 dark:text-gray-400">No projects yet. Create your first project!</p>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {projects.map((p) => {
            const progress = p.task_count > 0 ? Math.round((p.completed_task_count / p.task_count) * 100) : 0;
            return (
              <div key={p.id} className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5 hover:shadow-sm transition-shadow group">
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">{p.name}</h3>
                    {p.area && <span className="text-xs text-gray-400 dark:text-gray-500">{p.area}</span>}
                  </div>
                  <div className="flex items-center gap-1">
                    <span className={clsx('text-xs px-2 py-0.5 rounded-full font-medium', STATUS_COLORS[p.status])}>{p.status.replace('_', ' ')}</span>
                    <button onClick={() => openEdit(p)} className="p-1 text-gray-300 dark:text-gray-600 hover:text-charlie-600 opacity-0 group-hover:opacity-100 transition-all"><Edit2 className="w-3.5 h-3.5" /></button>
                    <button onClick={() => handleDelete(p.id)} className="p-1 text-gray-300 dark:text-gray-600 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-all"><Trash2 className="w-3.5 h-3.5" /></button>
                  </div>
                </div>
                {p.description && <p className="text-xs text-gray-500 dark:text-gray-400 mb-3 line-clamp-2">{p.description}</p>}
                <div className="flex items-center gap-3">
                  <div className="flex-1 bg-gray-100 dark:bg-gray-700 rounded-full h-2 overflow-hidden">
                    <div className="bg-charlie-500 h-full rounded-full transition-all" style={{ width: `${progress}%` }} />
                  </div>
                  <span className="text-xs text-gray-500 dark:text-gray-400 font-medium whitespace-nowrap">{p.completed_task_count}/{p.task_count} tasks</span>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {showForm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl w-full max-w-md mx-4">
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100 dark:border-gray-700">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">{editProject ? 'Edit Project' : 'New Project'}</h2>
              <button onClick={() => setShowForm(false)} className="p-1 text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300"><X className="w-5 h-5" /></button>
            </div>
            <form onSubmit={handleSubmit} className="px-6 py-4 space-y-3">
              <div>
                <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Name *</label>
                <input type="text" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required className={inputClass} />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Description</label>
                <textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} rows={2} className={inputClass} />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Area</label>
                  <input type="text" value={form.area} onChange={(e) => setForm({ ...form, area: e.target.value })} placeholder="Technology, Health..." className={inputClass} />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Status</label>
                  <select value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })} className={inputClass}>
                    <option value="active">Active</option>
                    <option value="on_hold">On Hold</option>
                    <option value="completed">Completed</option>
                    <option value="archived">Archived</option>
                  </select>
                </div>
              </div>
              <button type="submit" disabled={saving}
                className="w-full py-2.5 bg-charlie-600 text-white rounded-lg text-sm font-medium hover:bg-charlie-700 disabled:opacity-50 transition-colors">
                {saving ? 'Saving...' : editProject ? 'Update Project' : 'Create Project'}
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
