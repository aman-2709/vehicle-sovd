"""
Unit tests for SOVD protocol handler module.
"""

from app.services import sovd_protocol_handler


class TestValidateCommand:
    """Test cases for validate_command function."""

    def test_validate_read_dtc_valid(self):
        """Test validation succeeds for valid ReadDTC command."""
        result = sovd_protocol_handler.validate_command(
            "ReadDTC", {"ecuAddress": "0x10"}
        )
        assert result is None

    def test_validate_read_dtc_missing_ecu_address(self):
        """Test validation fails when ecuAddress is missing."""
        result = sovd_protocol_handler.validate_command("ReadDTC", {})
        assert result is not None
        assert "ecuAddress" in result or "required" in result.lower()

    def test_validate_read_dtc_invalid_ecu_format(self):
        """Test validation fails for invalid ECU address format."""
        result = sovd_protocol_handler.validate_command(
            "ReadDTC", {"ecuAddress": "10"}
        )
        assert result is not None

    def test_validate_clear_dtc_valid_required_only(self):
        """Test validation succeeds for ClearDTC with required params only."""
        result = sovd_protocol_handler.validate_command(
            "ClearDTC", {"ecuAddress": "0xFF"}
        )
        assert result is None

    def test_validate_clear_dtc_valid_with_optional(self):
        """Test validation succeeds for ClearDTC with optional dtcCode."""
        result = sovd_protocol_handler.validate_command(
            "ClearDTC", {"ecuAddress": "0x10", "dtcCode": "P0420"}
        )
        assert result is None

    def test_validate_read_data_by_id_valid(self):
        """Test validation succeeds for valid ReadDataByID command."""
        result = sovd_protocol_handler.validate_command(
            "ReadDataByID", {"ecuAddress": "0x10", "dataId": "0x010C"}
        )
        assert result is None

    def test_validate_read_data_by_id_missing_data_id(self):
        """Test validation fails when dataId is missing."""
        result = sovd_protocol_handler.validate_command(
            "ReadDataByID", {"ecuAddress": "0x10"}
        )
        assert result is not None
        assert "dataId" in result or "required" in result.lower()

    def test_validate_read_data_by_id_invalid_data_id_format(self):
        """Test validation fails for invalid dataId format."""
        result = sovd_protocol_handler.validate_command(
            "ReadDataByID", {"ecuAddress": "0x10", "dataId": "010C"}
        )
        assert result is not None

    def test_validate_unknown_command(self):
        """Test validation fails for unknown command."""
        result = sovd_protocol_handler.validate_command("InvalidCommand", {})
        assert result is not None
        assert "unknown command" in result.lower() or "invalidcommand" in result.lower()

    def test_validate_additional_properties_rejected(self):
        """Test validation fails when additional properties are provided."""
        result = sovd_protocol_handler.validate_command(
            "ReadDTC", {"ecuAddress": "0x10", "extraParam": "value"}
        )
        assert result is not None

    def test_validate_read_dtc_lowercase_ecu_address(self):
        """Test validation succeeds with lowercase hex in ECU address."""
        result = sovd_protocol_handler.validate_command(
            "ReadDTC", {"ecuAddress": "0xab"}
        )
        assert result is None

    def test_validate_clear_dtc_invalid_dtc_code_format(self):
        """Test validation fails for invalid DTC code format."""
        result = sovd_protocol_handler.validate_command(
            "ClearDTC", {"ecuAddress": "0x10", "dtcCode": "0420"}
        )
        assert result is not None

    def test_validate_read_data_by_id_uppercase_data_id(self):
        """Test validation succeeds with uppercase hex in dataId."""
        result = sovd_protocol_handler.validate_command(
            "ReadDataByID", {"ecuAddress": "0x10", "dataId": "0xABCD"}
        )
        assert result is None

    def test_validate_read_dtc_ecu_address_too_short(self):
        """Test validation fails for ECU address with insufficient hex digits."""
        result = sovd_protocol_handler.validate_command(
            "ReadDTC", {"ecuAddress": "0x1"}
        )
        assert result is not None

    def test_validate_read_data_by_id_data_id_too_short(self):
        """Test validation fails for dataId with insufficient hex digits."""
        result = sovd_protocol_handler.validate_command(
            "ReadDataByID", {"ecuAddress": "0x10", "dataId": "0x01"}
        )
        assert result is not None


class TestEncodeCommand:
    """Test cases for encode_command function."""

    def test_encode_command_returns_dict(self):
        """Test encode_command returns a dictionary."""
        result = sovd_protocol_handler.encode_command(
            "ReadDTC", {"ecuAddress": "0x10"}
        )
        assert isinstance(result, dict)
        assert result["command_name"] == "ReadDTC"
        assert result["command_params"] == {"ecuAddress": "0x10"}

    def test_encode_command_preserves_parameters(self):
        """Test encode_command preserves all parameters."""
        params = {"ecuAddress": "0xFF", "dtcCode": "P0420"}
        result = sovd_protocol_handler.encode_command("ClearDTC", params)
        assert result["command_params"] == params

    def test_encode_command_with_complex_params(self):
        """Test encode_command with multiple parameters."""
        params = {"ecuAddress": "0x10", "dataId": "0x010C"}
        result = sovd_protocol_handler.encode_command("ReadDataByID", params)
        assert result["command_name"] == "ReadDataByID"
        assert result["command_params"] == params


class TestDecodeResponse:
    """Test cases for decode_response function."""

    def test_decode_response_returns_dict(self):
        """Test decode_response returns a dictionary."""
        payload = {"status": "success", "data": []}
        result = sovd_protocol_handler.decode_response(payload)
        assert isinstance(result, dict)
        assert result == payload

    def test_decode_response_preserves_payload(self):
        """Test decode_response preserves complete payload."""
        payload = {
            "dtcCodes": [
                {"dtcCode": "P0420", "description": "Catalyst System Efficiency"}
            ],
            "ecuAddress": "0x10",
            "timestamp": "2025-01-15T12:00:00Z"
        }
        result = sovd_protocol_handler.decode_response(payload)
        assert result == payload

    def test_decode_response_with_empty_dict(self):
        """Test decode_response with empty dictionary."""
        payload = {}
        result = sovd_protocol_handler.decode_response(payload)
        assert result == payload
        assert isinstance(result, dict)
