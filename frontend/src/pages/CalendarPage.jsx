import React, { useState, useEffect, useCallback } from 'react';
import { Calendar, ChevronLeft, ChevronRight, Clock, AlertTriangle } from 'lucide-react';
import { tasksApi } from '../services/api';

const DAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December'];

function getDaysInMonth(year, month) {
  return new Date(year, month + 1, 0).getDate();
}

function getFirstDayOfMonth(year, month) {
  return new Date(year, month, 1).getDay();
}

export default function CalendarPage() {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [currentDate, setCurrentDate] = useState(new Date());
  const [selectedDate, setSelectedDate] = useState(null);

  const year = currentDate.getFullYear();
  const month = currentDate.getMonth();

  const loadTasks = useCallback(async () => {
    setLoading(true);
    try {
      const data = await tasksApi.list();
      setTasks(data.filter(t => t.due_date || t.reminder_at));
    } catch (err) {
      console.error('Failed to load tasks:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadTasks(); }, [loadTasks]);

  const prevMonth = () => setCurrentDate(new Date(year, month - 1, 1));
  const nextMonth = () => setCurrentDate(new Date(year, month + 1, 1));
  const goToday = () => setCurrentDate(new Date());

  const daysInMonth = getDaysInMonth(year, month);
  const firstDay = getFirstDayOfMonth(year, month);
  const today = new Date();
  const todayStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;

  const getTasksForDate = (dateStr) => {
    return tasks.filter(t => {
      const dueDate = t.due_date ? t.due_date.split('T')[0] : null;
      const reminderDate = t.reminder_at ? t.reminder_at.split('T')[0] : null;
      return dueDate === dateStr || reminderDate === dateStr;
    });
  };

  const selectedDateTasks = selectedDate ? getTasksForDate(selectedDate) : [];

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-xl bg-indigo-100 dark:bg-indigo-900/30 flex items-center justify-center">
          <Calendar className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Calendar</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400">Tasks with deadlines and reminders</p>
        </div>
      </div>

      {/* Google Calendar info */}
      <div className="mb-6 flex items-start gap-2 px-4 py-3 bg-indigo-50 dark:bg-indigo-900/20 border border-indigo-200 dark:border-indigo-700 rounded-xl text-xs text-indigo-700 dark:text-indigo-300">
        <Calendar className="w-4 h-4 flex-shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold">Google Calendar sync</span> — coming soon.
          Tasks with due dates are shown below. Full Google Calendar integration will allow bidirectional sync.
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Calendar grid */}
        <div className="lg:col-span-2 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
          {/* Month nav */}
          <div className="flex items-center justify-between mb-4">
            <button onClick={prevMonth} className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors">
              <ChevronLeft className="w-5 h-5 text-gray-500 dark:text-gray-400" />
            </button>
            <div className="flex items-center gap-3">
              <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100">
                {MONTHS[month]} {year}
              </h2>
              <button onClick={goToday} className="text-xs px-2 py-0.5 rounded bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600">
                Today
              </button>
            </div>
            <button onClick={nextMonth} className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors">
              <ChevronRight className="w-5 h-5 text-gray-500 dark:text-gray-400" />
            </button>
          </div>

          {/* Day headers */}
          <div className="grid grid-cols-7 gap-1 mb-1">
            {DAYS.map(d => (
              <div key={d} className="text-center text-xs font-medium text-gray-400 dark:text-gray-500 py-1">{d}</div>
            ))}
          </div>

          {/* Calendar cells */}
          <div className="grid grid-cols-7 gap-1">
            {Array.from({ length: firstDay }, (_, i) => (
              <div key={`empty-${i}`} className="h-16" />
            ))}
            {Array.from({ length: daysInMonth }, (_, i) => {
              const day = i + 1;
              const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
              const dayTasks = getTasksForDate(dateStr);
              const isToday = dateStr === todayStr;
              const isSelected = dateStr === selectedDate;

              return (
                <button
                  key={day}
                  onClick={() => setSelectedDate(dateStr)}
                  className={`h-16 rounded-lg p-1 text-left transition-all ${
                    isSelected
                      ? 'bg-charlie-100 dark:bg-charlie-900/30 ring-2 ring-charlie-400'
                      : isToday
                        ? 'bg-blue-50 dark:bg-blue-900/20'
                        : 'hover:bg-gray-50 dark:hover:bg-gray-700'
                  }`}
                >
                  <span className={`text-xs font-medium ${
                    isToday ? 'text-blue-600 dark:text-blue-400' : 'text-gray-700 dark:text-gray-300'
                  }`}>
                    {day}
                  </span>
                  {dayTasks.length > 0 && (
                    <div className="flex flex-wrap gap-0.5 mt-0.5">
                      {dayTasks.slice(0, 3).map((t, j) => (
                        <span
                          key={j}
                          className={`w-1.5 h-1.5 rounded-full ${
                            t.status === 'done'
                              ? 'bg-green-400'
                              : new Date(t.due_date) < today
                                ? 'bg-red-400'
                                : 'bg-charlie-400'
                          }`}
                        />
                      ))}
                      {dayTasks.length > 3 && (
                        <span className="text-xs text-gray-400">+{dayTasks.length - 3}</span>
                      )}
                    </div>
                  )}
                </button>
              );
            })}
          </div>
        </div>

        {/* Selected date tasks */}
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
          <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4">
            {selectedDate
              ? new Date(selectedDate + 'T12:00:00').toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })
              : 'Select a date'}
          </h3>

          {loading ? (
            <p className="text-sm text-gray-400 dark:text-gray-500">Loading...</p>
          ) : !selectedDate ? (
            <p className="text-sm text-gray-400 dark:text-gray-500">Click a date to see tasks</p>
          ) : selectedDateTasks.length === 0 ? (
            <p className="text-sm text-gray-400 dark:text-gray-500">No tasks on this date</p>
          ) : (
            <div className="space-y-3">
              {selectedDateTasks.map((task) => (
                <div key={task.id} className="p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <p className="text-sm font-medium text-gray-900 dark:text-gray-100">{task.title}</p>
                  <div className="flex items-center gap-2 mt-1.5 text-xs text-gray-400 dark:text-gray-500">
                    {task.due_date && (
                      <span className={`flex items-center gap-1 ${
                        new Date(task.due_date) < today && task.status !== 'done' ? 'text-red-500' : ''
                      }`}>
                        <AlertTriangle className="w-3 h-3" />Due
                      </span>
                    )}
                    {task.reminder_at && (
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />Reminder
                      </span>
                    )}
                    <span className={`px-1.5 py-0.5 rounded ${
                      task.status === 'done'
                        ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300'
                        : 'bg-gray-200 dark:bg-gray-600 text-gray-600 dark:text-gray-400'
                    }`}>
                      {task.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
