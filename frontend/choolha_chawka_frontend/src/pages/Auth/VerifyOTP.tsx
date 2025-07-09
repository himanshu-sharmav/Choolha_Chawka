import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import Button from '../../components/UI/Button';
import Input from '../../components/UI/Input';
import Card from '../../components/UI/Card';
import { Shield, RefreshCw } from 'lucide-react';
import toast from 'react-hot-toast';

const VerifyOTP: React.FC = () => {
  const [otp, setOtp] = useState('');
  const [loading, setLoading] = useState(false);
  const [resendLoading, setResendLoading] = useState(false);
  const [countdown, setCountdown] = useState(60);
  const [canResend, setCanResend] = useState(false);

  const { verifyOTP, resendOTP } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const phone = location.state?.phone;

  useEffect(() => {
    if (!phone) {
      navigate('/register');
      return;
    }

    const timer = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          setCanResend(true);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [phone, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!otp.trim()) {
      toast.error('Please enter the OTP');
      return;
    }

    if (otp.length !== 6) {
      toast.error('OTP must be 6 digits');
      return;
    }

    setLoading(true);
    try {
      const response = await verifyOTP(phone, otp);
      if (response.success) {
        // Check user status to determine next step
        const user = response.user;
        if (user.status === 'registration_complete') {
          navigate('/complete-profile');
        } else {
          navigate('/dashboard');
        }
      }
    } catch (error) {
      console.error('OTP verification error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleResendOTP = async () => {
    setResendLoading(true);
    try {
      const response = await resendOTP(phone);
      if (response.success) {
        toast.success('OTP sent successfully!');
        setCountdown(60);
        setCanResend(false);
      }
    } catch (error) {
      console.error('Resend OTP error:', error);
    } finally {
      setResendLoading(false);
    }
  };

  const formatPhone = (phone: string) => {
    return phone.replace(/(\d{2})(\d{5})(\d{5})/, '+91 $1 $2 $3');
  };

  return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <div className="flex justify-center">
            <div className="w-16 h-16 bg-yellow-400 text-black rounded-full flex items-center justify-center">
              <Shield size={32} />
            </div>
          </div>
          <h2 className="mt-6 text-3xl font-extrabold text-yellow-400">
            Verify Your Phone
          </h2>
          <p className="mt-2 text-sm text-gray-400">
            We've sent a 6-digit code to
          </p>
          <p className="text-yellow-400 font-medium">
            {formatPhone(phone)}
          </p>
        </div>

        <Card>
          <form onSubmit={handleSubmit} className="space-y-6">
            <Input
              label="Enter OTP"
              name="otp"
              type="text"
              value={otp}
              onChange={(e) => setOtp(e.target.value.replace(/\D/g, '').slice(0, 6))}
              placeholder="000000"
              maxLength={6}
              className="text-center text-2xl tracking-widest"
              required
            />

            <Button
              type="submit"
              loading={loading}
              className="w-full"
              size="lg"
            >
              <Shield size={20} className="mr-2" />
              Verify OTP
            </Button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-sm text-gray-400 mb-4">
              Didn't receive the code?
            </p>
            
            {canResend ? (
              <Button
                variant="outline"
                onClick={handleResendOTP}
                loading={resendLoading}
                size="sm"
              >
                <RefreshCw size={16} className="mr-2" />
                Resend OTP
              </Button>
            ) : (
              <p className="text-sm text-yellow-400">
                Resend OTP in {countdown}s
              </p>
            )}
          </div>

          <div className="mt-4 text-center">
            <button
              onClick={() => navigate('/register')}
              className="text-sm text-gray-400 hover:text-yellow-400"
            >
              Change phone number
            </button>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default VerifyOTP;