import { useState } from 'react';
import { Layout } from './components/Layout';
import { DashboardPage } from './pages/Dashboard';
import { ProjectsPage } from './pages/Projects';
import { RequirementsPage } from './pages/Requirements';
import { TestCasesPage } from './pages/TestCases';
import { TestCodePage } from './pages/TestCode';
import { TestPlansPage } from './pages/TestPlans';
import { TestRunsPage } from './pages/TestRuns';
import { ReportsPage } from './pages/Reports';
import { DevicesPage } from './pages/Devices';
import { LoginPage } from './pages/Login';

type PageKey = 'dashboard' | 'projects' | 'requirements' | 'testcases' | 'testcode' | 'testplans' | 'testruns' | 'reports' | 'devices';

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(!!localStorage.getItem('token'));
  const [currentPage, setCurrentPage] = useState<PageKey>('dashboard');

  const handleLogin = (_token: string, _user: { id: string; email: string; name: string }) => {
    setIsLoggedIn(true);
  };

  const renderPage = () => {
    switch (currentPage) {
      case 'dashboard': return <DashboardPage />;
      case 'projects': return <ProjectsPage />;
      case 'requirements': return <RequirementsPage />;
      case 'testcases': return <TestCasesPage />;
      case 'testcode': return <TestCodePage />;
      case 'testplans': return <TestPlansPage />;
      case 'testruns': return <TestRunsPage />;
      case 'reports': return <ReportsPage />;
      case 'devices': return <DevicesPage />;
      default: return <DashboardPage />;
    }
  };

  if (!isLoggedIn) {
    return <LoginPage onLogin={handleLogin} />;
  }

  return (
    <Layout selectedKey={currentPage} onMenuClick={(key) => setCurrentPage(key as PageKey)}>
      {renderPage()}
    </Layout>
  );
}

export default App;
