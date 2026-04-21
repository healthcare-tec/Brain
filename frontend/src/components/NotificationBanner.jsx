import React, { useState, useEffect } from 'react';
import { Bell, X, Clock, AlertTriangle } from 'lucide-react';
import { tasksApi } from '../services/api';

export default function NotificationBanner() {
  const [reminders, setReminders] = useState([]);
  const [dismissed, setDismissed] = useState(new Set());
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const check = async () => {
      try {
        const data = await tasksApi.reminders();
        setReminders(data || []);
        setVisible(data && data.length > 0);
      } catch {
        // Silently fail
      }
    };

    check();
    const interval = setInterval(check, 60000); // Check every minute
    return () => clearInterval(interval);
  }, []);

  // Request notification permission
  useEffect(() => {
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission();
    }
  }, []);

  // Send browser notifications for new reminders
  useEffect(() => {
    if ('Notification' in window && Notification.permission === 'granted') {
      reminders.forEach(r => {
        if (!dismissed.has(r.id)) {
          new Notification(`Charlie: ${r.type === 'overdue' ? 'Overdue' : 'Reminder'}`, {
            body: r.title,
            icon: '/brain.svg',
            tag: `charlie-${r.id}`,
          });
        }
      });
    }
  }, [reminders, dismissed]);

  const handleDismiss = (id) => {
    setDismissed(prev => new Set([...prev, id]));
  };

  const activeReminders = reminders.filter(r => !dismissed.has(r.id));

  if (!visible || activeReminders.length === 0) return null;

  return (
    <div className="mb-4 space-y-2">
      {activeReminders.slice(0, 3).map((reminder) => (
        <div
          key={reminder.id}
          className={`flex items-center gap-3 px-4 py-3 rounded-xl border text-sm ${
            reminder.type === 'overdue'
              ? 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-700 text-red-700 dark:text-red-300'
              : 'bg-amber-50 dark:bg-amber-900/20 border-amber-200 dark:border-amber-700 text-amber-700 dark:text-amber-300'
          }`}
        >
          {reminder.type === 'overdue' ? (
            <AlertTriangle className="w-4 h-4 flex-shrink-0" />
          ) : (
            <Clock className="w-4 h-4 flex-shrink-0" />
          )}
          <div className="flex-1">
            <span className="font-medium">{reminder.type === 'overdue' ? 'Overdue: ' : 'Reminder: '}</span>
            {reminder.title}
            {reminder.due_date && (
              <span className="ml-2 text-xs opacity-75">
                (due {new Date(reminder.due_date).toLocaleDateString()})
              </span>
            )}
          </div>
          <button
            onClick={() => handleDismiss(reminder.id)}
            className="p-1 hover:bg-black/10 rounded transition-colors"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      ))}
      {activeReminders.length > 3 && (
        <p className="text-xs text-gray-500 dark:text-gray-400 text-center">
          +{activeReminders.length - 3} more notifications
        </p>
      )}
    </div>
  );
}
