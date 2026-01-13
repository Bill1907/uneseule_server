"""
End-to-end tests for GraphQL API.
"""

import uuid
from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.graphql.schema import create_graphql_router


# Create test app with GraphQL router
def create_test_app():
    app = FastAPI()
    graphql_router = create_graphql_router()
    app.include_router(graphql_router, prefix="/graphql")
    return app


app = create_test_app()


def generate_mock_jwt_token(user_id: str) -> str:
    """Generate mock JWT token for testing."""
    return f"mock-jwt-token-{user_id}"


class TestGraphQLIntrospection:
    """Tests for GraphQL schema introspection."""

    def test_introspection_query(self):
        """Test that schema introspection works."""
        query = """
        {
            __schema {
                queryType {
                    fields {
                        name
                    }
                }
            }
        }
        """

        with patch("app.graphql.context.AsyncSessionLocal"):
            client = TestClient(app)
            response = client.post(
                "/graphql",
                json={"query": query},
            )

            assert response.status_code == 200
            data = response.json()
            assert "data" in data
            assert "__schema" in data["data"]

            field_names = [
                f["name"] for f in data["data"]["__schema"]["queryType"]["fields"]
            ]
            assert "me" in field_names
            assert "myChildren" in field_names
            assert "mySubscription" in field_names
            assert "myDevices" in field_names
            assert "device" in field_names
            assert "hello" in field_names

    def test_hello_query(self):
        """Test simple hello query."""
        query = "{ hello }"

        with patch("app.graphql.context.AsyncSessionLocal"):
            client = TestClient(app)
            response = client.post(
                "/graphql",
                json={"query": query},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["data"]["hello"] == "Hello from Uneseule GraphQL API"


class TestMeQuery:
    """Tests for me query."""

    @pytest.fixture
    def mock_user(self):
        """Create mock user."""
        user = MagicMock()
        user.id = uuid.uuid4()
        user.email = "test@example.com"
        user.name = "테스트유저"
        user.phone = "010-1234-5678"
        user.is_active = True
        user.email_verified = True
        user.created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
        user.updated_at = datetime(2024, 6, 1, tzinfo=timezone.utc)
        user.children = []
        user.subscription = None
        return user

    def test_me_without_auth(self):
        """Test me query without authentication returns null."""
        query = """
        {
            me {
                id
                email
                name
            }
        }
        """

        with patch("app.graphql.context.AsyncSessionLocal"):
            client = TestClient(app)
            response = client.post(
                "/graphql",
                json={"query": query},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["data"]["me"] is None

    def test_me_with_auth(self, mock_user):
        """Test me query with authentication."""
        query = """
        {
            me {
                id
                email
                name
                phone
                isActive
                emailVerified
            }
        }
        """

        user_id = str(mock_user.id)

        with patch("app.graphql.context.AsyncSessionLocal") as MockSession, patch(
            "app.graphql.context.neon_auth"
        ) as mock_neon_auth:
            # Setup JWT verification
            mock_neon_auth.verify_token = AsyncMock(return_value={"sub": user_id})
            mock_neon_auth.get_user_id_from_payload.return_value = user_id

            # Setup DB session
            mock_db = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_user
            mock_db.execute.return_value = mock_result
            MockSession.return_value = mock_db

            client = TestClient(app)
            response = client.post(
                "/graphql",
                json={"query": query},
                headers={"Authorization": f"Bearer {generate_mock_jwt_token(user_id)}"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["data"]["me"] is not None
            assert data["data"]["me"]["email"] == "test@example.com"
            assert data["data"]["me"]["name"] == "테스트유저"
            assert data["data"]["me"]["isActive"] is True


class TestMyChildrenQuery:
    """Tests for myChildren query."""

    @pytest.fixture
    def mock_children(self):
        """Create mock children list."""
        child1 = MagicMock()
        child1.id = uuid.uuid4()
        child1.name = "첫째아이"
        child1.birth_date = date(2019, 3, 15)
        child1.gender = "male"
        child1.age = 5
        child1.is_active = True
        child1.created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
        child1.updated_at = None
        child1.device = None

        child2 = MagicMock()
        child2.id = uuid.uuid4()
        child2.name = "둘째아이"
        child2.birth_date = date(2021, 7, 20)
        child2.gender = "female"
        child2.age = 3
        child2.is_active = True
        child2.created_at = datetime(2024, 2, 1, tzinfo=timezone.utc)
        child2.updated_at = None
        child2.device = None

        return [child1, child2]

    def test_my_children_without_auth(self):
        """Test myChildren query without authentication returns empty list."""
        query = """
        {
            myChildren {
                id
                name
            }
        }
        """

        with patch("app.graphql.context.AsyncSessionLocal"):
            client = TestClient(app)
            response = client.post(
                "/graphql",
                json={"query": query},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["data"]["myChildren"] == []

    def test_my_children_with_auth(self, mock_children):
        """Test myChildren query with authentication."""
        query = """
        {
            myChildren {
                id
                name
                age
                gender
            }
        }
        """

        user_id = str(uuid.uuid4())

        with patch("app.graphql.context.AsyncSessionLocal") as MockSession, patch(
            "app.graphql.context.neon_auth"
        ) as mock_neon_auth:
            mock_neon_auth.verify_token = AsyncMock(return_value={"sub": user_id})
            mock_neon_auth.get_user_id_from_payload.return_value = user_id

            mock_db = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = mock_children
            mock_db.execute.return_value = mock_result
            MockSession.return_value = mock_db

            client = TestClient(app)
            response = client.post(
                "/graphql",
                json={"query": query},
                headers={"Authorization": f"Bearer {generate_mock_jwt_token(user_id)}"},
            )

            assert response.status_code == 200
            data = response.json()
            children = data["data"]["myChildren"]
            assert len(children) == 2
            assert children[0]["name"] == "첫째아이"
            assert children[0]["age"] == 5
            assert children[1]["name"] == "둘째아이"
            assert children[1]["age"] == 3


class TestMyDevicesQuery:
    """Tests for myDevices query."""

    @pytest.fixture
    def mock_device(self):
        """Create mock device."""
        device = MagicMock()
        device.id = uuid.uuid4()
        device.serial_number = "ABC123XYZ"
        device.device_type = "bunny_v1"
        device.firmware_version = "1.2.3"
        device.battery_level = 85
        device.connection_status = "online"
        device.is_active = True
        device.paired_at = datetime(2024, 3, 1, tzinfo=timezone.utc)
        device.child_id = uuid.uuid4()
        device.child = MagicMock()
        device.child.name = "테스트아이"
        device.created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
        device.updated_at = None
        return device

    def test_my_devices_without_auth(self):
        """Test myDevices query without authentication returns empty list."""
        query = """
        {
            myDevices {
                id
                serialNumber
            }
        }
        """

        with patch("app.graphql.context.AsyncSessionLocal"):
            client = TestClient(app)
            response = client.post(
                "/graphql",
                json={"query": query},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["data"]["myDevices"] == []

    def test_my_devices_with_auth(self, mock_device):
        """Test myDevices query with authentication."""
        query = """
        {
            myDevices {
                id
                serialNumber
                deviceType
                firmwareVersion
                batteryLevel
                connectionStatus
                childName
            }
        }
        """

        user_id = str(uuid.uuid4())

        with patch("app.graphql.context.AsyncSessionLocal") as MockSession, patch(
            "app.graphql.context.neon_auth"
        ) as mock_neon_auth:
            mock_neon_auth.verify_token = AsyncMock(return_value={"sub": user_id})
            mock_neon_auth.get_user_id_from_payload.return_value = user_id

            mock_db = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = [mock_device]
            mock_db.execute.return_value = mock_result
            MockSession.return_value = mock_db

            client = TestClient(app)
            response = client.post(
                "/graphql",
                json={"query": query},
                headers={"Authorization": f"Bearer {generate_mock_jwt_token(user_id)}"},
            )

            assert response.status_code == 200
            data = response.json()
            devices = data["data"]["myDevices"]
            assert len(devices) == 1
            assert devices[0]["serialNumber"] == "ABC123XYZ"
            assert devices[0]["batteryLevel"] == 85
            assert devices[0]["connectionStatus"] == "ONLINE"
            assert devices[0]["childName"] == "테스트아이"


class TestMySubscriptionQuery:
    """Tests for mySubscription query."""

    @pytest.fixture
    def mock_subscription(self):
        """Create mock subscription."""
        sub = MagicMock()
        sub.id = uuid.uuid4()
        sub.plan_type = "premium"
        sub.status = "active"
        sub.started_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
        sub.expires_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
        sub.auto_renew = True
        sub.is_expired = False
        sub.created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
        sub.updated_at = None
        return sub

    def test_my_subscription_without_auth(self):
        """Test mySubscription query without authentication returns null."""
        query = """
        {
            mySubscription {
                id
                planType
            }
        }
        """

        with patch("app.graphql.context.AsyncSessionLocal"):
            client = TestClient(app)
            response = client.post(
                "/graphql",
                json={"query": query},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["data"]["mySubscription"] is None

    def test_my_subscription_with_auth(self, mock_subscription):
        """Test mySubscription query with authentication."""
        query = """
        {
            mySubscription {
                id
                planType
                status
                autoRenew
                isExpired
            }
        }
        """

        user_id = str(uuid.uuid4())

        with patch("app.graphql.context.AsyncSessionLocal") as MockSession, patch(
            "app.graphql.context.neon_auth"
        ) as mock_neon_auth:
            mock_neon_auth.verify_token = AsyncMock(return_value={"sub": user_id})
            mock_neon_auth.get_user_id_from_payload.return_value = user_id

            mock_db = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_subscription
            mock_db.execute.return_value = mock_result
            MockSession.return_value = mock_db

            client = TestClient(app)
            response = client.post(
                "/graphql",
                json={"query": query},
                headers={"Authorization": f"Bearer {generate_mock_jwt_token(user_id)}"},
            )

            assert response.status_code == 200
            data = response.json()
            subscription = data["data"]["mySubscription"]
            assert subscription is not None
            assert subscription["planType"] == "PREMIUM"
            assert subscription["status"] == "ACTIVE"
            assert subscription["autoRenew"] is True
            assert subscription["isExpired"] is False


class TestChildQuery:
    """Tests for child query by ID."""

    @pytest.fixture
    def mock_child(self):
        """Create mock child."""
        child = MagicMock()
        child.id = uuid.uuid4()
        child.name = "개별아이"
        child.birth_date = date(2020, 5, 10)
        child.gender = "female"
        child.age = 4
        child.is_active = True
        child.created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
        child.updated_at = None
        child.device = None
        return child

    def test_child_by_id(self, mock_child):
        """Test fetching specific child by ID."""
        query = """
        query GetChild($id: String!) {
            child(id: $id) {
                id
                name
                age
                gender
            }
        }
        """

        user_id = str(uuid.uuid4())
        child_id = str(mock_child.id)

        with patch("app.graphql.context.AsyncSessionLocal") as MockSession, patch(
            "app.graphql.context.neon_auth"
        ) as mock_neon_auth:
            mock_neon_auth.verify_token = AsyncMock(return_value={"sub": user_id})
            mock_neon_auth.get_user_id_from_payload.return_value = user_id

            mock_db = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_child
            mock_db.execute.return_value = mock_result
            MockSession.return_value = mock_db

            client = TestClient(app)
            response = client.post(
                "/graphql",
                json={"query": query, "variables": {"id": child_id}},
                headers={"Authorization": f"Bearer {generate_mock_jwt_token(user_id)}"},
            )

            assert response.status_code == 200
            data = response.json()
            child = data["data"]["child"]
            assert child is not None
            assert child["name"] == "개별아이"
            assert child["age"] == 4

    def test_child_not_found(self):
        """Test child query when child doesn't exist."""
        query = """
        query GetChild($id: String!) {
            child(id: $id) {
                id
                name
            }
        }
        """

        user_id = str(uuid.uuid4())

        with patch("app.graphql.context.AsyncSessionLocal") as MockSession, patch(
            "app.graphql.context.neon_auth"
        ) as mock_neon_auth:
            mock_neon_auth.verify_token = AsyncMock(return_value={"sub": user_id})
            mock_neon_auth.get_user_id_from_payload.return_value = user_id

            mock_db = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_db.execute.return_value = mock_result
            MockSession.return_value = mock_db

            client = TestClient(app)
            response = client.post(
                "/graphql",
                json={"query": query, "variables": {"id": str(uuid.uuid4())}},
                headers={"Authorization": f"Bearer {generate_mock_jwt_token(user_id)}"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["data"]["child"] is None
