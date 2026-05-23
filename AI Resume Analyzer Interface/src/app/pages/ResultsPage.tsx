import { useState } from 'react';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { ArrowLeft, RefreshCw, TrendingUp, TrendingDown, Lightbulb, CheckCircle2, XCircle, Download, FileText, FileCode, FileType } from 'lucide-react';
import { AnalysisResults, ExportFormat, exportReport } from '../../utils/api';
import { JobRecommendations } from '../components/JobRecommendations';
import { FeedbackWidget } from '../components/FeedbackWidget';

// Progress component - simple implementation
function Progress({ value, className }: { value: number; className?: string }) {
  return (
    <div className={`h-2 w-full bg-gray-200 rounded-full overflow-hidden ${className || ''}`}>
      <div
        className="h-full bg-blue-600 transition-all duration-300"
        style={{ width: `${Math.min(100, Math.max(0, value))}%` }}
      />
    </div>
  );
}

interface ResultsPageProps {
  results: AnalysisResults;
  onBack: () => void;
  onNewAnalysis: () => void;
}

export function ResultsPage({ results, onBack, onNewAnalysis }: ResultsPageProps) {
  const [showExportMenu, setShowExportMenu] = useState(false);
  const [exporting, setExporting] = useState(false);

  const handleExport = async (format: ExportFormat) => {
    setExporting(true);
    setShowExportMenu(false);
    try {
      await exportReport({
        matchScore: results.matchScore,
        foundSkills: results.foundSkills,
        missingSkills: results.missingSkills,
        strengths: results.strengths,
        weaknesses: results.weaknesses,
        recommendations: results.recommendations,
        aiInsight: results.aiInsight,
        historyId: results.historyId,
      }, format);
    } catch (err: any) {
      alert(err.message || 'Export failed');
    } finally {
      setExporting(false);
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreBgColor = (score: number) => {
    if (score >= 80) return 'bg-green-100';
    if (score >= 60) return 'bg-yellow-100';
    return 'bg-red-100';
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-white via-blue-50/30 to-white">
      <div className="max-w-6xl mx-auto px-6 py-12">
        {/* Header */}
        <div className="mb-8">
          <Button
            variant="ghost"
            onClick={onBack}
            className="mb-4"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Input
          </Button>
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold text-gray-900 mb-2">Analysis Results</h1>
              <p className="text-gray-600">Your resume match analysis and recommendations</p>
            </div>
            <div className="flex items-center gap-2">
              <div className="relative">
                <Button
                  variant="outline"
                  onClick={() => setShowExportMenu(!showExportMenu)}
                  disabled={exporting}
                >
                  <Download className="w-4 h-4 mr-2" />
                  {exporting ? 'Exporting...' : 'Export'}
                </Button>
                {showExportMenu && (
                  <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-10">
                    <button
                      className="w-full flex items-center gap-2 px-4 py-2.5 text-sm text-gray-700 hover:bg-gray-50 transition-colors"
                      onClick={() => handleExport('pdf')}
                    >
                      <FileText className="w-4 h-4 text-red-500" />
                      Export as PDF
                    </button>
                    <button
                      className="w-full flex items-center gap-2 px-4 py-2.5 text-sm text-gray-700 hover:bg-gray-50 transition-colors"
                      onClick={() => handleExport('docx')}
                    >
                      <FileType className="w-4 h-4 text-blue-500" />
                      Export as DOCX
                    </button>
                    <button
                      className="w-full flex items-center gap-2 px-4 py-2.5 text-sm text-gray-700 hover:bg-gray-50 transition-colors"
                      onClick={() => handleExport('html')}
                    >
                      <FileCode className="w-4 h-4 text-orange-500" />
                      Export as HTML
                    </button>
                  </div>
                )}
              </div>
              <Button
                variant="outline"
                onClick={onNewAnalysis}
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                New Analysis
              </Button>
            </div>
          </div>
        </div>

        {/* Match Score Card */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Match Score</CardTitle>
            <CardDescription>How well your resume matches the job requirements</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-center py-8">
              <div className="text-center">
                <div className={`text-6xl font-bold mb-2 ${getScoreColor(results.matchScore)}`}>
                  {results.matchScore}%
                </div>
                <div className={`inline-block px-4 py-2 rounded-full text-sm font-semibold ${getScoreBgColor(results.matchScore)} ${getScoreColor(results.matchScore)}`}>
                  {results.matchScore >= 80 ? 'Excellent Match' : results.matchScore >= 60 ? 'Good Match' : 'Needs Improvement'}
                </div>
                <div className="mt-4 w-64">
                  <Progress value={results.matchScore} className="h-3" />
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="grid md:grid-cols-2 gap-6 mb-6">
          {/* Found Skills */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5 text-green-600" />
                Found Skills ({results.foundSkills.length})
              </CardTitle>
              <CardDescription>Skills from your resume that match the job requirements</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {results.foundSkills.length > 0 ? (
                  results.foundSkills.map((skill, index) => (
                    <Badge key={index} variant="default" className="bg-green-100 text-green-800 hover:bg-green-200">
                      {skill}
                    </Badge>
                  ))
                ) : (
                  <p className="text-gray-500 text-sm">No matching skills found</p>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Missing Skills */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <XCircle className="w-5 h-5 text-red-600" />
                Missing Skills ({results.missingSkills.length})
              </CardTitle>
              <CardDescription>Skills in the job description that are not in your resume</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {results.missingSkills.length > 0 ? (
                  results.missingSkills.map((skill, index) => (
                    <Badge key={index} variant="outline" className="border-red-300 text-red-700">
                      {skill}
                    </Badge>
                  ))
                ) : (
                  <p className="text-gray-500 text-sm">No missing skills identified</p>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="grid md:grid-cols-2 gap-6 mb-6">
          {/* Strengths */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-blue-600" />
                Strengths
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2">
                {results.strengths.length > 0 ? (
                  results.strengths.map((strength, index) => (
                    <li key={index} className="flex items-start gap-2">
                      <CheckCircle2 className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                      <span className="text-gray-700">{strength}</span>
                    </li>
                  ))
                ) : (
                  <p className="text-gray-500 text-sm">No strengths identified</p>
                )}
              </ul>
            </CardContent>
          </Card>

          {/* Weaknesses */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingDown className="w-5 h-5 text-orange-600" />
                Areas for Improvement
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2">
                {results.weaknesses.length > 0 ? (
                  results.weaknesses.map((weakness, index) => (
                    <li key={index} className="flex items-start gap-2">
                      <XCircle className="w-5 h-5 text-orange-600 flex-shrink-0 mt-0.5" />
                      <span className="text-gray-700">{weakness}</span>
                    </li>
                  ))
                ) : (
                  <p className="text-gray-500 text-sm">No areas for improvement identified</p>
                )}
              </ul>
            </CardContent>
          </Card>
        </div>

        {/* Recommendations */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Lightbulb className="w-5 h-5 text-yellow-600" />
              Recommendations
            </CardTitle>
            <CardDescription>Actionable suggestions to improve your resume</CardDescription>
          </CardHeader>
          <CardContent>
            <ul className="space-y-3">
              {results.recommendations.map((recommendation, index) => (
                <li key={index} className="flex items-start gap-3">
                  <div className="w-6 h-6 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center flex-shrink-0 text-sm font-semibold">
                    {index + 1}
                  </div>
                  <span className="text-gray-700">{recommendation}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>

        {/* AI Insight */}
        <Card className="mb-6 bg-gradient-to-br from-blue-50 to-indigo-50 border-blue-200">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Lightbulb className="w-5 h-5 text-indigo-600" />
              AI Insight
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-gray-700 leading-relaxed">{results.aiInsight}</p>
          </CardContent>
        </Card>

        {/* User feedback widget — captures signal to improve the matcher */}
        <FeedbackWidget
          historyId={results.historyId}
          snapshot={{
            matchScore:    results.matchScore,
            foundSkills:   results.foundSkills,
            missingSkills: results.missingSkills,
            strengths:     results.strengths,
            weaknesses:    results.weaknesses,
            // Echo the calibrator feature vector back so the backend can
            // store it with the feedback row and use it in the next retrain.
            features:      results.scoringFeatures ?? null,
          }}
        />

        {/* Job Recommendations */}
        <JobRecommendations
          resumeSkills={
            results.resumeSkills && results.resumeSkills.length > 0
              ? results.resumeSkills
              : [...results.foundSkills, ...results.missingSkills]
          }
          experienceLevel={results.experienceLevel || 'mid'}
        />
      </div>
    </div>
  );
}

