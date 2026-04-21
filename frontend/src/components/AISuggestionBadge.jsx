/**
 * AISuggestionBadge
 *
 * Shows the AI classification result inline on an inbox item.
 * Displays category, confidence, suggested title, context, priority,
 * estimated time, and reasoning.
 *
 * Props:
 *   suggestion  — the AI classify response object (or null)
 *   loading     — boolean, show spinner while AI is processing
 *   onApply     — callback(suggestion) when user confirms the suggestion
 *   onEdit      — callback(suggestion) to open ClarifyModal pre-filled
 *   onDismiss   — callback() to hide the suggestion
 */

import React from 'react';
import {
  Sparkles, CheckCircle, AlertCircle, Loader2, X,
  CheckSquare, FolderKanban, FileText, Trash2, Lightbulb,
  Clock, Tag, MapPin,
} from 'lucide-react';

const CATEGORY_STYLES = {
  task:    { icon: CheckSquare,  bg: 'bg-blue-50',   border: 'border-blue-200',   badge: 'bg-blue-100 text-blue-700',   label: 'Task'    },
  project: { icon: FolderKanban, bg: 'bg-purple-50', border: 'border-purple-200', badge: 'bg-purple-100 text-purple-700', label: 'Project' },
  note:    { icon: FileText,     bg: 'bg-green-50',  border: 'border-green-200',  badge: 'bg-green-100 text-green-700',  label: 'Note'    },
  idea:    { icon: Lightbulb,    bg: 'bg-yellow-50', border: 'border-yellow-200', badge: 'bg-yellow-100 text-yellow-700', label: 'Idea'    },
  trash:   { icon: Trash2,       bg: 'bg-red-50',    border: 'border-red-200',    badge: 'bg-red-100 text-red-700',      label: 'Trash'   },
};

const PRIORITY_COLORS = {
  low:      'text-gray-500',
  medium:   'text-yellow-600',
  high:     'text-orange-600',
  critical: 'text-red-600',
};

function ConfidenceBar({ value }) {
  const pct = Math.round((value || 0) * 100);
  const color = pct >= 80 ? 'bg-green-400' : pct >= 60 ? 'bg-yellow-400' : 'bg-red-400';
  return (
    <div className="flex items-center gap-1.5">
      <div className="h-1.5 w-16 bg-gray-200 rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-gray-400">{pct}%</span>
    </div>
  );
}

export default function AISuggestionBadge({ suggestion, loading, onApply, onEdit, onDismiss }) {
  // Loading state
  if (loading) {
    return (
      <div className="mt-2 flex items-center gap-2 px-3 py-2 bg-charlie-50 border border-charlie-200 rounded-lg text-xs text-charlie-600">
        <Loader2 className="w-3.5 h-3.5 animate-spin" />
        <span>Analisando com IA...</span>
      </div>
    );
  }

  if (!suggestion) return null;

  // Error state
  if (suggestion.error && !suggestion.category) {
    return (
      <div className="mt-2 flex items-center gap-2 px-3 py-2 bg-red-50 border border-red-200 rounded-lg text-xs text-red-600">
        <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" />
        <span>Erro na IA: {suggestion.error}</span>
        <button onClick={onDismiss} className="ml-auto text-red-400 hover:text-red-600">
          <X className="w-3.5 h-3.5" />
        </button>
      </div>
    );
  }

  // AI not configured
  if (suggestion.ai_enabled === false && suggestion.reasoning?.includes('OPENAI_API_KEY')) {
    return (
      <div className="mt-2 px-3 py-2 bg-amber-50 border border-amber-200 rounded-lg text-xs">
        <div className="flex items-start gap-2">
          <AlertCircle className="w-3.5 h-3.5 text-amber-500 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="font-medium text-amber-700">IA não configurada</p>
            <p className="text-amber-600 mt-0.5">
              Adicione sua <code className="bg-amber-100 px-1 rounded">OPENAI_API_KEY</code> em{' '}
              <code className="bg-amber-100 px-1 rounded">backend/.env</code> para usar classificação inteligente.
            </p>
            <p className="text-amber-500 mt-1">
              Sugestão heurística: <strong>{suggestion.category}</strong>
            </p>
          </div>
          <button onClick={onDismiss} className="text-amber-400 hover:text-amber-600 flex-shrink-0">
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    );
  }

  const style = CATEGORY_STYLES[suggestion.category] || CATEGORY_STYLES.note;
  const CategoryIcon = style.icon;

  return (
    <div className={`mt-2 p-3 ${style.bg} border ${style.border} rounded-lg text-xs`}>
      {/* Header row */}
      <div className="flex items-center gap-2 mb-2">
        <Sparkles className="w-3.5 h-3.5 text-charlie-500 flex-shrink-0" />
        <span className="font-semibold text-gray-700">Sugestão da IA</span>
        {suggestion.ai_enabled && (
          <span className="ml-1 px-1.5 py-0.5 bg-charlie-100 text-charlie-600 rounded text-[10px] font-medium">
            GPT
          </span>
        )}
        <ConfidenceBar value={suggestion.confidence} />
        <button onClick={onDismiss} className="ml-auto text-gray-400 hover:text-gray-600">
          <X className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Category + title */}
      <div className="flex items-start gap-2 mb-2">
        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full font-medium ${style.badge}`}>
          <CategoryIcon className="w-3 h-3" />
          {style.label}
        </span>
        {suggestion.suggested_title && (
          <span className="text-gray-700 font-medium leading-tight">{suggestion.suggested_title}</span>
        )}
      </div>

      {/* Metadata row */}
      <div className="flex flex-wrap gap-2 mb-2">
        {suggestion.suggested_context && (
          <span className="inline-flex items-center gap-1 text-gray-500">
            <MapPin className="w-3 h-3" />
            {suggestion.suggested_context}
          </span>
        )}
        {suggestion.suggested_priority && (
          <span className={`inline-flex items-center gap-1 font-medium ${PRIORITY_COLORS[suggestion.suggested_priority] || 'text-gray-500'}`}>
            <Tag className="w-3 h-3" />
            {suggestion.suggested_priority}
          </span>
        )}
        {suggestion.estimated_minutes && (
          <span className="inline-flex items-center gap-1 text-gray-500">
            <Clock className="w-3 h-3" />
            ~{suggestion.estimated_minutes}min
          </span>
        )}
        {suggestion.is_time_sensitive && (
          <span className="px-1.5 py-0.5 bg-red-100 text-red-600 rounded font-medium">
            ⚡ urgente
          </span>
        )}
      </div>

      {/* Reasoning */}
      {suggestion.reasoning && (
        <p className="text-gray-500 italic mb-2 leading-relaxed">{suggestion.reasoning}</p>
      )}

      {/* Action buttons */}
      <div className="flex gap-2 mt-2">
        <button
          onClick={() => onApply(suggestion)}
          className="flex-1 flex items-center justify-center gap-1.5 py-1.5 bg-charlie-600 text-white rounded-lg font-medium hover:bg-charlie-700 transition-colors"
        >
          <CheckCircle className="w-3.5 h-3.5" />
          Aplicar sugestão
        </button>
        <button
          onClick={() => onEdit(suggestion)}
          className="flex-1 flex items-center justify-center gap-1.5 py-1.5 bg-white border border-gray-200 text-gray-700 rounded-lg font-medium hover:bg-gray-50 transition-colors"
        >
          Editar antes
        </button>
      </div>
    </div>
  );
}
