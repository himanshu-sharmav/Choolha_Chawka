import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Button from '../components/UI/Button';
import Card from '../components/UI/Card';
import { 
  Utensils, 
  Clock, 
  Shield, 
  Star, 
  ArrowRight,
  CheckCircle,
  Users,
  Truck
} from 'lucide-react';

const Home: React.FC = () => {
  const { isAuthenticated } = useAuth();

  const features = [
    {
      icon: Utensils,
      title: 'Fresh & Healthy',
      description: 'Home-style meals prepared with fresh ingredients daily'
    },
    {
      icon: Clock,
      title: 'On-Time Delivery',
      description: 'Reliable delivery service that respects your schedule'
    },
    {
      icon: Shield,
      title: 'Hygienic Preparation',
      description: 'Strict hygiene standards maintained in all our kitchens'
    },
    {
      icon: Star,
      title: 'Quality Assured',
      description: 'Consistent quality and taste you can trust every day'
    }
  ];

  const stats = [
    { number: '10,000+', label: 'Happy Customers' },
    { number: '50+', label: 'Partner Mess' },
    { number: '25+', label: 'Cities Served' },
    { number: '4.8/5', label: 'Average Rating' }
  ];

  const plans = [
    {
      type: 'Mess Service',
      description: 'Eat at our partner mess locations',
      features: ['Unlimited meals', 'Multiple locations', 'Flexible timings'],
      startingPrice: '₹2,500/month'
    },
    {
      type: 'Tiffin Service',
      description: 'Fresh meals delivered to your doorstep',
      features: ['Home delivery', 'Custom portions', 'Multiple cuisines'],
      startingPrice: '₹3,000/month'
    }
  ];

  return (
    <div className="bg-gray-900 text-white">
      {/* Hero Section */}
      <section className="relative py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center">
            <h1 className="text-4xl md:text-6xl font-bold text-yellow-400 mb-6">
              Choolha Chawka
            </h1>
            <p className="text-xl md:text-2xl text-gray-300 mb-8 max-w-3xl mx-auto">
              Experience the authentic taste of home-cooked meals with our 
              premium mess and tiffin services
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              {!isAuthenticated ? (
                <>
                  <Link to="/register">
                    <Button size="lg" className="w-full sm:w-auto">
                      Get Started
                      <ArrowRight size={20} className="ml-2" />
                    </Button>
                  </Link>
                  <Link to="/plans">
                    <Button variant="outline" size="lg" className="w-full sm:w-auto">
                      View Plans
                    </Button>
                  </Link>
                </>
              ) : (
                <>
                  <Link to="/dashboard">
                    <Button size="lg" className="w-full sm:w-auto">
                      Go to Dashboard
                      <ArrowRight size={20} className="ml-2" />
                    </Button>
                  </Link>
                  <Link to="/plans">
                    <Button variant="outline" size="lg" className="w-full sm:w-auto">
                      Browse Plans
                    </Button>
                  </Link>
                </>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-gray-800">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-yellow-400 mb-4">
              Why Choose Choolha Chawka?
            </h2>
            <p className="text-xl text-gray-300 max-w-2xl mx-auto">
              We're committed to providing you with the best dining experience
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {features.map((feature, index) => {
              const Icon = feature.icon;
              return (
                <Card key={index} className="text-center">
                  <div className="flex justify-center mb-4">
                    <div className="w-16 h-16 bg-yellow-400 text-black rounded-full flex items-center justify-center">
                      <Icon size={32} />
                    </div>
                  </div>
                  <h3 className="text-xl font-semibold text-yellow-400 mb-2">
                    {feature.title}
                  </h3>
                  <p className="text-gray-300">
                    {feature.description}
                  </p>
                </Card>
              );
            })}
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-8">
            {stats.map((stat, index) => (
              <div key={index} className="text-center">
                <div className="text-3xl md:text-4xl font-bold text-yellow-400 mb-2">
                  {stat.number}
                </div>
                <div className="text-gray-300">
                  {stat.label}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Services Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-gray-800">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-yellow-400 mb-4">
              Our Services
            </h2>
            <p className="text-xl text-gray-300 max-w-2xl mx-auto">
              Choose the service that fits your lifestyle
            </p>
          </div>
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {plans.map((plan, index) => (
              <Card key={index}>
                <div className="flex items-start space-x-4 mb-6">
                  <div className="w-12 h-12 bg-yellow-400 text-black rounded-full flex items-center justify-center">
                    {index === 0 ? <Users size={24} /> : <Truck size={24} />}
                  </div>
                  <div>
                    <h3 className="text-2xl font-semibold text-yellow-400 mb-2">
                      {plan.type}
                    </h3>
                    <p className="text-gray-300 mb-4">
                      {plan.description}
                    </p>
                  </div>
                </div>
                
                <div className="space-y-3 mb-6">
                  {plan.features.map((feature, featureIndex) => (
                    <div key={featureIndex} className="flex items-center space-x-2">
                      <CheckCircle size={16} className="text-yellow-400" />
                      <span className="text-gray-300">{feature}</span>
                    </div>
                  ))}
                </div>
                
                <div className="flex items-center justify-between">
                  <span className="text-2xl font-bold text-yellow-400">
                    {plan.startingPrice}
                  </span>
                  <Link to="/plans">
                    <Button variant="outline">
                      View Plans
                    </Button>
                  </Link>
                </div>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-yellow-400 mb-6">
            Ready to Start Your Food Journey?
          </h2>
          <p className="text-xl text-gray-300 mb-8">
            Join thousands of satisfied customers who trust Choolha Chawka for their daily meals
          </p>
          {!isAuthenticated ? (
            <Link to="/register">
              <Button size="lg">
                Sign Up Now
                <ArrowRight size={20} className="ml-2" />
              </Button>
            </Link>
          ) : (
            <Link to="/plans">
              <Button size="lg">
                Choose Your Plan
                <ArrowRight size={20} className="ml-2" />
              </Button>
            </Link>
          )}
        </div>
      </section>
    </div>
  );
};

export default Home;