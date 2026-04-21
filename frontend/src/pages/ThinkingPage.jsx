import React, { useState, useEffect, useCallback } from 'react';
import { Brain, Plus, X, Trash2, ChevronDown, ChevronUp } from 'lucide-react';
import { decisionLogsApi } from '../services/api';
import clsx from 'clsx';

const LOG_TYPES = [
  { value: 'decision', label: 'Decision Log', color: 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300' },
  { value: 'risk_analysis', label: 'Risk Analysis', color: 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300' },
  { value: 'problem_breakdown', label: 'Problem Breakdown', color: 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300' },
];

export default function ThinkingPage() {
  const [logs, setLogs] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [expanded, setExpanded] = useState({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    title: '', log_type: 'decision', context: '', hypotheses: '', options: '', decision: '', expected_outcome: '', tags: '',
  });

  const loadLogs = useCallback(async () => {
    setLoading(true);
    try { setLogs(await decisionLogsApi.list()); } catch (err) { console.error(err); } finally { setLoading(false); }
  }, []);

  useEffect(() => { loadLogs(); }, [loadLogs]);

  const handleSubmit = async (e) => {
    e.preventDefault(); setSaving(true);
    try {
      const data = {};
      for (const [k, v] of Object.entries(form)) { if (v) data[k] = v; }
      await decisionLogsApi.create(data);
      setShowForm(false);
      setForm({ title: '', log_type: 'decision', context: '', hypotheses: '', options: '', decision: '', expected_outcome: '', tags: '' });
      await loadLogs();
    } finally { setSaving(false); }
  };

  const handleDelete = async (id) => { if (!confirm('Delete?')) return; await decisionLogsApi.delete(id); await loadLogs(); };
  const toggleExpand = (id) => setExpanded((prev) => ({ ...prev, [id]: !prev[id] }));

  const inputClass = "w-full px-3 py-2 border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-700 dark:text-gray-100 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-charlie-300";

  return (
    <div className="max-w-3xl mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-xl bg-indigo-100 dark:bg-indigo-900/30 flex items-center justify-center">
          <Brain className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Thinking Engine</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400">System 2 — structured reasoning</p>
        </div>
        <button onClick={() => setShowForm(true)}
          className="ml-auto px-4 py-2 bg-charlie-600 text-white rounded-xl text-sm font-medium hover:bg-charlie-700 transition-colors flex items-center gap-2">
          <Plus className="w-4 h-4" /> New Log
        </button>
      </div>

      {loading ? (
        <div className="text-center py-12 text-gray-400 dark:text-gray-500">Loading...</div>
      ) : logs.length === 0 ? (
        <div className="text-center py-12">
          <Brain className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" />
          <p className="text-gray-500 dark:text-gray-400">No thinking notes yet. Start a decision log!</p>
        </div>
      ) : (
        <div className="space-y-3">
          {logs.map((log) => {
            const typeInfo = LOG_TYPES.find((t) => t.value === log.log_type) || LOG_TYPES[0];
            const isExpanded = expanded[log.id];
            return (
              <div key={log.id} className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4 group">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">{log.title}</h3>
                      <span className={clsx('text-xs px-2 py-0.5 rounded-full font-medium', typeInfo.color)}>{typeInfo.label}</span>
                    </div>
                    {log.tags && <p className="text-xs text-gray-400 dark:text-gray-500">Tags: {log.tags}</p>}
                    <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">{new Date(log.created_at).toLocaleString()}</p>
                  </div>
                  <div className="flex items-center gap-1">
                    <button onClick={() => toggleExpand(log.id)} className="p-1 text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300">
                      {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                    </button>
                    <button onClick={() => handleDelete(log.id)} className="p-1 text-gray-300 dark:text-gray-600 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-all">
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
                {isExpanded && (
                  <div className="mt-3 pt-3 border-t border-gray-100 dark:border-gray-700 space-y-2 text-xs">
                    {['context', 'hypotheses', 'options', 'decision', 'expected_outcome', 'actual_outcome'].map((f) =>
                      log[f] ? (
                        <div key={f}><span className="font-medium text-gray-600 dark:text-gray-400 capitalize">{f.replace('_', ' ')}:</span> <span className="text-gray-500 dark:text-gray-400">{log[f]}</span></div>
                      ) : null
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {showForm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100 dark:border-gray-700">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">New Thinking Note</h2>
              <button onClick={() => setShowForm(false)} className="p-1 text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300"><X className="w-5 h-5" /></button>
            </div>
            <form onSubmit={handleSubmit} className="px-6 py-4 space-y-3">
              <div>
                <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Title *</label>
                <input type="text" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} required className={inputClass} />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Type</label>
                <select value={form.log_type} onChange={(e) => setForm({ ...form, log_type: e.target.value })} className={inputClass}>
                  {LOG_TYPES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
                </select>
              </div>
              {['context', 'hypotheses', 'options', 'decision', 'expected_outcome'].map((field) => (
                <div key={field}>
                  <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1 capitalize">{field.replace('_', ' ')}</label>
                  <textarea value={form[field]} onChange={(e) => setForm({ ...form, [field]: e.target.value })} rows={2} className={inputClass} />
                </div>
              ))}
              <div>
                <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Tags</label>
                <input type="text" value={form.tags} onChange={(e) => setForm({ ...form, tags: e.target.value })} placeholder="comma,separated,tags" className={inputClass} />
              </div>
              <button type="submit" disabled={saving}
                className="w-full py-2.5 bg-charlie-600 text-white rounded-lg text-sm font-medium hover:bg-charlie-700 disabled:opacity-50 transition-colors">
                {saving ? 'Saving...' : 'Create Thinking Note'}
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
