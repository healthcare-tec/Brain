import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Inbox, ArrowRight, Trash2, Sparkles, Zap, AlertCircle, GripVertical } from 'lucide-react';
import QuickCapture from '../components/QuickCapture';
import ClarifyModal from '../components/ClarifyModal';
import AISuggestionBadge from '../components/AISuggestionBadge';
import { inboxApi, aiApi } from '../services/api';

// ── Drag & Drop Target Zone ──────────────────────────────────────────────

function DropZone({ label, icon, color, onDrop, isOver }) {
  return (
    <div
      onDragOver={(e) => { e.preventDefault(); e.dataTransfer.dropEffect = 'move'; }}
      onDragEnter={(e) => e.preventDefault()}
      onDrop={onDrop}
      className={`flex-1 flex flex-col items-center justify-center py-4 rounded-xl border-2 border-dashed transition-all ${
        isOver
          ? `${color} scale-105 shadow-lg`
          : 'border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-800/50'
      }`}
    >
      <span className="text-2xl mb-1">{icon}</span>
      <span className="text-xs font-medium text-gray-600 dark:text-gray-400">{label}</span>
    </div>
  );
}

export default function InboxPage() {
  const [items, setItems] = useState([]);
  const [filter, setFilter] = useState('pending');
  const [clarifyItem, setClarifyItem] = useState(null);
  const [clarifyInitialData, setClarifyInitialData] = useState(null);
  const [loading, setLoading] = useState(true);

  // AI state
  const [aiStates, setAiStates] = useState({});
  const [autoClarifyAllRunning, setAutoClarifyAllRunning] = useState(false);
  const [autoClarifyAllProgress, setAutoClarifyAllProgress] = useState({ done: 0, total: 0 });
  const [aiStatus, setAiStatus] = useState(null);
  const aiStatusLoaded = useRef(false);

  // Drag & Drop state
  const [draggedItem, setDraggedItem] = useState(null);
  const [dropTarget, setDropTarget] = useState(null);

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
    // Let errors propagate so ClarifyModal can display them
    await inboxApi.clarify(itemId, data);
    setAiStates((prev) => { const next = { ...prev }; delete next[itemId]; return next; });
    await loadItems();
  };

  const handleDelete = async (id) => {
    await inboxApi.delete(id);
    await loadItems();
  };

  // ── AI handlers ─────────────────────────────────────────────────────────

  const handleAIClarify = async (item) => {
    setAiStates((prev) => ({ ...prev, [item.id]: { loading: true, suggestion: null } }));
    try {
      const result = await aiApi.classify(item.content);
      setAiStates((prev) => ({ ...prev, [item.id]: { loading: false, suggestion: result } }));
    } catch (err) {
      setAiStates((prev) => ({ ...prev, [item.id]: { loading: false, suggestion: { error: err.message } } }));
    }
  };

  const handleApplySuggestion = async (item, suggestion) => {
    const clarifiedAs = suggestion.category === 'idea' ? 'note' : suggestion.category;
    await handleClarify(item.id, {
      clarified_as: clarifiedAs,
      title: suggestion.suggested_title || item.content.slice(0, 200),
      context: suggestion.suggested_context || undefined,
      category: clarifiedAs === 'note' ? 'resource' : undefined,
    });
  };

  const handleEditSuggestion = (item, suggestion) => {
    setClarifyInitialData(suggestion);
    setClarifyItem(item);
  };

  const handleDismissSuggestion = (itemId) => {
    setAiStates((prev) => { const next = { ...prev }; delete next[itemId]; return next; });
  };

  const handleAutoClarifyAll = async () => {
    const pending = items.filter((i) => i.status === 'pending');
    if (pending.length === 0) return;
    setAutoClarifyAllRunning(true);
    setAutoClarifyAllProgress({ done: 0, total: pending.length });
    for (let i = 0; i < pending.length; i++) {
      const item = pending[i];
      setAiStates((prev) => ({ ...prev, [item.id]: { loading: true, suggestion: null } }));
      try {
        const result = await aiApi.classify(item.content);
        setAiStates((prev) => ({ ...prev, [item.id]: { loading: false, suggestion: result } }));
      } catch (err) {
        setAiStates((prev) => ({ ...prev, [item.id]: { loading: false, suggestion: { error: err.message } } }));
      }
      setAutoClarifyAllProgress({ done: i + 1, total: pending.length });
    }
    setAutoClarifyAllRunning(false);
  };

  // ── Drag & Drop handlers ────────────────────────────────────────────────

  const handleDragStart = (e, item) => {
    setDraggedItem(item);
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', item.id);
  };

  const handleDragEnd = () => {
    setDraggedItem(null);
    setDropTarget(null);
  };

  const handleDrop = async (category) => {
    if (!draggedItem) return;
    const clarifiedAs = category === 'idea' ? 'note' : category;
    await handleClarify(draggedItem.id, {
      clarified_as: clarifiedAs,
      title: draggedItem.content.slice(0, 200),
      category: clarifiedAs === 'note' ? 'resource' : undefined,
    });
    setDraggedItem(null);
    setDropTarget(null);
  };

  // ── Keyboard shortcut: C to clarify first pending ───────────────────────

  useEffect(() => {
    const handler = (e) => {
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
      if (e.key === 'c' || e.key === 'C') {
        const firstPending = items.find(i => i.status === 'pending');
        if (firstPending) { setClarifyInitialData(null); setClarifyItem(firstPending); }
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [items]);

  const pendingCount = items.filter((i) => i.status === 'pending').length;

  return (
    <div className="max-w-3xl mx-auto">
      {/* Page header */}
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-xl bg-charlie-100 dark:bg-charlie-900/30 flex items-center justify-center">
          <Inbox className="w-5 h-5 text-charlie-600 dark:text-charlie-400" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Inbox</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400">Capture Engine — frictionless input</p>
        </div>
        {pendingCount > 0 && (
          <span className="ml-auto px-3 py-1 bg-charlie-100 dark:bg-charlie-900/30 text-charlie-700 dark:text-charlie-300 rounded-full text-sm font-medium">
            {pendingCount} pending
          </span>
        )}
      </div>

      {/* Quick capture */}
      <div className="mb-6">
        <QuickCapture onCapture={handleCapture} placeholder="Capture anything — tasks, ideas, notes..." autoFocus />
      </div>

      {/* AI status banner */}
      {aiStatus && !aiStatus.ai_enabled && (
        <div className="mb-4 flex items-start gap-2 px-4 py-3 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-700 rounded-xl text-xs text-amber-700 dark:text-amber-300">
          <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold">IA nao configurada.</span>{' '}
            Configure <code className="bg-amber-100 dark:bg-amber-800 px-1 rounded">AI_PROVIDER=ollama</code> (Ollama local){' '}
            ou <code className="bg-amber-100 dark:bg-amber-800 px-1 rounded">OPENAI_API_KEY</code> em{' '}
            <code className="bg-amber-100 dark:bg-amber-800 px-1 rounded">.env</code> para usar classificacao inteligente.
          </div>
        </div>
      )}

      {/* Drag & Drop zones (visible when dragging) */}
      {draggedItem && (
        <div className="mb-4 grid grid-cols-4 gap-3 animate-in fade-in">
          {[
            { key: 'task', label: 'Task', icon: '✅', color: 'border-blue-400 bg-blue-50 dark:bg-blue-900/30' },
            { key: 'project', label: 'Project', icon: '📁', color: 'border-purple-400 bg-purple-50 dark:bg-purple-900/30' },
            { key: 'note', label: 'Note', icon: '📝', color: 'border-green-400 bg-green-50 dark:bg-green-900/30' },
            { key: 'trash', label: 'Trash', icon: '🗑️', color: 'border-red-400 bg-red-50 dark:bg-red-900/30' },
          ].map((zone) => (
            <DropZone
              key={zone.key}
              label={zone.label}
              icon={zone.icon}
              color={zone.color}
              isOver={dropTarget === zone.key}
              onDrop={(e) => { e.preventDefault(); handleDrop(zone.key); }}
            />
          ))}
        </div>
      )}

      {/* Filter tabs + Auto-Clarify All */}
      <div className="flex gap-2 mb-4">
        <div className="flex gap-1 flex-1 bg-gray-100 dark:bg-gray-800 rounded-lg p-1">
          {['pending', 'processed', 'trashed', 'all'].map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`flex-1 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                filter === f
                  ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 shadow-sm'
                  : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200'
              }`}
            >
              {f.charAt(0).toUpperCase() + f.slice(1)}
            </button>
          ))}
        </div>
        {filter === 'pending' && pendingCount > 0 && (
          <button
            onClick={handleAutoClarifyAll}
            disabled={autoClarifyAllRunning}
            title="Classifica todos os itens pendentes com IA"
            className="flex items-center gap-1.5 px-3 py-1.5 bg-charlie-600 text-white rounded-lg text-xs font-medium hover:bg-charlie-700 disabled:opacity-60 transition-colors whitespace-nowrap"
          >
            {autoClarifyAllRunning ? (
              <><Zap className="w-3.5 h-3.5 animate-pulse" />{autoClarifyAllProgress.done}/{autoClarifyAllProgress.total}</>
            ) : (
              <><Sparkles className="w-3.5 h-3.5" />Clarificar Todos</>
            )}
          </button>
        )}
      </div>

      {/* Items list */}
      {loading ? (
        <div className="text-center py-12 text-gray-400 dark:text-gray-500">Loading...</div>
      ) : items.length === 0 ? (
        <div className="text-center py-12">
          <Inbox className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" />
          <p className="text-gray-500 dark:text-gray-400">Inbox is empty. Capture something!</p>
        </div>
      ) : (
        <div className="space-y-2">
          {items.map((item) => {
            const aiState = aiStates[item.id] || {};
            return (
              <div
                key={item.id}
                draggable={item.status === 'pending'}
                onDragStart={(e) => handleDragStart(e, item)}
                onDragEnd={handleDragEnd}
                className={`bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4 group hover:shadow-sm transition-all ${
                  item.status === 'pending' ? 'cursor-grab active:cursor-grabbing' : ''
                } ${draggedItem?.id === item.id ? 'opacity-50' : ''}`}
              >
                <div className="flex items-center gap-3">
                  {item.status === 'pending' && (
                    <GripVertical className="w-4 h-4 text-gray-300 dark:text-gray-600 flex-shrink-0" />
                  )}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-gray-900 dark:text-gray-100 truncate">{item.content}</p>
                    <div className="flex items-center gap-2 mt-1 text-xs text-gray-400 dark:text-gray-500">
                      {item.item_type && (
                        <span className="bg-gray-100 dark:bg-gray-700 px-2 py-0.5 rounded">{item.item_type}</span>
                      )}
                      <span>{new Date(item.captured_at).toLocaleString()}</span>
                      {item.clarified_as && (
                        <span className="bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 px-2 py-0.5 rounded">
                          {item.clarified_as}
                        </span>
                      )}
                    </div>
                  </div>

                  {item.status === 'pending' && (
                    <div className="flex items-center gap-1.5 flex-shrink-0">
                      <button
                        onClick={() => handleAIClarify(item)}
                        disabled={aiState.loading}
                        title="Classificar com IA"
                        className="px-2.5 py-1.5 bg-charlie-50 dark:bg-charlie-900/30 text-charlie-700 dark:text-charlie-300 border border-charlie-200 dark:border-charlie-700 rounded-lg text-xs font-medium hover:bg-charlie-100 dark:hover:bg-charlie-900/50 disabled:opacity-50 transition-colors flex items-center gap-1"
                      >
                        <Sparkles className="w-3 h-3" />IA
                      </button>
                      <button
                        onClick={() => { setClarifyInitialData(null); setClarifyItem(item); }}
                        className="px-2.5 py-1.5 bg-gray-50 dark:bg-gray-700 text-gray-700 dark:text-gray-300 border border-gray-200 dark:border-gray-600 rounded-lg text-xs font-medium hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors flex items-center gap-1"
                      >
                        <ArrowRight className="w-3 h-3" />Manual
                      </button>
                    </div>
                  )}

                  <button
                    onClick={() => handleDelete(item.id)}
                    className="p-1.5 text-gray-300 dark:text-gray-600 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-all flex-shrink-0"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>

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
