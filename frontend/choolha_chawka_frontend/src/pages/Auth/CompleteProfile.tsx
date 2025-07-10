import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { authAPI } from '../../services/api';
import Button from '../../components/UI/Button';
import Input from '../../components/UI/Input';
import Select from '../../components/UI/Select';
import Card from '../../components/UI/Card';
import { User, Building, Home } from 'lucide-react';
import toast from 'react-hot-toast';

const CompleteProfile: React.FC = () => {
  const [step, setStep] = useState(1);
  const [userType, setUserType] = useState('');
  const [formData, setFormData] = useState({
    // Common fields
    is_tiffin_user: false,
    is_mess_user: false,
    preferred_delivery_time: '',
    
    // Student fields
    institute: '',
    student_id: '',
    hostel: '',
    
    // Regular user fields
    address: '',
    landmark: '',
    
    // Mess owner fields
    mess_name: '',
    business_address: '',
    business_phone: '',
    business_email: '',
    gst_number: '',
  });
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const { updateUser } = useAuth();
  const navigate = useNavigate();

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    const checked = (e.target as HTMLInputElement).checked;
    
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
    
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const validateStep1 = () => {
    if (!userType) {
      toast.error('Please select your user type');
      return false;
    }
    return true;
  };

  const validateStep2 = () => {
    const newErrors: Record<string, string> = {};

    if (userType === 'student') {
      if (!formData.institute.trim()) newErrors.institute = 'Institute is required';
      if (!formData.hostel.trim()) newErrors.hostel = 'Hostel is required';
      if (!formData.is_tiffin_user && !formData.is_mess_user) {
        toast.error('Please select at least one service type');
        return false;
      }
    } else if (userType === 'regular') {
      if (!formData.address.trim()) newErrors.address = 'Address is required';
      if (!formData.is_tiffin_user && !formData.is_mess_user) {
        toast.error('Please select at least one service type');
        return false;
      }
    } else if (userType === 'mess_owner') {
      if (!formData.mess_name.trim()) newErrors.mess_name = 'Mess name is required';
      if (!formData.business_address.trim()) newErrors.business_address = 'Business address is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleNext = () => {
    if (step === 1 && validateStep1()) {
      setStep(2);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateStep2()) return;

    setLoading(true);
    try {
      const profileData: any = {
        user_type: userType,
      };

      if (userType === 'student') {
        profileData.is_tiffin_user = formData.is_tiffin_user;
        profileData.is_mess_user = formData.is_mess_user;
        profileData.preferred_delivery_time = formData.preferred_delivery_time;
        profileData.student_profile = {
          institute: formData.institute,
          student_id: formData.student_id,
          hostel: formData.hostel,
        };
      } else if (userType === 'regular') {
        profileData.is_tiffin_user = formData.is_tiffin_user;
        profileData.is_mess_user = formData.is_mess_user;
        profileData.preferred_delivery_time = formData.preferred_delivery_time;
        profileData.regular_profile = {
          address: formData.address,
          landmark: formData.landmark,
        };
      } else if (userType === 'mess_owner') {
        profileData.mess_owner_profile = {
          mess_name: formData.mess_name,
          business_address: formData.business_address,
          business_phone: formData.business_phone,
          business_email: formData.business_email,
          gst_number: formData.gst_number,
        };
      }

      const response = await authAPI.completeProfile(profileData);
      
      if (response.data.success) {
        updateUser(response.data.data);
        toast.success('Profile completed successfully!');
        navigate('/dashboard');
      }
    } catch (error: any) {
      const message = error.response?.data?.message || 'Failed to complete profile';
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  const renderStep1 = () => (
    <div className="space-y-6">
      <div className="text-center">
        <h3 className="text-xl font-semibold text-yellow-400 mb-4">
          What describes you best?
        </h3>
      </div>

      <div className="space-y-4">
        <div
          className={`p-4 border-2 rounded-lg cursor-pointer transition-colors ${
            userType === 'student'
              ? 'border-yellow-400 bg-yellow-400 bg-opacity-10'
              : 'border-gray-600 hover:border-yellow-400'
          }`}
          onClick={() => setUserType('student')}
        >
          <div className="flex items-center space-x-3">
            <User className="text-yellow-400" size={24} />
            <div>
              <h4 className="text-white font-medium">Student</h4>
              <p className="text-gray-400 text-sm">
                I'm a student looking for mess or tiffin services
              </p>
            </div>
          </div>
        </div>

        <div
          className={`p-4 border-2 rounded-lg cursor-pointer transition-colors ${
            userType === 'regular'
              ? 'border-yellow-400 bg-yellow-400 bg-opacity-10'
              : 'border-gray-600 hover:border-yellow-400'
          }`}
          onClick={() => setUserType('regular')}
        >
          <div className="flex items-center space-x-3">
            <Home className="text-yellow-400" size={24} />
            <div>
              <h4 className="text-white font-medium">Regular Customer</h4>
              <p className="text-gray-400 text-sm">
                I'm looking for home-style meal delivery services
              </p>
            </div>
          </div>
        </div>

        <div
          className={`p-4 border-2 rounded-lg cursor-pointer transition-colors ${
            userType === 'mess_owner'
              ? 'border-yellow-400 bg-yellow-400 bg-opacity-10'
              : 'border-gray-600 hover:border-yellow-400'
          }`}
          onClick={() => setUserType('mess_owner')}
        >
          <div className="flex items-center space-x-3">
            <Building className="text-yellow-400" size={24} />
            <div>
              <h4 className="text-white font-medium">Mess Owner</h4>
              <p className="text-gray-400 text-sm">
                I want to manage my mess and serve customers
              </p>
            </div>
          </div>
        </div>
      </div>

      <Button
        onClick={handleNext}
        disabled={!userType}
        className="w-full"
        size="lg"
      >
        Continue
      </Button>
    </div>
  );

  const renderStep2 = () => (
    <form onSubmit={handleSubmit} className="space-y-6">
      {userType === 'student' && (
        <>
          <Input
            label="Institute/College Name"
            name="institute"
            value={formData.institute}
            onChange={handleChange}
            error={errors.institute}
            placeholder="Enter your institute name"
            required
          />
          
          <Input
            label="Student ID (Optional)"
            name="student_id"
            value={formData.student_id}
            onChange={handleChange}
            placeholder="Enter your student ID"
          />
          
          <Input
            label="Hostel/Accommodation"
            name="hostel"
            value={formData.hostel}
            onChange={handleChange}
            error={errors.hostel}
            placeholder="Enter your hostel name"
            required
          />

          <div className="space-y-4">
            <label className="block text-sm font-medium text-yellow-400">
              Service Preferences
            </label>
            <div className="space-y-2">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  name="is_tiffin_user"
                  checked={formData.is_tiffin_user}
                  onChange={handleChange}
                  className="h-4 w-4 text-yellow-400 focus:ring-yellow-400 border-gray-600 rounded bg-gray-700"
                />
                <span className="ml-2 text-white">Tiffin Service</span>
              </label>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  name="is_mess_user"
                  checked={formData.is_mess_user}
                  onChange={handleChange}
                  className="h-4 w-4 text-yellow-400 focus:ring-yellow-400 border-gray-600 rounded bg-gray-700"
                />
                <span className="ml-2 text-white">Mess Service</span>
              </label>
            </div>
          </div>

          <Input
            label="Preferred Delivery Time (Optional)"
            name="preferred_delivery_time"
            value={formData.preferred_delivery_time}
            onChange={handleChange}
            placeholder="e.g., 12:00 PM - 1:00 PM"
          />
        </>
      )}

      {userType === 'regular' && (
        <>
          <div>
            <label className="block text-sm font-medium text-yellow-400 mb-1">
              Address
            </label>
            <textarea
              name="address"
              value={formData.address}
              onChange={handleChange}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-yellow-400 focus:border-transparent"
              rows={3}
              placeholder="Enter your complete address"
              required
            />
            {errors.address && (
              <p className="text-sm text-red-400 mt-1">{errors.address}</p>
            )}
          </div>
          
          <Input
            label="Landmark (Optional)"
            name="landmark"
            value={formData.landmark}
            onChange={handleChange}
            placeholder="Nearby landmark"
          />

          <div className="space-y-4">
            <label className="block text-sm font-medium text-yellow-400">
              Service Preferences
            </label>
            <div className="space-y-2">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  name="is_tiffin_user"
                  checked={formData.is_tiffin_user}
                  onChange={handleChange}
                  className="h-4 w-4 text-yellow-400 focus:ring-yellow-400 border-gray-600 rounded bg-gray-700"
                />
                <span className="ml-2 text-white">Tiffin Service</span>
              </label>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  name="is_mess_user"
                  checked={formData.is_mess_user}
                  onChange={handleChange}
                  className="h-4 w-4 text-yellow-400 focus:ring-yellow-400 border-gray-600 rounded bg-gray-700"
                />
                <span className="ml-2 text-white">Mess Service</span>
              </label>
            </div>
          </div>

          <Input
            label="Preferred Delivery Time (Optional)"
            name="preferred_delivery_time"
            value={formData.preferred_delivery_time}
            onChange={handleChange}
            placeholder="e.g., 12:00 PM - 1:00 PM"
          />
        </>
      )}

      {userType === 'mess_owner' && (
        <>
          <Input
            label="Mess Name"
            name="mess_name"
            value={formData.mess_name}
            onChange={handleChange}
            error={errors.mess_name}
            placeholder="Enter your mess name"
            required
          />
          
          <div>
            <label className="block text-sm font-medium text-yellow-400 mb-1">
              Business Address
            </label>
            <textarea
              name="business_address"
              value={formData.business_address}
              onChange={handleChange}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-yellow-400 focus:border-transparent"
              rows={3}
              placeholder="Enter your mess address"
              required
            />
            {errors.business_address && (
              <p className="text-sm text-red-400 mt-1">{errors.business_address}</p>
            )}
          </div>
          
          <Input
            label="Business Phone (Optional)"
            name="business_phone"
            value={formData.business_phone}
            onChange={handleChange}
            placeholder="Business contact number"
          />
          
          <Input
            label="Business Email (Optional)"
            name="business_email"
            type="email"
            value={formData.business_email}
            onChange={handleChange}
            placeholder="Business email address"
          />
          
          <Input
            label="GST Number (Optional)"
            name="gst_number"
            value={formData.gst_number}
            onChange={handleChange}
            placeholder="GST registration number"
          />
        </>
      )}

      <div className="flex space-x-4">
        <Button
          type="button"
          variant="outline"
          onClick={() => setStep(1)}
          className="flex-1"
        >
          Back
        </Button>
        <Button
          type="submit"
          loading={loading}
          className="flex-1"
          size="lg"
        >
          Complete Profile
        </Button>
      </div>
    </form>
  );

  return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <div className="flex justify-center">
            <div className="w-16 h-16 bg-yellow-400 text-black rounded-full flex items-center justify-center">
              <User size={32} />
            </div>
          </div>
          <h2 className="mt-6 text-3xl font-extrabold text-yellow-400">
            Complete Your Profile
          </h2>
          <p className="mt-2 text-sm text-gray-400">
            Step {step} of 2
          </p>
        </div>

        <Card>
          {step === 1 ? renderStep1() : renderStep2()}
        </Card>
      </div>
    </div>
  );
};

export default CompleteProfile;