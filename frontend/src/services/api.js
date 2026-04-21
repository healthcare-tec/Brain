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
  return res.json();
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
    const q = qs.toString();
    return request(`/tasks/${q ? `?${q}` : ''}`);
  },
  get: (id) => request(`/tasks/${id}`),
  update: (id, data) => request(`/tasks/${id}`, { method: 'PATCH', body: data }),
  complete: (id, data = {}) => request(`/tasks/${id}/complete`, { method: 'POST', body: data }),
  delete: (id) => request(`/tasks/${id}`, { method: 'DELETE' }),
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
  /** Check if AI is configured (returns { ai_enabled, models, message }) */
  status: () => request('/ai/status'),

  /**
   * L1 — Classify an inbox item.
   * Returns { category, confidence, suggested_title, suggested_context,
   *           suggested_priority, is_time_sensitive, estimated_minutes,
   *           reasoning, ai_enabled }
   */
  classify: (content, context = null) =>
    request('/ai/classify', {
      method: 'POST',
      body: { content, context },
    }),

  /**
   * L2 — Interpret content.
   * interpret_type: "task" | "note" | "decision"
   */
  interpret: (content, interpret_type = 'task', extra_context = null) =>
    request('/ai/interpret', {
      method: 'POST',
      body: { content, interpret_type, extra_context },
    }),

  /** L3 — Detect behavioral patterns */
  patterns: (days = 30) => request(`/ai/patterns?timeframe_days=${days}`),

  /** L3 — Generate weekly review narrative */
  weeklyReview: (reviewData = null) =>
    request('/ai/weekly-review', {
      method: 'POST',
      body: { review_data: reviewData },
    }),
};
