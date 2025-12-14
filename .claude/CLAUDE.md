# Uneseule Backend - Project Documentation

> AI Voice Agent Backend for Smart Toy (애착인형) System

## 🎯 Project Overview

**Purpose**: Backend API service for managing AI-powered smart toys that provide interactive voice experiences for children, with parent monitoring and subscription management.

**Project Name**: Uneseule Backend
**Version**: 0.1.0
**Framework**: FastAPI 0.124.4
**Python**: 3.14

### Key Capabilities
- Parent account and child profile management
- Smart toy device pairing and monitoring
- AI voice agent session management (ElevenLabs integration)
- Conversation data storage and context engineering
- Subscription and payment processing
- Parent dashboard analytics and insights

## 🏗️ Architecture Overview

### Design Pattern
**Clean Architecture** with **Hybrid API Strategy** (GraphQL + REST)

```
┌─────────────────────────────────────────────────────────────────┐
│                  API Layer (Hybrid)                              │
│  ┌──────────────────┬─────────────────┬────────────────────┐   │
│  │  GraphQL         │  REST API       │  WebSocket         │   │
│  │  (Parent App)    │  (Devices)      │  (Real-time)       │   │
│  │  /graphql        │  /api/v1/device │  /graphql/ws       │   │
│  └──────────────────┴─────────────────┴────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Webhooks (Event Receivers)                              │   │
│  │  /webhooks/elevenlabs, /webhooks/payment                 │   │
│  └──────────────────────────────────────────────────────────┘   │
└──────────────────────┬──────────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────────┐
│                  Service Layer                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Business Logic, Validation, Orchestration               │   │
│  │  Auth, Device, Voice, Conversation, Subscription         │   │
│  └──────────────────────────────────────────────────────────┘   │
└──────────────────────┬──────────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────────┐
│               Repository Layer                                   │
│  ┌──────────────────┬───────────────┬────────────────────────┐  │
│  │  PostgreSQL      │  NoSQL        │  Redis Cache           │  │
│  │  (SQLAlchemy)    │  (MongoDB)    │  (Sessions, Tokens)    │  │
│  └──────────────────┴───────────────┴────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Dual API Strategy

#### GraphQL API (`/graphql`) - Parent Mobile/Web App
**Technology**: Strawberry GraphQL
**Purpose**: Rich data queries with nested relationships for parent applications

**Capabilities**:
- **Queries**: Fetch users, children, conversations, insights with flexible field selection
- **Mutations**: User registration, profile updates, subscription management
- **Subscriptions**: Real-time device status updates (battery, connection) via WebSocket

**Example Schema**:
```graphql
type Query {
  me: User!
  children: [Child!]!
  conversations(childId: ID!): [Conversation!]!
  insights(childId: ID!): ChildInsights!
}

type Mutation {
  register(email: String!, password: String!): AuthPayload!
  addChild(input: CreateChildInput!): Child!
  updateSubscription(plan: PlanType!): Subscription!
}

