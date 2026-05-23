import { Card } from './ui/card';
import { Brain, FileSearch, TrendingUp, Users, Zap, Shield } from 'lucide-react';

const features = [
  {
    icon: Brain,
    title: 'AI-Powered Analysis',
    description: 'Advanced machine learning algorithms analyze your resume with precision and provide actionable insights.',
    color: 'blue',
  },
  {
    icon: FileSearch,
    title: 'Deep Resume Scanning',
    description: 'Comprehensive analysis of skills, experience, and qualifications to match with job requirements.',
    color: 'indigo',
  },
  {
    icon: TrendingUp,
    title: 'Career Insights',
    description: 'Get personalized career recommendations and identify areas for professional growth.',
    color: 'green',
  },
  {
    icon: Users,
    title: 'Job Matching',
    description: 'Intelligent matching system connects your profile with relevant job opportunities.',
    color: 'purple',
  },
  {
    icon: Zap,
    title: 'Instant Results',
    description: 'Upload your resume and receive comprehensive analysis results within seconds.',
    color: 'yellow',
  },
  {
    icon: Shield,
    title: 'Secure & Private',
    description: 'Your data is encrypted and processed securely. We never share your information.',
    color: 'red',
  },
];

const colorMap = {
  blue: 'bg-blue-50 text-blue-600',
  indigo: 'bg-indigo-50 text-indigo-600',
  green: 'bg-green-50 text-green-600',
  purple: 'bg-purple-50 text-purple-600',
  yellow: 'bg-amber-50 text-amber-600',
  red: 'bg-rose-50 text-rose-600',
};

export function FeaturesSection() {
  return (
    <section id="features" className="w-full py-20 px-6 bg-gradient-to-b from-gray-50 to-white">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-16 space-y-4">
          <h2 className="text-4xl font-bold text-gray-900">
            Powerful Features for Better Results
          </h2>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Everything you need to optimize your resume and land your dream job
          </p>
        </div>
        
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((feature, index) => {
            const Icon = feature.icon;
            return (
              <Card 
                key={index}
                className="p-6 border border-gray-200 hover:border-blue-200 hover:shadow-lg transition-all duration-300 bg-white"
              >
                <div className={`w-12 h-12 rounded-xl ${colorMap[feature.color as keyof typeof colorMap]} flex items-center justify-center mb-4`}>
                  <Icon className="w-6 h-6" />
                </div>
                <h3 className="font-semibold text-gray-900 mb-2">
                  {feature.title}
                </h3>
                <p className="text-gray-600">
                  {feature.description}
                </p>
              </Card>
            );
          })}
        </div>
      </div>
    </section>
  );
}
