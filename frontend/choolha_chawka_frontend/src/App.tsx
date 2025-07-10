import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AuthProvider, useAuth } from './context/AuthContext';
import Layout from './components/Layout/Layout';
import LoadingSpinner from './components/UI/LoadingSpinner';

// Pages
import Home from './pages/Home';
import Login from './pages/Auth/Login';
import Register from './pages/Auth/Register';
import VerifyOTP from './pages/Auth/VerifyOTP';
import CompleteProfile from './pages/Auth/CompleteProfile';
import Dashboard from './pages/Dashboard/Dashboard';

// Protected Route Component
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return isAuthenticated ? <>{children}</> : <Navigate to="/login" />;
};

// Public Route Component (redirect if authenticated)
const PublicRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return !isAuthenticated ? <>{children}</> : <Navigate to="/dashboard" />;
};

const AppRoutes: React.FC = () => {
  return (
    <Routes>
      {/* Public Routes */}
      <Route path="/" element={<Layout />}>
        <Route index element={<Home />} />
        
        {/* Auth Routes - Only accessible when not authenticated */}
        <Route path="/login" element={
          <PublicRoute>
            <Login />
          </PublicRoute>
        } />
        <Route path="/register" element={
          <PublicRoute>
            <Register />
          </PublicRoute>
        } />
        <Route path="/verify-otp" element={
          <PublicRoute>
            <VerifyOTP />
          </PublicRoute>
        } />
        <Route path="/complete-profile" element={
          <PublicRoute>
            <CompleteProfile />
          </PublicRoute>
        } />

        {/* Protected Routes */}
        <Route path="/dashboard" element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        } />

        {/* Placeholder routes for future pages */}
        <Route path="/plans" element={
          <ProtectedRoute>
            <div className="min-h-screen bg-gray-900 flex items-center justify-center">
              <div className="text-center">
                <h1 className="text-3xl font-bold text-yellow-400 mb-4">Plans Page</h1>
                <p className="text-gray-400">Coming Soon...</p>
              </div>
            </div>
          </ProtectedRoute>
        } />

        <Route path="/subscriptions" element={
          <ProtectedRoute>
            <div className="min-h-screen bg-gray-900 flex items-center justify-center">
              <div className="text-center">
                <h1 className="text-3xl font-bold text-yellow-400 mb-4">Subscriptions Page</h1>
                <p className="text-gray-400">Coming Soon...</p>
              </div>
            </div>
          </ProtectedRoute>
        } />

        <Route path="/leaves" element={
          <ProtectedRoute>
            <div className="min-h-screen bg-gray-900 flex items-center justify-center">
              <div className="text-center">
                <h1 className="text-3xl font-bold text-yellow-400 mb-4">Leave Requests Page</h1>
                <p className="text-gray-400">Coming Soon...</p>
              </div>
            </div>
          </ProtectedRoute>
        } />

        <Route path="/payments" element={
          <ProtectedRoute>
            <div className="min-h-screen bg-gray-900 flex items-center justify-center">
              <div className="text-center">
                <h1 className="text-3xl font-bold text-yellow-400 mb-4">Payments Page</h1>
                <p className="text-gray-400">Coming Soon...</p>
              </div>
            </div>
          </ProtectedRoute>
        } />

        <Route path="/feedback" element={
          <ProtectedRoute>
            <div className="min-h-screen bg-gray-900 flex items-center justify-center">
              <div className="text-center">
                <h1 className="text-3xl font-bold text-yellow-400 mb-4">Feedback Page</h1>
                <p className="text-gray-400">Coming Soon...</p>
              </div>
            </div>
          </ProtectedRoute>
        } />

        <Route path="/profile" element={
          <ProtectedRoute>
            <div className="min-h-screen bg-gray-900 flex items-center justify-center">
              <div className="text-center">
                <h1 className="text-3xl font-bold text-yellow-400 mb-4">Profile Page</h1>
                <p className="text-gray-400">Coming Soon...</p>
              </div>
            </div>
          </ProtectedRoute>
        } />

        {/* Owner Routes */}
        <Route path="/owner/*" element={
          <ProtectedRoute>
            <div className="min-h-screen bg-gray-900 flex items-center justify-center">
              <div className="text-center">
                <h1 className="text-3xl font-bold text-yellow-400 mb-4">Owner Dashboard</h1>
                <p className="text-gray-400">Coming Soon...</p>
              </div>
            </div>
          </ProtectedRoute>
        } />

        {/* 404 Route */}
        <Route path="*" element={
          <div className="min-h-screen bg-gray-900 flex items-center justify-center">
            <div className="text-center">
              <h1 className="text-6xl font-bold text-yellow-400 mb-4">404</h1>
              <p className="text-xl text-gray-400 mb-8">Page not found</p>
              <a href="/" className="text-yellow-400 hover:text-yellow-300">
                Go back home
              </a>
            </div>
          </div>
        } />
      </Route>
    </Routes>
  );
};

const App: React.FC = () => {
  return (
    <AuthProvider>
      <Router>
        <div className="App">
          <AppRoutes />
          <Toaster
            position="top-right"
            toastOptions={{
              duration: 4000,
              style: {
                background: '#1f2937',
                color: '#f3f4f6',
                border: '1px solid #fbbf24',
              },
              success: {
                iconTheme: {
                  primary: '#fbbf24',
                  secondary: '#1f2937',
                },
              },
              error: {
                iconTheme: {
                  primary: '#ef4444',
                  secondary: '#1f2937',
                },
              },
            }}
          />
        </div>
      </Router>
    </AuthProvider>
  );
};

export default App;