import React from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { 
  User, 
  LogOut, 
  Settings, 
  Bell, 
  Menu,
  X,
  Home,
  CreditCard,
  Calendar,
  MessageSquare,
  Users,
  BarChart3
} from 'lucide-react';

const Header: React.FC = () => {
  const { user, logout, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [isMenuOpen, setIsMenuOpen] = React.useState(false);

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const isActive = (path: string) => location.pathname === path;

  const customerNavItems = [
    { path: '/dashboard', label: 'Dashboard', icon: Home },
    { path: '/plans', label: 'Plans', icon: CreditCard },
    { path: '/subscriptions', label: 'My Subscriptions', icon: Calendar },
    { path: '/leaves', label: 'Leave Requests', icon: Calendar },
    { path: '/payments', label: 'Payments', icon: CreditCard },
    { path: '/feedback', label: 'Feedback', icon: MessageSquare },
  ];

  const ownerNavItems = [
    { path: '/owner/dashboard', label: 'Dashboard', icon: BarChart3 },
    { path: '/owner/leaves', label: 'Leave Requests', icon: Calendar },
    { path: '/owner/feedback', label: 'Feedback', icon: MessageSquare },
    { path: '/owner/refunds', label: 'Refunds', icon: CreditCard },
    { path: '/owner/users', label: 'Users', icon: Users },
  ];

  const navItems = user?.user_type === 'mess_owner' ? ownerNavItems : customerNavItems;

  return (
    <header className="bg-black text-yellow-400 shadow-lg border-b-2 border-yellow-400">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-yellow-400 text-black rounded-full flex items-center justify-center font-bold">
              CC
            </div>
            <span className="text-xl font-bold">Choolha Chawka</span>
          </Link>

          {/* Desktop Navigation */}
          {isAuthenticated && (
            <nav className="hidden md:flex space-x-6">
              {navItems.map((item) => {
                const Icon = item.icon;
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={`flex items-center space-x-1 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                      isActive(item.path)
                        ? 'bg-yellow-400 text-black'
                        : 'text-yellow-400 hover:bg-yellow-400 hover:text-black'
                    }`}
                  >
                    <Icon size={16} />
                    <span>{item.label}</span>
                  </Link>
                );
              })}
            </nav>
          )}

          {/* User Menu */}
          <div className="flex items-center space-x-4">
            {isAuthenticated ? (
              <>
                <button className="p-2 rounded-full hover:bg-yellow-400 hover:text-black transition-colors">
                  <Bell size={20} />
                </button>
                
                <div className="relative group">
                  <button className="flex items-center space-x-2 p-2 rounded-md hover:bg-yellow-400 hover:text-black transition-colors">
                    <User size={20} />
                    <span className="hidden sm:block">{user?.username}</span>
                  </button>
                  
                  <div className="absolute right-0 mt-2 w-48 bg-black border border-yellow-400 rounded-md shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-50">
                    <div className="py-1">
                      <Link
                        to="/profile"
                        className="flex items-center space-x-2 px-4 py-2 text-sm text-yellow-400 hover:bg-yellow-400 hover:text-black"
                      >
                        <Settings size={16} />
                        <span>Profile Settings</span>
                      </Link>
                      <button
                        onClick={handleLogout}
                        className="flex items-center space-x-2 w-full px-4 py-2 text-sm text-yellow-400 hover:bg-yellow-400 hover:text-black"
                      >
                        <LogOut size={16} />
                        <span>Logout</span>
                      </button>
                    </div>
                  </div>
                </div>
              </>
            ) : (
              <div className="flex items-center space-x-4">
                <Link
                  to="/login"
                  className="text-yellow-400 hover:text-yellow-300 font-medium"
                >
                  Login
                </Link>
                <Link
                  to="/register"
                  className="bg-yellow-400 text-black px-4 py-2 rounded-md font-medium hover:bg-yellow-300 transition-colors"
                >
                  Register
                </Link>
              </div>
            )}

            {/* Mobile menu button */}
            {isAuthenticated && (
              <button
                className="md:hidden p-2 rounded-md hover:bg-yellow-400 hover:text-black transition-colors"
                onClick={() => setIsMenuOpen(!isMenuOpen)}
              >
                {isMenuOpen ? <X size={20} /> : <Menu size={20} />}
              </button>
            )}
          </div>
        </div>

        {/* Mobile Navigation */}
        {isAuthenticated && isMenuOpen && (
          <div className="md:hidden border-t border-yellow-400 py-4">
            <nav className="space-y-2">
              {navItems.map((item) => {
                const Icon = item.icon;
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                      isActive(item.path)
                        ? 'bg-yellow-400 text-black'
                        : 'text-yellow-400 hover:bg-yellow-400 hover:text-black'
                    }`}
                    onClick={() => setIsMenuOpen(false)}
                  >
                    <Icon size={16} />
                    <span>{item.label}</span>
                  </Link>
                );
              })}
            </nav>
          </div>
        )}
      </div>
    </header>
  );
};

export default Header;