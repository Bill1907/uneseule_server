# Uneseule Backend

> AI Voice Agent Backend for Smart Toy (애착인형) System

FastAPI-based backend service for managing AI-powered smart toys that provide interactive voice experiences for children, with comprehensive parent monitoring and subscription management.

## 🎯 Features

- **User & Device Management**: Parent accounts, child profiles, smart toy pairing
- **AI Voice Integration**: ElevenLabs-powered conversational AI with session management
- **Conversation System**: NoSQL-based conversation storage with context engineering
- **Subscription Management**: Multi-tier subscription plans with payment integration
- **Analytics Dashboard**: Parent insights and child development tracking

## 🏗️ Architecture

**Clean Architecture** with feature-based modules:
- **API Layer**: FastAPI routers with request/response validation
- **Service Layer**: Business logic and external API orchestration
- **Repository Layer**: Database abstraction (PostgreSQL + MongoDB + Redis)
- **Model Layer**: SQLAlchemy ORM models

## 🚀 Quick Start

### Prerequisites

- Python 3.14
- PostgreSQL 14+
- Redis 7+
- MongoDB 6+
- UV package manager

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd uneseule_backend
```

2. **Install dependencies**
```bash
uv sync
```

3. **Set up environment**
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. **Initialize database**
```bash
# Run migrations
alembic upgrade head

# (Optional) Seed initial data
python scripts/seed_db.py
```

5. **Run development server**
```bash
uvicorn main:app --reload
```

The API will be available at:
- **API**: http://localhost:8000
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📁 Project Structure

```
uneseule_backend/
├── app/
│   ├── api/v1/             # API endpoints
│   │   ├── auth/           # Authentication
│   │   ├── users/          # User management
│   │   ├── children/       # Child profiles
│   │   ├── devices/        # Device management
│   │   ├── voice_agent/    # AI voice tokens
│   │   ├── conversations/  # Conversation APIs
│   │   ├── subscriptions/  # Payments & plans
│   │   └── insights/       # Analytics
│   ├── core/               # Core configuration
│   ├── models/             # SQLAlchemy models
│   ├── schemas/            # Pydantic schemas
│   ├── services/           # Business logic
│   ├── repositories/       # Data access
│   ├── integrations/       # External APIs
│   ├── middleware/         # Custom middleware
│   └── utils/              # Utilities
├── migrations/             # Alembic migrations
├── tests/                  # Test suite
├── scripts/                # Utility scripts
├── .claude/                # Project documentation
├── main.py                 # Application entry point
└── pyproject.toml          # Project dependencies
```

## 🔧 Configuration

All configuration is managed through environment variables. See [.env.example](.env.example) for required settings:

- **Database**: PostgreSQL connection
- **Cache**: Redis configuration
- **NoSQL**: MongoDB for conversations
- **Security**: JWT secret keys
- **External APIs**: ElevenLabs, payment gateway
- **Rate Limiting**: Tier-based limits

## 📊 Database

### PostgreSQL (Relational Data)
- Users (parents)
- Children profiles
- Devices
- Subscriptions

### MongoDB (Conversation Data)
- Conversation history
- Context snapshots
- Analytics events

### Redis (Cache & Sessions)
- Session tokens
- Rate limiting
- Temporary caching

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/unit/test_services.py
```

## 📖 API Documentation

Interactive API documentation is available when running the server:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `GET /api/v1/devices` - List user devices
- `POST /api/v1/voice-agent/token` - Get AI voice session token
- `GET /api/v1/conversations/{child_id}` - Get conversation history
- `POST /api/v1/subscriptions` - Create subscription

## 🔐 Security

- **Authentication**: JWT-based with access/refresh tokens
- **Password Hashing**: bcrypt with configurable rounds
- **Rate Limiting**: Tier-based API rate limits
- **CORS**: Configurable allowed origins
- **PII Protection**: Encryption at rest for sensitive data

## 🛠️ Development

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### Code Quality

```bash
# Type checking
mypy app/

# Linting and formatting
ruff check app/
ruff format app/
```

## 📚 Documentation

For comprehensive project documentation, see [.claude/CLAUDE.md](.claude/CLAUDE.md):

- Domain model and entity relationships
- Feature module details
- External integrations
- Development guidelines
- Common tasks and workflows

## 🎯 Roadmap

### Phase 1: Core Foundation ✅
- [x] Project structure
- [ ] Authentication system
- [ ] Database models
- [ ] Basic CRUD operations

### Phase 2: Device Integration
- [ ] Device pairing
- [ ] Status monitoring
- [ ] Remote control

### Phase 3: AI Voice
- [ ] ElevenLabs integration
- [ ] Token management
- [ ] Rate limiting

### Phase 4: Conversations
- [ ] NoSQL storage
- [ ] Context engineering
- [ ] Content moderation

### Phase 5: Business Logic
- [ ] Subscription system
- [ ] Payment integration
- [ ] Analytics dashboard

## 📄 License

[License Type] - See LICENSE file for details

## 🤝 Contributing

Contributions are welcome! Please read CONTRIBUTING.md for guidelines.

## 📞 Support

For questions or issues:
- Check [.claude/CLAUDE.md](.claude/CLAUDE.md) for detailed documentation
- Review API documentation at http://localhost:8000/docs
- Open an issue on GitHub

---

Built with ❤️ using FastAPI, SQLAlchemy, and modern Python tools
