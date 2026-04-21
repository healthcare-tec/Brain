import React, { useState, useEffect, useCallback } from 'react';
import { CheckSquare, Plus, Filter, Search, Tag, X } from 'lucide-react';
import TaskCard from '../components/TaskCard';
import TaskFormModal from '../components/TaskFormModal';
import { tasksApi } from '../services/api';

export default function TasksPage() {
  const [tasks, setTasks] = useState([]);
  const [filter, setFilter] = useState('next');
  const [showForm, setShowForm] = useState(false);
  const [editTask, setEditTask] = useState(null);
  const [loading, setLoading] = useState(true);

  // Advanced filters
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterPriority, setFilterPriority] = useState('');
  const [filterContext, setFilterContext] = useState('');
  const [filterTags, setFilterTags] = useState('');
  const [selectedTaskIdx, setSelectedTaskIdx] = useState(0);

  const loadTasks = useCallback(async () => {
    setLoading(true);
    try {
      const params = {};
      if (filter !== 'all') params.status = filter;
      if (searchQuery) params.search = searchQuery;
      if (filterPriority) params.priority = filterPriority;
      if (filterContext) params.context = filterContext;
      if (filterTags) params.tags = filterTags;
      const data = await tasksApi.list(params);
      setTasks(data);
    } catch (err) {
      console.error('Failed to load tasks:', err);
    } finally {
      setLoading(false);
    }
  }, [filter, searchQuery, filterPriority, filterContext, filterTags]);

  useEffect(() => { loadTasks(); }, [loadTasks]);

  // Keyboard shortcut: D to complete selected task
  useEffect(() => {
    const handler = (e) => {
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
      if ((e.key === 'd' || e.key === 'D') && tasks.length > 0) {
        const task = tasks[selectedTaskIdx];
        if (task && task.status !== 'done') {
          tasksApi.complete(task.id).then(loadTasks);
        }
      }
      if (e.key === 'ArrowDown') { e.preventDefault(); setSelectedTaskIdx(i => Math.min(i + 1, tasks.length - 1)); }
      if (e.key === 'ArrowUp') { e.preventDefault(); setSelectedTaskIdx(i => Math.max(i - 1, 0)); }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [tasks, selectedTaskIdx, loadTasks]);

  const handleComplete = async (taskId, data) => {
    await tasksApi.complete(taskId, data);
    await loadTasks();
  };

  const handleSave = async (data, taskId) => {
    if (taskId) await tasksApi.update(taskId, data);
    else await tasksApi.create(data);
    await loadTasks();
  };

  const handleEdit = (task) => { setEditTask(task); setShowForm(true); };

  const clearAdvanced = () => {
    setSearchQuery(''); setFilterPriority(''); setFilterContext(''); setFilterTags('');
    setShowAdvanced(false);
  };

  const hasActiveFilters = searchQuery || filterPriority || filterContext || filterTags;

  // Collect unique tags from tasks
  const allTags = [...new Set(tasks.flatMap(t => (t.tags || '').split(',').filter(Boolean).map(s => s.trim())))];

  return (
    <div className="max-w-3xl mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-xl bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center">
          <CheckSquare className="w-5 h-5 text-blue-600 dark:text-blue-400" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Tasks</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400">Next Actions — GTD execution layer</p>
        </div>
        <div className="ml-auto flex items-center gap-2">
          <button
            onClick={() => setShowAdvanced(!showAdvanced)}
            className={`px-3 py-2 rounded-xl text-sm font-medium transition-colors flex items-center gap-1.5 ${
              hasActiveFilters
                ? 'bg-charlie-100 dark:bg-charlie-900/30 text-charlie-700 dark:text-charlie-300'
                : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700'
            }`}
          >
            <Filter className="w-4 h-4" />Filters
            {hasActiveFilters && <span className="w-2 h-2 rounded-full bg-charlie-500" />}
          </button>
          <button
            onClick={() => { setEditTask(null); setShowForm(true); }}
            className="px-4 py-2 bg-charlie-600 text-white rounded-xl text-sm font-medium hover:bg-charlie-700 transition-colors flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />New Task
          </button>
        </div>
      </div>

      {/* Advanced Filters Panel */}
      {showAdvanced && (
        <div className="mb-4 p-4 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300">Advanced Filters</h3>
            {hasActiveFilters && (
              <button onClick={clearAdvanced} className="text-xs text-charlie-600 hover:underline flex items-center gap-1">
                <X className="w-3 h-3" />Clear all
              </button>
            )}
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-gray-500 dark:text-gray-400 mb-1 block">Search</label>
              <div className="relative">
                <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400" />
                <input
                  type="text" value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search tasks..."
                  className="w-full pl-8 pr-3 py-1.5 text-sm rounded-lg border border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 dark:text-gray-100 outline-none focus:ring-2 focus:ring-charlie-500"
                />
              </div>
            </div>
            <div>
              <label className="text-xs text-gray-500 dark:text-gray-400 mb-1 block">Priority</label>
              <select
                value={filterPriority} onChange={(e) => setFilterPriority(e.target.value)}
                className="w-full px-3 py-1.5 text-sm rounded-lg border border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 dark:text-gray-100 outline-none"
              >
                <option value="">All</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>
            </div>
            <div>
              <label className="text-xs text-gray-500 dark:text-gray-400 mb-1 block">Context</label>
              <input
                type="text" value={filterContext} onChange={(e) => setFilterContext(e.target.value)}
                placeholder="@work, @home..."
                className="w-full px-3 py-1.5 text-sm rounded-lg border border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 dark:text-gray-100 outline-none focus:ring-2 focus:ring-charlie-500"
              />
            </div>
            <div>
              <label className="text-xs text-gray-500 dark:text-gray-400 mb-1 block">Tags</label>
              <input
                type="text" value={filterTags} onChange={(e) => setFilterTags(e.target.value)}
                placeholder="tag1,tag2..."
                className="w-full px-3 py-1.5 text-sm rounded-lg border border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 dark:text-gray-100 outline-none focus:ring-2 focus:ring-charlie-500"
              />
            </div>
          </div>
          {allTags.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {allTags.map(tag => (
                <button
                  key={tag}
                  onClick={() => setFilterTags(tag)}
                  className={`text-xs px-2 py-0.5 rounded-full flex items-center gap-1 transition-colors ${
                    filterTags === tag
                      ? 'bg-charlie-600 text-white'
                      : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-charlie-100 dark:hover:bg-charlie-900/30'
                  }`}
                >
                  <Tag className="w-2.5 h-2.5" />{tag}
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Filter tabs */}
      <div className="flex gap-1 mb-4 bg-gray-100 dark:bg-gray-800 rounded-lg p-1">
        {['next', 'in_progress', 'waiting', 'someday', 'done', 'all'].map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`flex-1 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
              filter === f
                ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 shadow-sm'
                : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200'
            }`}
          >
            {f === 'in_progress' ? 'In Progress' : f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
      </div>

      {/* Task list */}
      {loading ? (
        <div className="text-center py-12 text-gray-400 dark:text-gray-500">Loading...</div>
      ) : tasks.length === 0 ? (
        <div className="text-center py-12">
          <CheckSquare className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" />
          <p className="text-gray-500 dark:text-gray-400">No tasks found. Create one or capture from Inbox!</p>
        </div>
      ) : (
        <div className="space-y-2">
          {tasks.map((task, idx) => (
            <div key={task.id} className={`rounded-xl transition-all ${idx === selectedTaskIdx ? 'ring-2 ring-charlie-400' : ''}`}>
              <TaskCard task={task} onComplete={handleComplete} onEdit={handleEdit} />
            </div>
          ))}
        </div>
      )}

      {showForm && (
        <TaskFormModal task={editTask} onSave={handleSave} onClose={() => { setShowForm(false); setEditTask(null); }} />
      )}
    </div>
  );
}
