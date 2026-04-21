import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Outlet, NavLink, useNavigate, useLocation } from 'react-router-dom';
import {
  Inbox, CheckSquare, FolderKanban, Brain, FileText, BarChart3,
  Menu, X, Search, Moon, Sun, Bell, Columns3, Mic, TrendingUp,
  Keyboard,
} from 'lucide-react';
import clsx from 'clsx';
import { searchApi, tasksApi } from '../services/api';

const NAV_ITEMS = [
  { to: '/inbox', label: 'Inbox', icon: Inbox, desc: 'Capture Engine' },
  { to: '/tasks', label: 'Tasks', icon: CheckSquare, desc: 'Next Actions' },
  { to: '/kanban', label: 'Kanban', icon: Columns3, desc: 'Board View' },
  { to: '/projects', label: 'Projects', icon: FolderKanban, desc: 'Project Dashboard' },
  { to: '/dashboard', label: 'Dashboard', icon: TrendingUp, desc: 'Analytics' },
  { to: '/thinking', label: 'Thinking', icon: Brain, desc: 'Decision Logs' },
  { to: '/notes', label: 'Notes', icon: FileText, desc: 'Knowledge Base' },
  { to: '/review', label: 'Review', icon: BarChart3, desc: 'Weekly Review' },
];

// ── Dark Mode Hook ──────────────────────────────────────────────────────

function useDarkMode() {
  const [dark, setDark] = useState(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('charlie-dark') === 'true';
    }
    return false;
  });

  useEffect(() => {
    const root = document.documentElement;
    if (dark) {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
    localStorage.setItem('charlie-dark', dark);
  }, [dark]);

  return [dark, setDark];
}

// ── Global Search Component ─────────────────────────────────────────────

