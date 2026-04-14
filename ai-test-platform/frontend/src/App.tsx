import { useState } from 'react';
import { Layout } from './components/Layout';
import { ProjectsPage } from './pages/Projects';
import { RequirementsPage } from './pages/Requirements';
import { TestCasesPage } from './pages/TestCases';
import { TestPlansPage } from './pages/TestPlans';
import { TestRunsPage } from './pages/TestRuns';
import { ReportsPage } from './pages/Reports';

type PageKey = 'projects' | 'requirements' | 'testcases' | 'testplans' | 'testruns' | 'reports';

function App() {
  const [currentPage, setCurrentPage] = useState<PageKey>('projects');

  const renderPage = () => {
    switch (currentPage) {
      case 'projects': return <ProjectsPage />;
      case 'requirements': return <RequirementsPage />;
      case 'testcases': return <TestCasesPage />;
      case 'testplans': return <TestPlansPage />;
      case 'testruns': return <TestRunsPage />;
      case 'reports': return <ReportsPage />;
      default: return <ProjectsPage />;
    }
  };

  return (
    <Layout selectedKey={currentPage} onMenuClick={(key) => setCurrentPage(key as PageKey)}>
      {renderPage()}
    </Layout>
  );
}

export default App;
