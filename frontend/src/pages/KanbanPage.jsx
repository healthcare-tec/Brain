/**
 * KanbanPage — GTD Kanban board with working drag & drop between columns.
 *
 * Drag & drop implementation notes:
 * - Uses dataTransfer.setData/getData as the source of truth for the dragged
 *   task ID. This avoids the race condition where React state (draggedTask)
 *   can be cleared by onDragEnd before onDrop fires in some browsers.
 * - Optimistic UI: the task moves visually immediately; if the API call fails,
 *   the board reloads to show the real state.
 * - onDragEnd on the card resets the "dragging" visual but does NOT clear
 *   draggedTaskId — that is only cleared after the drop is processed.
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Columns3, GripVertical, Clock, Tag, AlertCircle } from 'lucide-react';
import { tasksApi } from '../services/api';

const COLUMNS = [
  { key: 'next',        label: 'Next Actions', color: 'border-t-blue-500',   bg: 'bg-blue-50 dark:bg-blue-900/20'   },
  { key: 'in_progress', label: 'In Progress',  color: 'border-t-amber-500',  bg: 'bg-amber-50 dark:bg-amber-900/20' },
  { key: 'waiting',     label: 'Waiting For',  color: 'border-t-purple-500', bg: 'bg-purple-50 dark:bg-purple-900/20' },
  { key: 'done',        label: 'Done',         color: 'border-t-green-500',  bg: 'bg-green-50 dark:bg-green-900/20' },
];

const PRIORITY_COLORS = {
  critical: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300',
  high:     'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-300',
  medium:   'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300',
  low:      'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300',
};

function KanbanCard({ task, draggingId }) {
  const tags = task.tags ? task.tags.split(',').filter(Boolean) : [];
  const isDragging = draggingId === task.id;

  return (
    <div
      draggable
      onDragStart={(e) => {
        // Store task id in dataTransfer — this survives across React re-renders
        e.dataTransfer.setData('text/plain', task.id);
        e.dataTransfer.effectAllowed = 'move';
      }}
      className={`bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-3 cursor-grab active:cursor-grabbing hover:shadow-md transition-all group select-none ${
        isDragging ? 'opacity-40 scale-95' : ''
      }`}
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
  const [tasks, setTasks]           = useState([]);
  const [loading, setLoading]       = useState(true);
  const [dragOverCol, setDragOverCol] = useState(null);
  const [draggingId, setDraggingId] = useState(null);
  const [error, setError]           = useState(null);

  // Use a ref so the drop handler always has the latest tasks without stale closure
  const tasksRef = useRef(tasks);
  useEffect(() => { tasksRef.current = tasks; }, [tasks]);

  const loadTasks = useCallback(async () => {
    setLoading(true);
    try {
      const data = await tasksApi.list();
      setTasks(data);
    } catch (err) {
      console.error('Failed to load tasks:', err);
      setError('Failed to load tasks. Please refresh.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadTasks(); }, [loadTasks]);

  // ── Drag handlers ──────────────────────────────────────────────────────────

  const handleDragStart = (e) => {
    const taskId = e.dataTransfer.getData('text/plain');
    // dataTransfer is not yet available in dragstart on some browsers —
    // instead we read it from the event target's data attribute set by KanbanCard
    // Actually dataTransfer IS available in dragstart; just track visually:
    setDraggingId(e.target.closest('[draggable]')?.dataset?.taskId || null);
  };

  const handleColumnDragOver = (e, colKey) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    setDragOverCol(colKey);
  };

  const handleColumnDragLeave = (e) => {
    // Only clear if leaving the column element itself, not a child
    if (!e.currentTarget.contains(e.relatedTarget)) {
      setDragOverCol(null);
    }
  };

  const handleDrop = async (e, targetStatus) => {
    e.preventDefault();
    setDragOverCol(null);
    setDraggingId(null);

    const taskId = e.dataTransfer.getData('text/plain');
    if (!taskId) return;

    const task = tasksRef.current.find((t) => t.id === taskId);
    if (!task) return;
    if (task.status === targetStatus) return;  // no-op

    // Optimistic update — move card immediately in UI
    setTasks((prev) =>
      prev.map((t) => t.id === taskId ? { ...t, status: targetStatus } : t)
    );

    try {
      if (targetStatus === 'done') {
        await tasksApi.complete(taskId);
      } else {
        await tasksApi.update(taskId, { status: targetStatus });
      }
    } catch (err) {
      console.error('Failed to update task status:', err);
      setError(`Failed to move task: ${err.message}`);
      // Revert optimistic update
      await loadTasks();
    }
  };

  const getColumnTasks = (status) => tasks.filter((t) => t.status === status);

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6 flex-shrink-0">
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

      {/* Error banner */}
      {error && (
        <div className="mb-4 flex items-center gap-2 px-4 py-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-700 rounded-xl text-sm text-red-700 dark:text-red-300 flex-shrink-0">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
          <button onClick={() => setError(null)} className="ml-auto text-red-400 hover:text-red-600 text-xs underline">Dismiss</button>
        </div>
      )}

      {loading ? (
        <div className="text-center py-12 text-gray-400 dark:text-gray-500">Loading...</div>
      ) : (
        <div
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 flex-1 min-h-0"
          onDragStart={handleDragStart}
        >
          {COLUMNS.map((col) => {
            const colTasks = getColumnTasks(col.key);
            const isOver = dragOverCol === col.key;

            return (
              <div
                key={col.key}
                onDragOver={(e) => handleColumnDragOver(e, col.key)}
                onDragLeave={handleColumnDragLeave}
                onDrop={(e) => handleDrop(e, col.key)}
                className={`flex flex-col rounded-xl border-t-4 ${col.color} transition-all ${
                  isOver
                    ? `${col.bg} ring-2 ring-charlie-400 ring-offset-1 shadow-lg`
                    : 'bg-gray-50 dark:bg-gray-800/50'
                }`}
              >
                {/* Column header */}
                <div className="flex items-center justify-between px-4 py-3 flex-shrink-0">
                  <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300">{col.label}</h3>
                  <span className="text-xs px-2 py-0.5 rounded-full bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-400 font-medium">
                    {colTasks.length}
                  </span>
                </div>

                {/* Drop zone hint when dragging over empty column */}
                {isOver && colTasks.length === 0 && (
                  <div className="mx-3 mb-2 py-4 border-2 border-dashed border-charlie-300 dark:border-charlie-700 rounded-lg text-center text-xs text-charlie-500 dark:text-charlie-400">
                    Drop here
                  </div>
                )}

                {/* Cards */}
                <div className="flex-1 overflow-y-auto px-3 pb-3 space-y-2">
                  {colTasks.length === 0 && !isOver ? (
                    <div className="text-center py-8 text-xs text-gray-400 dark:text-gray-500">
                      No tasks
                    </div>
                  ) : (
                    colTasks.map((task) => (
                      <KanbanCard
                        key={task.id}
                        task={task}
                        draggingId={draggingId}
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
