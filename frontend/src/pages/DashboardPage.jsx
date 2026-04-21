import React, { useState, useEffect } from 'react';
import {
  TrendingUp, CheckCircle2, Clock, Target, AlertTriangle,
  BarChart3, PieChart, Activity, Download,
} from 'lucide-react';
import { analyticsApi, exportApi } from '../services/api';

// ── Simple Bar Chart (CSS-based, no deps) ────────────────────────────────

function BarChart({ data, maxValue, label }) {
  const max = maxValue || Math.max(...data.map(d => d.value), 1);
  return (
    <div className="space-y-1.5">
      {data.map((d, i) => (
        <div key={i} className="flex items-center gap-2">
          <span className="text-xs text-gray-500 dark:text-gray-400 w-16 text-right truncate">{d.label}</span>
          <div className="flex-1 bg-gray-100 dark:bg-gray-700 rounded-full h-5 overflow-hidden">
            <div
              className="h-full bg-charlie-500 rounded-full transition-all duration-500 flex items-center justify-end pr-2"
              style={{ width: `${Math.max((d.value / max) * 100, 2)}%` }}
            >
              {d.value > 0 && <span className="text-xs text-white font-medium">{d.value}</span>}
            </div>
          </div>
        </div>
      ))}
      {label && <p className="text-xs text-gray-400 dark:text-gray-500 text-center mt-1">{label}</p>}
    </div>
  );
}

// ── Stat Card ─────────────────────────────────────────────────────────────

