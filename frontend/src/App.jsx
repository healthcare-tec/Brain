import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import InboxPage from './pages/InboxPage';
import TasksPage from './pages/TasksPage';
import KanbanPage from './pages/KanbanPage';
import ProjectsPage from './pages/ProjectsPage';
import ThinkingPage from './pages/ThinkingPage';
import NotesPage from './pages/NotesPage';
import ReviewPage from './pages/ReviewPage';
import DashboardPage from './pages/DashboardPage';
import VoiceCapturePage from './pages/VoiceCapturePage';
import InsightsPage from './pages/InsightsPage';
import CalendarPage from './pages/CalendarPage';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/inbox" replace />} />
          <Route path="inbox" element={<InboxPage />} />
          <Route path="tasks" element={<TasksPage />} />
          <Route path="kanban" element={<KanbanPage />} />
          <Route path="projects" element={<ProjectsPage />} />
          <Route path="thinking" element={<ThinkingPage />} />
          <Route path="notes" element={<NotesPage />} />
          <Route path="review" element={<ReviewPage />} />
          <Route path="dashboard" element={<DashboardPage />} />
          <Route path="voice" element={<VoiceCapturePage />} />
          <Route path="insights" element={<InsightsPage />} />
          <Route path="calendar" element={<CalendarPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
