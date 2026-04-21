import React, { useState } from 'react';
import { Check, Clock, Tag, ChevronDown, ChevronUp, Repeat, Bell } from 'lucide-react';
import clsx from 'clsx';

const STATUS_COLORS = {
  next: 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300',
  in_progress: 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300',
  waiting: 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300',
  someday: 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400',
  done: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300',
};

const PRIORITY_COLORS = {
  low: 'text-gray-400 dark:text-gray-500',
  medium: 'text-blue-500 dark:text-blue-400',
  high: 'text-orange-500 dark:text-orange-400',
  critical: 'text-red-600 dark:text-red-400',
};

export default function TaskCard({ task, onComplete, onEdit, compact = false }) {
  const [expanded, setExpanded] = useState(false);
  const [completing, setCompleting] = useState(false);
  const [actualTime, setActualTime] = useState('');

  const handleQuickDone = async () => {
    setCompleting(true);
    try {
      await onComplete(task.id, { actual_time: actualTime ? parseInt(actualTime) : null });
    } finally {
      setCompleting(false);
    }
  };

  if (task.status === 'done' && compact) return null;

  const tags = task.tags ? task.tags.split(',').filter(Boolean).map(s => s.trim()) : [];
  const isOverdue = task.due_date && new Date(task.due_date) < new Date() && task.status !== 'done';

  return (
    <div className={clsx(
      'bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4 transition-shadow hover:shadow-sm',
      task.status === 'done' && 'opacity-60',
      isOverdue && 'border-l-4 border-l-red-400'
    )}>
      <div className="flex items-start gap-3">
        {/* Done button */}
        {task.status !== 'done' ? (
          <button
            onClick={handleQuickDone}
            disabled={completing}
            className="mt-0.5 w-6 h-6 rounded-full border-2 border-gray-300 dark:border-gray-600 hover:border-charlie-500 hover:bg-charlie-50 dark:hover:bg-charlie-900/30 flex items-center justify-center transition-colors flex-shrink-0"
            title="Mark as Done (D)"
          >
            {completing ? (
              <div className="w-3 h-3 border-2 border-charlie-500 border-t-transparent rounded-full animate-spin" />
            ) : (
              <Check className="w-3 h-3 text-transparent hover:text-charlie-500" />
            )}
          </button>
        ) : (
          <div className="mt-0.5 w-6 h-6 rounded-full bg-green-500 flex items-center justify-center flex-shrink-0">
            <Check className="w-3 h-3 text-white" />
          </div>
        )}

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <h3 className={clsx(
              'text-sm font-medium',
              task.status === 'done' ? 'line-through text-gray-400 dark:text-gray-500' : 'text-gray-900 dark:text-gray-100'
            )}>
              {task.title}
            </h3>
            <span className={clsx('text-xs px-2 py-0.5 rounded-full font-medium', STATUS_COLORS[task.status])}>
              {task.status === 'in_progress' ? 'in progress' : task.status}
            </span>
            {task.priority && (
              <span className={clsx('text-xs font-medium', PRIORITY_COLORS[task.priority])}>
                {task.priority}
              </span>
            )}
            {task.recurrence && task.recurrence !== 'none' && (
              <span className="text-xs px-1.5 py-0.5 rounded bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300 flex items-center gap-0.5">
                <Repeat className="w-3 h-3" />{task.recurrence}
              </span>
            )}
            {task.reminder_at && (
              <Bell className="w-3 h-3 text-amber-500" />
            )}
          </div>

          <div className="flex items-center gap-3 mt-1 text-xs text-gray-400 dark:text-gray-500">
            {task.context && (
              <span className="flex items-center gap-1">
                <Tag className="w-3 h-3" />
                {task.context}
              </span>
            )}
            {task.estimated_time && (
              <span className="flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {task.estimated_time}min est.
              </span>
            )}
            {task.actual_time && (
              <span className="flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {task.actual_time}min actual
              </span>
            )}
            {task.due_date && (
              <span className={isOverdue ? 'text-red-500 font-medium' : ''}>
                Due: {new Date(task.due_date).toLocaleDateString()}
              </span>
            )}
          </div>

          {/* Tags */}
          {tags.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-1.5">
              {tags.map((tag) => (
                <span key={tag} className="text-xs px-1.5 py-0.5 rounded-full bg-charlie-50 dark:bg-charlie-900/30 text-charlie-700 dark:text-charlie-300 flex items-center gap-0.5">
                  <Tag className="w-2.5 h-2.5" />{tag}
                </span>
              ))}
            </div>
          )}

          {task.description && expanded && (
            <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">{task.description}</p>
          )}
        </div>

        <div className="flex items-center gap-1">
          {(task.description || onEdit) && (
            <button
              onClick={() => setExpanded(!expanded)}
              className="p-1 text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300"
            >
              {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </button>
          )}
        </div>
      </div>

      {/* Expanded: time input + edit */}
      {task.status !== 'done' && expanded && (
        <div className="mt-3 pt-3 border-t border-gray-100 dark:border-gray-700 flex items-center gap-2">
          <input
            type="number"
            value={actualTime}
            onChange={(e) => setActualTime(e.target.value)}
            placeholder="Actual time (min)"
            className="px-3 py-1.5 border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-700 dark:text-gray-100 rounded-lg text-xs w-36 focus:outline-none focus:ring-2 focus:ring-charlie-300"
          />
          <button
            onClick={handleQuickDone}
            disabled={completing}
            className="px-3 py-1.5 bg-green-600 text-white rounded-lg text-xs font-medium hover:bg-green-700 disabled:opacity-50"
          >
            Done
          </button>
          {onEdit && (
            <button
              onClick={() => onEdit(task)}
              className="px-3 py-1.5 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg text-xs font-medium hover:bg-gray-200 dark:hover:bg-gray-600"
            >
              Edit
            </button>
          )}
        </div>
      )}
    </div>
  );
}
