import React, { useState, useEffect, useCallback } from 'react';
import { Inbox, ArrowRight, Trash2 } from 'lucide-react';
import QuickCapture from '../components/QuickCapture';
import ClarifyModal from '../components/ClarifyModal';
import { inboxApi } from '../services/api';

export default function InboxPage() {
  const [items, setItems] = useState([]);
  const [filter, setFilter] = useState('pending');
  const [clarifyItem, setClarifyItem] = useState(null);
  const [loading, setLoading] = useState(true);

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

  const handleCapture = async (content) => {
    await inboxApi.capture({ content });
    await loadItems();
  };

  const handleClarify = async (itemId, data) => {
    await inboxApi.clarify(itemId, data);
    await loadItems();
  };

  const handleDelete = async (id) => {
    await inboxApi.delete(id);
    await loadItems();
  };

  const pendingCount = items.filter((i) => i.status === 'pending').length;

  return (
    <div className="max-w-3xl mx-auto">
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

      {/* Filter tabs */}
      <div className="flex gap-1 mb-4 bg-gray-100 rounded-lg p-1">
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
          {items.map((item) => (
            <div
              key={item.id}
              className="bg-white rounded-xl border border-gray-200 p-4 flex items-center gap-3 group hover:shadow-sm transition-shadow"
            >
              <div className="flex-1 min-w-0">
                <p className="text-sm text-gray-900 truncate">{item.content}</p>
                <div className="flex items-center gap-2 mt-1 text-xs text-gray-400">
                  {item.item_type && <span className="bg-gray-100 px-2 py-0.5 rounded">{item.item_type}</span>}
                  <span>{new Date(item.captured_at).toLocaleString()}</span>
                  {item.clarified_as && (
                    <span className="bg-green-100 text-green-700 px-2 py-0.5 rounded">{item.clarified_as}</span>
                  )}
                </div>
              </div>

              {item.status === 'pending' && (
                <button
                  onClick={() => setClarifyItem(item)}
                  className="px-3 py-1.5 bg-charlie-50 text-charlie-700 rounded-lg text-xs font-medium hover:bg-charlie-100 transition-colors flex items-center gap-1"
                >
                  <ArrowRight className="w-3 h-3" />
                  Clarify
                </button>
              )}

              <button
                onClick={() => handleDelete(item.id)}
                className="p-1.5 text-gray-300 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-all"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Clarify modal */}
      {clarifyItem && (
        <ClarifyModal
          item={clarifyItem}
          onClarify={handleClarify}
          onClose={() => setClarifyItem(null)}
        />
      )}
    </div>
  );
}
