import React, { useState, useEffect } from 'react';
import { BarChart3, RefreshCw, Inbox, CheckSquare, FolderKanban, Clock, Activity } from 'lucide-react';
import { reviewsApi } from '../services/api';

export default function ReviewPage() {
  const [review, setReview] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadReview = async () => {
    setLoading(true);
    try { setReview(await reviewsApi.weekly()); } catch (err) { console.error(err); } finally { setLoading(false); }
  };

  useEffect(() => { loadReview(); }, []);

  const cards = review ? [
    { label: 'Pending Inbox', value: review.pending_inbox, icon: Inbox, bg: 'bg-yellow-100 dark:bg-yellow-900/30', iconColor: 'text-yellow-600 dark:text-yellow-400' },
    { label: 'Completed Tasks', value: review.completed_tasks, icon: CheckSquare, bg: 'bg-green-100 dark:bg-green-900/30', iconColor: 'text-green-600 dark:text-green-400' },
    { label: 'Next Actions', value: review.next_actions, icon: Activity, bg: 'bg-blue-100 dark:bg-blue-900/30', iconColor: 'text-blue-600 dark:text-blue-400' },
    { label: 'Waiting For', value: review.waiting_tasks, icon: Clock, bg: 'bg-orange-100 dark:bg-orange-900/30', iconColor: 'text-orange-600 dark:text-orange-400' },
    { label: 'Active Projects', value: review.active_projects, icon: FolderKanban, bg: 'bg-purple-100 dark:bg-purple-900/30', iconColor: 'text-purple-600 dark:text-purple-400' },
    { label: 'Total Events', value: review.total_events, icon: Activity, bg: 'bg-gray-100 dark:bg-gray-700', iconColor: 'text-gray-600 dark:text-gray-400' },
  ] : [];

  return (
    <div className="max-w-4xl mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-xl bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center">
          <BarChart3 className="w-5 h-5 text-amber-600 dark:text-amber-400" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Weekly Review</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400">Feedback System — reflect and improve</p>
        </div>
        <button onClick={loadReview}
          className="ml-auto px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-xl text-sm font-medium hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors flex items-center gap-2">
          <RefreshCw className="w-4 h-4" /> Refresh
        </button>
      </div>

      {loading ? (
        <div className="text-center py-12 text-gray-400 dark:text-gray-500">Loading review data...</div>
      ) : !review ? (
        <div className="text-center py-12 text-gray-400 dark:text-gray-500">Failed to load review data.</div>
      ) : (
        <>
          <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4 mb-6">
            <p className="text-sm text-gray-600 dark:text-gray-400">
              <span className="font-medium">Period:</span>{' '}
              {new Date(review.from_date).toLocaleDateString()} — {new Date(review.to_date).toLocaleDateString()}
            </p>
          </div>

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 mb-6">
            {cards.map(({ label, value, icon: Icon, bg, iconColor }) => (
              <div key={label} className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
                <div className="flex items-center gap-3 mb-2">
                  <div className={`w-9 h-9 rounded-lg ${bg} flex items-center justify-center`}>
                    <Icon className={`w-5 h-5 ${iconColor}`} />
                  </div>
                  <span className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide">{label}</span>
                </div>
                <p className="text-3xl font-bold text-gray-900 dark:text-gray-100">{value}</p>
              </div>
            ))}
          </div>

          {review.estimation_accuracy_pct !== null && (
            <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5 mb-6">
              <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-2">Time Estimation Accuracy</h3>
              <div className="flex items-center gap-4">
                <div className="flex-1 bg-gray-100 dark:bg-gray-700 rounded-full h-3 overflow-hidden">
                  <div className="bg-charlie-500 h-full rounded-full transition-all" style={{ width: `${Math.min(review.estimation_accuracy_pct, 100)}%` }} />
                </div>
                <span className="text-lg font-bold text-gray-900 dark:text-gray-100">{review.estimation_accuracy_pct}%</span>
              </div>
              <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">100% = perfect estimation.</p>
            </div>
          )}

          <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
            <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-3">Review Checklist</h3>
            <div className="space-y-2">
              {[
                { text: 'Clear inbox (process all pending items)', done: review.pending_inbox === 0 },
                { text: 'Review and update all active tasks', done: false },
                { text: 'Check project progress', done: false },
                { text: 'Validate next actions are current', done: review.next_actions > 0 },
                { text: 'Review completed tasks for learnings', done: review.completed_tasks > 0 },
              ].map(({ text, done }, i) => (
                <label key={i} className="flex items-center gap-3 p-2 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer">
                  <input type="checkbox" defaultChecked={done} className="w-4 h-4 rounded border-gray-300 dark:border-gray-600 text-charlie-600 focus:ring-charlie-500" />
                  <span className="text-sm text-gray-700 dark:text-gray-300">{text}</span>
                </label>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
