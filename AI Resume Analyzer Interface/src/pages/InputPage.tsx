import React, { useState } from 'react';
import { Button } from '../components/Button';
import { Card } from '../components/Card';
import { FileUpload } from '../components/FileUpload';
import { InfoMessage } from '../components/InfoMessage';
import { ArrowLeft, Sparkles, FileText, Clipboard, Zap, CheckCircle2 } from 'lucide-react';

interface InputPageProps {
  onAnalyze: (resumeFile: File | null, jobDescription: string) => void;
  onBack: () => void;
  error?: string | null;
}

export function InputPage({ onAnalyze, onBack, error }: InputPageProps) {
  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [jobDescription, setJobDescription] = useState('');
  
  const canSubmit = resumeFile && jobDescription.trim().length > 50;
  
  const handleSubmit = () => {
    if (canSubmit) {
      onAnalyze(resumeFile, jobDescription);
    }
  };
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 via-purple-50 to-pink-50 relative overflow-hidden">
      {/* Animated background elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 left-0 w-96 h-96 bg-blue-300 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob"></div>
        <div className="absolute top-0 right-0 w-96 h-96 bg-purple-300 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-2000"></div>
        <div className="absolute bottom-0 left-1/2 w-96 h-96 bg-pink-300 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-4000"></div>
      </div>

      {/* Header */}
      <header className="relative px-6 py-6 border-b border-slate-200/50 bg-white/60 backdrop-blur-md z-10">
        <div className="max-w-7xl mx-auto flex items-center gap-4">
          <Button variant="secondary" size="sm" onClick={onBack} className="hover:scale-105 transition-transform">
            <ArrowLeft className="w-4 h-4" />
          </Button>
          <div className="flex items-center gap-3">
            <div className="relative">
              <Sparkles className="w-7 h-7 text-blue-600" />
              <div className="absolute top-0 left-0 w-7 h-7 text-blue-400 animate-ping opacity-75">
                <Sparkles className="w-7 h-7" />
              </div>
            </div>
            <span className="text-xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              ResuMatch AI
            </span>
          </div>
        </div>
      </header>
      
      {/* Main Content - Full Height */}
      <main className="relative px-6 py-8 min-h-[calc(100vh-88px)] flex items-center z-10">
        <div className="max-w-7xl mx-auto w-full">
          {/* Title Section */}
          <div className="text-center mb-12">
            <h1 className="text-4xl md:text-5xl lg:text-6xl font-extrabold text-slate-900 mb-4">
              Analyze Your <span className="bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">Resume</span>
            </h1>
            <p className="text-xl md:text-2xl text-slate-600 max-w-2xl mx-auto">
              Upload your resume and paste the job description to get instant AI-powered insights
            </p>
          </div>
          
          {/* Two Column Layout */}
          <div className="grid lg:grid-cols-2 gap-8 items-start">
            {/* Step 1: Resume Upload - Left Side */}
            <div className="space-y-6">
              <Card className="bg-white/80 backdrop-blur-sm border-2 border-blue-100 shadow-xl hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-1 h-full">
                <div className="flex items-center gap-4 mb-6">
                  <div className="relative">
                    <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl flex items-center justify-center shadow-lg">
                      <span className="text-xl font-bold text-white">1</span>
                    </div>
                    <div className="absolute -top-1 -right-1 w-4 h-4 bg-blue-400 rounded-full border-2 border-white animate-pulse"></div>
                  </div>
                  <div>
                    <h3 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
                      <FileText className="w-6 h-6 text-blue-600" />
                      Upload Your Resume
                    </h3>
                    <p className="text-slate-500 text-sm">PDF or DOCX format</p>
                  </div>
                  {resumeFile && (
                    <div className="ml-auto">
                      <CheckCircle2 className="w-8 h-8 text-green-500" />
                    </div>
                  )}
                </div>
                
                <FileUpload onFileSelect={setResumeFile} />
                
                <InfoMessage type="info" className="mt-4">
                  <strong>Supported formats:</strong> PDF and DOCX. Make sure your resume is up-to-date and includes your skills, experience, and education.
                </InfoMessage>
              </Card>
            </div>
            
            {/* Step 2: Job Description - Right Side */}
            <div className="space-y-6">
              <Card className="bg-white/80 backdrop-blur-sm border-2 border-purple-100 shadow-xl hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-1 h-full flex flex-col">
                <div className="flex items-center gap-4 mb-6">
                  <div className="relative">
                    <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl flex items-center justify-center shadow-lg">
                      <span className="text-xl font-bold text-white">2</span>
                    </div>
                    <div className="absolute -top-1 -right-1 w-4 h-4 bg-purple-400 rounded-full border-2 border-white animate-pulse"></div>
                  </div>
                  <div>
                    <h3 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
                      <Clipboard className="w-6 h-6 text-purple-600" />
                      Paste Job Description
                    </h3>
                    <p className="text-slate-500 text-sm">Minimum 50 characters</p>
                  </div>
                  {jobDescription.length >= 50 && (
                    <div className="ml-auto">
                      <CheckCircle2 className="w-8 h-8 text-green-500" />
                    </div>
                  )}
                </div>
                
                <div className="flex-1 flex flex-col">
                  <textarea
                    value={jobDescription}
                    onChange={(e) => setJobDescription(e.target.value)}
                    placeholder="Paste the complete job description here, including required skills, qualifications, and responsibilities..."
                    className="flex-1 w-full p-6 border-2 border-slate-300 rounded-xl resize-none focus:outline-none focus:ring-4 focus:ring-purple-500/20 focus:border-purple-500 transition-all text-slate-700 placeholder-slate-400 font-medium"
                    style={{ minHeight: '300px' }}
                  />
                  
                  {/* Character Counter with Progress */}
                  <div className="mt-4 space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <small className={`font-semibold ${
                          jobDescription.length < 50 ? 'text-slate-500' : 'text-green-600'
                        }`}>
                          {jobDescription.length} characters
                        </small>
                        {jobDescription.length < 50 && (
                          <span className="text-xs text-slate-400">(minimum 50 required)</span>
                        )}
                      </div>
                      {jobDescription.length >= 50 && (
                        <div className="flex items-center gap-2 text-green-600 font-semibold">
                          <CheckCircle2 className="w-4 h-4" />
                          <small>Ready to analyze</small>
                        </div>
                      )}
                    </div>
                    {/* Progress Bar */}
                    <div className="w-full h-2 bg-slate-200 rounded-full overflow-hidden">
                      <div 
                        className={`h-full transition-all duration-300 ${
                          jobDescription.length >= 50 
                            ? 'bg-gradient-to-r from-green-500 to-emerald-500' 
                            : 'bg-gradient-to-r from-blue-500 to-purple-500'
                        }`}
                        style={{ width: `${Math.min((jobDescription.length / 50) * 100, 100)}%` }}
                      ></div>
                    </div>
                  </div>
                </div>
              </Card>
            </div>
          </div>
          
          {/* Submit Button Section */}
          <div className="mt-12 flex flex-col items-center gap-6">
            <Button 
              onClick={handleSubmit} 
              disabled={!canSubmit}
              size="lg"
              className={`group relative overflow-hidden transform transition-all duration-300 ${
                canSubmit 
                  ? 'hover:scale-105 shadow-2xl bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 hover:from-blue-500 hover:via-purple-500 hover:to-pink-500' 
                  : 'shadow-lg'
              }`}
            >
              <span className="relative z-10 flex items-center gap-3 text-lg font-bold">
                <Sparkles className={`w-6 h-6 ${canSubmit ? 'animate-pulse' : ''}`} />
                Generate Match Score
                {canSubmit && <Zap className="w-5 h-5 group-hover:rotate-12 transition-transform" />}
              </span>
              {canSubmit && (
                <div className="absolute inset-0 bg-gradient-to-r from-pink-600 via-purple-600 to-blue-600 opacity-0 group-hover:opacity-100 transition-opacity"></div>
              )}
            </Button>
            
            {!canSubmit && (
              <div className="text-center space-y-2">
                <p className="text-slate-500 font-medium">
                  {!resumeFile && !jobDescription && 'Please upload a resume and provide a job description to continue'}
                  {!resumeFile && jobDescription && 'Please upload a resume file to continue'}
                  {resumeFile && jobDescription.length < 50 && 'Please provide a job description (minimum 50 characters)'}
                </p>
                <div className="flex items-center justify-center gap-4 text-sm text-slate-400">
                  <div className={`flex items-center gap-2 ${resumeFile ? 'text-green-600' : ''}`}>
                    <div className={`w-2 h-2 rounded-full ${resumeFile ? 'bg-green-500' : 'bg-slate-300'}`}></div>
                    Resume uploaded
                  </div>
                  <div className={`flex items-center gap-2 ${jobDescription.length >= 50 ? 'text-green-600' : ''}`}>
                    <div className={`w-2 h-2 rounded-full ${jobDescription.length >= 50 ? 'bg-green-500' : 'bg-slate-300'}`}></div>
                    Job description ready
                  </div>
                </div>
              </div>
            )}

            {/* Error Message */}
            {error && (
              <InfoMessage type="error" className="max-w-2xl">
                <strong>Error:</strong> {error}
              </InfoMessage>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
