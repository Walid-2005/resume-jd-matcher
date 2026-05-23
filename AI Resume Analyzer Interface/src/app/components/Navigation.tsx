import { Sparkles, LogIn, LogOut, Clock, User as UserIcon } from 'lucide-react';
import { Button } from './ui/button';
import { User } from '../../utils/api';

interface NavigationProps {
  user?: User | null;
  onLogin?: () => void;
  onLogout?: () => void;
  onHistory?: () => void;
}

export function Navigation({ user, onLogin, onLogout, onHistory }: NavigationProps) {
  return (
    <nav className="w-full border-b border-gray-100 bg-white fixed top-0 z-50">
      <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg flex items-center justify-center">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <span className="font-semibold text-gray-900">ResuMatch AI</span>
        </div>

        <div className="hidden md:flex items-center gap-8">
          <a href="#features" className="text-gray-600 hover:text-gray-900 transition-colors">
            Features
          </a>
          <a href="#how-it-works" className="text-gray-600 hover:text-gray-900 transition-colors">
            How It Works
          </a>
          <a href="#about" className="text-gray-600 hover:text-gray-900 transition-colors">
            About
          </a>

          {user ? (
            <>
              <button
                onClick={onHistory}
                className="flex items-center gap-1.5 text-gray-600 hover:text-gray-900 transition-colors"
              >
                <Clock className="w-4 h-4" />
                History
              </button>
              <div className="flex items-center gap-3 pl-2 border-l border-gray-200">
                <span className="flex items-center gap-1.5 text-sm text-gray-700">
                  <UserIcon className="w-4 h-4" />
                  {user.username}
                </span>
                <Button variant="ghost" size="sm" onClick={onLogout}>
                  <LogOut className="w-4 h-4 mr-1" />
                  Logout
                </Button>
              </div>
            </>
          ) : (
            onLogin && (
              <Button variant="outline" size="sm" onClick={onLogin}>
                <LogIn className="w-4 h-4 mr-2" />
                Login
              </Button>
            )
          )}
        </div>
      </div>
    </nav>
  );
}