type Subscription {
  deviceStatusChanged(deviceId: ID!): DeviceStatus!
}
```

#### REST API (`/api/v1/device`) - IoT Devices
**Purpose**: Simple, stateless operations for smart toy devices

**Endpoints**:
- `POST /api/v1/device/register` - Device registration
- `POST /api/v1/device/pair` - Pair device with child
- `POST /api/v1/device/token` - Get AI voice session token
- `GET /api/v1/device/health` - Health check
- `DELETE /api/v1/device/pair` - Unpair device

**Authentication**: HMAC-SHA256 signature-based (serial number + device secret)

#### Webhook API (`/webhooks`) - External Event Receivers
**Purpose**: Receive events from external services

**Endpoints**:
- `POST /webhooks/elevenlabs` - ElevenLabs conversation data
- `POST /webhooks/payment` - Payment gateway events (Stripe/Toss)

**Security**: HMAC signature verification for each provider

### Layer Responsibilities

**GraphQL Layer** (`app/graphql/`)
- Schema definition (types, queries, mutations, subscriptions)
- Context management (authentication, database sessions)
- Resolver implementation
- Real-time subscriptions via WebSocket

**REST API Layer** (`app/api/v1/`)
- Device-specific endpoints
- Webhook handlers
- Request/response validation
- HTTP status codes

**Service Layer** (`app/services/`)
- Business logic implementation (shared by GraphQL and REST)
- Cross-entity operations
- External API orchestration
- Error handling

**Repository Layer** (`app/repositories/`)
- Database abstraction
- CRUD operations
- Query optimization
- Transaction management

**Model Layer** (`app/models/`)
- SQLAlchemy ORM models
- Database schema definitions
- Relationships and constraints

## 📊 Domain Model

### Core Entities

#### 1. User (Parent Account)
```python
User
├── id: UUID (PK)
├── email: str (unique)
├── password_hash: str
├── name: str
├── phone: str (optional)
├── created_at: datetime
├── updated_at: datetime
└── children: List[Child] (one-to-many)
```

**Relationships**: One User → Many Children, Many Devices, One Subscription

#### 2. Child (Child Profile)
```python
Child
├── id: UUID (PK)
├── user_id: UUID (FK → User)
├── name: str
├── birth_date: date
├── gender: str (optional)
├── personality_traits: JSON (analyzed from conversations)
├── created_at: datetime
└── device: Device (one-to-one)
```

**Relationships**: Many Children → One User, One Child → One Device

#### 3. Device (Smart Toy)
```python
Device
├── id: UUID (PK)
├── serial_number: str (unique)
├── child_id: UUID (FK → Child, nullable)
├── device_type: str
├── firmware_version: str
├── battery_level: int
├── connection_status: enum (online, offline, sleep)
├── last_seen: datetime
├── is_active: bool
├── paired_at: datetime (nullable)
└── created_at: datetime
```

**Relationships**: One Device → One Child (optional)

#### 4. Subscription
```python
Subscription
├── id: UUID (PK)
├── user_id: UUID (FK → User)
├── plan_type: enum (free, basic, premium)
├── status: enum (active, cancelled, expired, trial)
├── started_at: datetime
├── expires_at: datetime
├── auto_renew: bool
├── payment_method_id: str (nullable)
└── usage_limits: JSON
```

**Relationships**: One Subscription → One User

#### 5. Conversation (NoSQL - MongoDB)
```json
{
  "_id": "ObjectId",
  "child_id": "UUID",
  "device_id": "UUID",
  "session_id": "UUID",
  "messages": [
    {
      "role": "child|assistant",
      "content": "str",
      "timestamp": "datetime",
      "audio_url": "str (optional)"
    }
  ],
  "context": {
    "mood": "str",
    "topics": ["str"],
    "sentiment_score": "float"
  },
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### Entity Relationship Diagram

```
User (1) ──┬── (n) Child
           │
           ├── (n) Device
           │
           └── (1) Subscription

Child (1) ──── (1) Device

Device (1) ──── (n) Conversation (NoSQL)

User (1) ──── (n) Usage Statistics
```

## 🎨 Feature Modules

### 1. User & Child Management (GraphQL)

**Endpoints**:
- GraphQL: `/graphql` (queries: `me`, `children`, mutations: `register`, `login`, `addChild`, `updateChild`)

**Core Features**:
- ✅ Parent account registration/login (GraphQL mutation)
- ✅ Email verification
- ✅ Password reset
- ✅ Profile management (GraphQL queries/mutations)
- ✅ Child profile CRUD (GraphQL mutations)
- ✅ Nested data fetching (user with children in single query)

**Key Files**:
- [app/graphql/mutations/auth.py](app/graphql/mutations/auth.py)
- [app/graphql/mutations/user.py](app/graphql/mutations/user.py)
- [app/graphql/mutations/child.py](app/graphql/mutations/child.py)
- [app/graphql/queries/user.py](app/graphql/queries/user.py)
- [app/graphql/queries/child.py](app/graphql/queries/child.py)
- [app/graphql/types/user.py](app/graphql/types/user.py)
- [app/graphql/types/child.py](app/graphql/types/child.py)
- [app/services/auth_service.py](app/services/auth_service.py)
- [app/services/user_service.py](app/services/user_service.py)
- [app/models/user.py](app/models/user.py), [app/models/child.py](app/models/child.py)

**GraphQL Example**:
```graphql
# Query user with children
query {
  me {
    id
    email
    name
    children {
      id
      name
      birthDate
      device {
        serialNumber
        batteryLevel
      }
    }
  }
}

# Mutation: Add child
mutation {
  addChild(input: {
    name: "지훈"
    birthDate: "2020-05-15"
  }) {
    id
    name
  }
}
```

**Business Rules**:
- One parent can have multiple children
- GraphQL context provides authenticated user
- Nested queries optimize data fetching for mobile apps

### 2. Device Management (REST API)

**Endpoints**: `/api/v1/device/*`

**Core Features**:
- ✅ Device registration (REST POST)
- ✅ Device pairing/unpairing (REST POST/DELETE)
- ✅ Device health check (REST GET)
- ✅ Session token issuance (REST POST)
- ✅ HMAC-based device authentication

**Key Files**:
- [app/api/v1/device/router.py](app/api/v1/device/router.py)
- [app/api/v1/device/auth.py](app/api/v1/device/auth.py)
- [app/services/device_service.py](app/services/device_service.py)
- [app/services/device_auth_service.py](app/services/device_auth_service.py)
- [app/models/device.py](app/models/device.py)

**Device Authentication**:
```python
# Request headers
X-Device-Serial: ABC123XYZ
X-Device-Signature: hmac_sha256(serial + timestamp + body, secret)
X-Device-Timestamp: 1234567890

# Signature verification
def verify_device_signature(serial, signature, timestamp, body, secret):
    # Verify HMAC-SHA256 signature
    # Check timestamp freshness (within 5 minutes)
    # Return authenticated device
```

**REST Endpoints**:
```bash
POST   /api/v1/device/register        # Register new device
POST   /api/v1/device/pair            # Pair device with child
POST   /api/v1/device/token           # Get AI voice session token
GET    /api/v1/device/health          # Device health check
DELETE /api/v1/device/pair            # Unpair device
```

**Business Rules**:
- One child can have one active device
- Device must be unpaired before reassignment
- HMAC signature required for all device operations
- Device authentication separate from user JWT

### 3. AI Voice Agent Integration (REST API)

**Endpoints**: `/api/v1/device/token`

**Core Features**:
- ✅ Session token generation (ElevenLabs)
- ✅ Token expiration/renewal
- ✅ Context initialization
- ✅ Rate limiting (per subscription tier)
- ✅ Token delivery to authenticated devices

**Key Files**:
- [app/api/v1/device/router.py](app/api/v1/device/router.py)
- [app/services/voice_agent_service.py](app/services/voice_agent_service.py)
- [app/integrations/elevenlabs.py](app/integrations/elevenlabs.py)
- [app/middleware/rate_limiter.py](app/middleware/rate_limiter.py)

**Business Rules**:
- Token TTL: 30 minutes (renewable)
- Rate limits based on subscription tier:
  - Free: 50 requests/day
  - Basic: 200 requests/day
  - Premium: Unlimited
- Context includes: child age, personality, conversation history

**Integration Flow**:
```
Device → POST /api/v1/device/token (HMAC auth)
         Backend → ElevenLabs API (create conversation session)
         Backend ← Session token
Device ← Token + Context data
Device → Direct ElevenLabs WebSocket connection (with token)
       → Voice conversation
ElevenLabs → POST /webhooks/elevenlabs (conversation data)
```

### 4. Conversation Data & Context Engineering (GraphQL + Webhook)

**Endpoints**:
- GraphQL: `/graphql` (query: `conversations`)
- Webhook: `POST /webhooks/elevenlabs`

**Core Features**:
- ✅ Conversation storage (NoSQL via webhook)
- ✅ Real-time context updates
- ✅ Personality analysis (from conversation data)
- ✅ Content moderation (inappropriate content detection)
- ✅ Conversation summarization (long history compression)
- ✅ Context optimization for token efficiency
- ✅ ElevenLabs webhook integration

**Key Files**:
- [app/graphql/queries/conversation.py](app/graphql/queries/conversation.py)
- [app/graphql/types/conversation.py](app/graphql/types/conversation.py)
- [app/api/v1/webhooks/elevenlabs.py](app/api/v1/webhooks/elevenlabs.py)
- [app/services/conversation_service.py](app/services/conversation_service.py)
- [app/services/webhook_service.py](app/services/webhook_service.py)
- [app/repositories/conversation_repository.py](app/repositories/conversation_repository.py)
- [app/integrations/nosql.py](app/integrations/nosql.py)
- [app/utils/webhook_validators.py](app/utils/webhook_validators.py)

**Data Strategy**:
- **Storage**: MongoDB (flexible schema for conversation data)
- **Indexing**: child_id, session_id, created_at
- **TTL**: Conversations older than 6 months archived
- **Context Window**: Last 10 messages + personality summary

**ElevenLabs Webhook Flow**:
```
ElevenLabs → POST /webhooks/elevenlabs
           → Verify HMAC signature (ElevenLabs-Signature header)
           → Extract conversation data (transcript, analysis)
           → Store in MongoDB
           → Update child personality traits
           → Trigger GraphQL subscription (new conversation event)
           → Notify parent app
```

**Webhook Payload Example**:
```json
{
  "type": "post_call_transcription",
  "event_timestamp": 1234567890,
  "data": {
    "conversation_id": "uuid",
    "child_id": "uuid",
    "transcript": [
      {"role": "child", "content": "Tell me about dinosaurs"},
      {"role": "assistant", "content": "Dinosaurs were..."}
    ],
    "analysis": {
      "mood": "curious",
      "topics": ["dinosaurs", "science"],
      "sentiment_score": 0.85
    }
  }
}
```

**Context Engineering**:
```python
{
  "child_profile": {
    "name": "str",
    "age": "int",
    "personality_traits": ["curious", "energetic"]
  },
  "recent_topics": ["dinosaurs", "space", "family"],
  "conversation_summary": "str (compressed history)",
  "mood": "happy|sad|curious|tired",
  "preferences": {
    "favorite_activities": ["str"],
    "interests": ["str"]
  }
}
```

### 5. Subscription Management (GraphQL + Webhook)

**Endpoints**:
- GraphQL: `/graphql` (query: `subscription`, mutation: `updateSubscription`)
- Webhook: `POST /webhooks/payment`

**Core Features**:
- ✅ Subscription plan selection (GraphQL mutation)
- ✅ Payment processing (Stripe/Toss webhook)
- ✅ Usage tracking (voice minutes, API calls)
- ✅ Subscription status management
- ✅ Auto-renewal handling
- ✅ Feature gating by plan

**Key Files**:
- [app/graphql/queries/subscription.py](app/graphql/queries/subscription.py)
- [app/graphql/mutations/subscription.py](app/graphql/mutations/subscription.py)
- [app/graphql/types/subscription.py](app/graphql/types/subscription.py)
- [app/api/v1/webhooks/payment.py](app/api/v1/webhooks/payment.py)
- [app/services/subscription_service.py](app/services/subscription_service.py)
- [app/integrations/payment.py](app/integrations/payment.py)
- [app/models/subscription.py](app/models/subscription.py)

**Subscription Tiers**:
```yaml
free:
  price: 0
  voice_minutes: 100/month
  api_calls: 50/day
  children: 1
  features: [basic_conversation]

basic:
  price: 9900  # KRW
  voice_minutes: 500/month
  api_calls: 200/day
  children: 3
  features: [basic_conversation, personality_analysis, insights_basic]

premium:
  price: 19900  # KRW
  voice_minutes: unlimited
  api_calls: unlimited
  children: unlimited
  features: [all_features, priority_support, custom_voices]
```

### 6. Parent Dashboard Analytics (GraphQL)

**Endpoints**: `/graphql` (query: `insights`)

**Core Features**:
- ✅ Conversation summaries (GraphQL query)
- ✅ Child development insights
- ✅ Usage statistics
- ✅ Personality trend analysis
- ✅ Activity timeline
- ✅ Real-time updates via subscriptions

**Key Files**:
- [app/graphql/queries/insights.py](app/graphql/queries/insights.py)
- [app/graphql/types/insights.py](app/graphql/types/insights.py)
- [app/services/analytics_service.py](app/services/analytics_service.py)

**GraphQL Example**:
```graphql
query {
  insights(childId: "uuid") {
    totalConversationTime
    topicDistribution {
      topic
      count
    }
    moodPatterns {
      date
      mood
      score
    }
    deviceUsage {
      date
      minutes
    }
    engagementScore
  }
}
```

**Metrics Provided**:
- Total conversation time
- Topic distribution
- Mood patterns
- Device usage patterns
- Engagement scores

### 7. Real-time Updates (WebSocket Subscriptions)

**Endpoints**: `WS /graphql/ws`

**Core Features**:
- ✅ Real-time device status updates
- ✅ New conversation notifications
- ✅ Subscription status changes
- ✅ WebSocket connection management

**Key Files**:
- [app/graphql/subscriptions/device_status.py](app/graphql/subscriptions/device_status.py)
- [app/graphql/subscriptions/conversation.py](app/graphql/subscriptions/conversation.py)

**Subscription Example**:
```graphql
subscription {
  deviceStatusChanged(deviceId: "uuid") {
    deviceId
    batteryLevel
    connectionStatus
    lastSeen
  }
}
```

## 🔌 External Integrations

### 1. ElevenLabs API & Webhook
**Purpose**: Voice synthesis and conversation AI with event-driven data collection
**Files**:
- [app/integrations/elevenlabs.py](app/integrations/elevenlabs.py) - API client
- [app/api/v1/webhooks/elevenlabs.py](app/api/v1/webhooks/elevenlabs.py) - Webhook handler

**Operations**:
- **API**: Generate session tokens for voice conversations
- **API**: Voice synthesis (text-to-speech)
- **API**: Voice cloning (custom voices for premium)
- **Webhook**: Receive conversation data after calls
- **Webhook**: Post-call transcription and analysis

**Configuration**:
```python
ELEVENLABS_API_KEY: str
ELEVENLABS_BASE_URL: str = "https://api.elevenlabs.io/v1"
ELEVENLABS_VOICE_ID: str  # Default voice for toys
ELEVENLABS_WEBHOOK_SECRET: str  # For HMAC signature verification
```

**Webhook Security**:
```python
# Verify HMAC signature
def verify_elevenlabs_webhook(signature: str, payload: bytes, secret: str) -> bool:
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature, expected)
```

### 2. Payment Gateway (Stripe/Toss)
**Purpose**: Subscription payments
**File**: [app/integrations/payment.py](app/integrations/payment.py)

**Operations**:
- Create payment intent
- Confirm payment
- Handle webhooks
- Manage recurring billing

**Configuration**:
```python
PAYMENT_PROVIDER: str = "stripe"  # or "toss"
STRIPE_API_KEY: str (if Stripe)
TOSS_CLIENT_KEY: str (if Toss)
```

### 3. NoSQL Database (MongoDB)
**Purpose**: Conversation data storage
**File**: [app/integrations/nosql.py](app/integrations/nosql.py)

**Collections**:
- `conversations`: Conversation history
- `context_snapshots`: Periodic context checkpoints
- `analytics_events`: User interaction events

**Configuration**:
```python
MONGODB_URL: str
MONGODB_DATABASE: str = "uneseule"
```

### 4. Redis Cache
**Purpose**: Session management, rate limiting, caching
**Configuration**:
```python
REDIS_URL: str
REDIS_TTL_SESSION: int = 1800  # 30 minutes
REDIS_TTL_CACHE: int = 300  # 5 minutes
```

## 🛠️ Development Guidelines

### Code Organization

**Naming Conventions**:
- Files: `snake_case.py`
- Classes: `PascalCase`
- Functions/variables: `snake_case`
- Constants: `UPPER_SNAKE_CASE`

**Import Order**:
1. Standard library
2. Third-party packages
3. Local application imports

```python
# Standard library
from datetime import datetime
from typing import List, Optional

# Third-party
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

# Local
from app.core.dependencies import get_db
from app.models.user import User
from app.schemas.user import UserCreate
```

### API Design Principles

**RESTful Conventions**:
- `GET /api/v1/users` - List users
- `POST /api/v1/users` - Create user
- `GET /api/v1/users/{id}` - Get user
- `PUT /api/v1/users/{id}` - Update user
- `DELETE /api/v1/users/{id}` - Delete user

**Response Format**:
```json
{
  "success": true,
  "data": { ... },
  "message": "Optional message",
  "meta": {
    "timestamp": "2025-12-13T10:00:00Z",
    "request_id": "uuid"
  }
}
```

**Error Format**:
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed",
    "details": [
      {
        "field": "email",
        "message": "Invalid email format"
      }
    ]
  }
}
```

### Database Migration Workflow

**Create Migration**:
```bash
alembic revision --autogenerate -m "Add device table"
```

**Apply Migration**:
```bash
alembic upgrade head
```

**Rollback**:
```bash
alembic downgrade -1
```

### Testing Strategy

**Test Structure**:
```
tests/
├── unit/               # Isolated unit tests
│   ├── test_services.py
│   └── test_utils.py
├── integration/        # Database integration tests
│   └── test_repositories.py
└── e2e/               # End-to-end API tests
    └── test_auth_flow.py
