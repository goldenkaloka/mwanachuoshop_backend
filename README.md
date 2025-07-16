# MwanachuoShop Backend

A comprehensive multi-university marketplace platform built with Django REST Framework.

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.11+ (for local development)

### Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd mwanachuoshop_backend
   ```

2. **Set up environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your actual values
   ```

3. **Start the development environment**
   ```bash
   chmod +x setup_dev.sh
   ./setup_dev.sh
   ```

### Manual Setup (Alternative)

1. **Start services**
   ```bash
   docker-compose up -d db redis
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run migrations**
   ```bash
   python manage.py migrate
   ```

4. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

5. **Start the server**
   ```bash
   python manage.py runserver
   ```

## 📁 Project Structure

```
mwanachuoshop_backend/
├── core/                 # Main Django app
│   ├── views.py         # Core views and search functionality
│   ├── models.py        # University, Location, Campus models
│   └── settings.py      # Django settings
├── users/               # User management
├── marketplace/         # Products and categories
├── estates/            # Property listings
├── shops/              # Shop management
├── payments/           # Payment processing
├── dashboard/          # Admin dashboard
├── docker-compose.yml  # Docker services
├── Dockerfile          # Application container
└── requirements.txt    # Python dependencies
```

## 🔧 Configuration

### Environment Variables

Key environment variables (see `env.example` for full list):

- `SECRET_KEY`: Django secret key
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `CLOUDFLARE_R2_*`: File storage configuration
- `PESAPAL_*`: Payment gateway configuration

### Database

The project uses PostgreSQL in production and development. SQLite is supported but not recommended.

## 🚀 API Endpoints

### Authentication
- `POST /api/token/` - Get JWT token
- `POST /api/token/refresh/` - Refresh JWT token
- `POST /api/users/auth/register/` - User registration
- `POST /api/users/auth/login/` - User login

### Core Features
- `GET /api/search/` - Unified search across all content
- `GET /api/content/smart/` - Smart content filtering
- `GET /api/location/context/` - Location-based context

### Documentation
- `GET /api/schema/swagger-ui/` - Interactive API docs
- `GET /api/schema/redoc/` - Alternative API docs

## 🧪 Testing

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test users

# Run with coverage
coverage run --source='.' manage.py test
coverage report
```

## 🐳 Docker Commands

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f web

# Run management commands
docker-compose run --rm web python manage.py migrate

# Stop all services
docker-compose down
```

## 🔒 Security

### Production Checklist
- [ ] Set `DEBUG=False`
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Set up proper CORS origins
- [ ] Use HTTPS
- [ ] Rotate `SECRET_KEY`
- [ ] Configure secure database connection
- [ ] Set up monitoring and logging

## 📊 Monitoring

### Health Check
- `GET /health/` - Application health status

### Logging
- Application logs are available via Docker Compose
- Use `docker-compose logs -f web` to view real-time logs

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📝 License

This project is proprietary software.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Contact the development team

---

**Built with ❤️ for the university community** 