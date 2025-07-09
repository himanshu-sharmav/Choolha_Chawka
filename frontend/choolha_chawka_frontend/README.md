# Choolha Chawka Frontend

A modern React TypeScript frontend for the Choolha Chawka food subscription management system.

## 🚀 Features

- **Modern React with TypeScript** - Type-safe development
- **Responsive Design** - Works on all devices
- **Dark Theme with Yellow Accents** - Beautiful black and yellow color scheme
- **Authentication System** - Complete user registration, login, and profile management
- **Dashboard** - Comprehensive user dashboard with statistics
- **Real-time Updates** - Live data updates and notifications
- **API Integration** - Full integration with Django backend
- **Toast Notifications** - User-friendly feedback system

## 🛠️ Tech Stack

- **React 18** - Latest React with hooks
- **TypeScript** - Type safety and better development experience
- **Tailwind CSS** - Utility-first CSS framework
- **React Router** - Client-side routing
- **Axios** - HTTP client for API calls
- **React Hot Toast** - Beautiful toast notifications
- **Lucide React** - Beautiful icons

## 📋 Prerequisites

- Node.js 16+ 
- npm or yarn
- Backend API running on `http://localhost:8000`

## 🚀 Getting Started

### 1. Install Dependencies

```bash
cd frontend/choolha_chawka_frontend
npm install
```

### 2. Environment Setup

Create a `.env` file in the frontend directory:

```bash
cp .env.example .env
```

Update the environment variables:

```env
REACT_APP_API_URL=http://localhost:8000/api
REACT_APP_APP_NAME=Choolha Chawka
```

### 3. Start Development Server

```bash
npm start
```

The app will be available at `http://localhost:3000`

## 📁 Project Structure

```
src/
├── components/          # Reusable UI components
│   ├── Layout/         # Layout components (Header, Footer)
│   └── UI/             # Basic UI components (Button, Input, etc.)
├── context/            # React context providers
├── pages/              # Page components
│   ├── Auth/           # Authentication pages
│   └── Dashboard/      # Dashboard pages
├── services/           # API service functions
├── types/              # TypeScript type definitions
├── App.tsx             # Main app component
└── index.tsx           # App entry point
```

## 🎨 Design System

### Colors
- **Primary**: Yellow (#fbbf24)
- **Background**: Dark Gray (#111827, #1f2937)
- **Text**: White (#ffffff) and Gray variants
- **Accent**: Yellow variants for highlights

### Components
- **Cards**: Dark background with yellow borders
- **Buttons**: Yellow primary, outlined secondary
- **Forms**: Dark inputs with yellow focus states
- **Navigation**: Dark header with yellow accents

## 🔐 Authentication Flow

1. **Registration** - User creates account with phone verification
2. **OTP Verification** - SMS-based phone number verification
3. **Profile Completion** - User selects type and completes profile
4. **Dashboard Access** - Full access to application features

## 📱 Pages Overview

### Public Pages
- **Home** - Landing page with features and pricing
- **Login** - User authentication
- **Register** - New user registration
- **OTP Verification** - Phone number verification

### Protected Pages
- **Dashboard** - Main user dashboard with statistics
- **Plans** - Available meal plans
- **Subscriptions** - User's subscription management
- **Leaves** - Leave request management
- **Payments** - Payment history and management
- **Feedback** - Feedback and complaints system
- **Profile** - User profile management

### Owner Pages (Mess Owners)
- **Owner Dashboard** - Mess owner analytics
- **Leave Management** - Approve/reject leave requests
- **User Management** - View and manage customers
- **Feedback Management** - Handle customer feedback

## 🔧 API Integration

The frontend integrates with the Django backend through:

- **Authentication API** - Login, register, OTP verification
- **User Management** - Profile management and updates
- **Subscription API** - Plan browsing and subscription management
- **Payment API** - Razorpay integration for payments
- **Leave API** - Leave request management
- **Feedback API** - Customer feedback system

## 🚀 Build and Deployment

### Development Build
```bash
npm run build
```

### Production Deployment
1. Update environment variables for production
2. Build the application
3. Deploy to your hosting service (Netlify, Vercel, etc.)

## 🧪 Available Scripts

- `npm start` - Start development server
- `npm run build` - Build for production
- `npm test` - Run tests
- `npm run eject` - Eject from Create React App

## 🎯 Key Features Implementation

### Authentication Context
- JWT token management
- Automatic token refresh
- User state management
- Protected route handling

### API Service Layer
- Centralized API calls
- Request/response interceptors
- Error handling
- Token management

### Responsive Design
- Mobile-first approach
- Tailwind CSS utilities
- Flexible grid layouts
- Touch-friendly interfaces

### User Experience
- Loading states
- Error handling
- Toast notifications
- Smooth transitions

## 🔒 Security Features

- JWT token storage and management
- Automatic token refresh
- Protected routes
- Input validation
- XSS protection

## 📊 Performance Optimizations

- Code splitting with React.lazy
- Optimized bundle size
- Efficient re-renders
- Image optimization
- Caching strategies

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License.

## 🆘 Support

For support and questions:
- Check the documentation
- Create an issue on GitHub
- Contact the development team

---

**Made with ❤️ for the Choolha Chawka community**