```

**Running Tests**:
```bash
# All tests
pytest

# Specific test file
pytest tests/unit/test_services.py

# With coverage
pytest --cov=app --cov-report=html
```

## 🔐 Security Considerations

### Authentication
- **Method**: JWT (JSON Web Tokens)
- **Access Token TTL**: 30 minutes
- **Refresh Token TTL**: 7 days
- **Password Hashing**: bcrypt (cost factor: 12)

### Authorization
- **Parent Access**: Full CRUD on own children/devices
- **Device Access**: Limited to paired child's data
- **Admin Access**: System-wide operations (future)

### Data Protection
- **PII Encryption**: Child names, birthdates at rest
- **Conversation Privacy**: Parents can view summaries only
- **Device Security**: Serial number verification for pairing

### Rate Limiting
```python
# Per subscription tier
FREE_TIER_LIMIT = "50/day"
BASIC_TIER_LIMIT = "200/day"
PREMIUM_TIER_LIMIT = "unlimited"

# Global API protection
GLOBAL_RATE_LIMIT = "1000/minute"
```

## 📚 Common Tasks

### Adding a New GraphQL Query

1. **Define GraphQL Type**:
```python
# app/graphql/types/product.py
import strawberry
from typing import Optional

@strawberry.type
class Product:
    id: str
    name: str
    price: float
    description: Optional[str] = None
