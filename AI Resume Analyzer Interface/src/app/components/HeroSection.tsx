import { CircleCheck, Lightbulb, Target, Sparkles } from 'lucide-react';

interface HeroSectionProps {
  onGetStarted?: () => void;
}

export function HeroSection({ onGetStarted }: HeroSectionProps) {
  return (
    <section className="w-full pt-32 pb-20 px-6">
      <div className="max-w-7xl mx-auto">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          {/* Left Content */}
          <div className="space-y-8">
            <div className="space-y-4">
              <h1 className="text-5xl lg:text-6xl font-bold text-gray-900 leading-tight">
                AI-Powered Resume Analyzer and Job Matcher
              </h1>
              
              <p className="text-xl text-gray-600 leading-relaxed">
                Smart resume analysis for better job matches. Get instant feedback, 
                skill insights, and personalized recommendations.
              </p>
            </div>
            
            <div>
              <button
                onClick={onGetStarted}
                className="inline-flex items-center gap-2.5 bg-blue-600 hover:bg-blue-700 text-white font-semibold text-lg px-8 py-4 rounded-full cursor-pointer select-none transition-transform duration-150 hover:-translate-y-0.5 active:translate-y-0"
              >
                <Sparkles className="w-5 h-5" />
                Analyze My Resume
              </button>
            </div>
            
            {/* Feature Highlights */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-4">
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 rounded-lg bg-green-50 flex items-center justify-center flex-shrink-0">
                  <CircleCheck className="w-5 h-5 text-green-600" />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">Instant Match Score</h3>
                  <p className="text-sm text-gray-600">Real-time compatibility</p>
                </div>
              </div>
              
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 rounded-lg bg-blue-50 flex items-center justify-center flex-shrink-0">
                  <Target className="w-5 h-5 text-blue-600" />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">Skill Analysis</h3>
                  <p className="text-sm text-gray-600">Deep skill mapping</p>
                </div>
              </div>
              
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 rounded-lg bg-indigo-50 flex items-center justify-center flex-shrink-0">
                  <Lightbulb className="w-5 h-5 text-indigo-600" />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">AI Recommendations</h3>
                  <p className="text-sm text-gray-600">Personalized insights</p>
                </div>
              </div>
            </div>
          </div>
          
          {/* Right Visual */}
          <div className="relative">
            <div className="absolute inset-0 bg-gradient-to-br from-blue-100 via-indigo-50 to-purple-50 rounded-3xl opacity-40"></div>
            <div className="relative bg-white rounded-3xl shadow-xl p-8 border border-gray-100">
              {/* Abstract AI Visual */}
              <div className="w-full aspect-square rounded-2xl bg-gradient-to-br from-blue-500/20 via-indigo-500/20 to-purple-500/20 flex items-center justify-center overflow-hidden relative">
                {/* Geometric Pattern */}
                <div className="absolute inset-0">
                  <div className="absolute top-1/4 left-1/4 w-32 h-32 bg-blue-300/20 rounded-full"></div>
                  <div className="absolute top-1/2 right-1/4 w-40 h-40 bg-indigo-300/20 rounded-full"></div>
                  <div className="absolute bottom-1/4 left-1/3 w-36 h-36 bg-purple-300/20 rounded-full"></div>
                </div>
                {/* Grid Pattern */}
                <svg className="absolute inset-0 w-full h-full opacity-20" xmlns="http://www.w3.org/2000/svg">
                  <defs>
                    <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
                      <path d="M 40 0 L 0 0 0 40" fill="none" stroke="currentColor" strokeWidth="1" className="text-indigo-600"/>
                    </pattern>
                  </defs>
                  <rect width="100%" height="100%" fill="url(#grid)" />
                </svg>
                {/* Central Icon */}
                <div className="relative z-10 text-indigo-600">
                  <svg className="w-32 h-32" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                  </svg>
                </div>
              </div>
              
              {/* Floating Elements */}
              <div className="absolute -top-4 -right-4 bg-white rounded-2xl shadow-lg p-4 border border-gray-100">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                  <span className="text-sm font-medium text-gray-900">AI Active</span>
                </div>
              </div>
              
              <div className="absolute -bottom-4 -left-4 bg-white rounded-2xl shadow-lg p-4 border border-gray-100">
                <div className="text-sm text-gray-600">Match Accuracy</div>
                <div className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
                  98%
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}