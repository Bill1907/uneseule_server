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
# 예시: 디바이스 토큰 발급 기능
"""
테스트 시나리오:
1. 정상 케이스: 유효한 디바이스가 토큰 발급 성공
2. 실패 케이스: 미등록 디바이스 → 401 에러
3. 실패 케이스: 페어링 안된 디바이스 → 403 에러
4. 실패 케이스: 만료된 구독 → 403 에러
5. 경계 케이스: Rate limit 초과 → 429 에러
"""
```

### 2단계: 테스트 코드 작성

```bash
# 테스트 파일 위치
tests/
├── unit/           # 단위 테스트 (서비스, 유틸리티)
├── integration/    # 통합 테스트 (리포지토리, DB)
└── e2e/            # API 엔드포인트 테스트
```

### 3단계: 테스트 실행 및 확인

```bash
# 특정 테스트 파일 실행
pytest tests/unit/test_device_auth.py -v

# 특정 테스트 클래스/함수 실행
pytest tests/unit/test_device_auth.py::TestVerifyDeviceSignature -v
pytest tests/unit/test_device_auth.py::TestVerifyDeviceSignature::test_valid_signature -v

# 실패한 테스트만 재실행
pytest --lf -v

# 커버리지 포함
pytest --cov=app --cov-report=term-missing
```

### 4단계: 구현 후 전체 테스트

```bash
# 전체 테스트 실행
pytest

# 특정 디렉토리 테스트
pytest tests/unit/ -v
pytest tests/e2e/ -v
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
API Layer
├── /graphql (Strawberry) → Parent App (모바일/웹)
├── /api/v1/device (REST) → IoT 디바이스
└── /webhooks → External events (ElevenLabs, Payment)

Service Layer → Business logic (GraphQL/REST 공유)
Repository Layer → DB 추상화 (PostgreSQL, MongoDB, Redis)
Model Layer → SQLAlchemy ORM
```

### Dual API Strategy

- **GraphQL** (`/graphql`): 부모 앱용. 중첩 쿼리, 유연한 필드 선택
- **REST** (`/api/v1/device`): IoT 디바이스용. HMAC-SHA256 인증
- **Webhooks**: ElevenLabs 대화 데이터, 결제 이벤트 수신

### Test Structure

```
tests/
├── conftest.py         # 공유 fixtures (mock_db_session, mock_redis_client)
├── unit/               # 서비스, 유틸리티 테스트
├── integration/        # DB 연동 테스트
└── e2e/                # API 엔드포인트 테스트
```

### Test Fixtures (conftest.py)

```python
@pytest.fixture
def mock_db_session():     # AsyncMock DB 세션
    ...

@pytest.fixture
def mock_redis_client():   # AsyncMock Redis 클라이언트
    ...
```

## Key Patterns

### Device Authentication (HMAC)

```python
# Headers
X-Device-Serial: ABC123XYZ
X-Device-Signature: hmac_sha256(serial + timestamp + body, secret)
X-Device-Timestamp: 1234567890
```

### Test Pattern Example

```python
class TestFeatureName:
    """Feature 테스트 클래스"""

    @pytest.fixture
    def setup_data(self):
        """테스트 데이터 준비"""
        return {...}

    def test_success_case(self, setup_data):
        """정상 케이스"""
        result = function_under_test(...)
        assert result is True

    def test_failure_case(self, setup_data):
        """실패 케이스"""
        result = function_under_test(...)
        assert result is False
```

## Environment Variables

테스트 실행 시 `tests/conftest.py`에서 환경 변수가 자동 설정됩니다:
- `DATABASE_URL`, `SECRET_KEY`, `MONGODB_URL`
- `ELEVENLABS_API_KEY`, `ELEVENLABS_VOICE_ID`, `ELEVENLABS_AGENT_ID`

실제 환경은 `.env` 파일에서 관리 (`.env.example` 참조).