```

2. **Create Query Resolver**:
```python
# app/graphql/queries/product.py
import strawberry
from typing import List
from app.graphql.types.product import Product
from app.services.product_service import get_products

@strawberry.type
class ProductQueries:
    @strawberry.field
    async def products(self, info) -> List[Product]:
        # Access GraphQL context
        db = info.context.db
        user = info.context.user

        # Call service layer
        products = await get_products(db)
        return products
```

3. **Register in Main Schema**:
```python
# app/graphql/schema.py
import strawberry
from app.graphql.queries.product import ProductQueries

@strawberry.type
class Query(ProductQueries, ...):
    pass

schema = strawberry.Schema(query=Query)
```

### Adding a New GraphQL Mutation

1. **Define Input Type**:
```python
# app/graphql/types/product.py
@strawberry.input
class CreateProductInput:
    name: str
    price: float
    description: Optional[str] = None
```

2. **Create Mutation Resolver**:
```python
# app/graphql/mutations/product.py
import strawberry
from app.graphql.types.product import Product, CreateProductInput

@strawberry.type
class ProductMutations:
    @strawberry.mutation
    async def create_product(
        self,
        info,
        input: CreateProductInput
    ) -> Product:
        db = info.context.db
        user = info.context.user

        product = await create_product_service(db, input)
        return product
