import React from 'react';
import { Routes, Route } from 'react-router-dom';
import ProfileView from './components/ProfileView';
import ProfileBuilder from './components/ProfileBuilder';
import JobAnalyzer from "./components/JobAnalyzer";
import GeneratedDocuments from './components/GeneratedDocuments';
import MatchScore from './components/MatchScore'; 
import JobTracker from './components/JobTracker'; 
import './index.css';

function App() {
  return (
    <Routes>
      <Route path="/" element={<ProfileView />} />
      <Route path="/edit" element={<ProfileBuilder />} />
      <Route path="/analyze-job" element={<JobAnalyzer />} />
      <Route path="/generate-documents" element={<GeneratedDocuments />} />
      <Route path="/match-score" element={<MatchScore />} />
      <Route path="/job-tracker" element={<JobTracker />} />
    </Routes>
  );
}

export default App;
