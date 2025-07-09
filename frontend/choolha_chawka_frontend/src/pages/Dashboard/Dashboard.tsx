import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { subscriptionsAPI, leavesAPI, paymentsAPI, feedbackAPI } from '../../services/api';
import Card from '../../components/UI/Card';
import Button from '../../components/UI/Button';
import LoadingSpinner from '../../components/UI/LoadingSpinner';
import { 
  Calendar, 
  CreditCard, 
  MessageSquare, 
  Clock, 
  CheckCircle, 
  AlertCircle,
  Plus,
  Eye,
  TrendingUp
} from 'lucide-react';
import { Subscription, Leave, Payment } from '../../types';

const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [activeSubscription, setActiveSubscription] = useState<Subscription | null>(null);
  const [recentLeaves, setRecentLeaves] = useState<Leave[]>([]);
  const [recentPayments, setRecentPayments] = useState<Payment[]>([]);
  const [stats, setStats] = useState({
    totalSubscriptions: 0,
    activeLeaves: 0,
    totalPayments: 0,
    feedbackCount: 0,
  });

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      
      // Fetch active subscription
      try {
        const activeSubResponse = await subscriptionsAPI.getActiveSubscription();
        setActiveSubscription(activeSubResponse.data);
      } catch (error) {
        // No active subscription
        setActiveSubscription(null);
      }

      // Fetch recent leaves
      const leavesResponse = await leavesAPI.getLeaves();
      setRecentLeaves(leavesResponse.data.slice(0, 3));

      // Fetch recent payments
      const paymentsResponse = await paymentsAPI.getPayments();
      setRecentPayments(paymentsResponse.data.slice(0, 3));

      // Fetch all subscriptions for stats
      const subscriptionsResponse = await subscriptionsAPI.getSubscriptions();
      
      // Fetch feedback stats
      let feedbackStats = { total_feedbacks: 0 };
      try {
        const feedbackStatsResponse = await feedbackAPI.getMyStats();
        feedbackStats = feedbackStatsResponse.data;
      } catch (error) {
        console.error('Failed to fetch feedback stats:', error);
      }

      setStats({
        totalSubscriptions: subscriptionsResponse.data.length,
        activeLeaves: leavesResponse.data.filter((leave: Leave) => leave.status === 'PENDING').length,
        totalPayments: paymentsResponse.data.length,
        feedbackCount: feedbackStats.total_feedbacks,
      });

    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'active':
        return 'text-green-400';
      case 'pending':
      case 'pending_payment':
        return 'text-yellow-400';
      case 'cancelled':
      case 'rejected':
        return 'text-red-400';
      case 'expired':
        return 'text-gray-400';
      default:
        return 'text-gray-400';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'active':
      case 'success':
      case 'approved':
        return <CheckCircle size={16} className="text-green-400" />;
      case 'pending':
      case 'pending_payment':
        return <Clock size={16} className="text-yellow-400" />;
      case 'cancelled':
      case 'rejected':
      case 'failed':
        return <AlertCircle size={16} className="text-red-400" />;
      default:
        return <Clock size={16} className="text-gray-400" />;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-yellow-400">
            Welcome back, {user?.username}!
          </h1>
          <p className="text-gray-400 mt-2">
            Here's what's happening with your account
          </p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Card>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Total Subscriptions</p>
                <p className="text-2xl font-bold text-yellow-400">{stats.totalSubscriptions}</p>
              </div>
              <Calendar className="text-yellow-400" size={32} />
            </div>
          </Card>

          <Card>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Pending Leaves</p>
                <p className="text-2xl font-bold text-yellow-400">{stats.activeLeaves}</p>
              </div>
              <Clock className="text-yellow-400" size={32} />
            </div>
          </Card>

          <Card>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Total Payments</p>
                <p className="text-2xl font-bold text-yellow-400">{stats.totalPayments}</p>
              </div>
              <CreditCard className="text-yellow-400" size={32} />
            </div>
          </Card>

          <Card>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Feedback Given</p>
                <p className="text-2xl font-bold text-yellow-400">{stats.feedbackCount}</p>
              </div>
              <MessageSquare className="text-yellow-400" size={32} />
            </div>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Active Subscription */}
          <Card>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-yellow-400">Active Subscription</h2>
              <Link to="/subscriptions">
                <Button variant="outline" size="sm">
                  <Eye size={16} className="mr-2" />
                  View All
                </Button>
              </Link>
            </div>

            {activeSubscription ? (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-lg font-medium text-white">
                      {activeSubscription.plan.name}
                    </h3>
                    <p className="text-gray-400 text-sm">
                      {activeSubscription.subscription_type.charAt(0).toUpperCase() + 
                       activeSubscription.subscription_type.slice(1)} Service
                    </p>
                  </div>
                  <div className="flex items-center space-x-2">
                    {getStatusIcon(activeSubscription.status)}
                    <span className={`text-sm font-medium ${getStatusColor(activeSubscription.status)}`}>
                      {activeSubscription.status.replace('_', ' ')}
                    </span>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-gray-400">Days Remaining</p>
                    <p className="text-white font-medium">{activeSubscription.days_remaining} days</p>
                  </div>
                  <div>
                    <p className="text-gray-400">End Date</p>
                    <p className="text-white font-medium">
                      {new Date(activeSubscription.adjusted_end_date).toLocaleDateString()}
                    </p>
                  </div>
                </div>

                <div className="flex space-x-2">
                  <Link to="/leaves" className="flex-1">
                    <Button variant="outline" size="sm" className="w-full">
                      Request Leave
                    </Button>
                  </Link>
                  <Link to={`/subscriptions/${activeSubscription.id}`} className="flex-1">
                    <Button size="sm" className="w-full">
                      View Details
                    </Button>
                  </Link>
                </div>
              </div>
            ) : (
              <div className="text-center py-8">
                <Calendar className="mx-auto text-gray-600 mb-4" size={48} />
                <p className="text-gray-400 mb-4">No active subscription</p>
                <Link to="/plans">
                  <Button>
                    <Plus size={16} className="mr-2" />
                    Browse Plans
                  </Button>
                </Link>
              </div>
            )}
          </Card>

          {/* Recent Leaves */}
          <Card>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-yellow-400">Recent Leave Requests</h2>
              <Link to="/leaves">
                <Button variant="outline" size="sm">
                  <Eye size={16} className="mr-2" />
                  View All
                </Button>
              </Link>
            </div>

            {recentLeaves.length > 0 ? (
              <div className="space-y-4">
                {recentLeaves.map((leave) => (
                  <div key={leave.id} className="border-b border-gray-700 pb-3 last:border-b-0">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-white font-medium">
                        {new Date(leave.leave_start_date).toLocaleDateString()} - {' '}
                        {new Date(leave.leave_end_date).toLocaleDateString()}
                      </span>
                      <div className="flex items-center space-x-2">
                        {getStatusIcon(leave.status)}
                        <span className={`text-xs font-medium ${getStatusColor(leave.status)}`}>
                          {leave.status.replace('_', ' ')}
                        </span>
                      </div>
                    </div>
                    <p className="text-gray-400 text-sm">
                      {leave.duration_days} day{leave.duration_days !== 1 ? 's' : ''}
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <Calendar className="mx-auto text-gray-600 mb-4" size={48} />
                <p className="text-gray-400 mb-4">No leave requests yet</p>
                <Link to="/leaves">
                  <Button>
                    <Plus size={16} className="mr-2" />
                    Request Leave
                  </Button>
                </Link>
              </div>
            )}
          </Card>

          {/* Recent Payments */}
          <Card>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-yellow-400">Recent Payments</h2>
              <Link to="/payments">
                <Button variant="outline" size="sm">
                  <Eye size={16} className="mr-2" />
                  View All
                </Button>
              </Link>
            </div>

            {recentPayments.length > 0 ? (
              <div className="space-y-4">
                {recentPayments.map((payment) => (
                  <div key={payment.id} className="border-b border-gray-700 pb-3 last:border-b-0">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-white font-medium">
                        ₹{payment.amount_inr}
                      </span>
                      <div className="flex items-center space-x-2">
                        {getStatusIcon(payment.status)}
                        <span className={`text-xs font-medium ${getStatusColor(payment.status)}`}>
                          {payment.status}
                        </span>
                      </div>
                    </div>
                    <p className="text-gray-400 text-sm">
                      {new Date(payment.created_at).toLocaleDateString()}
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <CreditCard className="mx-auto text-gray-600 mb-4" size={48} />
                <p className="text-gray-400">No payments yet</p>
              </div>
            )}
          </Card>

          {/* Quick Actions */}
          <Card>
            <h2 className="text-xl font-semibold text-yellow-400 mb-4">Quick Actions</h2>
            <div className="space-y-3">
              <Link to="/plans" className="block">
                <Button variant="outline" className="w-full justify-start">
                  <Plus size={16} className="mr-2" />
                  Subscribe to New Plan
                </Button>
              </Link>
              
              <Link to="/leaves" className="block">
                <Button variant="outline" className="w-full justify-start">
                  <Calendar size={16} className="mr-2" />
                  Request Leave
                </Button>
              </Link>
              
              <Link to="/feedback" className="block">
                <Button variant="outline" className="w-full justify-start">
                  <MessageSquare size={16} className="mr-2" />
                  Give Feedback
                </Button>
              </Link>
              
              <Link to="/profile" className="block">
                <Button variant="outline" className="w-full justify-start">
                  <TrendingUp size={16} className="mr-2" />
                  Update Profile
                </Button>
              </Link>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;