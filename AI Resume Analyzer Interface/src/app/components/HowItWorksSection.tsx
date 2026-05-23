import { Upload, Cpu, ChartBar } from 'lucide-react';

const steps = [
  {
    icon: Upload,
    number: '01',
    title: 'Upload Your Resume',
    description: 'Simply drag and drop your resume in PDF or DOCX format. Our system supports all standard formats.',
  },
  {
    icon: Cpu,
    number: '02',
    title: 'AI Analysis',
    description: 'Our advanced AI engine analyzes your resume, extracting skills, experience, and qualifications.',
  },
  {
    icon: ChartBar,
    number: '03',
    title: 'Get Insights',
    description: 'Receive detailed match scores, skill gaps, and personalized recommendations for improvement.',
  },
];

export function HowItWorksSection() {
  return (
    <section id="how-it-works" className="w-full py-20 px-6 bg-white">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-16 space-y-4">
          <h2 className="text-4xl font-bold text-gray-900">
            How It Works
          </h2>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Three simple steps to unlock your career potential
          </p>
        </div>
        
        <div className="grid md:grid-cols-3 gap-8 relative">
          {/* Connection Lines - Hidden on mobile */}
          <div 
            className="hidden md:block absolute top-16 h-0.5 bg-gradient-to-r from-blue-200 via-indigo-200 to-blue-200 z-0"
            style={{ width: 'calc(100% - 12rem)', left: '6rem' }}
          />
          
          {steps.map((step, index) => {
            const Icon = step.icon;
            return (
              <div key={index} className="relative z-10">
                <div className="flex flex-col items-center text-center space-y-4">
                  {/* Icon Circle */}
                  <div className="w-24 h-24 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shadow-lg relative">
                    <Icon className="w-10 h-10 text-white" />
                    <div className="absolute -top-2 -right-2 w-8 h-8 bg-white rounded-full flex items-center justify-center shadow-md">
                      <span className="text-sm font-bold text-indigo-600">{step.number}</span>
                    </div>
                  </div>
                  
                  {/* Content */}
                  <div className="space-y-2">
                    <h3 className="text-xl font-semibold text-gray-900">
                      {step.title}
                    </h3>
                    <p className="text-gray-600 max-w-xs">
                      {step.description}
                    </p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}