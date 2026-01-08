# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI Voice Agent Backend for Smart Toy (애착인형) System. FastAPI 기반의 백엔드 서비스로, 아이들을 위한 AI 음성 경험을 제공하는 스마트 토이를 관리합니다.

**Stack**: Python 3.14, FastAPI, SQLAlchemy, Strawberry GraphQL, PostgreSQL, MongoDB, Redis

## Development Workflow (TDD)

**이 프로젝트는 TDD(Test-Driven Development) 방식으로 개발합니다.**

### 작업 순서

```
1. 테스트 시나리오 설계 → 2. 테스트 코드 작성 → 3. 테스트 실패 확인 (Red)
       ↓                                              ↓
4. 구현 코드 작성 → 5. 테스트 통과 확인 (Green) → 6. 리팩토링 (Refactor)
```

### 1단계: 테스트 시나리오 설계

새 기능 개발 전 먼저 테스트 시나리오를 정의합니다:

```python
"""
테스트 시나리오 예시 (디바이스 토큰 발급):
1. 정상 케이스: 유효한 디바이스가 토큰 발급 성공
2. 실패 케이스: 미등록 디바이스 → 401 에러
3. 실패 케이스: 페어링 안된 디바이스 → 403 에러
4. 경계 케이스: Rate limit 초과 → 429 에러
"""
```

### 2단계: 테스트 코드 작성

```
tests/
├── conftest.py         # 공유 fixtures (mock_db_session, mock_redis_client)
├── unit/               # 단위 테스트 (서비스, 유틸리티)
├── integration/        # 통합 테스트 (리포지토리, DB)
└── e2e/                # API 엔드포인트 테스트
```

### 3~6단계: 테스트 실행 → 구현 → 확인 → 리팩토링

```bash
# 특정 테스트 실행
pytest tests/unit/test_device_auth.py -v
pytest tests/unit/test_device_auth.py::TestClass::test_method -v

# 실패한 테스트만 재실행
pytest --lf -v

# 전체 테스트 + 커버리지
pytest --cov=app --cov-report=term-missing
```

## Commands

```bash
# Dependencies
uv sync                                    # 의존성 설치

# Server
uvicorn main:app --reload                  # 개발 서버 실행

# Database
alembic revision --autogenerate -m "msg"   # 마이그레이션 생성
alembic upgrade head                       # 마이그레이션 적용
alembic downgrade -1                       # 롤백

# Testing
pytest                                     # 전체 테스트
pytest tests/unit/test_file.py -v          # 단일 파일
pytest tests/unit/test_file.py::TestClass::test_method -v  # 단일 테스트
pytest --cov=app --cov-report=html         # 커버리지 리포트

# Code Quality
ruff check app/                            # 린트
ruff format app/                           # 포맷
mypy app/                                  # 타입 체크
```

## Architecture

**Clean Architecture + Hybrid API (GraphQL + REST)**

```
┌─────────────────────────────────────────────────────────────┐
│                      API Layer                               │
│  ┌─────────────┬──────────────┬──────────────────────────┐  │
│  │  GraphQL    │  REST API    │  Webhooks                │  │
│  │  /graphql   │  /api/v1/    │  /webhooks/payment       │  │
│  │  (Parent)   │  (Device)    │                          │  │
│  └─────────────┴──────────────┴──────────────────────────┘  │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│  Service Layer (비즈니스 로직, GraphQL/REST 공유)            │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│  Repository Layer (PostgreSQL, MongoDB, Redis)              │
└─────────────────────────────────────────────────────────────┘
```

### API Strategy

| API | 경로 | 용도 | 인증 |
|-----|------|------|------|
| GraphQL | `/graphql` | 부모 앱 (모바일/웹) | JWT |
| REST | `/api/v1/device/*` | IoT 디바이스 | HMAC-SHA256 |
| Webhook | `/webhooks/*` | 외부 이벤트 수신 | HMAC 서명 |

### Layer Responsibilities

- **GraphQL Layer** (`app/graphql/`): Strawberry 스키마, 리졸버, 구독
- **REST API Layer** (`app/api/v1/`): 디바이스 엔드포인트, 웹훅 핸들러
- **Service Layer** (`app/services/`): 비즈니스 로직 (API 레이어 공유)
- **Repository Layer** (`app/repositories/`): DB 추상화, CRUD
- **Model Layer** (`app/models/`): SQLAlchemy ORM

## Domain Model

```
User (1) ──┬── (n) Child ──── (1) Device
           │
           └── (1) Subscription

Device (1) ──── (n) Conversation (MongoDB)
```

### Core Entities

- **User**: 부모 계정 (email, password_hash, children)
- **Child**: 자녀 프로필 (name, birth_date, personality_traits)
- **Device**: 스마트 토이 (serial_number, battery_level, connection_status)
- **Subscription**: 구독 (plan_type: free/basic/premium)
- **Conversation**: 대화 기록 (MongoDB, messages, context)

## Key Patterns

### Device Authentication (HMAC)

```python
# Request Headers
X-Device-Serial: ABC123XYZ
X-Device-Signature: hmac_sha256(serial + timestamp + body, secret)
X-Device-Timestamp: 1234567890

# 5분 이내 타임스탬프만 허용
```

### Test Pattern

```python
class TestFeatureName:
    @pytest.fixture
    def setup_data(self):
        return {...}

    def test_success_case(self, setup_data):
        result = function_under_test(...)
        assert result is True

    def test_failure_case(self, setup_data):
        result = function_under_test(...)
        assert result is False
```

### Test Fixtures (conftest.py)

```python
@pytest.fixture
def mock_db_session():     # AsyncMock DB 세션

@pytest.fixture
def mock_redis_client():   # AsyncMock Redis 클라이언트
```

## External Integrations

| 서비스 | 용도 | 파일 |
|--------|------|------|
| LiveKit Cloud | 실시간 음성/비디오 통신 | `app/integrations/livekit.py` |
| Payment (Stripe/Toss) | 구독 결제 | `app/integrations/payment.py` |
| MongoDB | 대화 데이터 저장 | `app/integrations/nosql.py` |

## Environment

테스트: `tests/conftest.py`에서 환경 변수 자동 설정
실제 환경: `.env` 파일 (`.env.example` 참조)

```
DATABASE_URL, SECRET_KEY, MONGODB_URL
LIVEKIT_API_KEY, LIVEKIT_API_SECRET, LIVEKIT_URL
```
