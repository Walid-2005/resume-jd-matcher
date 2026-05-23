import { useState } from 'react';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Textarea } from '../components/ui/textarea';
import { Input } from '../components/ui/input';
import { Alert, AlertDescription, AlertTitle } from '../components/ui/alert';
import { Upload, FileText, ArrowLeft, AlertCircle, CheckCircle2, Link2, Briefcase, Linkedin } from 'lucide-react';
import { cn } from '../components/ui/utils';
import { fetchJobDescription } from '../../utils/api';

type JobInputMode = 'manual' | 'url';

interface InputPageProps {
  onAnalyze: (resumeFile: File, jobDescription: string) => void;
  onBack: () => void;
}

export function InputPage({ onAnalyze, onBack }: InputPageProps) {
  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [jobDescription, setJobDescription] = useState('');
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Job URL import state
  const [jobInputMode, setJobInputMode] = useState<JobInputMode>('manual');
  const [jobUrl, setJobUrl] = useState('');
  const [isFetchingJob, setIsFetchingJob] = useState(false);
  const [fetchedJob, setFetchedJob] = useState<{ title: string; company: string; location: string; platform: string } | null>(null);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (file.type === 'application/pdf' || file.name.endsWith('.docx') || file.name.endsWith('.doc')) {
        setResumeFile(file);
        setError(null);
      } else {
        setError('Please upload a PDF or DOCX file');
      }
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      if (file.type === 'application/pdf' || file.name.endsWith('.docx') || file.name.endsWith('.doc')) {
        setResumeFile(file);
        setError(null);
      } else {
        setError('Please upload a PDF or DOCX file');
      }
    }
  };

  const handleFetchJob = async () => {
    if (!jobUrl.trim()) {
      setError('Please enter a job listing URL');
      return;
    }
    setError(null);
    setIsFetchingJob(true);
    setFetchedJob(null);
    try {
      const result = await fetchJobDescription(jobUrl.trim());
      setJobDescription(result.description);
      setFetchedJob({
        title: result.title,
        company: result.company,
        location: result.location,
        platform: result.platform,
      });
    } catch (err: any) {
      setError(err.message || 'Failed to fetch job description');
    } finally {
      setIsFetchingJob(false);
    }
  };

  const handleSubmit = () => {
    if (!resumeFile) {
      setError('Please upload a resume file');
      return;
    }
    if (jobDescription.trim().length < 50) {
      setError('Job description must be at least 50 characters');
      return;
    }
    setError(null);
    onAnalyze(resumeFile, jobDescription);
  };

  const canSubmit = resumeFile && jobDescription.trim().length >= 50;

  return (
    <div className="min-h-screen bg-gradient-to-b from-white via-blue-50/30 to-white">
      <div className="max-w-4xl mx-auto px-6 py-12">
        {/* Header */}
        <div className="mb-8">
          <Button
            variant="ghost"
            onClick={onBack}
            className="mb-4"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Home
          </Button>
          <h1 className="text-4xl font-bold text-gray-900 mb-2">Analyze Your Resume</h1>
          <p className="text-gray-600">Upload your resume and paste the job description to get AI-powered insights</p>
        </div>

        {error && (
          <Alert variant="destructive" className="mb-6">
            <AlertCircle className="w-4 h-4" />
            <AlertTitle>Error</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        <div className="grid md:grid-cols-2 gap-6">
          {/* Resume Upload Card */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="w-5 h-5" />
                Upload Resume
              </CardTitle>
              <CardDescription>
                Upload your resume in PDF or DOCX format
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div
                className={cn(
                  "border-2 border-dashed rounded-lg p-8 text-center transition-colors cursor-pointer",
                  dragActive ? "border-blue-500 bg-blue-50" : "border-gray-300 hover:border-gray-400",
                  resumeFile && "border-green-500 bg-green-50"
                )}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
                onClick={() => document.getElementById('file-input')?.click()}
              >
                <input
                  id="file-input"
                  type="file"
                  accept=".pdf,.docx,.doc"
                  onChange={handleFileChange}
                  className="hidden"
                />
                
                {resumeFile ? (
                  <div className="space-y-2">
                    <CheckCircle2 className="w-12 h-12 text-green-600 mx-auto" />
                    <div className="font-semibold text-gray-900">{resumeFile.name}</div>
                    <div className="text-sm text-gray-600">
                      {(resumeFile.size / 1024).toFixed(1)} KB
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        setResumeFile(null);
                      }}
                      className="mt-2"
                    >
                      Change File
                    </Button>
                  </div>
                ) : (
                  <div className="space-y-2">
                    <Upload className="w-12 h-12 text-gray-400 mx-auto" />
                    <div className="font-semibold text-gray-900">
                      Drag and drop your resume here
                    </div>
                    <div className="text-sm text-gray-600">or click to browse</div>
                    <div className="text-xs text-gray-500 mt-2">
                      PDF or DOCX files only
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Job Description Card */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Briefcase className="w-5 h-5" />
                Job Description
              </CardTitle>
              <CardDescription>
                Paste manually or import from a job listing URL
              </CardDescription>
            </CardHeader>
            <CardContent>
              {/* Mode Tabs */}
              <div className="flex border-b border-gray-200 mb-4">
                <button
                  className={cn(
                    "flex items-center gap-1.5 px-4 py-2 text-sm font-medium border-b-2 transition-colors -mb-px",
                    jobInputMode === 'manual'
                      ? "border-blue-500 text-blue-600"
                      : "border-transparent text-gray-500 hover:text-gray-700"
                  )}
                  onClick={() => setJobInputMode('manual')}
                >
                  <FileText className="w-4 h-4" />
                  Paste Manually
                </button>
                <button
                  className={cn(
                    "flex items-center gap-1.5 px-4 py-2 text-sm font-medium border-b-2 transition-colors -mb-px",
                    jobInputMode === 'url'
                      ? "border-blue-500 text-blue-600"
                      : "border-transparent text-gray-500 hover:text-gray-700"
                  )}
                  onClick={() => setJobInputMode('url')}
                >
                  <Link2 className="w-4 h-4" />
                  Import from URL
                </button>
              </div>

              {/* URL Import Section */}
              {jobInputMode === 'url' && (
                <div className="mb-4">
                  <div className="flex gap-2 mb-3">
                    <div className="relative flex-1">
                      <Input
                        value={jobUrl}
                        onChange={(e) => setJobUrl(e.target.value)}
                        placeholder="https://www.linkedin.com/jobs/view/..."
                        className="pl-9"
                        onKeyDown={(e) => { if (e.key === 'Enter') handleFetchJob(); }}
                      />
                      <Link2 className="w-4 h-4 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" />
                    </div>
                    <Button
                      onClick={handleFetchJob}
                      disabled={isFetchingJob || !jobUrl.trim()}
                    >
                      {isFetchingJob ? (
                        <>
                          <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                          Fetching...
                        </>
                      ) : (
                        'Fetch'
                      )}
                    </Button>
                  </div>

                  {/* Supported platforms */}
                  <div className="flex items-center gap-3 text-xs text-gray-400 mb-3">
                    <span>Supported:</span>
                    <span className="flex items-center gap-1">
                      <Linkedin className="w-3.5 h-3.5" />
                      LinkedIn
                    </span>
                    <span className="flex items-center gap-1">
                      <Briefcase className="w-3.5 h-3.5" />
                      Indeed
                    </span>
                  </div>

                  {/* Fetched job info banner */}
                  {fetchedJob && (
                    <div className="bg-green-50 border border-green-200 rounded-lg p-3 mb-3">
                      <div className="flex items-start gap-2">
                        <CheckCircle2 className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-green-800">
                            Job description imported successfully
                          </p>
                          <div className="text-xs text-green-700 mt-1 space-y-0.5">
                            {fetchedJob.title && <p><span className="font-medium">Title:</span> {fetchedJob.title}</p>}
                            {fetchedJob.company && <p><span className="font-medium">Company:</span> {fetchedJob.company}</p>}
                            {fetchedJob.location && <p><span className="font-medium">Location:</span> {fetchedJob.location}</p>}
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Job Description Textarea (always visible) */}
              <Textarea
                value={jobDescription}
                onChange={(e) => {
                  setJobDescription(e.target.value);
                  if (fetchedJob && jobInputMode === 'url') {
                    // User edited fetched text — that's fine, keep the banner
                  }
                }}
                placeholder={
                  jobInputMode === 'url'
                    ? "Job description will appear here after fetching..."
                    : "Paste the job description here..."
                }
                className="min-h-[240px]"
              />
              <div className="mt-2 text-sm text-gray-500">
                {jobDescription.length} characters
                {jobDescription.length < 50 && (
                  <span className="text-red-500 ml-2">
                    (minimum 50 characters required)
                  </span>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Submit Button */}
        <div className="mt-8 flex justify-end">
          <Button
            size="lg"
            onClick={handleSubmit}
            disabled={!canSubmit}
            className="px-8"
          >
            Analyze Resume
            <FileText className="w-4 h-4 ml-2" />
          </Button>
        </div>
      </div>
    </div>
  );
}

