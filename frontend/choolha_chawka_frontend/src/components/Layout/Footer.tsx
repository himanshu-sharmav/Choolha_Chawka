import React from 'react';
import { Link } from 'react-router-dom';
import { Mail, Phone, MapPin, Facebook, Twitter, Instagram } from 'lucide-react';

const Footer: React.FC = () => {
  return (
    <footer className="bg-black text-yellow-400 border-t-2 border-yellow-400">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Company Info */}
          <div className="col-span-1 md:col-span-2">
            <div className="flex items-center space-x-2 mb-4">
              <div className="w-8 h-8 bg-yellow-400 text-black rounded-full flex items-center justify-center font-bold">
                CC
              </div>
              <span className="text-xl font-bold">Choolha Chawka</span>
            </div>
            <p className="text-yellow-300 mb-4 max-w-md">
              Delicious home-style meals delivered fresh to your doorstep. 
              Experience the taste of authentic Indian cuisine with our mess and tiffin services.
            </p>
            <div className="flex space-x-4">
              <a href="#" className="text-yellow-400 hover:text-yellow-300 transition-colors">
                <Facebook size={20} />
              </a>
              <a href="#" className="text-yellow-400 hover:text-yellow-300 transition-colors">
                <Twitter size={20} />
              </a>
              <a href="#" className="text-yellow-400 hover:text-yellow-300 transition-colors">
                <Instagram size={20} />
              </a>
            </div>
          </div>

          {/* Quick Links */}
          <div>
            <h3 className="text-lg font-semibold mb-4">Quick Links</h3>
            <ul className="space-y-2">
              <li>
                <Link to="/plans" className="text-yellow-300 hover:text-yellow-400 transition-colors">
                  Our Plans
                </Link>
              </li>
              <li>
                <Link to="/about" className="text-yellow-300 hover:text-yellow-400 transition-colors">
                  About Us
                </Link>
              </li>
              <li>
                <Link to="/contact" className="text-yellow-300 hover:text-yellow-400 transition-colors">
                  Contact
                </Link>
              </li>
              <li>
                <Link to="/faq" className="text-yellow-300 hover:text-yellow-400 transition-colors">
                  FAQ
                </Link>
              </li>
            </ul>
          </div>

          {/* Contact Info */}
          <div>
            <h3 className="text-lg font-semibold mb-4">Contact Us</h3>
            <div className="space-y-3">
              <div className="flex items-center space-x-2">
                <Phone size={16} />
                <span className="text-yellow-300">+91 98765 43210</span>
              </div>
              <div className="flex items-center space-x-2">
                <Mail size={16} />
                <span className="text-yellow-300">support@choolhachawka.com</span>
              </div>
              <div className="flex items-start space-x-2">
                <MapPin size={16} className="mt-1" />
                <span className="text-yellow-300">
                  123 Food Street,<br />
                  Bangalore, Karnataka 560001
                </span>
              </div>
            </div>
          </div>
        </div>

        <div className="border-t border-yellow-400 mt-8 pt-8 flex flex-col md:flex-row justify-between items-center">
          <p className="text-yellow-300 text-sm">
            © 2024 Choolha Chawka. All rights reserved.
          </p>
          <div className="flex space-x-6 mt-4 md:mt-0">
            <Link to="/privacy" className="text-yellow-300 hover:text-yellow-400 text-sm transition-colors">
              Privacy Policy
            </Link>
            <Link to="/terms" className="text-yellow-300 hover:text-yellow-400 text-sm transition-colors">
              Terms of Service
            </Link>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;