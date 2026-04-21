import React, { useState, useEffect } from 'react';
import { X, CheckSquare, FolderKanban, FileText, Trash2 } from 'lucide-react';
import { projectsApi } from '../services/api';

const TYPES = [
  { value: 'task', label: 'Task', icon: CheckSquare, color: 'bg-blue-100 text-blue-700' },
  { value: 'project', label: 'Project', icon: FolderKanban, color: 'bg-purple-100 text-purple-700' },
  { value: 'note', label: 'Note', icon: FileText, color: 'bg-green-100 text-green-700' },
  { value: 'trash', label: 'Trash', icon: Trash2, color: 'bg-red-100 text-red-700' },
];

export default function ClarifyModal({ item, onClarify, onClose }) {
  const [clarifiedAs, setClarifiedAs] = useState('task');
  const [title, setTitle] = useState(item?.content?.slice(0, 200) || '');
  const [description, setDescription] = useState('');
  const [context, setContext] = useState('');
  const [projectId, setProjectId] = useState('');
  const [category, setCategory] = useState('resource');
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    projectsApi.list().then(setProjects).catch(() => {});
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await onClarify(item.id, {
        clarified_as: clarifiedAs,
        title: clarifiedAs !== 'trash' ? title : undefined,
        description: description || undefined,
        context: context || undefined,
        project_id: projectId || undefined,
        category: clarifiedAs === 'note' ? category : undefined,
      });
      onClose();
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <h2 className="text-lg font-semibold text-gray-900">Clarify Item</h2>
          <button onClick={onClose} className="p-1 text-gray-400 hover:text-gray-600">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="px-6 py-4">
          <div className="p-3 bg-gray-50 rounded-lg text-sm text-gray-700 mb-4">
            {item?.content}
          </div>

          {/* Type selection */}
          <div className="grid grid-cols-4 gap-2 mb-4">
            {TYPES.map(({ value, label, icon: Icon, color }) => (
              <button
                key={value}
                type="button"
                onClick={() => setClarifiedAs(value)}
                className={`flex flex-col items-center gap-1 p-3 rounded-xl border-2 transition-all text-xs font-medium ${
                  clarifiedAs === value
                    ? `border-charlie-400 ${color}`
                    : 'border-gray-200 text-gray-500 hover:border-gray-300'
                }`}
              >
                <Icon className="w-5 h-5" />
                {label}
              </button>
            ))}
          </div>

          {clarifiedAs !== 'trash' && (
            <form onSubmit={handleSubmit} className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Title</label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-charlie-300"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Description</label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  rows={2}
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-charlie-300"
                />
              </div>

              {clarifiedAs === 'task' && (
                <>
                  <div>
                    <label className="block text-xs font-medium text-gray-600 mb-1">Context</label>
                    <input
                      type="text"
                      value={context}
                      onChange={(e) => setContext(e.target.value)}
                      placeholder="@work, @home, @computer..."
                      className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-charlie-300"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-600 mb-1">Project</label>
                    <select
                      value={projectId}
                      onChange={(e) => setProjectId(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-charlie-300"
                    >
                      <option value="">No project</option>
                      {projects.map((p) => (
                        <option key={p.id} value={p.id}>{p.name}</option>
                      ))}
                    </select>
                  </div>
                </>
              )}

              {clarifiedAs === 'note' && (
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Category (PARA)</label>
                  <select
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-charlie-300"
                  >
                    <option value="project">Project</option>
                    <option value="area">Area</option>
                    <option value="resource">Resource</option>
                    <option value="archive">Archive</option>
                  </select>
                </div>
              )}

              <button
                type="submit"
                disabled={loading}
                className="w-full py-2.5 bg-charlie-600 text-white rounded-lg text-sm font-medium hover:bg-charlie-700 disabled:opacity-50 transition-colors"
              >
                {loading ? 'Processing...' : `Clarify as ${clarifiedAs}`}
              </button>
            </form>
          )}

          {clarifiedAs === 'trash' && (
            <button
              onClick={handleSubmit}
              disabled={loading}
              className="w-full py-2.5 bg-red-600 text-white rounded-lg text-sm font-medium hover:bg-red-700 disabled:opacity-50 transition-colors"
            >
              {loading ? 'Processing...' : 'Move to Trash'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
