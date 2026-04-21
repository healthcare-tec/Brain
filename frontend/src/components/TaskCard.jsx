import React, { useState } from 'react';
import { Check, Clock, Tag, ChevronDown, ChevronUp } from 'lucide-react';
import clsx from 'clsx';

const STATUS_COLORS = {
  next: 'bg-blue-100 text-blue-700',
  waiting: 'bg-yellow-100 text-yellow-700',
  someday: 'bg-gray-100 text-gray-600',
  done: 'bg-green-100 text-green-700',
};

const PRIORITY_COLORS = {
  low: 'text-gray-400',
  medium: 'text-blue-500',
  high: 'text-orange-500',
  critical: 'text-red-600',
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

  return (
    <div className={clsx(
      'bg-white rounded-xl border border-gray-200 p-4 transition-shadow hover:shadow-sm',
      task.status === 'done' && 'opacity-60'
    )}>
      <div className="flex items-start gap-3">
        {/* Done button */}
        {task.status !== 'done' && (
          <button
            onClick={handleQuickDone}
            disabled={completing}
            className="mt-0.5 w-6 h-6 rounded-full border-2 border-gray-300 hover:border-charlie-500 hover:bg-charlie-50 flex items-center justify-center transition-colors flex-shrink-0"
            title="Mark as Done"
          >
            {completing ? (
              <div className="w-3 h-3 border-2 border-charlie-500 border-t-transparent rounded-full animate-spin" />
            ) : (
              <Check className="w-3 h-3 text-transparent hover:text-charlie-500" />
            )}
          </button>
        )}
        {task.status === 'done' && (
          <div className="mt-0.5 w-6 h-6 rounded-full bg-green-500 flex items-center justify-center flex-shrink-0">
            <Check className="w-3 h-3 text-white" />
          </div>
        )}

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <h3 className={clsx(
              'text-sm font-medium',
              task.status === 'done' ? 'line-through text-gray-400' : 'text-gray-900'
            )}>
              {task.title}
            </h3>
            <span className={clsx('text-xs px-2 py-0.5 rounded-full font-medium', STATUS_COLORS[task.status])}>
              {task.status}
            </span>
            <span className={clsx('text-xs font-medium', PRIORITY_COLORS[task.priority])}>
              {task.priority}
            </span>
          </div>

          <div className="flex items-center gap-3 mt-1 text-xs text-gray-400">
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
          </div>

          {task.description && expanded && (
            <p className="mt-2 text-xs text-gray-500">{task.description}</p>
          )}
        </div>

        <div className="flex items-center gap-1">
          {task.description && (
            <button
              onClick={() => setExpanded(!expanded)}
              className="p-1 text-gray-400 hover:text-gray-600"
            >
              {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </button>
          )}
        </div>
      </div>

      {/* Quick time input when completing */}
      {task.status !== 'done' && expanded && (
        <div className="mt-3 pt-3 border-t border-gray-100 flex items-center gap-2">
          <input
            type="number"
            value={actualTime}
            onChange={(e) => setActualTime(e.target.value)}
            placeholder="Actual time (min)"
            className="px-3 py-1.5 border border-gray-200 rounded-lg text-xs w-36 focus:outline-none focus:ring-2 focus:ring-charlie-300"
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
              className="px-3 py-1.5 bg-gray-100 text-gray-700 rounded-lg text-xs font-medium hover:bg-gray-200"
            >
              Edit
            </button>
          )}
        </div>
      )}
    </div>
  );
}
