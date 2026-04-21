import React, { useState, useEffect } from 'react';
import {
  Lightbulb, AlertTriangle, AlertCircle, Info, Clock,
  TrendingDown, RefreshCw, Sparkles,
} from 'lucide-react';
import { insightsApi } from '../services/api';

const SEVERITY_STYLES = {
  critical: {
    bg: 'bg-red-50 dark:bg-red-900/20',
    border: 'border-red-200 dark:border-red-700',
    icon: AlertCircle,
    iconColor: 'text-red-500',
    badge: 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300',
  },
  warning: {
    bg: 'bg-amber-50 dark:bg-amber-900/20',
    border: 'border-amber-200 dark:border-amber-700',
    icon: AlertTriangle,
    iconColor: 'text-amber-500',
    badge: 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300',
  },
  info: {
    bg: 'bg-blue-50 dark:bg-blue-900/20',
    border: 'border-blue-200 dark:border-blue-700',
    icon: Info,
    iconColor: 'text-blue-500',
    badge: 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300',
  },
};

export default function InsightsPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const result = await insightsApi.get();
      setData(result);
    } catch (err) {
      console.error('Failed to load insights:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  return (
    <div className="max-w-3xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-xl bg-violet-100 dark:bg-violet-900/30 flex items-center justify-center">
          <Lightbulb className="w-5 h-5 text-violet-600 dark:text-violet-400" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">AI Insights</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400">Proactive analysis of your productivity patterns</p>
        </div>
        <button
          onClick={load}
          disabled={loading}
          className="ml-auto px-3 py-2 bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 rounded-xl text-sm hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors flex items-center gap-1.5"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {loading ? (
        <div className="text-center py-12 text-gray-400 dark:text-gray-500">Analyzing your data...</div>
      ) : !data ? (
        <div className="text-center py-12 text-gray-400 dark:text-gray-500">Failed to load insights</div>
      ) : (
        <>
          {/* Summary stats */}
          <div className="grid grid-cols-4 gap-3 mb-6">
            <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-3 text-center">
              <p className="text-lg font-bold text-gray-900 dark:text-gray-100">{data.raw_data?.stale_count || 0}</p>
              <p className="text-xs text-gray-500 dark:text-gray-400">Stale Tasks</p>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-3 text-center">
              <p className="text-lg font-bold text-red-600 dark:text-red-400">{data.raw_data?.overdue_count || 0}</p>
              <p className="text-xs text-gray-500 dark:text-gray-400">Overdue</p>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-3 text-center">
              <p className="text-lg font-bold text-amber-600 dark:text-amber-400">{data.raw_data?.bad_estimate_count || 0}</p>
              <p className="text-xs text-gray-500 dark:text-gray-400">Bad Estimates</p>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-3 text-center">
              <p className="text-lg font-bold text-green-600 dark:text-green-400">
                {data.raw_data?.completion_rate_7d?.completed || 0}/{data.raw_data?.completion_rate_7d?.created || 0}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400">Done/Created (7d)</p>
            </div>
          </div>

          {/* Rule-based insights */}
          {data.insights && data.insights.length > 0 ? (
            <div className="space-y-4 mb-6">
              {data.insights.map((insight, i) => {
                const style = SEVERITY_STYLES[insight.severity] || SEVERITY_STYLES.info;
                const Icon = style.icon;
                return (
                  <div key={i} className={`${style.bg} border ${style.border} rounded-xl p-4`}>
                    <div className="flex items-start gap-3">
                      <Icon className={`w-5 h-5 ${style.iconColor} flex-shrink-0 mt-0.5`} />
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">{insight.title}</h3>
                          <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${style.badge}`}>
                            {insight.severity}
                          </span>
                        </div>
                        <p className="text-sm text-gray-600 dark:text-gray-400">{insight.description}</p>
                        {insight.items && insight.items.length > 0 && (
                          <div className="mt-3 space-y-1">
                            {insight.items.slice(0, 5).map((item, j) => (
                              <div key={j} className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
                                <span className="w-1.5 h-1.5 rounded-full bg-gray-400" />
                                <span className="truncate">{item.title || item.content || JSON.stringify(item)}</span>
                                {item.days_old && <span className="text-gray-400">({item.days_old}d)</span>}
                                {item.ratio && <span className="text-amber-500">({item.ratio}x)</span>}
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-700 rounded-xl p-6 text-center mb-6">
              <p className="text-sm text-green-700 dark:text-green-300 font-medium">
                Tudo em ordem! Nenhum problema detectado.
              </p>
            </div>
          )}

          {/* AI analysis (if available) */}
          {data.ai_analysis && data.ai_analysis.length > 0 && (
            <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
              <div className="flex items-center gap-2 mb-4">
                <Sparkles className="w-4 h-4 text-charlie-500" />
                <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300">AI Coach Insights</h3>
                <span className="text-xs px-2 py-0.5 rounded-full bg-charlie-100 dark:bg-charlie-900/30 text-charlie-700 dark:text-charlie-300">GPT</span>
              </div>
              <div className="space-y-3">
                {data.ai_analysis.map((insight, i) => (
                  <div key={i} className="flex items-start gap-2">
                    <span className="text-charlie-500 font-bold text-sm mt-0.5">{i + 1}.</span>
                    <p className="text-sm text-gray-700 dark:text-gray-300">{insight}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          <p className="text-xs text-gray-400 dark:text-gray-500 text-center mt-4">
            Generated at {data.generated_at ? new Date(data.generated_at).toLocaleString() : 'unknown'}
          </p>
        </>
      )}
    </div>
  );
}
