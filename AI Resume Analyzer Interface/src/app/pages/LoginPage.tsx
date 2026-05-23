import { useState } from 'react';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Alert, AlertDescription, AlertTitle } from '../components/ui/alert';
import { LogIn, UserPlus, ArrowLeft, AlertCircle, Sparkles } from 'lucide-react';
import { login, register, AuthResponse } from '../../utils/api';

interface LoginPageProps {
  onLogin: (user: { id: number; username: string; email: string }) => void;
  onBack: () => void;
}

export function LoginPage({ onLogin, onBack }: LoginPageProps) {
  const [isLogin, setIsLogin] = useState(true);
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      let response: AuthResponse;
      
      if (isLogin) {
        response = await login(username, password);
      } else {
        if (!email) {
          setError('Email is required for registration');
          setLoading(false);
          return;
        }
        response = await register(username, email, password);
      }

      if (response.status === 'success' && response.user) {
        onLogin(response.user);
      }
    } catch (err: any) {
      setError(err.message || 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-white via-blue-50/30 to-white flex items-center justify-center p-6">
      <div className="w-full max-w-md">
        <Button
          variant="ghost"
          onClick={onBack}
          className="mb-6"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Home
        </Button>

        <Card>
          <CardHeader className="text-center">
            <div className="flex items-center justify-center gap-2 mb-4">
              <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
                <Sparkles className="w-6 h-6 text-white" />
              </div>
              <span className="text-2xl font-bold">ResuMatch AI</span>
            </div>
            <CardTitle>{isLogin ? 'Login' : 'Create Account'}</CardTitle>
            <CardDescription>
              {isLogin 
                ? 'Sign in to your account to continue' 
                : 'Create a new account to get started'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex gap-2 mb-6">
              <Button
                type="button"
                variant={isLogin ? 'default' : 'outline'}
                className="flex-1"
                onClick={() => {
                  setIsLogin(true);
                  setError('');
                }}
              >
                <LogIn className="w-4 h-4 mr-2" />
                Login
              </Button>
              <Button
                type="button"
                variant={!isLogin ? 'default' : 'outline'}
                className="flex-1"
                onClick={() => {
                  setIsLogin(false);
                  setError('');
                }}
              >
                <UserPlus className="w-4 h-4 mr-2" />
                Register
              </Button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Username</label>
                <Input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                  placeholder="Enter your username"
                />
              </div>

              {!isLogin && (
                <div>
                  <label className="block text-sm font-medium mb-2">Email</label>
                  <Input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    placeholder="Enter your email"
                  />
                </div>
              )}

              <div>
                <label className="block text-sm font-medium mb-2">Password</label>
                <Input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  placeholder="Enter your password"
                  minLength={6}
                />
              </div>

              {error && (
                <Alert variant="destructive">
                  <AlertCircle className="w-4 h-4" />
                  <AlertTitle>Error</AlertTitle>
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              <Button
                type="submit"
                disabled={loading}
                className="w-full"
                size="lg"
              >
                {loading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                    {isLogin ? 'Logging in...' : 'Registering...'}
                  </>
                ) : (
                  <>
                    {isLogin ? 'Login' : 'Register'}
                    {isLogin ? <LogIn className="w-4 h-4 ml-2" /> : <UserPlus className="w-4 h-4 ml-2" />}
                  </>
                )}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

