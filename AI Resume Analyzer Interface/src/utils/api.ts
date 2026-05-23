export interface AnalysisResults {
  matchScore: number;
  foundSkills: string[];
  missingSkills: string[];
  strengths: string[];
  weaknesses: string[];
  recommendations: string[];
  aiInsight: string;
  historyId?: number | null;
  resumeSkills?: string[];
  experienceLevel?: string;
  // Calibrator diagnostics. scoringFeatures is echoed on feedback submit
  // so the next retraining cycle can learn from real-user rows.
  scoringFeatures?: Record<string, number> | null;
  calibratorDelta?: number;
}

export interface AnalysisHistoryItem {
  id: number;
  matchScore: number;
  foundSkills: string[];
  missingSkills: string[];
  strengths: string[];
  weaknesses: string[];
  recommendations: string[];
  aiInsight: string;
  jobDescription: string;
  createdAt: string;
}

export interface User {
  id: number;
  username: string;
  email: string;
}

export interface AuthResponse {
  status: 'success' | 'error';
  message?: string;
  user?: User;
  authenticated?: boolean;
}

// Use relative paths when served from Django (same origin = no CORS, cookies work).
// Set VITE_API_BASE_URL in .env only when running the Vite dev server separately.
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

// Authentication APIs
export async function register(username: string, email: string, password: string): Promise<AuthResponse> {
  const response = await fetch(`${API_BASE_URL}/api/register/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
    body: JSON.stringify({ username, email, password }),
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.message || 'Registration failed');
  }
  return data;
}

export async function login(username: string, password: string): Promise<AuthResponse> {
  const response = await fetch(`${API_BASE_URL}/api/login/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
    body: JSON.stringify({ username, password }),
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.message || 'Login failed');
  }
  return data;
}

export async function logout(): Promise<AuthResponse> {
  const response = await fetch(`${API_BASE_URL}/api/logout/`, {
    method: 'POST',
    credentials: 'include',
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.message || 'Logout failed');
  }
  return data;
}

export async function checkAuth(): Promise<AuthResponse> {
  const response = await fetch(`${API_BASE_URL}/api/check-auth/`, {
    method: 'GET',
    credentials: 'include',
  });

  const data = await response.json();
  return data;
}

// Resume Analysis API
export async function analyzeResume(resumeFile: File, jobDescription: string): Promise<AnalysisResults> {
  const formData = new FormData();
  formData.append('resume_file', resumeFile);
  formData.append('job_description', jobDescription);

  const response = await fetch(`${API_BASE_URL}/api/analyze/`, {
    method: 'POST',
    body: formData,
    credentials: 'include',
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.message || 'Failed to analyze resume');
  }

  const data = await response.json();
  if (data.status === 'error') {
    throw new Error(data.message || 'Backend returned an error');
  }

  return {
    matchScore: data.matchScore,
    foundSkills: data.foundSkills,
    missingSkills: data.missingSkills,
    strengths: data.strengths,
    weaknesses: data.weaknesses,
    recommendations: data.recommendations,
    aiInsight: data.aiInsight,
    historyId: data.historyId ?? null,
    resumeSkills: data.resumeSkills ?? [],
    experienceLevel: data.experienceLevel ?? 'mid',
    scoringFeatures: data.scoringFeatures ?? null,
    calibratorDelta: data.calibratorDelta ?? 0,
  };
}

// History APIs
export async function getHistory(): Promise<AnalysisHistoryItem[]> {
  const response = await fetch(`${API_BASE_URL}/api/history/`, {
    method: 'GET',
    credentials: 'include',
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.message || 'Failed to fetch history');
  }

  const data = await response.json();
  return data.history;
}

export async function getHistoryDetail(id: number): Promise<AnalysisHistoryItem> {
  const response = await fetch(`${API_BASE_URL}/api/history/${id}/`, {
    method: 'GET',
    credentials: 'include',
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.message || 'Failed to fetch record');
  }

  const data = await response.json();
  return data as AnalysisHistoryItem;
}

export async function deleteHistory(id: number): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/history/${id}/delete/`, {
    method: 'DELETE',
    credentials: 'include',
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.message || 'Failed to delete record');
  }
}

// Job Fetch API
export interface JobFetchResult {
  title: string;
  company: string;
  location: string;
  description: string;
  platform: string;
  url: string;
}

export async function fetchJobDescription(url: string): Promise<JobFetchResult> {
  const response = await fetch(`${API_BASE_URL}/api/fetch-job/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ url }),
  });

  const data = await response.json();
  if (!response.ok || data.status === 'error') {
    throw new Error(data.message || 'Failed to fetch job description');
  }

  return {
    title: data.title,
    company: data.company,
    location: data.location,
    description: data.description,
    platform: data.platform,
    url: data.url,
  };
}

// Job Recommendations API
export interface JobRecommendation {
  title: string;
  company: string;
  location: string;
  required_skills: string[];
  matched_skills: string[];
  missing_skills: string[];
  match_count: number;
  total_skills: number;
  match_percentage: number;
  description: string;
  experience_level: string;
  category: string;
  linkedin_url: string;
}

export async function getJobRecommendations(
  skills: string[],
  experienceLevel: string,
  location: string,
): Promise<JobRecommendation[]> {
  const response = await fetch(`${API_BASE_URL}/api/recommend-jobs/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ skills, experienceLevel, location }),
  });

  const data = await response.json();
  if (!response.ok || data.status === 'error') {
    throw new Error(data.message || 'Failed to get recommendations');
  }

  return data.recommendations;
}

// Export APIs
export type ExportFormat = 'pdf' | 'docx' | 'html';

// Feedback API
export type ScoreRating = 'too_high' | 'accurate' | 'too_low';

export interface FeedbackSnapshot {
  matchScore?: number;
  foundSkills?: string[];
  missingSkills?: string[];
  strengths?: string[];
  weaknesses?: string[];
  jdExcerpt?: string;
  // Calibrator feature vector captured at analysis time.  Stored on the
  // AnalysisFeedback row so the next retraining cycle can use this user's
  // feedback as a labeled training example (label derived from scoreRating).
  features?: Record<string, number> | null;
}

export interface FeedbackPayload {
  historyId?: number | null;
  scoreRating?: ScoreRating | null;
  usefulness?: number | null;   // 1–5
  comment?: string;
  snapshot?: FeedbackSnapshot;
}

export async function submitFeedback(payload: FeedbackPayload): Promise<{ feedbackId: number }> {
  const response = await fetch(`${API_BASE_URL}/api/feedback/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(payload),
  });

  const data = await response.json();
  if (!response.ok || data.status === 'error') {
    throw new Error(data.message || 'Failed to submit feedback');
  }
  return { feedbackId: data.feedbackId };
}

export async function exportReport(data: Record<string, unknown>, format: ExportFormat): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/export/${format}/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    let message = 'Export failed';
    try {
      const err = await response.json();
      message = err.message || message;
    } catch { /* blob response */ }
    throw new Error(message);
  }

  const blob = await response.blob();
  const ext = format === 'docx' ? 'docx' : format;
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `ResuMatch_Report.${ext}`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}
