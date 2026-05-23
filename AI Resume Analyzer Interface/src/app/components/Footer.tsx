import { Sparkles, Github, Linkedin, Mail } from 'lucide-react';

export function Footer() {
  return (
    <footer className="w-full bg-gray-50 border-t border-gray-200 py-12 px-6">
      <div className="max-w-7xl mx-auto">
        <div className="grid md:grid-cols-4 gap-8 mb-8">
          {/* Brand */}
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg flex items-center justify-center">
                <Sparkles className="w-5 h-5 text-white" />
              </div>
              <span className="font-semibold text-gray-900">ResuMatch AI</span>
            </div>
            <p className="text-sm text-gray-600">
              AI-powered resume analysis for better career outcomes.
            </p>
          </div>
          
          {/* Product */}
          <div>
            <h4 className="font-semibold text-gray-900 mb-3">Product</h4>
            <ul className="space-y-2">
              <li><a href="#features" className="text-sm text-gray-600 hover:text-gray-900">Features</a></li>
              <li><a href="#how-it-works" className="text-sm text-gray-600 hover:text-gray-900">How It Works</a></li>
              <li><a href="#" className="text-sm text-gray-600 hover:text-gray-900">Pricing</a></li>
            </ul>
          </div>
          
          {/* Company */}
          <div>
            <h4 className="font-semibold text-gray-900 mb-3">Company</h4>
            <ul className="space-y-2">
              <li><a href="#about" className="text-sm text-gray-600 hover:text-gray-900">About</a></li>
              <li><a href="#" className="text-sm text-gray-600 hover:text-gray-900">Team</a></li>
              <li><a href="#" className="text-sm text-gray-600 hover:text-gray-900">Contact</a></li>
            </ul>
          </div>
          
          {/* Social */}
          <div>
            <h4 className="font-semibold text-gray-900 mb-3">Connect</h4>
            <div className="flex items-center gap-3">
              <a href="#" className="w-9 h-9 rounded-lg bg-gray-200 hover:bg-gray-300 flex items-center justify-center transition-colors">
                <Github className="w-4 h-4 text-gray-700" />
              </a>
              <a href="#" className="w-9 h-9 rounded-lg bg-gray-200 hover:bg-gray-300 flex items-center justify-center transition-colors">
                <Linkedin className="w-4 h-4 text-gray-700" />
              </a>
              <a href="#" className="w-9 h-9 rounded-lg bg-gray-200 hover:bg-gray-300 flex items-center justify-center transition-colors">
                <Mail className="w-4 h-4 text-gray-700" />
              </a>
            </div>
          </div>
        </div>
        
        <div className="pt-8 border-t border-gray-200">
          <p className="text-center text-sm text-gray-600">
            © 2025 ResuMatch AI. Final Year Project. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  );
}
