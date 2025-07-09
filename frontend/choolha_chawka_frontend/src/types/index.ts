export interface User {
  id: number;
  username: string;
  email: string;
  phone: string;
  user_type: 'student' | 'regular' | 'mess_owner';
  status: 'unverified' | 'registration_complete' | 'profile_complete';
  is_tiffin_user: boolean;
  is_mess_user: boolean;
  preferred_delivery_time: string;
  student_profile?: StudentProfile;
  regular_profile?: RegularProfile;
  mess_owner_profile?: MessOwnerProfile;
}

export interface StudentProfile {
  institute: string;
  student_id: string;
  hostel: string;
}

export interface RegularProfile {
  address: string;
  landmark: string;
}

export interface MessOwnerProfile {
  mess_name: string;
  business_address: string;
  business_phone: string;
  business_email: string;
  gst_number: string;
}

export interface Plan {
  id: number;
  code: string;
  name: string;
  description: string;
  service_type: 'mess' | 'tiffin';
  base_price: number;
  included_meals: string[];
  can_add_breakfast: boolean;
  breakfast_addon_price: number;
  duration_days: number;
  is_active: boolean;
}

export interface Subscription {
  id: number;
  plan: Plan;
  breakfast_included: boolean;
  base_price: number;
  breakfast_addon_price: number;
  total_paid: number;
  subscription_type: 'mess' | 'tiffin';
  start_date: string;
  base_end_date: string;
  adjusted_end_date: string;
  leave_days: number;
  status: 'ACTIVE' | 'CANCELLED' | 'EXPIRED' | 'PENDING_PAYMENT' | 'RENEWED';
  cancelled_at?: string;
  days_remaining: number;
  is_active: boolean;
  created_at: string;
}

export interface Leave {
  id: number;
  subscription: Subscription;
  leave_start_date: string;
  leave_end_date: string;
  duration_days: number;
  reason: string;
  status: 'PENDING' | 'APPROVED' | 'REJECTED' | 'AUTO_APPROVED';
  requested_at: string;
  reviewed_at?: string;
  reviewed_by_name?: string;
  admin_comment?: string;
}

export interface Payment {
  id: number;
  subscription: Subscription;
  payment_gateway: string;
  transaction_id: string;
  amount: number;
  amount_inr: number;
  currency: string;
  status: 'INITIATED' | 'SUCCESS' | 'FAILED' | 'PENDING';
  gateway_order_id: string;
  gateway_payment_id: string;
  failure_reason?: string;
  created_at: string;
  updated_at: string;
}

export interface Feedback {
  id: number;
  user: User;
  feedback_type: 'food_complaint' | 'general_feedback';
  subject: string;
  message: string;
  rating?: number;
  subscription?: Subscription;
  meal_date?: string;
  meal_type?: 'breakfast' | 'lunch' | 'dinner';
  priority: 'low' | 'medium' | 'high' | 'urgent';
  status: 'open' | 'in_progress' | 'resolved' | 'closed';
  created_at: string;
  updated_at: string;
  admin_response?: string;
  responded_at?: string;
  responded_by?: User;
  attachments: any[];
  days_since_created: number;
  is_food_complaint: boolean;
  is_urgent: boolean;
}

export interface RefundRequest {
  id: number;
  subscription: Subscription;
  original_payment: Payment;
  requested_at: string;
  amount: number;
  amount_inr: number;
  status: 'PENDING' | 'APPROVED' | 'REJECTED' | 'PROCESSED' | 'PAID';
  admin_comment?: string;
  processed_at?: string;
  refund_transaction_id?: string;
}

export interface AuthTokens {
  access: string;
  refresh: string;
}

export interface ApiResponse<T> {
  success: boolean;
  message?: string;
  data?: T;
  error?: string;
}