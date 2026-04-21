/**
 * AISuggestionBadge — Shows AI classification result inline with dark mode support.
 */
import React from 'react';
import {
  Sparkles, CheckCircle, AlertCircle, Loader2, X,
  CheckSquare, FolderKanban, FileText, Trash2, Lightbulb,
  Clock, Tag, MapPin,
} from 'lucide-react';

const CATEGORY_STYLES = {
  task:    { icon: CheckSquare,  bg: 'bg-blue-50 dark:bg-blue-900/20',   border: 'border-blue-200 dark:border-blue-800',   badge: 'bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300',   label: 'Task'    },
  project: { icon: FolderKanban, bg: 'bg-purple-50 dark:bg-purple-900/20', border: 'border-purple-200 dark:border-purple-800', badge: 'bg-purple-100 dark:bg-purple-900/40 text-purple-700 dark:text-purple-300', label: 'Project' },
  note:    { icon: FileText,     bg: 'bg-green-50 dark:bg-green-900/20',  border: 'border-green-200 dark:border-green-800',  badge: 'bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-300',  label: 'Note'    },
  idea:    { icon: Lightbulb,    bg: 'bg-yellow-50 dark:bg-yellow-900/20', border: 'border-yellow-200 dark:border-yellow-800', badge: 'bg-yellow-100 dark:bg-yellow-900/40 text-yellow-700 dark:text-yellow-300', label: 'Idea'    },
  trash:   { icon: Trash2,       bg: 'bg-red-50 dark:bg-red-900/20',    border: 'border-red-200 dark:border-red-800',    badge: 'bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-300',      label: 'Trash'   },
};

const PRIORITY_COLORS = {
  low:      'text-gray-500 dark:text-gray-400',
  medium:   'text-yellow-600 dark:text-yellow-400',
  high:     'text-orange-600 dark:text-orange-400',
  critical: 'text-red-600 dark:text-red-400',
};

function ConfidenceBar({ value }) {
  const pct = Math.round((value || 0) * 100);
  const color = pct >= 80 ? 'bg-green-400' : pct >= 60 ? 'bg-yellow-400' : 'bg-red-400';
  return (
    <div className="flex items-center gap-1.5">
      <div className="h-1.5 w-16 bg-gray-200 dark:bg-gray-600 rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-gray-400 dark:text-gray-500">{pct}%</span>
    </div>
  );
}

export default function AISuggestionBadge({ suggestion, loading, onApply, onEdit, onDismiss }) {
  if (loading) {
    return (
      <div className="mt-2 flex items-center gap-2 px-3 py-2 bg-charlie-50 dark:bg-charlie-900/20 border border-charlie-200 dark:border-charlie-800 rounded-lg text-xs text-charlie-600 dark:text-charlie-400">
        <Loader2 className="w-3.5 h-3.5 animate-spin" />
        <span>Analyzing with AI...</span>
      </div>
    );
  }

  if (!suggestion) return null;

  if (suggestion.error && !suggestion.category) {
    return (
      <div className="mt-2 flex items-center gap-2 px-3 py-2 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-xs text-red-600 dark:text-red-400">
        <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" />
        <span>AI Error: {suggestion.error}</span>
        <button onClick={onDismiss} className="ml-auto text-red-400 hover:text-red-600"><X className="w-3.5 h-3.5" /></button>
      </div>
    );
  }

  if (suggestion.ai_enabled === false && suggestion.reasoning?.includes('OPENAI_API_KEY')) {
    return (
      <div className="mt-2 px-3 py-2 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg text-xs">
        <div className="flex items-start gap-2">
          <AlertCircle className="w-3.5 h-3.5 text-amber-500 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="font-medium text-amber-700 dark:text-amber-400">AI not configured</p>
            <p className="text-amber-600 dark:text-amber-500 mt-0.5">
              Add your <code className="bg-amber-100 dark:bg-amber-900/40 px-1 rounded">OPENAI_API_KEY</code> to{' '}
              <code className="bg-amber-100 dark:bg-amber-900/40 px-1 rounded">backend/.env</code>
            </p>
            <p className="text-amber-500 dark:text-amber-600 mt-1">Heuristic suggestion: <strong>{suggestion.category}</strong></p>
          </div>
          <button onClick={onDismiss} className="text-amber-400 hover:text-amber-600 flex-shrink-0"><X className="w-3.5 h-3.5" /></button>
        </div>
      </div>
    );
  }

  const style = CATEGORY_STYLES[suggestion.category] || CATEGORY_STYLES.note;
  const CategoryIcon = style.icon;

  return (
    <div className={`mt-2 p-3 ${style.bg} border ${style.border} rounded-lg text-xs`}>
      <div className="flex items-center gap-2 mb-2">
        <Sparkles className="w-3.5 h-3.5 text-charlie-500 flex-shrink-0" />
        <span className="font-semibold text-gray-700 dark:text-gray-300">AI Suggestion</span>
        {suggestion.ai_enabled && (
          <span className="ml-1 px-1.5 py-0.5 bg-charlie-100 dark:bg-charlie-900/40 text-charlie-600 dark:text-charlie-400 rounded text-[10px] font-medium">GPT</span>
        )}
        <ConfidenceBar value={suggestion.confidence} />
        <button onClick={onDismiss} className="ml-auto text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300"><X className="w-3.5 h-3.5" /></button>
      </div>

      <div className="flex items-start gap-2 mb-2">
        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full font-medium ${style.badge}`}>
          <CategoryIcon className="w-3 h-3" />{style.label}
        </span>
        {suggestion.suggested_title && <span className="text-gray-700 dark:text-gray-300 font-medium leading-tight">{suggestion.suggested_title}</span>}
      </div>

      <div className="flex flex-wrap gap-2 mb-2">
        {suggestion.suggested_context && <span className="inline-flex items-center gap-1 text-gray-500 dark:text-gray-400"><MapPin className="w-3 h-3" />{suggestion.suggested_context}</span>}
        {suggestion.suggested_priority && <span className={`inline-flex items-center gap-1 font-medium ${PRIORITY_COLORS[suggestion.suggested_priority] || 'text-gray-500'}`}><Tag className="w-3 h-3" />{suggestion.suggested_priority}</span>}
        {suggestion.estimated_minutes && <span className="inline-flex items-center gap-1 text-gray-500 dark:text-gray-400"><Clock className="w-3 h-3" />~{suggestion.estimated_minutes}min</span>}
        {suggestion.is_time_sensitive && <span className="px-1.5 py-0.5 bg-red-100 dark:bg-red-900/40 text-red-600 dark:text-red-400 rounded font-medium">urgent</span>}
      </div>

      {suggestion.reasoning && <p className="text-gray-500 dark:text-gray-400 italic mb-2 leading-relaxed">{suggestion.reasoning}</p>}

      <div className="flex gap-2 mt-2">
        <button onClick={() => onApply(suggestion)}
          className="flex-1 flex items-center justify-center gap-1.5 py-1.5 bg-charlie-600 text-white rounded-lg font-medium hover:bg-charlie-700 transition-colors">
          <CheckCircle className="w-3.5 h-3.5" />Apply
        </button>
        <button onClick={() => onEdit(suggestion)}
          className="flex-1 flex items-center justify-center gap-1.5 py-1.5 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg font-medium hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors">
          Edit first
        </button>
      </div>
    </div>
  );
}
