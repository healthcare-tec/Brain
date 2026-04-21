/**
 * Charlie — API service layer.
 * All backend communication goes through this module.
 */

const BASE = '/api';

async function request(path, options = {}) {
  const url = `${BASE}${path}`;
  const config = {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  };
  if (config.body && typeof config.body === 'object') {
    config.body = JSON.stringify(config.body);
  }
  const res = await fetch(url, config);
  if (res.status === 204) return null;
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Request failed');
  }
  // For export downloads, return blob
  const ct = res.headers.get('content-type') || '';
  if (ct.includes('text/csv') || ct.includes('text/markdown')) {
    return { blob: await res.blob(), filename: _extractFilename(res) };
  }
  return res.json();
}

function _extractFilename(res) {
  const cd = res.headers.get('content-disposition') || '';
  const match = cd.match(/filename=(.+)/);
  return match ? match[1] : 'export';
}

// ── Inbox ───────────────────────────────────────────────────────────────

export const inboxApi = {
  capture: (data) => request('/inbox/', { method: 'POST', body: data }),
  list: (status) => request(`/inbox/${status ? `?status=${status}` : ''}`),
  get: (id) => request(`/inbox/${id}`),
  clarify: (id, data) => request(`/inbox/${id}/clarify`, { method: 'POST', body: data }),
  delete: (id) => request(`/inbox/${id}`, { method: 'DELETE' }),
};

// ── Tasks ───────────────────────────────────────────────────────────────

export const tasksApi = {
  create: (data) => request('/tasks/', { method: 'POST', body: data }),
  list: (params = {}) => {
    const qs = new URLSearchParams();
    if (params.status) qs.set('status', params.status);
    if (params.project_id) qs.set('project_id', params.project_id);
    if (params.context) qs.set('context', params.context);
    if (params.tags) qs.set('tags', params.tags);
    if (params.priority) qs.set('priority', params.priority);
    if (params.search) qs.set('search', params.search);
    const q = qs.toString();
    return request(`/tasks/${q ? `?${q}` : ''}`);
  },
  get: (id) => request(`/tasks/${id}`),
  update: (id, data) => request(`/tasks/${id}`, { method: 'PATCH', body: data }),
  complete: (id, data = {}) => request(`/tasks/${id}/complete`, { method: 'POST', body: data }),
  delete: (id) => request(`/tasks/${id}`, { method: 'DELETE' }),
  reminders: () => request('/tasks/reminders'),
};

// ── Projects ────────────────────────────────────────────────────────────

export const projectsApi = {
  create: (data) => request('/projects/', { method: 'POST', body: data }),
  list: (status) => request(`/projects/${status ? `?status=${status}` : ''}`),
  get: (id) => request(`/projects/${id}`),
  update: (id, data) => request(`/projects/${id}`, { method: 'PATCH', body: data }),
  delete: (id) => request(`/projects/${id}`, { method: 'DELETE' }),
};

// ── Decision Logs ───────────────────────────────────────────────────────

export const decisionLogsApi = {
  create: (data) => request('/decision-logs/', { method: 'POST', body: data }),
  list: (logType) => request(`/decision-logs/${logType ? `?log_type=${logType}` : ''}`),
  get: (id) => request(`/decision-logs/${id}`),
  update: (id, data) => request(`/decision-logs/${id}`, { method: 'PATCH', body: data }),
  delete: (id) => request(`/decision-logs/${id}`, { method: 'DELETE' }),
};

// ── Notes ───────────────────────────────────────────────────────────────

export const notesApi = {
  create: (data) => request('/notes/', { method: 'POST', body: data }),
  list: (category) => request(`/notes/${category ? `?category=${category}` : ''}`),
  get: (id) => request(`/notes/${id}`),
  update: (id, data) => request(`/notes/${id}`, { method: 'PATCH', body: data }),
  delete: (id) => request(`/notes/${id}`, { method: 'DELETE' }),
};

// ── Reviews ─────────────────────────────────────────────────────────────

export const reviewsApi = {
  weekly: () => request('/reviews/weekly'),
};

// ── Events ──────────────────────────────────────────────────────────────

export const eventsApi = {
  list: (params = {}) => {
    const qs = new URLSearchParams();
    if (params.event_type) qs.set('event_type', params.event_type);
    if (params.task_id) qs.set('task_id', params.task_id);
    if (params.limit) qs.set('limit', params.limit);
    const q = qs.toString();
    return request(`/events/${q ? `?${q}` : ''}`);
  },
};

// ── AI ──────────────────────────────────────────────────────────────────

export const aiApi = {
  status: () => request('/ai/status'),
  classify: (content, context = null) =>
    request('/ai/classify', { method: 'POST', body: { content, context } }),
  interpret: (content, interpret_type = 'task', extra_context = null) =>
    request('/ai/interpret', { method: 'POST', body: { content, interpret_type, extra_context } }),
  patterns: (days = 30) => request(`/ai/patterns?timeframe_days=${days}`),
  weeklyReview: (reviewData = null) =>
    request('/ai/weekly-review', { method: 'POST', body: { review_data: reviewData } }),
};

// ── Global Search ───────────────────────────────────────────────────────

export const searchApi = {
  search: (q, limit = 20) => request(`/search/?q=${encodeURIComponent(q)}&limit=${limit}`),
};

// ── Analytics Dashboard ─────────────────────────────────────────────────

export const analyticsApi = {
  summary: (days = 30) => request(`/analytics/summary?days=${days}`),
  completionsByDay: (days = 30) => request(`/analytics/completions-by-day?days=${days}`),
  byContext: () => request('/analytics/by-context'),
  byProject: () => request('/analytics/by-project'),
  timeEstimation: (days = 30) => request(`/analytics/time-estimation?days=${days}`),
  eventsTimeline: (days = 7) => request(`/analytics/events-timeline?days=${days}`),
};

// ── Data Export ─────────────────────────────────────────────────────────

export const exportApi = {
  tasks: (format = 'json') => request(`/export/tasks?format=${format}`),
  notes: (format = 'json') => request(`/export/notes?format=${format}`),
  decisionLogs: (format = 'json') => request(`/export/decision_logs?format=${format}`),
  download: async (entityType, format) => {
    const result = await request(`/export/${entityType}?format=${format}`);
    if (result && result.blob) {
      const url = URL.createObjectURL(result.blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = result.filename;
      a.click();
      URL.revokeObjectURL(url);
    }
    return result;
  },
};

// ── Voice Capture ───────────────────────────────────────────────────────

export const voiceApi = {
  capture: (text) => request('/voice/capture', { method: 'POST', body: { text } }),
};

// ── AI Proactive Insights ───────────────────────────────────────────────

export const insightsApi = {
  get: () => request('/insights/'),
};
