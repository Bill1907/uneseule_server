# Uneseule Backend - Project Structure Setup Plan

## Project Overview

**Project Type**: AI Voice Agent Backend for Smart Toy (애착인형)
**Framework**: FastAPI + SQLAlchemy + PostgreSQL + Redis
**Architecture**: Clean Architecture with Feature-based Modules

## Core Features Analysis

### 1. User & Device Management
- Parent account authentication (회원가입/로그인)
- Child profile management (multiple children per account)
- Device pairing/unpairing
- Device monitoring (battery, connection, firmware)
- Remote device deactivation

### 2. AI Voice Agent Token Management
- Session token issuance (ElevenLabs integration)
- Context initialization
- Token expiration/renewal
- Rate limiting

### 3. Conversation Data & Context Engineering
- NoSQL conversation storage
- Personality analysis
- Context optimization
- Content moderation
- Conversation summarization

### 4. Subscription Management
- Subscription plans
- Payment processing
- Usage tracking (voice minutes, API calls)
- Feature limitations by plan

### 5. Parent App Data Service
- Conversation data aggregation
- Insights dashboard statistics

## Proposed Folder Structure

```
uneseule_backend/
├── app/
│   ├── api/                    # API endpoints (FastAPI routers)
│   │   └── v1/
│   │       ├── auth/           # Authentication endpoints
│   │       ├── users/          # User management
│   │       ├── children/       # Child profile management
│   │       ├── devices/        # Device management
│   │       ├── voice_agent/    # AI voice token management
│   │       ├── conversations/  # Conversation data APIs
│   │       ├── subscriptions/  # Subscription & payment
│   │       └── insights/       # Parent dashboard data
│   │
│   ├── core/                   # Core configuration
│   │   ├── config.py           # Settings (Pydantic Settings)
│   │   ├── security.py         # JWT, password hashing
│   │   ├── dependencies.py     # FastAPI dependencies
│   │   └── events.py           # Startup/shutdown events
│   │
│   ├── models/                 # SQLAlchemy ORM models
│   │   ├── user.py
│   │   ├── child.py
│   │   ├── device.py
│   │   ├── subscription.py
│   │   └── base.py
│   │
│   ├── schemas/                # Pydantic schemas (request/response)
│   │   ├── auth.py
│   │   ├── user.py
│   │   ├── child.py
│   │   ├── device.py
│   │   ├── conversation.py
│   │   └── subscription.py
│   │
│   ├── services/               # Business logic layer
│   │   ├── auth_service.py
│   │   ├── user_service.py
│   │   ├── device_service.py
│   │   ├── voice_agent_service.py
│   │   ├── conversation_service.py
│   │   ├── subscription_service.py
│   │   └── analytics_service.py
│   │
│   ├── repositories/           # Data access layer
│   │   ├── user_repository.py
│   │   ├── device_repository.py
│   │   ├── conversation_repository.py  # NoSQL operations
│   │   └── subscription_repository.py
│   │
│   ├── integrations/           # External service integrations
│   │   ├── elevenlabs.py       # ElevenLabs API client
│   │   ├── payment.py          # Payment gateway (Stripe/Toss)
│   │   └── nosql.py            # MongoDB/DynamoDB client
│   │
│   ├── middleware/             # Custom middleware
│   │   ├── rate_limiter.py
│   │   ├── logging.py
│   │   └── error_handler.py
│   │
│   └── utils/                  # Utility functions
│       ├── validators.py
│       ├── helpers.py
│       └── constants.py
│
├── migrations/                 # Alembic database migrations
│   └── versions/
│
├── tests/                      # Test suite
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── scripts/                    # Utility scripts
│   ├── seed_db.py
│   └── generate_test_data.py
│
├── .claude/                    # Claude Code context
│   └── CLAUDE.md
│
├── main.py                     # Application entry point
├── pyproject.toml
└── README.md
```

## Database Architecture

### PostgreSQL (Relational Data)
- Users (parents)
- Children profiles
- Devices
- Subscriptions
- Usage tracking

### NoSQL (MongoDB/DynamoDB)
- Conversation history
- Context data
- Analytics events

### Redis
- Session tokens
- Rate limiting
- Caching (frequently accessed data)

## External Integrations

1. **ElevenLabs**: Voice synthesis API
2. **Payment Gateway**: Stripe or Toss Payments
3. **NoSQL Database**: MongoDB or DynamoDB
4. **Monitoring**: Sentry (error tracking)

## Implementation Phases

### Phase 1: Core Infrastructure
- Project structure setup
- Database models
- Authentication system
- Basic CRUD operations

### Phase 2: Device Management
- Device pairing logic
- Device monitoring
- Remote control features

### Phase 3: AI Voice Integration
- ElevenLabs integration
- Token management
- Rate limiting

### Phase 4: Conversation System
- NoSQL storage setup
- Context engineering
- Content moderation

### Phase 5: Subscription & Analytics
- Payment integration
- Usage tracking
- Insights dashboard

## Critical Files to Create

1. **Core Configuration**
   - `app/core/config.py`: Environment-based settings
   - `app/core/security.py`: JWT utilities
   - `app/core/dependencies.py`: Dependency injection

2. **Database Models**
   - `app/models/user.py`: User model
   - `app/models/child.py`: Child profile model
   - `app/models/device.py`: Device model
   - `app/models/subscription.py`: Subscription model

3. **API Routers**
   - `app/api/v1/auth/router.py`: Authentication endpoints
   - `app/api/v1/devices/router.py`: Device management
   - `app/api/v1/voice_agent/router.py`: Voice agent endpoints

4. **Services**
   - `app/services/auth_service.py`: Authentication logic
   - `app/services/voice_agent_service.py`: ElevenLabs integration
   - `app/services/conversation_service.py`: Context management

5. **Integrations**
   - `app/integrations/elevenlabs.py`: ElevenLabs client
   - `app/integrations/nosql.py`: NoSQL database client

## Next Steps

1. Create CLAUDE.md for project context
2. Generate folder structure
3. Create core configuration files
4. Initialize database models
5. Set up API routers skeleton