```

### Adding a New REST Endpoint (Device API)

1. **Create Router**:
```python
# app/api/v1/device/router.py
from fastapi import APIRouter, Depends, Header
from app.api.v1/device.auth import verify_device

router = APIRouter(prefix="/device", tags=["device"])

@router.post("/action")
async def device_action(
    device = Depends(verify_device),
    x_device_serial: str = Header(...),
    x_device_signature: str = Header(...),
):
    # Device-specific logic
    return {"status": "success"}
```

2. **Register Router**:
```python
# In main.py
from app.api.v1.device.router import router as device_router
app.include_router(device_router, prefix="/api/v1")
```

### Adding a New Webhook Handler

1. **Create Webhook Handler**:
```python
# app/api/v1/webhooks/new_service.py
from fastapi import APIRouter, Request, HTTPException
from app.utils.webhook_validators import verify_webhook_signature

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

@router.post("/new-service")
async def new_service_webhook(request: Request):
    # Get raw body for signature verification
    body = await request.body()
    signature = request.headers.get("X-Service-Signature")

    # Verify signature
    if not verify_webhook_signature(signature, body, settings.SERVICE_SECRET):
        raise HTTPException(status_code=401, detail="Invalid signature")

    # Process webhook data
    data = await request.json()
    await process_webhook_data(data)

    return {"status": "received"}
