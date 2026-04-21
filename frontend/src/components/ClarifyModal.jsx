/**
 * ClarifyModal — GTD clarification modal with dark mode and proper error handling.
 * Can be opened manually or pre-filled from AI suggestion.
 */
import React, { useState, useEffect } from 'react';
import { X, CheckSquare, FolderKanban, FileText, Trash2, Lightbulb, Sparkles, AlertCircle } from 'lucide-react';
import { projectsApi } from '../services/api';

const TYPES = [
  { value: 'task',    label: 'Task',    icon: CheckSquare,  color: 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300' },
  { value: 'project', label: 'Project', icon: FolderKanban, color: 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300' },
  { value: 'note',    label: 'Note',    icon: FileText,     color: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300' },
  { value: 'idea',    label: 'Idea',    icon: Lightbulb,    color: 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300' },
  { value: 'trash',   label: 'Trash',   icon: Trash2,       color: 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300' },
];

export default function ClarifyModal({ item, initialData, onClarify, onClose }) {
  const aiPrefilled = !!initialData;
  const initType     = initialData?.category     || 'task';
  const initTitle    = initialData?.suggested_title   || item?.content?.slice(0, 200) || '';
  const initContext  = initialData?.suggested_context || '';
  const initPriority = initialData?.suggested_priority || 'medium';

  const [clarifiedAs,  setClarifiedAs]  = useState(initType);
  const [title,        setTitle]        = useState(initTitle);
  const [description,  setDescription]  = useState('');
  const [context,      setContext]      = useState(initContext);
  const [priority,     setPriority]     = useState(initPriority);
  const [projectId,    setProjectId]    = useState('');
  const [category,     setCategory]     = useState('resource');
  const [projects,     setProjects]     = useState([]);
  const [loading,      setLoading]      = useState(false);
  const [error,        setError]        = useState(null);

  useEffect(() => { projectsApi.list().then(setProjects).catch(() => {}); }, []);

  useEffect(() => {
    if (initialData) {
      setClarifiedAs(initialData.category || 'task');
      setTitle(initialData.suggested_title || item?.content?.slice(0, 200) || '');
      setContext(initialData.suggested_context || '');
      setPriority(initialData.suggested_priority || 'medium');
    }
  }, [initialData, item]);

  const handleSubmit = async (e) => {
    e?.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await onClarify(item.id, {
        clarified_as: clarifiedAs,   // backend now accepts: task|project|note|idea|trash
        title:       clarifiedAs !== 'trash' ? (title || item.content.slice(0, 200)) : undefined,
        description: description || undefined,
        context:     context     || undefined,
        priority:    priority    || 'medium',
        project_id:  projectId   || undefined,
        category:    (clarifiedAs === 'note' || clarifiedAs === 'idea') ? category : undefined,
      });
      onClose();
    } catch (err) {
      // Show a visible error instead of silently failing
      setError(err?.message || 'Something went wrong. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const inputClass  = "w-full px-3 py-2 border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-700 dark:text-gray-100 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-charlie-300";
  const labelClass  = "block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">

        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100 dark:border-gray-700">
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Clarify Item</h2>
            {aiPrefilled && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-charlie-100 dark:bg-charlie-900/30 text-charlie-700 dark:text-charlie-300 rounded-full text-xs font-medium">
                <Sparkles className="w-3 h-3" /> AI pre-filled
              </span>
            )}
          </div>
          <button onClick={onClose} className="p-1 text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="px-6 py-4">
          {/* Original content */}
          <div className="p-3 bg-gray-50 dark:bg-gray-700 rounded-lg text-sm text-gray-700 dark:text-gray-300 mb-4 leading-relaxed">
            {item?.content}
          </div>

          {/* AI reasoning */}
          {aiPrefilled && initialData?.reasoning && (
            <div className="flex items-start gap-2 p-3 bg-charlie-50 dark:bg-charlie-900/20 border border-charlie-100 dark:border-charlie-800 rounded-lg text-xs text-charlie-700 dark:text-charlie-300 mb-4">
              <Sparkles className="w-3.5 h-3.5 flex-shrink-0 mt-0.5" />
              <span className="italic">{initialData.reasoning}</span>
            </div>
          )}

          {/* Error banner */}
          {error && (
            <div className="flex items-start gap-2 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-sm text-red-700 dark:text-red-300 mb-4">
              <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          {/* Type selector */}
          <div className="grid grid-cols-5 gap-1.5 mb-4">
            {TYPES.map(({ value, label, icon: Icon, color }) => (
              <button key={value} type="button" onClick={() => { setClarifiedAs(value); setError(null); }}
                className={`flex flex-col items-center gap-1 p-2.5 rounded-xl border-2 transition-all text-xs font-medium ${
                  clarifiedAs === value
                    ? `border-charlie-400 ${color}`
                    : 'border-gray-200 dark:border-gray-600 text-gray-500 dark:text-gray-400 hover:border-gray-300 dark:hover:border-gray-500'
                }`}>
                <Icon className="w-4 h-4" />{label}
              </button>
            ))}
          </div>

          {/* Form fields (hidden for trash) */}
          {clarifiedAs !== 'trash' && (
            <form onSubmit={handleSubmit} className="space-y-3">
              <div>
                <label className={labelClass}>
                  Title {aiPrefilled && initTitle === title && <span className="ml-1 text-charlie-500 font-normal">(AI)</span>}
                </label>
                <input type="text" value={title} onChange={(e) => setTitle(e.target.value)} className={inputClass} required />
              </div>

              <div>
                <label className={labelClass}>Description</label>
                <textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={2} className={inputClass} />
              </div>

              <div>
                <label className={labelClass}>
                  Priority {aiPrefilled && initPriority === priority && <span className="ml-1 text-charlie-500 font-normal">(AI)</span>}
                </label>
                <select value={priority} onChange={(e) => setPriority(e.target.value)} className={inputClass}>
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="urgent">Urgent</option>
                </select>
              </div>

              {(clarifiedAs === 'task' || clarifiedAs === 'idea') && (
                <>
                  <div>
                    <label className={labelClass}>
                      Context {aiPrefilled && initContext === context && context && <span className="ml-1 text-charlie-500 font-normal">(AI)</span>}
                    </label>
                    <input type="text" value={context} onChange={(e) => setContext(e.target.value)} placeholder="@work, @home..." className={inputClass} />
                  </div>
                  <div>
                    <label className={labelClass}>Project</label>
                    <select value={projectId} onChange={(e) => setProjectId(e.target.value)} className={inputClass}>
                      <option value="">No project</option>
                      {projects.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
                    </select>
                  </div>
                </>
              )}

              {(clarifiedAs === 'note' || clarifiedAs === 'idea') && (
                <div>
                  <label className={labelClass}>Category (PARA)</label>
                  <select value={category} onChange={(e) => setCategory(e.target.value)} className={inputClass}>
                    <option value="project">Project</option>
                    <option value="area">Area</option>
                    <option value="resource">Resource</option>
                    <option value="archive">Archive</option>
                  </select>
                </div>
              )}

              <button type="submit" disabled={loading}
                className="w-full py-2.5 bg-charlie-600 text-white rounded-lg text-sm font-medium hover:bg-charlie-700 disabled:opacity-50 transition-colors">
                {loading ? 'Processing...' : `Clarify as ${clarifiedAs}`}
              </button>
            </form>
          )}

          {/* Trash confirmation */}
          {clarifiedAs === 'trash' && (
            <div className="space-y-3">
              <p className="text-sm text-gray-500 dark:text-gray-400 text-center">
                This item will be marked as trashed and removed from your inbox.
              </p>
              <button onClick={handleSubmit} disabled={loading}
                className="w-full py-2.5 bg-red-600 text-white rounded-lg text-sm font-medium hover:bg-red-700 disabled:opacity-50 transition-colors">
                {loading ? 'Processing...' : 'Move to Trash'}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