function GlobalSearch() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const ref = useRef(null);
  const navigate = useNavigate();
  const debounceRef = useRef(null);

  useEffect(() => {
    const handleClick = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  const doSearch = useCallback(async (q) => {
    if (q.length < 2) { setResults([]); return; }
    setLoading(true);
    try {
      const data = await searchApi.search(q);
      setResults(data);
      setOpen(true);
    } catch { setResults([]); }
    setLoading(false);
  }, []);

  const handleChange = (e) => {
    const v = e.target.value;
    setQuery(v);
    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => doSearch(v), 300);
  };

  const typeRoutes = { task: '/tasks', note: '/notes', project: '/projects', decision_log: '/thinking' };
  const typeLabels = { task: 'Task', note: 'Note', project: 'Project', decision_log: 'Decision' };
  const typeColors = {
    task: 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300',
    note: 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300',
    project: 'bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300',
    decision_log: 'bg-amber-100 text-amber-700 dark:bg-amber-900 dark:text-amber-300',
  };

  return (
    <div ref={ref} className="relative flex-1 max-w-md">
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
        <input
          type="text"
          value={query}
          onChange={handleChange}
          onFocus={() => results.length > 0 && setOpen(true)}
          placeholder="Search everything... (Ctrl+K)"
          className="w-full pl-9 pr-3 py-2 text-sm rounded-lg border border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 dark:text-gray-100 focus:ring-2 focus:ring-charlie-500 focus:border-transparent outline-none"
        />
        {loading && <div className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 border-2 border-charlie-500 border-t-transparent rounded-full animate-spin" />}
      </div>
      {open && results.length > 0 && (
        <div className="absolute top-full mt-1 w-full bg-white dark:bg-gray-800 rounded-lg shadow-xl border border-gray-200 dark:border-gray-600 max-h-80 overflow-y-auto z-50">
          {results.map((r, i) => (
            <button
              key={`${r.type}-${r.id}-${i}`}
              onClick={() => { navigate(typeRoutes[r.type] || '/'); setOpen(false); setQuery(''); }}
              className="w-full text-left px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-700 border-b border-gray-100 dark:border-gray-700 last:border-0"
            >
              <div className="flex items-center gap-2">
                <span className={clsx('text-xs px-2 py-0.5 rounded-full font-medium', typeColors[r.type])}>
                  {typeLabels[r.type]}
                </span>
                <span className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">{r.title}</span>
              </div>
              {r.snippet && <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 truncate">{r.snippet}</p>}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Notification Bell ───────────────────────────────────────────────────

function NotificationBell() {
  const [reminders, setReminders] = useState([]);
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    const check = async () => {
      try {
        const data = await tasksApi.reminders();
        setReminders(data || []);
        // Web Notification
        if (data && data.length > 0 && Notification.permission === 'granted') {
          new Notification(`Charlie: ${data.length} reminder(s)`, {
            body: data.map(t => t.title).join(', '),
          });
        }
      } catch { /* ignore */ }
    };
    check();
    const interval = setInterval(check, 60000); // Check every minute
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (Notification.permission === 'default') {
      Notification.requestPermission();
    }
  }, []);

  useEffect(() => {
    const handleClick = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="relative p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-300"
      >
        <Bell className="w-5 h-5" />
        {reminders.length > 0 && (
          <span className="absolute -top-0.5 -right-0.5 w-5 h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center font-bold">
            {reminders.length}
          </span>
        )}
      </button>
      {open && (
        <div className="absolute right-0 top-full mt-1 w-80 bg-white dark:bg-gray-800 rounded-lg shadow-xl border border-gray-200 dark:border-gray-600 max-h-64 overflow-y-auto z-50">
          {reminders.length === 0 ? (
            <p className="p-4 text-sm text-gray-500 dark:text-gray-400 text-center">No reminders</p>
          ) : (
            reminders.map((t) => (
              <div key={t.id} className="px-4 py-3 border-b border-gray-100 dark:border-gray-700 last:border-0">
                <p className="text-sm font-medium text-gray-900 dark:text-gray-100">{t.title}</p>
                <p className="text-xs text-red-500 mt-1">
                  Reminder: {new Date(t.reminder_at).toLocaleString()}
                </p>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}

// ── Keyboard Shortcuts Help ─────────────────────────────────────────────

function ShortcutsHelp({ open, onClose }) {
  if (!open) return null;
  const shortcuts = [
    ['N', 'New capture (focus inbox)'],
    ['D', 'Mark selected task as done'],
    ['C', 'Clarify selected inbox item'],
    ['Ctrl+K', 'Focus global search'],
    ['1-8', 'Navigate to page (Inbox, Tasks, ...)'],
    ['?', 'Show this help'],
    ['Esc', 'Close modals / search'],
  ];
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={onClose}>
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl p-6 w-96" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 flex items-center gap-2">
            <Keyboard className="w-5 h-5" /> Keyboard Shortcuts
          </h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600"><X className="w-5 h-5" /></button>
        </div>
        <div className="space-y-2">
          {shortcuts.map(([key, desc]) => (
            <div key={key} className="flex items-center justify-between">
              <span className="text-sm text-gray-600 dark:text-gray-300">{desc}</span>
              <kbd className="px-2 py-1 text-xs font-mono bg-gray-100 dark:bg-gray-700 rounded border border-gray-200 dark:border-gray-600 text-gray-700 dark:text-gray-300">{key}</kbd>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ── Main Layout ─────────────────────────────────────────────────────────

export default function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [dark, setDark] = useDarkMode();
  const [showShortcuts, setShowShortcuts] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  // Global keyboard shortcuts
  useEffect(() => {
    const handler = (e) => {
      // Don't trigger when typing in inputs
      const tag = e.target.tagName;
      const isInput = tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT' || e.target.isContentEditable;

      // Ctrl+K: focus search
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        const searchInput = document.querySelector('input[placeholder*="Search"]');
        if (searchInput) searchInput.focus();
        return;
      }

      if (isInput) return;

      // Number keys for navigation
      const navMap = { '1': '/inbox', '2': '/tasks', '3': '/kanban', '4': '/projects', '5': '/dashboard', '6': '/thinking', '7': '/notes', '8': '/review' };
      if (navMap[e.key]) { navigate(navMap[e.key]); return; }

      // N: new capture
      if (e.key === 'n' || e.key === 'N') {
        navigate('/inbox');
        setTimeout(() => {
          const captureInput = document.querySelector('input[placeholder*="capture"], input[placeholder*="Capture"], textarea[placeholder*="capture"]');
          if (captureInput) captureInput.focus();
        }, 100);
        return;
      }

      // ?: show shortcuts
      if (e.key === '?') { setShowShortcuts(true); return; }

      // Esc: close shortcuts
      if (e.key === 'Escape') { setShowShortcuts(false); return; }
    };

    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [navigate]);

  return (
    <div className={clsx('flex h-screen overflow-hidden', dark ? 'dark' : '')}>
      <div className="flex h-full w-full bg-gray-50 dark:bg-gray-900">
        {/* Mobile overlay */}
        {sidebarOpen && (
          <div className="fixed inset-0 z-20 bg-black/30 lg:hidden" onClick={() => setSidebarOpen(false)} />
        )}

        {/* Sidebar */}
        <aside className={clsx(
          'fixed inset-y-0 left-0 z-30 w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 transform transition-transform lg:translate-x-0 lg:static lg:z-auto',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        )}>
          <div className="flex items-center gap-3 px-6 py-5 border-b border-gray-100 dark:border-gray-700">
            <div className="w-9 h-9 rounded-lg bg-charlie-600 flex items-center justify-center">
              <Brain className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-gray-900 dark:text-gray-100">Charlie</h1>
              <p className="text-xs text-gray-500 dark:text-gray-400">Cognitive OS</p>
            </div>
          </div>

          <nav className="px-3 py-4 space-y-1 overflow-y-auto" style={{ maxHeight: 'calc(100vh - 140px)' }}>
            {NAV_ITEMS.map(({ to, label, icon: Icon, desc }) => (
              <NavLink
                key={to}
                to={to}
                onClick={() => setSidebarOpen(false)}
                className={({ isActive }) =>
                  clsx(
                    'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-charlie-50 dark:bg-charlie-900/30 text-charlie-700 dark:text-charlie-300'
                      : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 hover:text-gray-900 dark:hover:text-gray-100'
                  )
                }
              >
                <Icon className="w-5 h-5 flex-shrink-0" />
                <div>
                  <div>{label}</div>
                  <div className="text-xs font-normal text-gray-400 dark:text-gray-500">{desc}</div>
                </div>
              </NavLink>
            ))}
          </nav>

          <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-100 dark:border-gray-700">
            <p className="text-xs text-gray-400 dark:text-gray-500 text-center">
              Charlie v0.2.0 — Better Thinking
            </p>
          </div>
        </aside>

        {/* Main content */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Top bar */}
          <header className="flex items-center gap-3 px-4 py-3 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
            <button onClick={() => setSidebarOpen(true)} className="p-1 text-gray-600 dark:text-gray-300 lg:hidden">
              <Menu className="w-6 h-6" />
            </button>

            <GlobalSearch />

            <div className="flex items-center gap-1">
              <NotificationBell />

              <button
                onClick={() => setShowShortcuts(true)}
                className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-300"
                title="Keyboard shortcuts (?)"
              >
                <Keyboard className="w-5 h-5" />
              </button>

              <button
                onClick={() => setDark(!dark)}
                className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-300"
                title={dark ? 'Light mode' : 'Dark mode'}
              >
                {dark ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
              </button>
            </div>
          </header>

          <main className="flex-1 overflow-y-auto p-4 lg:p-8">
            <Outlet />
          </main>
        </div>

        <ShortcutsHelp open={showShortcuts} onClose={() => setShowShortcuts(false)} />
      </div>
    </div>
  );
}
