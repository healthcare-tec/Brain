import React, { useState, useEffect, useCallback } from 'react';
import { Brain, Plus, X, Trash2, ChevronDown, ChevronUp } from 'lucide-react';
import { decisionLogsApi } from '../services/api';
import clsx from 'clsx';

const LOG_TYPES = [
  { value: 'decision', label: 'Decision Log', color: 'bg-blue-100 text-blue-700' },
  { value: 'risk_analysis', label: 'Risk Analysis', color: 'bg-orange-100 text-orange-700' },
  { value: 'problem_breakdown', label: 'Problem Breakdown', color: 'bg-purple-100 text-purple-700' },
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
    try {
      setLogs(await decisionLogsApi.list());
    } catch (err) {
      console.error('Failed to load decision logs:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadLogs(); }, [loadLogs]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      const data = {};
      for (const [k, v] of Object.entries(form)) {
        if (v) data[k] = v;
      }
      await decisionLogsApi.create(data);
      setShowForm(false);
      setForm({ title: '', log_type: 'decision', context: '', hypotheses: '', options: '', decision: '', expected_outcome: '', tags: '' });
      await loadLogs();
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id) => {
    if (!confirm('Delete this decision log?')) return;
    await decisionLogsApi.delete(id);
    await loadLogs();
  };

  const toggleExpand = (id) => setExpanded((prev) => ({ ...prev, [id]: !prev[id] }));

  return (
    <div className="max-w-3xl mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-xl bg-indigo-100 flex items-center justify-center">
          <Brain className="w-5 h-5 text-indigo-600" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Thinking Engine</h1>
          <p className="text-sm text-gray-500">System 2 — structured reasoning</p>
        </div>
        <button onClick={() => setShowForm(true)}
          className="ml-auto px-4 py-2 bg-charlie-600 text-white rounded-xl text-sm font-medium hover:bg-charlie-700 transition-colors flex items-center gap-2">
          <Plus className="w-4 h-4" /> New Log
        </button>
      </div>

      {loading ? (
        <div className="text-center py-12 text-gray-400">Loading...</div>
      ) : logs.length === 0 ? (
        <div className="text-center py-12">
          <Brain className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500">No thinking notes yet. Start a decision log!</p>
        </div>
      ) : (
        <div className="space-y-3">
          {logs.map((log) => {
            const typeInfo = LOG_TYPES.find((t) => t.value === log.log_type) || LOG_TYPES[0];
            const isExpanded = expanded[log.id];
            return (
              <div key={log.id} className="bg-white rounded-xl border border-gray-200 p-4 group">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="text-sm font-semibold text-gray-900">{log.title}</h3>
                      <span className={clsx('text-xs px-2 py-0.5 rounded-full font-medium', typeInfo.color)}>
                        {typeInfo.label}
                      </span>
                    </div>
                    {log.tags && <p className="text-xs text-gray-400">Tags: {log.tags}</p>}
                    <p className="text-xs text-gray-400 mt-1">{new Date(log.created_at).toLocaleString()}</p>
                  </div>
                  <div className="flex items-center gap-1">
                    <button onClick={() => toggleExpand(log.id)} className="p-1 text-gray-400 hover:text-gray-600">
                      {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                    </button>
                    <button onClick={() => handleDelete(log.id)} className="p-1 text-gray-300 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-all">
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                {isExpanded && (
                  <div className="mt-3 pt-3 border-t border-gray-100 space-y-2 text-xs">
                    {log.context && <div><span className="font-medium text-gray-600">Context:</span> <span className="text-gray-500">{log.context}</span></div>}
                    {log.hypotheses && <div><span className="font-medium text-gray-600">Hypotheses:</span> <span className="text-gray-500">{log.hypotheses}</span></div>}
                    {log.options && <div><span className="font-medium text-gray-600">Options:</span> <span className="text-gray-500">{log.options}</span></div>}
                    {log.decision && <div><span className="font-medium text-gray-600">Decision:</span> <span className="text-gray-500">{log.decision}</span></div>}
                    {log.expected_outcome && <div><span className="font-medium text-gray-600">Expected Outcome:</span> <span className="text-gray-500">{log.expected_outcome}</span></div>}
                    {log.actual_outcome && <div><span className="font-medium text-gray-600">Actual Outcome:</span> <span className="text-gray-500">{log.actual_outcome}</span></div>}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Form modal */}
      {showForm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
              <h2 className="text-lg font-semibold">New Thinking Note</h2>
              <button onClick={() => setShowForm(false)} className="p-1 text-gray-400 hover:text-gray-600"><X className="w-5 h-5" /></button>
            </div>
            <form onSubmit={handleSubmit} className="px-6 py-4 space-y-3">
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Title *</label>
                <input type="text" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} required
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-charlie-300" />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Type</label>
                <select value={form.log_type} onChange={(e) => setForm({ ...form, log_type: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-charlie-300">
                  {LOG_TYPES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
                </select>
              </div>
              {['context', 'hypotheses', 'options', 'decision', 'expected_outcome'].map((field) => (
                <div key={field}>
                  <label className="block text-xs font-medium text-gray-600 mb-1 capitalize">{field.replace('_', ' ')}</label>
                  <textarea value={form[field]} onChange={(e) => setForm({ ...form, [field]: e.target.value })} rows={2}
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-charlie-300" />
                </div>
              ))}
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Tags</label>
                <input type="text" value={form.tags} onChange={(e) => setForm({ ...form, tags: e.target.value })} placeholder="comma,separated,tags"
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-charlie-300" />
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
