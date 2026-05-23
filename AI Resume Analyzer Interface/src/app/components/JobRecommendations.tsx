import { useState } from 'react';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './ui/card';
import { Badge } from './ui/badge';
import { Input } from './ui/input';
import {
  Briefcase, MapPin, ExternalLink, Search, Linkedin,
  ChevronDown, ChevronUp, CheckCircle2, XCircle, Sparkles,
} from 'lucide-react';
import { JobRecommendation, getJobRecommendations } from '../../utils/api';

interface JobRecommendationsProps {
  resumeSkills: string[];
  experienceLevel: string;
}

export function JobRecommendations({ resumeSkills, experienceLevel }: JobRecommendationsProps) {
  const [location, setLocation] = useState('');
  const [recommendations, setRecommendations] = useState<JobRecommendation[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasFetched, setHasFetched] = useState(false);
  const [expandedId, setExpandedId] = useState<number | null>(null);

  async function handleSearch() {
    setLoading(true);
    setError(null);
    try {
      const data = await getJobRecommendations(resumeSkills, experienceLevel, location);
      setRecommendations(data);
      setHasFetched(true);
    } catch (err: any) {
      setError(err.message || 'Failed to get recommendations');
    } finally {
      setLoading(false);
    }
  }

  function getMatchColor(pct: number) {
    if (pct >= 70) return 'text-green-600';
    if (pct >= 40) return 'text-yellow-600';
    return 'text-blue-600';
  }

  function getMatchBg(pct: number) {
    if (pct >= 70) return 'bg-green-50 border-green-200';
    if (pct >= 40) return 'bg-yellow-50 border-yellow-200';
    return 'bg-blue-50 border-blue-200';
  }

  function getCategoryIcon(category: string) {
    const colors: Record<string, string> = {
      technology: 'bg-blue-100 text-blue-700',
      ai: 'bg-violet-100 text-violet-700',
      data: 'bg-purple-100 text-purple-700',
      devops: 'bg-cyan-100 text-cyan-700',
      security: 'bg-red-100 text-red-700',
      it: 'bg-sky-100 text-sky-700',
      engineering: 'bg-slate-100 text-slate-700',
      management: 'bg-amber-100 text-amber-700',
      marketing: 'bg-pink-100 text-pink-700',
      sales: 'bg-orange-100 text-orange-700',
      finance: 'bg-emerald-100 text-emerald-700',
      healthcare: 'bg-rose-100 text-rose-700',
      legal: 'bg-indigo-100 text-indigo-700',
      education: 'bg-yellow-100 text-yellow-700',
      media: 'bg-fuchsia-100 text-fuchsia-700',
      hr: 'bg-lime-100 text-lime-700',
      operations: 'bg-stone-100 text-stone-700',
      hospitality: 'bg-teal-100 text-teal-700',
      real_estate: 'bg-green-100 text-green-700',
      executive: 'bg-zinc-100 text-zinc-700',
      science: 'bg-blue-100 text-blue-800',
      trades: 'bg-amber-100 text-amber-800',
      sports: 'bg-green-100 text-green-800',
      public_service: 'bg-sky-100 text-sky-800',
      writing: 'bg-neutral-100 text-neutral-700',
    };
    return colors[category] || 'bg-gray-100 text-gray-700';
  }

  return (
    <Card className="bg-gradient-to-br from-indigo-50 via-white to-blue-50 border-indigo-200">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-xl">
          <Briefcase className="w-6 h-6 text-indigo-600" />
          Job Recommendations
        </CardTitle>
        <CardDescription>
          Discover roles that match your skills — with direct links to LinkedIn job listings
        </CardDescription>
      </CardHeader>
      <CardContent>
        {/* Search bar */}
        <div className="flex gap-2 mb-6">
          <div className="relative flex-1">
            <Input
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              placeholder="Enter your preferred location (e.g. London, UK)"
              className="pl-9 bg-white"
              onKeyDown={(e) => { if (e.key === 'Enter') handleSearch(); }}
            />
            <MapPin className="w-4 h-4 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" />
          </div>
          <Button onClick={handleSearch} disabled={loading}>
            {loading ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                Searching...
              </>
            ) : (
              <>
                <Search className="w-4 h-4 mr-2" />
                Find Jobs
              </>
            )}
          </Button>
        </div>

        {error && (
          <div className="text-red-600 text-sm mb-4 p-3 bg-red-50 rounded-lg border border-red-200">
            {error}
          </div>
        )}

        {/* Results */}
        {hasFetched && recommendations.length === 0 && !loading && (
          <div className="text-center py-10">
            <Briefcase className="w-10 h-10 text-gray-300 mx-auto mb-3" />
            <p className="text-gray-500">No matching roles found for your current skill set.</p>
            <p className="text-gray-400 text-sm mt-1">Try broadening your search or adding more skills to your resume.</p>
          </div>
        )}

        {recommendations.length > 0 && (
          <div className="space-y-3">
            <p className="text-sm text-gray-500 mb-2">
              Found <strong>{recommendations.length}</strong> roles matching your profile — sorted by highest skill match
            </p>

            {recommendations.map((job, index) => {
              const isExpanded = expandedId === index;
              return (
                <div
                  key={index}
                  className={`rounded-xl border bg-white transition-all ${
                    isExpanded ? 'shadow-md' : 'hover:shadow-sm'
                  }`}
                >
                  {/* Main row */}
                  <div className="p-4">
                    <div className="flex items-start justify-between gap-3">
                      {/* Left: info */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1.5 flex-wrap">
                          <h3 className="font-semibold text-gray-900">{job.title}</h3>
                          <Badge className={`text-xs ${getCategoryIcon(job.category)}`}>
                            {job.category}
                          </Badge>
                        </div>

                        <div className="flex items-center gap-4 text-sm text-gray-500 mb-2">
                          <span className="flex items-center gap-1">
                            <MapPin className="w-3.5 h-3.5" />
                            {job.location}
                          </span>
                          <span>{job.experience_level} experience</span>
                        </div>

                        <p className="text-sm text-gray-600 line-clamp-2">{job.description}</p>

                        {/* Skill match bar */}
                        <div className="mt-3 flex items-center gap-3">
                          <div className="flex-1 max-w-[200px]">
                            <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                              <div
                                className={`h-full rounded-full transition-all ${
                                  job.match_percentage >= 70 ? 'bg-green-500' :
                                  job.match_percentage >= 40 ? 'bg-yellow-500' : 'bg-blue-500'
                                }`}
                                style={{ width: `${job.match_percentage}%` }}
                              />
                            </div>
                          </div>
                          <span className={`text-sm font-semibold ${getMatchColor(job.match_percentage)}`}>
                            {job.match_percentage}% skill match
                          </span>
                          <span className="text-xs text-gray-400">
                            ({job.match_count}/{job.total_skills} skills)
                          </span>
                        </div>
                      </div>

                      {/* Right: actions */}
                      <div className="flex flex-col items-end gap-2 flex-shrink-0">
                        <a
                          href={job.linkedin_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1.5 px-3 py-2 bg-[#0A66C2] text-white text-sm font-medium rounded-lg hover:bg-[#004182] transition-colors"
                        >
                          <Linkedin className="w-4 h-4" />
                          View on LinkedIn
                        </a>
                        <button
                          onClick={() => setExpandedId(isExpanded ? null : index)}
                          className="text-xs text-gray-400 hover:text-gray-600 flex items-center gap-1"
                        >
                          {isExpanded ? (
                            <><ChevronUp className="w-3.5 h-3.5" /> Less detail</>
                          ) : (
                            <><ChevronDown className="w-3.5 h-3.5" /> More detail</>
                          )}
                        </button>
                      </div>
                    </div>
                  </div>

                  {/* Expanded detail */}
                  {isExpanded && (
                    <div className="px-4 pb-4 border-t border-gray-100 pt-3">
                      <div className="grid md:grid-cols-2 gap-4">
                        <div>
                          <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2 flex items-center gap-1">
                            <CheckCircle2 className="w-3.5 h-3.5 text-green-500" />
                            Your matching skills
                          </p>
                          <div className="flex flex-wrap gap-1.5">
                            {job.matched_skills.map((skill, i) => (
                              <Badge key={i} className="bg-green-100 text-green-800 text-xs">
                                {skill}
                              </Badge>
                            ))}
                          </div>
                        </div>
                        {job.missing_skills.length > 0 && (
                          <div>
                            <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2 flex items-center gap-1">
                              <XCircle className="w-3.5 h-3.5 text-orange-500" />
                              Skills to develop
                            </p>
                            <div className="flex flex-wrap gap-1.5">
                              {job.missing_skills.map((skill, i) => (
                                <Badge key={i} variant="outline" className="border-orange-200 text-orange-700 text-xs">
                                  {skill}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {/* Initial state - not yet searched */}
        {!hasFetched && !loading && (
          <div className="text-center py-8">
            <Sparkles className="w-10 h-10 text-indigo-300 mx-auto mb-3" />
            <p className="text-gray-500">Enter your preferred location and click <strong>Find Jobs</strong></p>
            <p className="text-gray-400 text-sm mt-1">
              We'll match your {resumeSkills.length} detected skills against real job roles
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
