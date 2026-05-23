import { useState, useEffect } from 'react';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { ArrowLeft, Trash2, Clock, Eye, TrendingUp, Download, FileText, FileType, FileCode } from 'lucide-react';
import { AnalysisHistoryItem, AnalysisResults, ExportFormat, getHistory, deleteHistory, exportReport } from '../../utils/api';

interface HistoryPageProps {
  onBack: () => void;
  onViewResult: (results: AnalysisResults) => void;
}

export function HistoryPage({ onBack, onViewResult }: HistoryPageProps) {
  const [history, setHistory] = useState<AnalysisHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [exportMenuId, setExportMenuId] = useState<number | null>(null);

  useEffect(() => {
    fetchHistory();
  }, []);

  async function fetchHistory() {
    setLoading(true);
    setError(null);
    try {
      const data = await getHistory();
      setHistory(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load history');
    } finally {
      setLoading(false);
    }
  }

  async function handleDelete(id: number) {
    if (!confirm('Delete this analysis record?')) return;
    try {
      await deleteHistory(id);
      setHistory((prev) => prev.filter((item) => item.id !== id));
    } catch (err: any) {
      alert(err.message || 'Failed to delete record');
    }
  }

  async function handleExport(item: AnalysisHistoryItem, format: ExportFormat) {
    setExportMenuId(null);
    try {
      await exportReport({ historyId: item.id }, format);
    } catch (err: any) {
      alert(err.message || 'Export failed');
    }
  }

  function handleView(item: AnalysisHistoryItem) {
    onViewResult({
      matchScore: item.matchScore,
      foundSkills: item.foundSkills,
      missingSkills: item.missingSkills,
      strengths: item.strengths,
      weaknesses: item.weaknesses,
      recommendations: item.recommendations,
      aiInsight: item.aiInsight,
    });
  }

  function getScoreColor(score: number) {
    if (score >= 70) return 'text-green-600';
    if (score >= 35) return 'text-yellow-600';
    return 'text-red-600';
  }

  function getScoreBadge(score: number) {
    if (score >= 70) return { label: 'High', className: 'bg-green-100 text-green-800' };
    if (score >= 35) return { label: 'Medium', className: 'bg-yellow-100 text-yellow-800' };
    return { label: 'Low', className: 'bg-red-100 text-red-800' };
  }

  function formatDate(iso: string) {
    const date = new Date(iso);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-white via-blue-50/30 to-white">
      <div className="max-w-5xl mx-auto px-6 py-12">
        {/* Header */}
        <div className="mb-8">
          <Button variant="ghost" onClick={onBack} className="mb-4">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
          <div className="flex items-center gap-3 mb-2">
            <TrendingUp className="w-8 h-8 text-blue-600" />
            <h1 className="text-4xl font-bold text-gray-900">Analysis History</h1>
          </div>
          <p className="text-gray-600">Your past resume analyses and match scores</p>
        </div>

        {/* Content */}
        {loading && (
          <div className="text-center py-20">
            <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-gray-600">Loading history...</p>
          </div>
        )}

        {error && (
          <Card className="border-red-200 bg-red-50">
            <CardContent className="py-8 text-center">
              <p className="text-red-600 mb-4">{error}</p>
              <Button variant="outline" onClick={fetchHistory}>
                Try Again
              </Button>
            </CardContent>
          </Card>
        )}

        {!loading && !error && history.length === 0 && (
          <Card>
            <CardContent className="py-16 text-center">
              <Clock className="w-12 h-12 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-700 mb-2">No analyses yet</h3>
              <p className="text-gray-500 mb-6">
                Your analysis results will appear here after you analyze a resume.
              </p>
              <Button onClick={onBack}>Start an Analysis</Button>
            </CardContent>
          </Card>
        )}

        {!loading && !error && history.length > 0 && (
          <div className="space-y-4">
            {history.map((item) => {
              const badge = getScoreBadge(item.matchScore);
              return (
                <Card key={item.id} className="hover:shadow-md transition-shadow">
                  <CardContent className="py-5">
                    <div className="flex items-start justify-between gap-4">
                      {/* Left: score + details */}
                      <div className="flex items-start gap-5 flex-1 min-w-0">
                        {/* Score circle */}
                        <div className="flex-shrink-0 w-16 h-16 rounded-full bg-gray-50 border-2 border-gray-200 flex items-center justify-center">
                          <span className={`text-xl font-bold ${getScoreColor(item.matchScore)}`}>
                            {item.matchScore}%
                          </span>
                        </div>
                        {/* Info */}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1.5">
                            <Badge className={badge.className}>{badge.label} Match</Badge>
                            <span className="text-sm text-gray-400 flex items-center gap-1">
                              <Clock className="w-3.5 h-3.5" />
                              {formatDate(item.createdAt)}
                            </span>
                          </div>
                          <p className="text-gray-700 text-sm line-clamp-2 mb-2">
                            {item.jobDescription}
                          </p>
                          <div className="flex flex-wrap gap-1.5">
                            {item.foundSkills.slice(0, 5).map((skill, i) => (
                              <Badge key={i} variant="outline" className="text-xs border-green-200 text-green-700">
                                {skill}
                              </Badge>
                            ))}
                            {item.foundSkills.length > 5 && (
                              <Badge variant="outline" className="text-xs">
                                +{item.foundSkills.length - 5} more
                              </Badge>
                            )}
                          </div>
                        </div>
                      </div>
                      {/* Right: actions */}
                      <div className="flex items-center gap-2 flex-shrink-0">
                        <Button variant="outline" size="sm" onClick={() => handleView(item)}>
                          <Eye className="w-4 h-4 mr-1" />
                          View
                        </Button>
                        <div className="relative">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => setExportMenuId(exportMenuId === item.id ? null : item.id)}
                          >
                            <Download className="w-4 h-4" />
                          </Button>
                          {exportMenuId === item.id && (
                            <div className="absolute right-0 mt-2 w-44 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-10">
                              <button
                                className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-700 hover:bg-gray-50"
                                onClick={() => handleExport(item, 'pdf')}
                              >
                                <FileText className="w-4 h-4 text-red-500" />
                                PDF
                              </button>
                              <button
                                className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-700 hover:bg-gray-50"
                                onClick={() => handleExport(item, 'docx')}
                              >
                                <FileType className="w-4 h-4 text-blue-500" />
                                DOCX
                              </button>
                              <button
                                className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-700 hover:bg-gray-50"
                                onClick={() => handleExport(item, 'html')}
                              >
                                <FileCode className="w-4 h-4 text-orange-500" />
                                HTML
                              </button>
                            </div>
                          )}
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="text-red-500 hover:text-red-700 hover:bg-red-50"
                          onClick={() => handleDelete(item.id)}
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