function StatCard({ icon: Icon, label, value, sub, color }) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
      <div className="flex items-center gap-3">
        <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${color}`}>
          <Icon className="w-5 h-5" />
        </div>
        <div>
          <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">{value}</p>
          <p className="text-xs text-gray-500 dark:text-gray-400">{label}</p>
          {sub && <p className="text-xs text-gray-400 dark:text-gray-500">{sub}</p>}
        </div>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const [summary, setSummary] = useState(null);
  const [completions, setCompletions] = useState([]);
  const [byContext, setByContext] = useState([]);
  const [byProject, setByProject] = useState([]);
  const [timeEst, setTimeEst] = useState(null);
  const [loading, setLoading] = useState(true);
  const [days, setDays] = useState(30);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const [s, c, ctx, proj, te] = await Promise.all([
          analyticsApi.summary(days),
          analyticsApi.completionsByDay(days),
          analyticsApi.byContext(),
          analyticsApi.byProject(),
          analyticsApi.timeEstimation(days),
        ]);
        setSummary(s);
        setCompletions(c || []);
        setByContext(ctx || []);
        setByProject(proj || []);
        setTimeEst(te);
      } catch (err) {
        console.error('Failed to load analytics:', err);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [days]);

  const handleExport = async (entity, format) => {
    try {
      await exportApi.download(entity, format);
    } catch (err) {
      console.error('Export failed:', err);
    }
  };

  if (loading) {
    return (
      <div className="max-w-5xl mx-auto">
        <div className="text-center py-12 text-gray-400 dark:text-gray-500">Loading analytics...</div>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-xl bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center">
          <TrendingUp className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Dashboard</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400">Productivity analytics and insights</p>
        </div>
        <div className="ml-auto flex items-center gap-2">
          <select
            value={days}
            onChange={(e) => setDays(Number(e.target.value))}
            className="px-3 py-1.5 text-sm rounded-lg border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-800 dark:text-gray-100 outline-none"
          >
            <option value={7}>Last 7 days</option>
            <option value={30}>Last 30 days</option>
            <option value={90}>Last 90 days</option>
          </select>
        </div>
      </div>

      {/* Stat cards */}
      {summary && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <StatCard
            icon={CheckCircle2} label="Completed" value={summary.completed_tasks || 0}
            sub={`of ${summary.total_tasks || 0} total`}
            color="bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400"
          />
          <StatCard
            icon={Target} label="Active Tasks" value={summary.active_tasks || 0}
            sub="next + in_progress"
            color="bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400"
          />
          <StatCard
            icon={Clock} label="Avg Time" value={`${summary.avg_actual_time || 0}m`}
            sub={`est: ${summary.avg_estimated_time || 0}m`}
            color="bg-amber-100 dark:bg-amber-900/30 text-amber-600 dark:text-amber-400"
          />
          <StatCard
            icon={AlertTriangle} label="Overdue" value={summary.overdue_tasks || 0}
            sub="past deadline"
            color="bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400"
          />
        </div>
      )}

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Completions by day */}
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
          <div className="flex items-center gap-2 mb-4">
            <BarChart3 className="w-4 h-4 text-gray-500 dark:text-gray-400" />
            <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300">Completions by Day</h3>
          </div>
          {completions.length > 0 ? (
            <div className="flex items-end gap-1 h-40">
              {completions.slice(-14).map((d, i) => {
                const max = Math.max(...completions.map(x => x.count), 1);
                const h = Math.max((d.count / max) * 100, 4);
                return (
                  <div key={i} className="flex-1 flex flex-col items-center gap-1">
                    <span className="text-xs text-gray-500 dark:text-gray-400">{d.count || ''}</span>
                    <div
                      className="w-full bg-charlie-500 rounded-t transition-all"
                      style={{ height: `${h}%` }}
                      title={`${d.date}: ${d.count} tasks`}
                    />
                    <span className="text-xs text-gray-400 dark:text-gray-500 -rotate-45 origin-top-left">
                      {d.date?.slice(5)}
                    </span>
                  </div>
                );
              })}
            </div>
          ) : (
            <p className="text-sm text-gray-400 dark:text-gray-500 text-center py-8">No data yet</p>
          )}
        </div>

        {/* Time estimation accuracy */}
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
          <div className="flex items-center gap-2 mb-4">
            <Activity className="w-4 h-4 text-gray-500 dark:text-gray-400" />
            <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300">Time Estimation Accuracy</h3>
          </div>
          {timeEst ? (
            <div className="space-y-4">
              <div className="text-center">
                <p className="text-4xl font-bold text-gray-900 dark:text-gray-100">
                  {timeEst.accuracy_percentage || 0}%
                </p>
                <p className="text-sm text-gray-500 dark:text-gray-400">accuracy (within 50% margin)</p>
              </div>
              <div className="grid grid-cols-2 gap-3 text-center">
                <div className="p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <p className="text-lg font-bold text-gray-900 dark:text-gray-100">{timeEst.avg_estimated || 0}m</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">Avg estimated</p>
                </div>
                <div className="p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <p className="text-lg font-bold text-gray-900 dark:text-gray-100">{timeEst.avg_actual || 0}m</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">Avg actual</p>
                </div>
              </div>
              <div className="text-center">
                <p className="text-xs text-gray-400 dark:text-gray-500">
                  Based on {timeEst.sample_size || 0} completed tasks with time data
                </p>
              </div>
            </div>
          ) : (
            <p className="text-sm text-gray-400 dark:text-gray-500 text-center py-8">No data yet</p>
          )}
        </div>
      </div>

      {/* Distribution charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* By context */}
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
          <div className="flex items-center gap-2 mb-4">
            <PieChart className="w-4 h-4 text-gray-500 dark:text-gray-400" />
            <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300">Tasks by Context</h3>
          </div>
          {byContext.length > 0 ? (
            <BarChart data={byContext.map(c => ({ label: `@${c.context || 'none'}`, value: c.count }))} />
          ) : (
            <p className="text-sm text-gray-400 dark:text-gray-500 text-center py-8">No data yet</p>
          )}
        </div>

        {/* By project */}
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
          <div className="flex items-center gap-2 mb-4">
            <PieChart className="w-4 h-4 text-gray-500 dark:text-gray-400" />
            <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300">Tasks by Project</h3>
          </div>
          {byProject.length > 0 ? (
            <BarChart data={byProject.map(p => ({ label: p.project_name || 'No project', value: p.count }))} />
          ) : (
            <p className="text-sm text-gray-400 dark:text-gray-500 text-center py-8">No data yet</p>
          )}
        </div>
      </div>

      {/* Export section */}
      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
        <div className="flex items-center gap-2 mb-4">
          <Download className="w-4 h-4 text-gray-500 dark:text-gray-400" />
          <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300">Export Data</h3>
        </div>
        <div className="grid grid-cols-3 gap-3">
          {['tasks', 'notes', 'decision_logs'].map((entity) => (
            <div key={entity} className="space-y-2">
              <p className="text-sm font-medium text-gray-700 dark:text-gray-300 capitalize">
                {entity.replace('_', ' ')}
              </p>
              <div className="flex gap-1.5">
                {['json', 'csv', 'markdown'].map((fmt) => (
                  <button
                    key={fmt}
                    onClick={() => handleExport(entity, fmt)}
                    className="px-2.5 py-1 text-xs rounded-lg bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-charlie-100 dark:hover:bg-charlie-900/30 hover:text-charlie-700 dark:hover:text-charlie-300 transition-colors"
                  >
                    {fmt.toUpperCase()}
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
