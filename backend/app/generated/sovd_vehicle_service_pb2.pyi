from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class CommandRequest(_message.Message):
    __slots__ = ("command_id", "vehicle_id", "command_name", "command_params")
    class CommandParamsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    COMMAND_ID_FIELD_NUMBER: _ClassVar[int]
    VEHICLE_ID_FIELD_NUMBER: _ClassVar[int]
    COMMAND_NAME_FIELD_NUMBER: _ClassVar[int]
    COMMAND_PARAMS_FIELD_NUMBER: _ClassVar[int]
    command_id: str
    vehicle_id: str
    command_name: str
    command_params: _containers.ScalarMap[str, str]
    def __init__(self, command_id: _Optional[str] = ..., vehicle_id: _Optional[str] = ..., command_name: _Optional[str] = ..., command_params: _Optional[_Mapping[str, str]] = ...) -> None: ...

class CommandResponse(_message.Message):
    __slots__ = ("command_id", "response_payload", "sequence_number", "is_final", "timestamp")
    COMMAND_ID_FIELD_NUMBER: _ClassVar[int]
    RESPONSE_PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    SEQUENCE_NUMBER_FIELD_NUMBER: _ClassVar[int]
    IS_FINAL_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    command_id: str
    response_payload: str
    sequence_number: int
    is_final: bool
    timestamp: str
    def __init__(self, command_id: _Optional[str] = ..., response_payload: _Optional[str] = ..., sequence_number: _Optional[int] = ..., is_final: bool = ..., timestamp: _Optional[str] = ...) -> None: ...
