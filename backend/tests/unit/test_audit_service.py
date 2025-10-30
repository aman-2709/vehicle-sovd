"""
Unit tests for audit service.

Tests audit log creation for various event types with different data combinations.
"""

import uuid
from unittest.mock import MagicMock, patch

import pytest

from app.services.audit_service import log_audit_event


class TestAuditService:
    """Test audit logging functionality."""

    @pytest.mark.asyncio
    async def test_log_audit_event_user_login_success(self):
        """Test logging a successful user login event."""
        # Arrange
        user_id = uuid.uuid4()
        action = "user_login"
        entity_type = "user"
        entity_id = user_id
        details = {"username": "test_user", "session_id": str(uuid.uuid4())}
        ip_address = "192.168.1.100"
        user_agent = "Mozilla/5.0"

        mock_db_session = MagicMock()
        mock_audit_log = MagicMock()
        mock_audit_log.log_id = uuid.uuid4()
        mock_audit_log.action = action

        with patch("app.services.audit_service.audit_repository.create_audit_log") as mock_create:
            mock_create.return_value = mock_audit_log

            # Act
            result = await log_audit_event(
                user_id=user_id,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                details=details,
                ip_address=ip_address,
                user_agent=user_agent,
                db_session=mock_db_session,
            )

            # Assert
            assert result is True
            mock_create.assert_called_once_with(
                db=mock_db_session,
                user_id=user_id,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                details=details,
                ip_address=ip_address,
                user_agent=user_agent,
                vehicle_id=None,
                command_id=None,
            )

    @pytest.mark.asyncio
    async def test_log_audit_event_user_logout_success(self):
        """Test logging a successful user logout event."""
        # Arrange
        user_id = uuid.uuid4()
        action = "user_logout"
        entity_type = "user"
        entity_id = user_id
        details = {"username": "test_user"}
        ip_address = "10.0.0.50"
        user_agent = "Chrome/98.0"

        mock_db_session = MagicMock()
        mock_audit_log = MagicMock()

        with patch("app.services.audit_service.audit_repository.create_audit_log") as mock_create:
            mock_create.return_value = mock_audit_log

            # Act
            result = await log_audit_event(
                user_id=user_id,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                details=details,
                ip_address=ip_address,
                user_agent=user_agent,
                db_session=mock_db_session,
            )

            # Assert
            assert result is True
            mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_log_audit_event_command_submitted_success(self):
        """Test logging a command submission event."""
        # Arrange
        user_id = uuid.uuid4()
        vehicle_id = uuid.uuid4()
        command_id = uuid.uuid4()
        action = "command_submitted"
        entity_type = "command"
        entity_id = command_id
        details = {
            "command_name": "ReadDTC",
            "command_params": {"ecuAddress": "0x10"}
        }
        ip_address = "172.16.0.1"
        user_agent = "PostmanRuntime/7.29.0"

        mock_db_session = MagicMock()
        mock_audit_log = MagicMock()

        with patch("app.services.audit_service.audit_repository.create_audit_log") as mock_create:
            mock_create.return_value = mock_audit_log

            # Act
            result = await log_audit_event(
                user_id=user_id,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                details=details,
                ip_address=ip_address,
                user_agent=user_agent,
                db_session=mock_db_session,
                vehicle_id=vehicle_id,
                command_id=command_id,
            )

            # Assert
            assert result is True
            mock_create.assert_called_once_with(
                db=mock_db_session,
                user_id=user_id,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                details=details,
                ip_address=ip_address,
                user_agent=user_agent,
                vehicle_id=vehicle_id,
                command_id=command_id,
            )

    @pytest.mark.asyncio
    async def test_log_audit_event_command_completed_success(self):
        """Test logging a command completion event."""
        # Arrange
        user_id = uuid.uuid4()
        vehicle_id = uuid.uuid4()
        command_id = uuid.uuid4()
        action = "command_completed"
        entity_type = "command"
        entity_id = command_id
        details = {
            "command_name": "ReadDTC",
            "response_payload": {"dtcs": []}
        }

        mock_db_session = MagicMock()
        mock_audit_log = MagicMock()

        with patch("app.services.audit_service.audit_repository.create_audit_log") as mock_create:
            mock_create.return_value = mock_audit_log

            # Act
            result = await log_audit_event(
                user_id=user_id,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                details=details,
                ip_address=None,  # Not available in background task
                user_agent=None,  # Not available in background task
                db_session=mock_db_session,
                vehicle_id=vehicle_id,
                command_id=command_id,
            )

            # Assert
            assert result is True
            mock_create.assert_called_once()
            # Verify that None values are passed for IP and user agent
            call_args = mock_create.call_args
            assert call_args.kwargs["ip_address"] is None
            assert call_args.kwargs["user_agent"] is None

    @pytest.mark.asyncio
    async def test_log_audit_event_command_failed_success(self):
        """Test logging a command failure event."""
        # Arrange
        user_id = uuid.uuid4()
        vehicle_id = uuid.uuid4()
        command_id = uuid.uuid4()
        action = "command_failed"
        entity_type = "command"
        entity_id = command_id
        details = {
            "command_name": "ReadDTC",
            "error": "Connection timeout"
        }

        mock_db_session = MagicMock()
        mock_audit_log = MagicMock()

        with patch("app.services.audit_service.audit_repository.create_audit_log") as mock_create:
            mock_create.return_value = mock_audit_log

            # Act
            result = await log_audit_event(
                user_id=user_id,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                details=details,
                ip_address=None,
                user_agent=None,
                db_session=mock_db_session,
                vehicle_id=vehicle_id,
                command_id=command_id,
            )

            # Assert
            assert result is True
            mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_log_audit_event_with_null_user_id(self):
        """Test logging an event with null user_id (system event)."""
        # Arrange
        action = "system_maintenance"
        entity_type = "system"
        details = {"task": "cleanup_old_sessions"}

        mock_db_session = MagicMock()
        mock_audit_log = MagicMock()

        with patch("app.services.audit_service.audit_repository.create_audit_log") as mock_create:
            mock_create.return_value = mock_audit_log

            # Act
            result = await log_audit_event(
                user_id=None,  # System event, no user
                action=action,
                entity_type=entity_type,
                entity_id=None,
                details=details,
                ip_address=None,
                user_agent=None,
                db_session=mock_db_session,
            )

            # Assert
            assert result is True
            mock_create.assert_called_once()
            call_args = mock_create.call_args
            assert call_args.kwargs["user_id"] is None

    @pytest.mark.asyncio
    async def test_log_audit_event_with_ipv6_address(self):
        """Test logging an event with IPv6 address."""
        # Arrange
        user_id = uuid.uuid4()
        action = "user_login"
        entity_type = "user"
        entity_id = user_id
        details = {"username": "test_user"}
        ip_address = "2001:0db8:85a3:0000:0000:8a2e:0370:7334"  # IPv6
        user_agent = "Firefox/96.0"

        mock_db_session = MagicMock()
        mock_audit_log = MagicMock()

        with patch("app.services.audit_service.audit_repository.create_audit_log") as mock_create:
            mock_create.return_value = mock_audit_log

            # Act
            result = await log_audit_event(
                user_id=user_id,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                details=details,
                ip_address=ip_address,
                user_agent=user_agent,
                db_session=mock_db_session,
            )

            # Assert
            assert result is True
            mock_create.assert_called_once()
            call_args = mock_create.call_args
            assert call_args.kwargs["ip_address"] == ip_address

    @pytest.mark.asyncio
    async def test_log_audit_event_with_empty_details(self):
        """Test logging an event with empty details dict."""
        # Arrange
        user_id = uuid.uuid4()
        action = "user_login"
        entity_type = "user"
        entity_id = user_id
        details = None  # Will be converted to empty dict
        ip_address = "192.168.1.1"
        user_agent = "Safari/14.0"

        mock_db_session = MagicMock()
        mock_audit_log = MagicMock()

        with patch("app.services.audit_service.audit_repository.create_audit_log") as mock_create:
            mock_create.return_value = mock_audit_log

            # Act
            result = await log_audit_event(
                user_id=user_id,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                details=details,
                ip_address=ip_address,
                user_agent=user_agent,
                db_session=mock_db_session,
            )

            # Assert
            assert result is True
            mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_log_audit_event_handles_exception_gracefully(self):
        """Test that audit logging failures don't raise exceptions."""
        # Arrange
        user_id = uuid.uuid4()
        action = "user_login"
        entity_type = "user"
        entity_id = user_id
        details = {"username": "test_user"}
        ip_address = "192.168.1.1"
        user_agent = "Chrome/98.0"

        mock_db_session = MagicMock()

        with patch("app.services.audit_service.audit_repository.create_audit_log") as mock_create:
            # Simulate database error
            mock_create.side_effect = Exception("Database connection failed")

            # Act
            result = await log_audit_event(
                user_id=user_id,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                details=details,
                ip_address=ip_address,
                user_agent=user_agent,
                db_session=mock_db_session,
            )

            # Assert
            assert result is False  # Should return False on failure
            mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_log_audit_event_complex_details(self):
        """Test logging an event with complex nested details."""
        # Arrange
        user_id = uuid.uuid4()
        command_id = uuid.uuid4()
        action = "command_submitted"
        entity_type = "command"
        entity_id = command_id
        details = {
            "command_name": "ReadDataByID",
            "command_params": {
                "dataId": "0x010C",
                "ecuAddress": "0x10",
                "nested": {
                    "level1": {
                        "level2": "deep_value"
                    }
                }
            },
            "metadata": {
                "source": "api",
                "version": "1.0"
            }
        }
        ip_address = "203.0.113.42"
        user_agent = "Custom-Client/1.0"

        mock_db_session = MagicMock()
        mock_audit_log = MagicMock()

        with patch("app.services.audit_service.audit_repository.create_audit_log") as mock_create:
            mock_create.return_value = mock_audit_log

            # Act
            result = await log_audit_event(
                user_id=user_id,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                details=details,
                ip_address=ip_address,
                user_agent=user_agent,
                db_session=mock_db_session,
                command_id=command_id,
            )

            # Assert
            assert result is True
            mock_create.assert_called_once()
            call_args = mock_create.call_args
            assert call_args.kwargs["details"] == details
