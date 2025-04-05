import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';

// Import components
import Layout from './components/Layout';

// Import pages
import Dashboard from './pages/Dashboard';
import Documents from './pages/Documents';
import Requirements from './pages/Requirements';
import Repositories from './pages/Repositories';
import PRReviews from './pages/PRReviews';
import ProjectPlans from './pages/ProjectPlans';
import Workflows from './pages/Workflows';
import Settings from './pages/Settings';
import CodeExplorer from './pages/CodeExplorer';

// Create theme
const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Layout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/documents" element={<Documents />} />
            <Route path="/requirements" element={<Requirements />} />
            <Route path="/repositories" element={<Repositories />} />
            <Route path="/pr-reviews" element={<PRReviews />} />
            <Route path="/project-plans" element={<ProjectPlans />} />
            <Route path="/workflows" element={<Workflows />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/code-explorer" element={<CodeExplorer />} />
          </Routes>
        </Layout>
      </Router>
    </ThemeProvider>
  );
}

export default App;