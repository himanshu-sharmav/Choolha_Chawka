import axios, { AxiosResponse } from 'axios';
import { AuthTokens, User, Plan, Subscription, Leave, Payment, Feedback, RefundRequest } from '../types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Token management
const getToken = () => localStorage.getItem('access_token');
const getRefreshToken = () => localStorage.getItem('refresh_token');
const setTokens = (tokens: AuthTokens) => {
  localStorage.setItem('access_token', tokens.access);
  localStorage.setItem('refresh_token', tokens.refresh);
};
const clearTokens = () => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user');
};

// Request interceptor to add auth token
api.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor to handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      const refreshToken = getRefreshToken();
      if (refreshToken) {
        try {
          const response = await axios.post(`${API_BASE_URL}/accounts/token/refresh/`, {
            refresh: refreshToken,
          });
          
          const newToken = response.data.access;
          localStorage.setItem('access_token', newToken);
          originalRequest.headers.Authorization = `Bearer ${newToken}`;
          
          return api(originalRequest);
        } catch (refreshError) {
          clearTokens();
          window.location.href = '/login';
        }
      } else {
        clearTokens();
        window.location.href = '/login';
      }
    }
    
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  register: (data: {
    username: string;
    email: string;
    phone: string;
    password: string;
    confirm_password: string;
  }) => api.post('/accounts/register/', data),

  verifyOTP: (data: { phone: string; otp: string }) =>
    api.post('/accounts/verify-otp/', data),

  resendOTP: (data: { phone: string }) =>
    api.post('/accounts/resend-otp/', data),

  login: (data: { username: string; password: string }) =>
    api.post('/accounts/login/', data),

  logout: (data: { refresh: string }) =>
    api.post('/accounts/logout/', data),

  getProfile: () => api.get('/accounts/profile/'),

  completeProfile: (data: any) =>
    api.post('/accounts/complete-profile/', data),

  changePassword: (data: {
    old_password: string;
    new_password: string;
    confirm_password: string;
  }) => api.post('/accounts/change-password/', data),

  passwordReset: (data: { email: string }) =>
    api.post('/accounts/password-reset/', data),

  passwordResetConfirm: (data: {
    uidb64: string;
    token: string;
    new_password: string;
    confirm_password: string;
  }) => api.post('/accounts/password-reset-confirm/', data),
};

// Plans API
export const plansAPI = {
  getPlans: (serviceType?: string) => {
    const params = serviceType ? { service_type: serviceType } : {};
    return api.get('/subscriptions/plans/', { params });
  },
  getPlan: (id: number) => api.get(`/subscriptions/plans/${id}/`),
};

// Subscriptions API
export const subscriptionsAPI = {
  getSubscriptions: () => api.get('/subscriptions/subscriptions/'),
  getSubscription: (id: number) => api.get(`/subscriptions/subscriptions/${id}/`),
  createSubscription: (data: { plan: number; breakfast_included: boolean }) =>
    api.post('/subscriptions/subscriptions/', data),
  getActiveSubscription: () => api.get('/subscriptions/subscriptions/active/'),
  cancelSubscription: (id: number) =>
    api.post(`/subscriptions/subscriptions/${id}/cancel/`),
  renewSubscription: (id: number) =>
    api.post(`/subscriptions/subscriptions/${id}/renew/`),
};

// Leaves API
export const leavesAPI = {
  getLeaves: () => api.get('/subscriptions/leaves/'),
  createLeave: (data: {
    subscription: number;
    leave_start_date: string;
    leave_end_date: string;
    reason: string;
  }) => api.post('/subscriptions/leaves/', data),
  getLeave: (id: number) => api.get(`/subscriptions/leaves/${id}/`),
};

// Owner Leaves API (for mess owners)
export const ownerLeavesAPI = {
  getLeaves: () => api.get('/owner/leaves/'),
  getPendingLeaves: () => api.get('/owner/leaves/pending/'),
  approveLeave: (id: number, data: { admin_comment?: string }) =>
    api.post(`/owner/leaves/${id}/approve/`, data),
  rejectLeave: (id: number, data: { admin_comment?: string }) =>
    api.post(`/owner/leaves/${id}/reject/`, data),
  getDashboardStats: () => api.get('/owner/leaves/dashboard_stats/'),
};

// Payments API
export const paymentsAPI = {
  getPayments: () => api.get('/payments/payments/'),
  getPayment: (id: number) => api.get(`/payments/payments/${id}/`),
  getReceipt: (id: number) => api.get(`/payments/payments/${id}/receipt/`),
  getReceiptPDF: (id: number) => api.get(`/payments/payments/${id}/receipt_pdf/`),
  
  // Razorpay Orders
  createOrder: (data: { subscription: number }) =>
    api.post('/payments/orders/', data),
  verifyPayment: (data: {
    razorpay_order_id: string;
    razorpay_payment_id: string;
    razorpay_signature: string;
  }) => api.post('/payments/orders/verify_payment/', data),
};

// Refunds API
export const refundsAPI = {
  getRefunds: () => api.get('/payments/refunds/'),
  getPendingRefunds: () => api.get('/payments/refunds/pending/'),
  getApprovedRefunds: () => api.get('/payments/refunds/approved/'),
  approveRefund: (id: number, data: { admin_comment?: string }) =>
    api.post(`/payments/refunds/${id}/approve/`, data),
  rejectRefund: (id: number, data: { admin_comment?: string }) =>
    api.post(`/payments/refunds/${id}/reject/`, data),
  markRefundPaid: (id: number, data: { admin_comment?: string }) =>
    api.post(`/payments/refunds/${id}/mark_paid/`, data),
};

// Feedback API
export const feedbackAPI = {
  getFeedbacks: () => api.get('/feedback/'),
  createFeedback: (data: {
    feedback_type: string;
    subject: string;
    message: string;
    rating?: number;
    subscription?: number;
    meal_date?: string;
    meal_type?: string;
  }) => api.post('/feedback/', data),
  getFeedback: (id: number) => api.get(`/feedback/${id}/`),
  getMyStats: () => api.get('/feedback/my_stats/'),
  
  // Admin feedback
  getAdminFeedbacks: () => api.get('/feedback/admin/feedback/'),
  respondToFeedback: (id: number, data: { admin_response: string }) =>
    api.post(`/feedback/admin/feedback/${id}/respond/`, data),
  updateFeedbackStatus: (id: number, data: { status: string }) =>
    api.patch(`/feedback/admin/feedback/${id}/update_status/`, data),
  getDashboardStats: () => api.get('/feedback/admin/feedback/dashboard_stats/'),
  getUrgentComplaints: () => api.get('/feedback/admin/feedback/urgent_complaints/'),
  getPendingResponses: () => api.get('/feedback/admin/feedback/pending_responses/'),
};

// Notifications API
export const notificationsAPI = {
  getLogs: () => api.get('/notifications/logs/'),
  getStats: () => api.get('/notifications/logs/stats/'),
  getByType: () => api.get('/notifications/logs/by_type/'),
};

export { setTokens, clearTokens, getToken };
export default api;