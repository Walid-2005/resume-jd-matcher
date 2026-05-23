export function StatsSection() {
  const stats = [
    { value: '10K+', label: 'Resumes Analyzed' },
    { value: '95%', label: 'Accuracy Rate' },
    { value: '500+', label: 'Job Matches' },
    { value: '4.9/5', label: 'User Rating' },
  ];

  return (
    <section className="w-full py-16 px-6 bg-gradient-to-r from-blue-600 to-indigo-600">
      <div className="max-w-7xl mx-auto">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-8">
          {stats.map((stat, index) => (
            <div key={index} className="text-center">
              <div className="text-4xl font-bold text-white mb-2">
                {stat.value}
              </div>
              <div className="text-blue-100">
                {stat.label}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
