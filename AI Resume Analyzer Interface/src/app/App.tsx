import { useState, useEffect } from 'react';
import { Navigation } from './components/Navigation';
import { HeroSection } from './components/HeroSection';
import { FeaturesSection } from './components/FeaturesSection';
import { HowItWorksSection } from './components/HowItWorksSection';
import { StatsSection } from './components/StatsSection';
import { Footer } from './components/Footer';
import { InputPage } from './pages/InputPage';
import { ResultsPage } from './pages/ResultsPage';
import { LoginPage } from './pages/LoginPage';
import { HistoryPage } from './pages/HistoryPage';
import { analyzeResume, checkAuth, logout as apiLogout, User, AnalysisResults } from '../utils/api';

type Page = 'landing' | 'input' | 'results' | 'login' | 'history';

export default function App() {
  const [currentPage, setCurrentPage] = useState<Page>('landing');
  const [analysisResults, setAnalysisResults] = useState<AnalysisResults | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [user, setUser] = useState<User | null>(null);
  const [isCheckingAuth, setIsCheckingAuth] = useState(true);

  useEffect(() => {
    // Check if user is authenticated on mount
    checkAuth()
      .then((response) => {
        if (response.authenticated && response.user) {
          setUser(response.user);
        }
      })
      .catch(() => {
        // User not authenticated
      })
      .finally(() => {
        setIsCheckingAuth(false);
      });
  }, []);

  const handleGetStarted = () => {
    setCurrentPage('input');
  };

  const handleLogin = () => {
    setCurrentPage('login');
  };

  const handleUserLogin = (loggedInUser: User) => {
    setUser(loggedInUser);
    setCurrentPage('landing');
  };

  const handleLogout = async () => {
    try {
      await apiLogout();
    } catch {
      // ignore
    }
    setUser(null);
    setCurrentPage('landing');
  };

  const handleHistory = () => {
    setCurrentPage('history');
  };

  const handleViewHistoryResult = (results: AnalysisResults) => {
    setAnalysisResults(results);
    setCurrentPage('results');
  };

  const handleAnalyze = async (resumeFile: File, jobDescription: string) => {
    setIsAnalyzing(true);
    
    try {
      const results = await analyzeResume(resumeFile, jobDescription);
      setAnalysisResults(results);
      setCurrentPage('results');
    } catch (error: any) {
      alert(error.message || 'Failed to analyze resume');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleBackToInput = () => {
    setCurrentPage('input');
  };

  const handleBackToLanding = () => {
    setCurrentPage('landing');
    setAnalysisResults(null);
  };

  const handleNewAnalysis = () => {
    setCurrentPage('input');
    setAnalysisResults(null);
  };

  // Loading state
  if (isCheckingAuth) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-white via-blue-50/30 to-white flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-6"></div>
          <h3 className="text-gray-800 mb-2">Loading...</h3>
        </div>
      </div>
    );
  }

  if (isAnalyzing) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-white via-blue-50/30 to-white flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-6"></div>
          <h3 className="text-gray-800 mb-2">Analyzing Your Resume...</h3>
          <p className="text-gray-600">Our AI is processing your information</p>
        </div>
      </div>
    );
  }

  const isLanding = currentPage === 'landing';

  return (
    <>
      {/* Landing page — always mounted, hidden via CSS so there's no unmount/remount cost on navigation */}
      <div style={{ display: isLanding ? 'block' : 'none' }} aria-hidden={!isLanding}>
        <div className="min-h-screen bg-gradient-to-b from-white via-blue-50/30 to-white">
          <Navigation
            user={user}
            onLogin={handleLogin}
            onLogout={handleLogout}
            onHistory={handleHistory}
          />
          <main>
            <HeroSection onGetStarted={handleGetStarted} />
            <StatsSection />
            <FeaturesSection />
            <HowItWorksSection />
          </main>
          <Footer />
        </div>
      </div>

      {/* Other pages — conditionally mounted */}
      {currentPage === 'login' && (
        <LoginPage onLogin={handleUserLogin} onBack={handleBackToLanding} />
      )}
      {currentPage === 'history' && user && (
        <HistoryPage onBack={handleBackToLanding} onViewResult={handleViewHistoryResult} />
      )}
      {currentPage === 'input' && (
        <InputPage onAnalyze={handleAnalyze} onBack={handleBackToLanding} />
      )}
      {currentPage === 'results' && analysisResults && (
        <ResultsPage
          results={analysisResults}
          onBack={handleBackToInput}
          onNewAnalysis={handleNewAnalysis}
        />
      )}
    </>
  );
}