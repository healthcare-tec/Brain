import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Inbox, ArrowRight, Trash2, Sparkles, Zap, AlertCircle } from 'lucide-react';
import QuickCapture from '../components/QuickCapture';
import ClarifyModal from '../components/ClarifyModal';
import AISuggestionBadge from '../components/AISuggestionBadge';
import { inboxApi, aiApi } from '../services/api';

export default function InboxPage() {
  const [items, setItems] = useState([]);
  const [filter, setFilter] = useState('pending');
  const [clarifyItem, setClarifyItem] = useState(null);
  const [clarifyInitialData, setClarifyInitialData] = useState(null);
  const [loading, setLoading] = useState(true);

  // AI state: { [itemId]: { loading, suggestion, error } }
  const [aiStates, setAiStates] = useState({});

  // Auto-Clarify All state
  const [autoClarifyAllRunning, setAutoClarifyAllRunning] = useState(false);
  const [autoClarifyAllProgress, setAutoClarifyAllProgress] = useState({ done: 0, total: 0 });

  // AI status (is the API key configured?)
  const [aiStatus, setAiStatus] = useState(null);
  const aiStatusLoaded = useRef(false);

  // ── Data loading ────────────────────────────────────────────────────────

  const loadItems = useCallback(async () => {
    setLoading(true);
    try {
      const data = await inboxApi.list(filter !== 'all' ? filter : undefined);
      setItems(data);
    } catch (err) {
      console.error('Failed to load inbox:', err);
    } finally {
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => { loadItems(); }, [loadItems]);

  // Load AI status once
  useEffect(() => {
    if (aiStatusLoaded.current) return;
    aiStatusLoaded.current = true;
    aiApi.status().then(setAiStatus).catch(() => setAiStatus({ ai_enabled: false }));
  }, []);

  // ── Handlers ────────────────────────────────────────────────────────────

  const handleCapture = async (content) => {
    await inboxApi.capture({ content });
    await loadItems();
  };

  const handleClarify = async (itemId, data) => {
    await inboxApi.clarify(itemId, data);
    // Clear AI suggestion for this item
    setAiStates((prev) => {
      const next = { ...prev };
      delete next[itemId];
      return next;
    });
    await loadItems();
  };

  const handleDelete = async (id) => {
    await inboxApi.delete(id);
    await loadItems();
  };

  // ── AI: classify a single item ──────────────────────────────────────────

  const handleAIClarify = async (item) => {
    setAiStates((prev) => ({
      ...prev,
      [item.id]: { loading: true, suggestion: null },
    }));
    try {
      const result = await aiApi.classify(item.content);
      setAiStates((prev) => ({
        ...prev,
        [item.id]: { loading: false, suggestion: result },
      }));
    } catch (err) {
      setAiStates((prev) => ({
        ...prev,
        [item.id]: { loading: false, suggestion: { error: err.message } },
      }));
    }
  };

  // ── AI: apply suggestion directly (skip modal) ──────────────────────────

  const handleApplySuggestion = async (item, suggestion) => {
    // Map AI category → clarified_as (idea → note for storage)
    const clarifiedAs = suggestion.category === 'idea' ? 'note' : suggestion.category;
    await handleClarify(item.id, {
      clarified_as: clarifiedAs,
      title: suggestion.suggested_title || item.content.slice(0, 200),
      context: suggestion.suggested_context || undefined,
      category: clarifiedAs === 'note' ? 'resource' : undefined,
    });
  };

  // ── AI: open modal pre-filled with suggestion ───────────────────────────

  const handleEditSuggestion = (item, suggestion) => {
    setClarifyInitialData(suggestion);
    setClarifyItem(item);
  };

  // ── AI: dismiss suggestion ──────────────────────────────────────────────

  const handleDismissSuggestion = (itemId) => {
    setAiStates((prev) => {
      const next = { ...prev };
      delete next[itemId];
      return next;
    });
  };

  // ── AI: Auto-Clarify All ────────────────────────────────────────────────

  const handleAutoClarifyAll = async () => {
    const pending = items.filter((i) => i.status === 'pending');
    if (pending.length === 0) return;

    setAutoClarifyAllRunning(true);
    setAutoClarifyAllProgress({ done: 0, total: pending.length });

    for (let i = 0; i < pending.length; i++) {
      const item = pending[i];
      setAiStates((prev) => ({
        ...prev,
        [item.id]: { loading: true, suggestion: null },
      }));
      try {
        const result = await aiApi.classify(item.content);
        setAiStates((prev) => ({
          ...prev,
          [item.id]: { loading: false, suggestion: result },
        }));
      } catch (err) {
        setAiStates((prev) => ({
          ...prev,
          [item.id]: { loading: false, suggestion: { error: err.message } },
        }));
      }
      setAutoClarifyAllProgress({ done: i + 1, total: pending.length });
    }

    setAutoClarifyAllRunning(false);
  };

  // ── Derived state ───────────────────────────────────────────────────────

  const pendingCount = items.filter((i) => i.status === 'pending').length;
  const pendingItems = items.filter((i) => i.status === 'pending');

  return (
    <div className="max-w-3xl mx-auto">
      {/* Page header */}
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-xl bg-charlie-100 flex items-center justify-center">
          <Inbox className="w-5 h-5 text-charlie-600" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Inbox</h1>
          <p className="text-sm text-gray-500">Capture Engine — frictionless input</p>
        </div>
        {pendingCount > 0 && (
          <span className="ml-auto px-3 py-1 bg-charlie-100 text-charlie-700 rounded-full text-sm font-medium">
            {pendingCount} pending
          </span>
        )}
      </div>

      {/* Quick capture */}
      <div className="mb-6">
        <QuickCapture onCapture={handleCapture} placeholder="Capture anything — tasks, ideas, notes..." autoFocus />
      </div>

      {/* AI status banner (only when not configured) */}
      {aiStatus && !aiStatus.ai_enabled && (
        <div className="mb-4 flex items-start gap-2 px-4 py-3 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-700">
          <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold">IA não configurada.</span>{' '}
            Adicione <code className="bg-amber-100 px-1 rounded">OPENAI_API_KEY</code> em{' '}
            <code className="bg-amber-100 px-1 rounded">backend/.env</code> para usar classificação inteligente.
            Os botões de IA ainda funcionam com heurísticas.
          </div>
        </div>
      )}

      {/* Filter tabs + Auto-Clarify All button */}
      <div className="flex gap-2 mb-4">
        <div className="flex gap-1 flex-1 bg-gray-100 rounded-lg p-1">
          {['pending', 'processed', 'trashed', 'all'].map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`flex-1 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                filter === f ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              {f.charAt(0).toUpperCase() + f.slice(1)}
            </button>
          ))}
        </div>

        {/* Auto-Clarify All button */}
        {filter === 'pending' && pendingCount > 0 && (
          <button
            onClick={handleAutoClarifyAll}
            disabled={autoClarifyAllRunning}
            title="Classifica todos os itens pendentes com IA de uma vez"
            className="flex items-center gap-1.5 px-3 py-1.5 bg-charlie-600 text-white rounded-lg text-xs font-medium hover:bg-charlie-700 disabled:opacity-60 transition-colors whitespace-nowrap"
          >
            {autoClarifyAllRunning ? (
              <>
                <Zap className="w-3.5 h-3.5 animate-pulse" />
                {autoClarifyAllProgress.done}/{autoClarifyAllProgress.total}
              </>
            ) : (
              <>
                <Sparkles className="w-3.5 h-3.5" />
                🧠 Clarificar Todos
              </>
            )}
          </button>
        )}
      </div>

      {/* Items list */}
      {loading ? (
        <div className="text-center py-12 text-gray-400">Loading...</div>
      ) : items.length === 0 ? (
        <div className="text-center py-12">
          <Inbox className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500">Inbox is empty. Capture something!</p>
        </div>
      ) : (
        <div className="space-y-2">
          {items.map((item) => {
            const aiState = aiStates[item.id] || {};
            return (
              <div
                key={item.id}
                className="bg-white rounded-xl border border-gray-200 p-4 group hover:shadow-sm transition-shadow"
              >
                {/* Item row */}
                <div className="flex items-center gap-3">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-gray-900 truncate">{item.content}</p>
                    <div className="flex items-center gap-2 mt-1 text-xs text-gray-400">
                      {item.item_type && (
                        <span className="bg-gray-100 px-2 py-0.5 rounded">{item.item_type}</span>
                      )}
                      <span>{new Date(item.captured_at).toLocaleString()}</span>
                      {item.clarified_as && (
                        <span className="bg-green-100 text-green-700 px-2 py-0.5 rounded">
                          {item.clarified_as}
                        </span>
                      )}
                    </div>
                  </div>

                  {item.status === 'pending' && (
                    <div className="flex items-center gap-1.5 flex-shrink-0">
                      {/* 🧠 AI Clarify button */}
                      <button
                        onClick={() => handleAIClarify(item)}
                        disabled={aiState.loading}
                        title="Classificar com IA"
                        className="px-2.5 py-1.5 bg-charlie-50 text-charlie-700 border border-charlie-200 rounded-lg text-xs font-medium hover:bg-charlie-100 disabled:opacity-50 transition-colors flex items-center gap-1"
                      >
                        <Sparkles className="w-3 h-3" />
                        🧠 IA
                      </button>

                      {/* Manual Clarify button */}
                      <button
                        onClick={() => { setClarifyInitialData(null); setClarifyItem(item); }}
                        className="px-2.5 py-1.5 bg-gray-50 text-gray-700 border border-gray-200 rounded-lg text-xs font-medium hover:bg-gray-100 transition-colors flex items-center gap-1"
                      >
                        <ArrowRight className="w-3 h-3" />
                        Manual
                      </button>
                    </div>
                  )}

                  <button
                    onClick={() => handleDelete(item.id)}
                    className="p-1.5 text-gray-300 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-all flex-shrink-0"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>

                {/* AI Suggestion Badge (shown below the item row) */}
                {(aiState.loading || aiState.suggestion) && (
                  <AISuggestionBadge
                    suggestion={aiState.suggestion}
                    loading={aiState.loading}
                    onApply={(s) => handleApplySuggestion(item, s)}
                    onEdit={(s) => handleEditSuggestion(item, s)}
                    onDismiss={() => handleDismissSuggestion(item.id)}
                  />
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Clarify modal */}
      {clarifyItem && (
        <ClarifyModal
          item={clarifyItem}
          initialData={clarifyInitialData}
          onClarify={handleClarify}
          onClose={() => { setClarifyItem(null); setClarifyInitialData(null); }}
        />
      )}
    </div>
  );
}
