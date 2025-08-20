<<<<<<< HEAD
# QuikScribe Backend API

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

QuikScribe is a powerful backend API for managing Google Meet recordings with automated bot integration. The application provides user authentication, meeting management, and real-time transcription capabilities through containerized bots.

## 🚀 Features

- **User Authentication**: JWT-based authentication with OAuth2 (Google) integration
- **Meeting Bot Management**: Automated Google Meet bot deployment using Docker containers
- **Real-time Transcription**: Meeting transcription and recording capabilities
- **Admin Panel**: Administrative functionality for user and system management
- **RESTful API**: Complete REST API with OpenAPI/Swagger documentation
- **Database Integration**: PostgreSQL database with SQLAlchemy ORM
- **Production Ready**: Comprehensive error handling, logging, and security features

## 📋 Prerequisites

- Python 3.8+
- Docker & Docker Compose
- PostgreSQL database
- Google OAuth2 credentials (for authentication)

## 🛠️ Installation

### 1. Environment Setup

```bash
# Create virtual environment
python -m venv .venv_quikscribe

# Activate virtual environment
# Windows
.venv_quikscribe\Scripts\activate
# macOS/Linux
source .venv_quikscribe/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Variables

Create a `.env` file in the root directory:

```env
# Application Settings
DEBUG=true
SECRET_KEY=your-super-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Frontend Configuration
FRONTEND_URL=http://localhost:3000
FRONTEND_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_USER=quikscribe_user
DB_PASSWORD=your_db_password
DB_NAME=quikscribe_db

# Google OAuth2
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Docker Configuration
DOCKER_IMAGE_NAME=google_meet_bot_image_v1.2
```

### 3. Database Setup

```bash
# Create PostgreSQL database
createdb quikscribe_db

# The application will automatically create tables on startup
```

### 4. Docker Bot Image

```bash
# Navigate to google_bot directory
cd google_bot

# Build the meeting bot Docker image
docker build -t google_meet_bot_image_v1.2 .

# Return to root directory
cd ..
```

### 5. Start the Application

```bash
# Development mode
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 📚 API Documentation

### Base URL
```
http://localhost:8000/api/v1
```

### Authentication

The API uses JWT (JSON Web Token) for authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

### API Endpoints

#### 🔐 Authentication Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/auth/register` | Register new user | No |
| POST | `/auth/token` | Login and get access token | No |
| GET | `/auth/me` | Get current user info | Yes |
| GET | `/auth/google/login` | Google OAuth login | No |
| GET | `/auth/google/callback` | Google OAuth callback | No |
| POST | `/auth/refresh` | Refresh access token | Yes |
| POST | `/auth/change-password` | Change user password | Yes |
| POST | `/auth/forgot-password` | Request password reset | No |
| POST | `/auth/reset-password` | Reset password with token | No |

#### 🤖 Meeting Bot Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/meeting-bot/meeting-url` | Start meeting bot | Yes |
| GET | `/meeting-bot/my-meetings` | Get user's meetings | Yes |
| POST | `/meeting-bot/meeting/{uuid}/pause` | Pause meeting recording | Yes |
| POST | `/meeting-bot/meeting/{uuid}/resume` | Resume meeting recording | Yes |
| POST | `/meeting-bot/meeting/{uuid}/stop` | Stop meeting recording | Yes |

## 🔧 API Usage Examples

### 1. User Registration

```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
     -H "Content-Type: application/json" \
     -d '{
       "email": "user@example.com",
       "username": "testuser",
       "password": "SecurePass123"
     }'
```

### 2. User Login

```bash
curl -X POST "http://localhost:8000/api/v1/auth/token" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=user@example.com&password=SecurePass123"
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### 3. Start Meeting Bot

```bash
curl -X POST "http://localhost:8000/api/v1/meeting-bot/meeting-url" \
     -H "Authorization: Bearer <your_token>" \
     -H "Content-Type: application/json" \
     -d '{
       "meeting_url": "https://meet.google.com/abc-def-ghi",
       "duration": 60
     }'
```

**Response:**
```json
{
  "message": "Meeting bot started successfully",
  "meeting_id": "550e8400-e29b-41d4-a716-446655440000",
  "container_id": "docker_container_id",
  "port": 3001
}
```

### 4. Control Meeting Bot

```bash
# Pause recording
curl -X POST "http://localhost:8000/api/v1/meeting-bot/meeting/{meeting_id}/pause" \
     -H "Authorization: Bearer <your_token>"

# Resume recording
curl -X POST "http://localhost:8000/api/v1/meeting-bot/meeting/{meeting_id}/resume" \
     -H "Authorization: Bearer <your_token>"

# Stop recording
curl -X POST "http://localhost:8000/api/v1/meeting-bot/meeting/{meeting_id}/stop" \
     -H "Authorization: Bearer <your_token>"
```

### 5. Get User Meetings

```bash
curl -X GET "http://localhost:8000/api/v1/meeting-bot/my-meetings" \
     -H "Authorization: Bearer <your_token>"
```

## 🔍 Interactive API Documentation

Once the server is running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🏗️ Project Structure

```
quikscribe/
├── app/
│   ├── api/
│   │   └── route.py              # Main API router
│   ├── core/
│   │   ├── config.py             # Configuration settings
│   │   ├── database.py           # Database connection
│   │   └── security.py           # Security utilities
│   └── modules/
│       ├── admin/
│       │   └── models.py         # Admin models
│       ├── auth/
│       │   ├── models.py         # Auth models
│       │   ├── oauth.py          # OAuth integration
│       │   ├── repository.py     # Data access layer
│       │   ├── routes.py         # Auth endpoints
│       │   ├── schemas.py        # Pydantic schemas
│       │   └── services.py       # Business logic
│       └── google_meeting_bot/
│           ├── docker_container.py # Docker management
│           ├── models.py         # Meeting models
│           └── routes.py         # Meeting endpoints
├── google_bot/                  # Docker bot implementation
├── static/                      # Static files
├── main.py                      # Application entry point
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## 🔒 Security Features

- **JWT Authentication**: Secure token-based authentication
- **OAuth2 Integration**: Google OAuth for social login
- **Password Hashing**: Bcrypt password hashing
- **CORS Protection**: Configurable CORS middleware
- **Input Validation**: Pydantic schema validation
- **SQL Injection Protection**: SQLAlchemy ORM protection

## 🚀 Deployment

### Docker Deployment

```bash
# Build application image
docker build -t quikscribe-api .

# Run with Docker Compose
docker-compose up -d
```

### Environment-specific Settings

- **Development**: Set `DEBUG=true` for detailed error messages
- **Production**: Set `DEBUG=false` and configure proper secrets

## 📊 Monitoring & Logging

The application includes comprehensive logging:

```python
# View logs
tail -f quikscribe.log

# Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:

- **Email**: support@quikscribe.com
- **Documentation**: http://localhost:8000/docs
- **Issues**: [GitHub Issues](https://github.com/your-org/quikscribe/issues)

## 🔄 Changelog

### v0.1.0 (Current)
- Initial release
- User authentication system
- Google Meeting bot integration
- RESTful API with OpenAPI documentation
- Docker containerization support

---

**Built with ❤️ by the QuikScribe Team**

=======
# backend-quikscribe
>>>>>>> cf1130291e16b9275c7c9272523e6ca368639866
