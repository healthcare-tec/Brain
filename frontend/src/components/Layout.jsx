import React, { useState } from 'react';
import { Outlet, NavLink } from 'react-router-dom';
import { Inbox, CheckSquare, FolderKanban, Brain, FileText, BarChart3, Menu, X } from 'lucide-react';
import clsx from 'clsx';

const NAV_ITEMS = [
  { to: '/inbox', label: 'Inbox', icon: Inbox, desc: 'Capture Engine' },
  { to: '/tasks', label: 'Tasks', icon: CheckSquare, desc: 'Next Actions' },
  { to: '/projects', label: 'Projects', icon: FolderKanban, desc: 'Project Dashboard' },
  { to: '/thinking', label: 'Thinking', icon: Brain, desc: 'Decision Logs' },
  { to: '/notes', label: 'Notes', icon: FileText, desc: 'Knowledge Base' },
  { to: '/review', label: 'Review', icon: BarChart3, desc: 'Weekly Review' },
];

export default function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="flex h-screen overflow-hidden bg-gray-50">
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-20 bg-black/30 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={clsx(
          'fixed inset-y-0 left-0 z-30 w-64 bg-white border-r border-gray-200 transform transition-transform lg:translate-x-0 lg:static lg:z-auto',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        <div className="flex items-center gap-3 px-6 py-5 border-b border-gray-100">
          <div className="w-9 h-9 rounded-lg bg-charlie-600 flex items-center justify-center">
            <Brain className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-gray-900">Charlie</h1>
            <p className="text-xs text-gray-500">Cognitive OS</p>
          </div>
        </div>

        <nav className="px-3 py-4 space-y-1">
          {NAV_ITEMS.map(({ to, label, icon: Icon, desc }) => (
            <NavLink
              key={to}
              to={to}
              onClick={() => setSidebarOpen(false)}
              className={({ isActive }) =>
                clsx(
                  'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-charlie-50 text-charlie-700'
                    : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                )
              }
            >
              <Icon className="w-5 h-5 flex-shrink-0" />
              <div>
                <div>{label}</div>
                <div className="text-xs font-normal text-gray-400">{desc}</div>
              </div>
            </NavLink>
          ))}
        </nav>

        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-100">
          <p className="text-xs text-gray-400 text-center">
            Charlie v0.1.0 — Better Thinking
          </p>
        </div>
      </aside>

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top bar (mobile) */}
        <header className="lg:hidden flex items-center gap-3 px-4 py-3 bg-white border-b border-gray-200">
          <button onClick={() => setSidebarOpen(true)} className="p-1 text-gray-600">
            <Menu className="w-6 h-6" />
          </button>
          <h1 className="text-lg font-bold text-gray-900">Charlie</h1>
        </header>

        <main className="flex-1 overflow-y-auto p-4 lg:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
