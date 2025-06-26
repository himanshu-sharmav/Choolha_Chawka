# Choolha Chawka - Food Subscription Management System

A comprehensive Django-based food subscription platform that enables users to subscribe to meal plans, manage leaves, process payments, and receive automated notifications.

## 🚀 Features

### User Management
- **Multi-role Authentication** - Students, Regular Users, and Mess Owners
- **OTP-based Registration** - SMS verification for phone numbers
- **Profile Management** - Complete user profiles with role-specific data
- **Password Reset** - Email-based password recovery

### Subscription Management
- **Flexible Meal Plans** - Mess and Tiffin services with customizable options
- **Leave Management** - Request leaves with automatic subscription extension
- **Smart Pricing** - Dynamic pricing based on plan duration and add-ons
- **Subscription Lifecycle** - Complete management from creation to renewal

### Payment Processing
- **Razorpay Integration** - Secure payment gateway integration
- **Order Management** - Complete order tracking and verification
- **Refund System** - Manual refund processing with admin approval
- **Receipt Generation** - PDF and HTML receipt downloads

### Notification System
- **Multi-channel Notifications** - Email and SMS support
- **Amazon SES Integration** - Reliable email delivery
- **Event-driven Alerts** - Automated notifications for all user actions
- **Template Management** - Customizable notification templates

### Admin Dashboard
- **Mess Owner Portal** - Comprehensive management interface
- **Leave Approval System** - Review and approve/reject leave requests
- **User Management** - View and manage all subscribers
- **Analytics** - Dashboard statistics and insights

## 🛠️ Tech Stack

- **Backend**: Django 4.2.7, Django REST Framework
- **Database**: PostgreSQL
- **Authentication**: Token-based authentication
- **Payments**: Razorpay API
- **Email**: Amazon SES
- **SMS**: Custom SMS service integration
- **File Storage**: Django file handling
- **API Documentation**: Django REST Framework browsable API

## 📋 Prerequisites

- Python 3.11+
- PostgreSQL 12+
- Redis (for caching)
- AWS Account (for SES)
- Razorpay Account

## 🚀 Quick Start with Docker

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/choolha-chawka.git
cd choolha-chawka
```

### 2. Start with Docker Compose
```bash
docker-compose up -d --build
```

### 3. Access the Application
- **Backend API**: http://localhost:8000
- **Admin Panel**: http://localhost:8000/admin
- **API Documentation**: http://localhost:8000/api/

### 4. Default Credentials
- **Admin**: admin / admin123
- **Mess Owner**: messowner / owner123

## 🔧 Manual Installation

### 1. Clone and Setup
```bash
git clone https://github.com/yourusername/choolha-chawka.git
cd choolha-chawka
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Environment Configuration
Create `.env` file:
```env
# Django Settings
DEBUG=1
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://user:password@localhost:5432/choolha_chawka

# AWS SES
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key

# Razorpay
RAZORPAY_KEY_ID=your-razorpay-key
RAZORPAY_KEY_SECRET=your-razorpay-secret

# Email Settings
DEFAULT_FROM_EMAIL=noreply@choolhachawka.com

# Frontend URL
FRONTEND_URL=http://localhost:3000
```

### 3. Database Setup
```bash
python manage.py migrate
python manage.py create_default_plans
python manage.py create_notification_templates
python manage.py createsuperuser
```

### 4. Run Development Server
```bash
python manage.py runserver
```

## 📚 API Documentation

### Authentication Endpoints
```
POST /api/accounts/register/          # User registration
POST /api/accounts/verify-otp/        # OTP verification
POST /api/accounts/login/             # User login
POST /api/accounts/password-reset/    # Password reset request
```

### Subscription Endpoints
```
GET  /api/subscriptions/plans/        # List meal plans
POST /api/subscriptions/subscriptions/ # Create subscription
GET  /api/subscriptions/subscriptions/ # User subscriptions
POST /api/subscriptions/leaves/       # Submit leave request
```

### Payment Endpoints
```
POST /api/payments/orders/            # Create payment order
POST /api/payments/orders/verify_payment/ # Verify payment
GET  /api/payments/payments/          # Payment history
GET  /api/payments/payments/{id}/receipt/ # Download receipt
```

### Owner Dashboard Endpoints
```
GET  /api/owner/leaves/pending/       # Pending leave requests
POST /api/owner/leaves/{id}/approve/  # Approve leave
POST /api/owner/leaves/{id}/reject/   # Reject leave
GET  /api/owner/users/               # List all users
```

## 🔐 User Roles & Permissions

### Student/Regular User
- Create and manage subscriptions
- Submit leave requests
- Make payments
- View payment history
- Update profile

### Mess Owner
- View all users and subscriptions
- Approve/reject leave requests
- Manage refund requests
- Access dashboard analytics
- View payment reports

### Admin
- Full system access
- User management
- Plan management
- System configuration

## 📧 Notification Events

The system automatically sends notifications for:

- **User Onboarding**: Welcome emails, profile completion
- **Subscriptions**: Creation, activation, cancellation, renewal
- **Payments**: Success, failure, refund processing
- **Leave Management**: Submission, approval, rejection
- **Account Security**: Password changes, login alerts

## 🏗️ Project Structure

```
choolha-chawka/Backend/
├── accounts/              # User management and authentication
├── subscriptions/         # Meal plans and subscription logic
├── payments/             # Payment processing and refunds
├── notifications/        # Email/SMS notification system
├── core/                # Shared utilities and permissions
├── config/              # Django settings and configuration
├── static/              # Static files
├── media/               # User uploaded files
├── templates/           # Email templates
├── requirements.txt     # Python dependencies
├── docker-compose.yml   # Docker configuration
└── manage.py           # Django management script
```

## 🧪 Testing

### Run Tests
```bash
python manage.py test
```

### Test Notifications
```bash
python manage.py send_payment_reminders --days 2
python manage.py send_expiry_notifications
```

### API Testing with Postman
Import the Postman collection from `docs/postman_collection.json`

## 🚀 Deployment

### AWS Deployment
1. **Setup EC2 instance** with Ubuntu 20.04+
2. **Configure RDS** for PostgreSQL
3. **Setup Route 53** for domain management
4. **Configure SES** for email delivery
5. **Deploy with Docker** or traditional setup

### Environment Variables for Production
```env
DEBUG=0
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DATABASE_URL=postgresql://user:pass@rds-endpoint:5432/db
AWS_SES_REGION_NAME=ap-south-1
```

## 📊 Monitoring & Analytics

- **Django Admin**: User and subscription management
- **SES Dashboard**: Email delivery metrics
- **Razorpay Dashboard**: Payment analytics
- **Custom Analytics**: Built-in dashboard for mess owners

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [Wiki](https://github.com/himanshu-sharmav/choolha-chawka/wiki)
- **Issues**: [GitHub Issues](https://github.com/himanshu-sharmav/choolha-chawka/issues)
- **Email**: support@choolhachawka.com

## 🎯 Roadmap

- [ ] Mobile app development
- [ ] Advanced analytics dashboard
- [ ] Multi-language support
- [ ] Integration with food delivery platforms
- [ ] AI-powered meal recommendations
- [ ] Inventory management system

## 👥 Team

- **Backend Development**: [Himanshu Sharma]
- **Frontend Development**: [Abhimanyu Singh]
- **DevOps**: [Himanshu Sharma]

**Made with ❤️ for the food community**