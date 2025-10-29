"""
Unit tests for response repository.

Tests response repository functions with database mocks.
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.response import Response
from app.repositories import response_repository


class TestCreateResponse:
    """Test create_response function."""

    @pytest.mark.asyncio
    async def test_create_response_success(self):
        """Test successful response creation."""
        command_id = uuid.uuid4()
        response_payload = {"status": "success", "data": {"locked": True}}
        sequence_number = 1
        is_final = True

        mock_db = AsyncMock(spec=AsyncSession)

        # Create a mock response with a generated ID
        mock_response = Response(
            response_id=uuid.uuid4(),
            command_id=command_id,
            response_payload=response_payload,
            sequence_number=sequence_number,
            is_final=is_final,
            received_at=datetime.now(timezone.utc),
        )

        # Mock the session methods
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        with patch(
            "app.repositories.response_repository.Response", return_value=mock_response
        ):
            result = await response_repository.create_response(
                db=mock_db,
                command_id=command_id,
                response_payload=response_payload,
                sequence_number=sequence_number,
                is_final=is_final,
            )

            # Assertions
            assert result is not None
            assert result.command_id == command_id
            assert result.response_payload == response_payload
            assert result.sequence_number == sequence_number
            assert result.is_final == is_final

            # Verify database operations
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()
            mock_db.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_response_not_final(self):
        """Test creating a non-final response."""
        command_id = uuid.uuid4()
        response_payload = {"status": "in_progress", "percent": 50}
        sequence_number = 1
        is_final = False

        mock_db = AsyncMock(spec=AsyncSession)

        mock_response = Response(
            response_id=uuid.uuid4(),
            command_id=command_id,
            response_payload=response_payload,
            sequence_number=sequence_number,
            is_final=is_final,
            received_at=datetime.now(timezone.utc),
        )

        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        with patch(
            "app.repositories.response_repository.Response", return_value=mock_response
        ):
            result = await response_repository.create_response(
                db=mock_db,
                command_id=command_id,
                response_payload=response_payload,
                sequence_number=sequence_number,
                is_final=is_final,
            )

            assert result is not None
            assert result.is_final is False
            assert result.sequence_number == 1

    @pytest.mark.asyncio
    async def test_create_response_multiple_sequence(self):
        """Test creating responses with different sequence numbers."""
        command_id = uuid.uuid4()

        for seq_num in range(1, 4):
            response_payload = {"chunk": seq_num}
            is_final = seq_num == 3

            mock_db = AsyncMock(spec=AsyncSession)
            mock_response = Response(
                response_id=uuid.uuid4(),
                command_id=command_id,
                response_payload=response_payload,
                sequence_number=seq_num,
                is_final=is_final,
                received_at=datetime.now(timezone.utc),
            )

            mock_db.add = MagicMock()
            mock_db.commit = AsyncMock()
            mock_db.refresh = AsyncMock()

            with patch(
                "app.repositories.response_repository.Response", return_value=mock_response
            ):
                result = await response_repository.create_response(
                    db=mock_db,
                    command_id=command_id,
                    response_payload=response_payload,
                    sequence_number=seq_num,
                    is_final=is_final,
                )

                assert result.sequence_number == seq_num
                assert result.is_final == is_final


class TestGetResponsesByCommandId:
    """Test get_responses_by_command_id function."""

    @pytest.mark.asyncio
    async def test_get_responses_by_command_id_single_response(self):
        """Test retrieving a single response for a command."""
        command_id = uuid.uuid4()
        mock_response = Response(
            response_id=uuid.uuid4(),
            command_id=command_id,
            response_payload={"status": "success"},
            sequence_number=1,
            is_final=True,
            received_at=datetime.now(timezone.utc),
        )

        mock_db = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_response]
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await response_repository.get_responses_by_command_id(mock_db, command_id)

        assert len(result) == 1
        assert result[0].command_id == command_id
        assert result[0].sequence_number == 1
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_responses_by_command_id_multiple_responses(self):
        """Test retrieving multiple responses ordered by sequence."""
        command_id = uuid.uuid4()
        mock_responses = [
            Response(
                response_id=uuid.uuid4(),
                command_id=command_id,
                response_payload={"chunk": i},
                sequence_number=i,
                is_final=(i == 3),
                received_at=datetime.now(timezone.utc),
            )
            for i in range(1, 4)
        ]

        mock_db = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = mock_responses
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await response_repository.get_responses_by_command_id(mock_db, command_id)

        assert len(result) == 3
        assert result[0].sequence_number == 1
        assert result[1].sequence_number == 2
        assert result[2].sequence_number == 3
        assert result[2].is_final is True
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_responses_by_command_id_no_responses(self):
        """Test retrieving responses when none exist."""
        command_id = uuid.uuid4()

        mock_db = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await response_repository.get_responses_by_command_id(mock_db, command_id)

        assert len(result) == 0
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_responses_by_command_id_ordering(self):
        """Test that responses are ordered by sequence number."""
        command_id = uuid.uuid4()
        # Create responses in reverse order to test ordering
        mock_responses = [
            Response(
                response_id=uuid.uuid4(),
                command_id=command_id,
                response_payload={"chunk": 3},
                sequence_number=3,
                is_final=True,
                received_at=datetime.now(timezone.utc),
            ),
            Response(
                response_id=uuid.uuid4(),
                command_id=command_id,
                response_payload={"chunk": 1},
                sequence_number=1,
                is_final=False,
                received_at=datetime.now(timezone.utc),
            ),
            Response(
                response_id=uuid.uuid4(),
                command_id=command_id,
                response_payload={"chunk": 2},
                sequence_number=2,
                is_final=False,
                received_at=datetime.now(timezone.utc),
            ),
        ]

        mock_db = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        # Simulate that the database returns them ordered
        mock_scalars.all.return_value = sorted(
            mock_responses, key=lambda r: r.sequence_number
        )
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await response_repository.get_responses_by_command_id(mock_db, command_id)

        assert len(result) == 3
        # Verify they are in correct order
        for i, response in enumerate(result, start=1):
            assert response.sequence_number == i
