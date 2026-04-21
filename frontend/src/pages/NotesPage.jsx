import React, { useState, useEffect, useCallback } from 'react';
import { FileText, Plus, X, Trash2, Edit2 } from 'lucide-react';
import { notesApi } from '../services/api';
import clsx from 'clsx';

const CATEGORIES = [
  { value: 'project', label: 'Projects', color: 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300' },
  { value: 'area', label: 'Areas', color: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300' },
  { value: 'resource', label: 'Resources', color: 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300' },
  { value: 'archive', label: 'Archive', color: 'bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400' },
];

export default function NotesPage() {
  const [notes, setNotes] = useState([]);
  const [filter, setFilter] = useState('all');
  const [showForm, setShowForm] = useState(false);
  const [editNote, setEditNote] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({ title: '', category: 'resource', tags: '', content: '' });

  const loadNotes = useCallback(async () => {
    setLoading(true);
    try { setNotes(await notesApi.list(filter !== 'all' ? filter : undefined)); } catch (err) { console.error(err); } finally { setLoading(false); }
  }, [filter]);

  useEffect(() => { loadNotes(); }, [loadNotes]);

  const openCreate = () => { setEditNote(null); setForm({ title: '', category: 'resource', tags: '', content: '' }); setShowForm(true); };
  const openEdit = (n) => { setEditNote(n); setForm({ title: n.title, category: n.category, tags: n.tags || '', content: n.content || '' }); setShowForm(true); };

  const handleSubmit = async (e) => {
    e.preventDefault(); setSaving(true);
    try {
      const data = { ...form, tags: form.tags || null, content: form.content || null };
      if (editNote) await notesApi.update(editNote.id, data); else await notesApi.create(data);
      setShowForm(false); await loadNotes();
    } finally { setSaving(false); }
  };

  const handleDelete = async (id) => { if (!confirm('Delete?')) return; await notesApi.delete(id); await loadNotes(); };

  const inputClass = "w-full px-3 py-2 border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-700 dark:text-gray-100 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-charlie-300";

  return (
    <div className="max-w-3xl mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-xl bg-green-100 dark:bg-green-900/30 flex items-center justify-center">
          <FileText className="w-5 h-5 text-green-600 dark:text-green-400" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Knowledge Base</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400">Second Brain — PARA structure</p>
        </div>
        <button onClick={openCreate}
          className="ml-auto px-4 py-2 bg-charlie-600 text-white rounded-xl text-sm font-medium hover:bg-charlie-700 transition-colors flex items-center gap-2">
          <Plus className="w-4 h-4" /> New Note
        </button>
      </div>

      {/* PARA tabs */}
      <div className="flex gap-1 mb-4 bg-gray-100 dark:bg-gray-800 rounded-lg p-1">
        <button onClick={() => setFilter('all')}
          className={clsx('flex-1 px-3 py-1.5 rounded-md text-xs font-medium transition-colors',
            filter === 'all' ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 shadow-sm' : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300')}>
          All
        </button>
        {CATEGORIES.map((c) => (
          <button key={c.value} onClick={() => setFilter(c.value)}
            className={clsx('flex-1 px-3 py-1.5 rounded-md text-xs font-medium transition-colors',
              filter === c.value ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 shadow-sm' : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300')}>
            {c.label}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="text-center py-12 text-gray-400 dark:text-gray-500">Loading...</div>
      ) : notes.length === 0 ? (
        <div className="text-center py-12">
          <FileText className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" />
          <p className="text-gray-500 dark:text-gray-400">No notes yet. Start building your knowledge base!</p>
        </div>
      ) : (
        <div className="space-y-2">
          {notes.map((note) => {
            const catInfo = CATEGORIES.find((c) => c.value === note.category) || CATEGORIES[2];
            return (
              <div key={note.id} className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4 group hover:shadow-sm transition-shadow">
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100 truncate">{note.title}</h3>
                      <span className={clsx('text-xs px-2 py-0.5 rounded-full font-medium flex-shrink-0', catInfo.color)}>{catInfo.label.slice(0, -1)}</span>
                    </div>
                    {note.tags && <p className="text-xs text-gray-400 dark:text-gray-500 mb-1">Tags: {note.tags}</p>}
                    {note.content && <p className="text-xs text-gray-500 dark:text-gray-400 line-clamp-2">{note.content}</p>}
                    <p className="text-xs text-gray-300 dark:text-gray-600 mt-1">{new Date(note.created_at).toLocaleString()}</p>
                  </div>
                  <div className="flex items-center gap-1 ml-2">
                    <button onClick={() => openEdit(note)} className="p-1 text-gray-300 dark:text-gray-600 hover:text-charlie-600 opacity-0 group-hover:opacity-100 transition-all"><Edit2 className="w-3.5 h-3.5" /></button>
                    <button onClick={() => handleDelete(note.id)} className="p-1 text-gray-300 dark:text-gray-600 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-all"><Trash2 className="w-3.5 h-3.5" /></button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {showForm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100 dark:border-gray-700">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">{editNote ? 'Edit Note' : 'New Note'}</h2>
              <button onClick={() => setShowForm(false)} className="p-1 text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300"><X className="w-5 h-5" /></button>
            </div>
            <form onSubmit={handleSubmit} className="px-6 py-4 space-y-3">
              <div>
                <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Title *</label>
                <input type="text" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} required className={inputClass} />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Category (PARA)</label>
                  <select value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} className={inputClass}>
                    {CATEGORIES.map((c) => <option key={c.value} value={c.value}>{c.label}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Tags</label>
                  <input type="text" value={form.tags} onChange={(e) => setForm({ ...form, tags: e.target.value })} placeholder="comma,separated" className={inputClass} />
                </div>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Content (Markdown)</label>
                <textarea value={form.content} onChange={(e) => setForm({ ...form, content: e.target.value })} rows={8} className={inputClass + ' font-mono'} />
              </div>
              <button type="submit" disabled={saving}
                className="w-full py-2.5 bg-charlie-600 text-white rounded-lg text-sm font-medium hover:bg-charlie-700 disabled:opacity-50 transition-colors">
                {saving ? 'Saving...' : editNote ? 'Update Note' : 'Create Note'}
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