```

### Creating a Database Model

1. **Define Model**:
```python
# app/models/new_model.py
from sqlalchemy import Column, String, DateTime
from app.models.base import Base
import uuid

class NewModel(Base):
    __tablename__ = "new_models"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
```

2. **Create Migration**:
```bash
alembic revision --autogenerate -m "Add new_model table"
alembic upgrade head
```

### Adding External Integration

1. **Create Integration Module**:
```python
# app/integrations/new_service.py
import httpx
from app.core.config import settings

class NewServiceClient:
    def __init__(self):
        self.api_key = settings.NEW_SERVICE_API_KEY
        self.base_url = settings.NEW_SERVICE_URL

    async def call_api(self):
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/endpoint")
            return response.json()
```

2. **Add Configuration**:
```python
# app/core/config.py
class Settings(BaseSettings):
    NEW_SERVICE_API_KEY: str
    NEW_SERVICE_URL: str
```

## 🚀 Getting Started

### Prerequisites
- Python 3.14
- PostgreSQL 14+
- Redis 7+
- MongoDB 6+ (for conversations)

### Installation
```bash
# Install dependencies
uv sync

# Set up environment
cp .env.example .env
# Edit .env with your configuration

# Initialize database
alembic upgrade head

# Run development server
uvicorn main:app --reload
```

### Environment Variables
See [.env.example](.env.example) for required configuration.

## 📖 API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🎯 Roadmap

### Phase 1: Core Foundation (Current)
- ✅ Project structure
- ⏳ Authentication system
- ⏳ Database models
- ⏳ Basic CRUD operations

### Phase 2: Device Integration
- ⏳ Device pairing
- ⏳ Status monitoring
- ⏳ Remote control

### Phase 3: AI Voice
- ⏳ ElevenLabs integration
- ⏳ Token management
- ⏳ Rate limiting

### Phase 4: Conversations
- ⏳ NoSQL storage
- ⏳ Context engineering
- ⏳ Content moderation

### Phase 5: Business Logic
- ⏳ Subscription system
- ⏳ Payment integration
- ⏳ Analytics dashboard

## 📞 Support

For questions or issues, refer to:
- [Project README](README.md)
- API documentation (http://localhost:8000/docs)
- Code comments
