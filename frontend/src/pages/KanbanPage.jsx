import React, { useState, useEffect, useCallback } from 'react';
import { Columns3, GripVertical, Clock, Tag, CheckCircle2 } from 'lucide-react';
import { tasksApi } from '../services/api';

const COLUMNS = [
  { key: 'next', label: 'Next Actions', color: 'border-t-blue-500', bg: 'bg-blue-50 dark:bg-blue-900/20' },
  { key: 'in_progress', label: 'In Progress', color: 'border-t-amber-500', bg: 'bg-amber-50 dark:bg-amber-900/20' },
  { key: 'waiting', label: 'Waiting For', color: 'border-t-purple-500', bg: 'bg-purple-50 dark:bg-purple-900/20' },
  { key: 'done', label: 'Done', color: 'border-t-green-500', bg: 'bg-green-50 dark:bg-green-900/20' },
];

const PRIORITY_COLORS = {
  high: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300',
  medium: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300',
  low: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300',
};

function KanbanCard({ task, onDragStart }) {
  const tags = task.tags ? task.tags.split(',').filter(Boolean) : [];

  return (
    <div
      draggable
      onDragStart={(e) => { e.dataTransfer.setData('text/plain', task.id); onDragStart(task); }}
      className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-3 cursor-grab active:cursor-grabbing hover:shadow-md transition-shadow group"
    >
      <div className="flex items-start gap-2">
        <GripVertical className="w-4 h-4 text-gray-300 dark:text-gray-600 flex-shrink-0 mt-0.5 opacity-0 group-hover:opacity-100 transition-opacity" />
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-gray-900 dark:text-gray-100 leading-snug">{task.title}</p>

          <div className="flex flex-wrap items-center gap-1.5 mt-2">
            {task.priority && (
              <span className={`text-xs px-1.5 py-0.5 rounded font-medium ${PRIORITY_COLORS[task.priority] || ''}`}>
                {task.priority}
              </span>
            )}
            {task.context && (
              <span className="text-xs px-1.5 py-0.5 rounded bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400">
                @{task.context}
              </span>
            )}
            {task.estimated_time && (
              <span className="text-xs text-gray-400 dark:text-gray-500 flex items-center gap-0.5">
                <Clock className="w-3 h-3" />{task.estimated_time}m
              </span>
            )}
            {task.recurrence && task.recurrence !== 'none' && (
              <span className="text-xs px-1.5 py-0.5 rounded bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300">
                {task.recurrence}
              </span>
            )}
          </div>

          {tags.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-1.5">
              {tags.map((tag) => (
                <span key={tag} className="text-xs px-1.5 py-0.5 rounded-full bg-charlie-50 dark:bg-charlie-900/30 text-charlie-700 dark:text-charlie-300 flex items-center gap-0.5">
                  <Tag className="w-2.5 h-2.5" />{tag.trim()}
                </span>
              ))}
            </div>
          )}

          {task.due_date && (
            <p className={`text-xs mt-1.5 ${new Date(task.due_date) < new Date() ? 'text-red-500 font-medium' : 'text-gray-400 dark:text-gray-500'}`}>
              Due: {new Date(task.due_date).toLocaleDateString()}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

export default function KanbanPage() {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [draggedTask, setDraggedTask] = useState(null);
  const [dragOverCol, setDragOverCol] = useState(null);

  const loadTasks = useCallback(async () => {
    setLoading(true);
    try {
      const data = await tasksApi.list();
      setTasks(data);
    } catch (err) {
      console.error('Failed to load tasks:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadTasks(); }, [loadTasks]);

  const handleDrop = async (targetStatus) => {
    if (!draggedTask || draggedTask.status === targetStatus) {
      setDraggedTask(null);
      setDragOverCol(null);
      return;
    }

    // If dropping to "done", use the complete endpoint
    if (targetStatus === 'done') {
      await tasksApi.complete(draggedTask.id);
    } else {
      await tasksApi.update(draggedTask.id, { status: targetStatus });
    }

    setDraggedTask(null);
    setDragOverCol(null);
    await loadTasks();
  };

  const getColumnTasks = (status) => tasks.filter((t) => t.status === status);

  return (
    <div className="h-full">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-xl bg-charlie-100 dark:bg-charlie-900/30 flex items-center justify-center">
          <Columns3 className="w-5 h-5 text-charlie-600 dark:text-charlie-400" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Kanban Board</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400">Drag tasks between columns to change status</p>
        </div>
        <span className="ml-auto px-3 py-1 bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 rounded-full text-sm">
          {tasks.length} tasks
        </span>
      </div>

      {loading ? (
        <div className="text-center py-12 text-gray-400 dark:text-gray-500">Loading...</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 h-[calc(100vh-200px)]">
          {COLUMNS.map((col) => {
            const colTasks = getColumnTasks(col.key);
            return (
              <div
                key={col.key}
                onDragOver={(e) => { e.preventDefault(); setDragOverCol(col.key); }}
                onDragLeave={() => setDragOverCol(null)}
                onDrop={(e) => { e.preventDefault(); handleDrop(col.key); }}
                className={`flex flex-col rounded-xl border-t-4 ${col.color} ${
                  dragOverCol === col.key ? `${col.bg} ring-2 ring-charlie-400` : 'bg-gray-50 dark:bg-gray-800/50'
                } transition-all`}
              >
                {/* Column header */}
                <div className="flex items-center justify-between px-4 py-3">
                  <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300">{col.label}</h3>
                  <span className="text-xs px-2 py-0.5 rounded-full bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-400 font-medium">
                    {colTasks.length}
                  </span>
                </div>

                {/* Cards */}
                <div className="flex-1 overflow-y-auto px-3 pb-3 space-y-2">
                  {colTasks.length === 0 ? (
                    <div className="text-center py-8 text-xs text-gray-400 dark:text-gray-500">
                      {draggedTask ? 'Drop here' : 'No tasks'}
                    </div>
                  ) : (
                    colTasks.map((task) => (
                      <KanbanCard
                        key={task.id}
                        task={task}
                        onDragStart={setDraggedTask}
                      />
                    ))
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
