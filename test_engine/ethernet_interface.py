"""TCP JSON-line adapter for a gateway exposing the virtual ECU protocol.

Each request is one JSON object terminated by a newline, with ``can_id``,
``rpm``, ``throttle`` and ``coolant_temperature`` fields. Each response is one
JSON line with ``can_id``, ``rpm``, ``state`` and ``fault`` fields.
"""

from __future__ import annotations

import json
import socket
import time
from typing import Any

from .can_interface import EngineResponse, INPUT_CAN_ID, OUTPUT_CAN_ID

MAX_LINE_LENGTH = 4096


class EthernetInterface:
    """TCP client for an ECU gateway using the JSON-lines format above."""

    def __init__(
        self,
        host: str,
        port: int,
        timeout: float = 1.0,
    ) -> None:
        if not 0 < port < 65536:
            raise ValueError("port must be between 1 and 65535")
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        self.timeout = timeout
        self._socket = socket.create_connection((host, port), timeout=timeout)
        self._buffer = bytearray()

    def close(self) -> None:
        self._socket.close()

    def __enter__(self) -> EthernetInterface:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def send_can(
        self,
        can_id: int = INPUT_CAN_ID,
        *,
        rpm: int,
        throttle: int,
        coolant_temperature: int = 85,
    ) -> None:
        if can_id != INPUT_CAN_ID:
            raise ValueError(f"input CAN ID must be 0x{INPUT_CAN_ID:X}")
        if not 0 <= rpm <= 0xFFFF:
            raise ValueError("rpm must fit in an unsigned 16-bit value")
        if not 0 <= throttle <= 0xFF:
            raise ValueError("throttle must fit in an unsigned 8-bit value")
        if not -128 <= coolant_temperature <= 127:
            raise ValueError("coolant_temperature must fit in a signed 8-bit value")

        request = {
            "can_id": can_id,
            "rpm": rpm,
            "throttle": throttle,
            "coolant_temperature": coolant_temperature,
        }
        self._socket.sendall(json.dumps(request, separators=(",", ":")).encode() + b"\n")

    def wait_for_can(
        self,
        can_id: int = OUTPUT_CAN_ID,
        *,
        timeout: float | None = None,
    ) -> EngineResponse:
        if can_id != OUTPUT_CAN_ID:
            raise ValueError(f"response CAN ID must be 0x{OUTPUT_CAN_ID:X}")
        wait_timeout = self.timeout if timeout is None else timeout
        if wait_timeout <= 0:
            raise ValueError("timeout must be positive")
        deadline = time.monotonic() + wait_timeout

        while True:
            line = self._readline(deadline)
            try:
                message: Any = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError("gateway returned invalid JSON") from error
            if not isinstance(message, dict):
                raise ValueError("gateway response must be a JSON object")
            if message.get("can_id") != can_id:
                continue
            try:
                rpm = message["rpm"]
                state = message["state"]
                fault = message["fault"]
            except KeyError as error:
                raise ValueError(
                    f"gateway response is missing {error.args[0]!r}"
                ) from error
            if any(type(value) is not int for value in (rpm, state, fault)):
                raise ValueError("gateway response values must be integers")
            if not 0 <= rpm <= 0xFFFF or not 0 <= state <= 0xFF or not 0 <= fault <= 0xFF:
                raise ValueError("gateway response values are outside protocol ranges")
            return EngineResponse(rpm=rpm, state=state, fault=fault)

    def _readline(self, deadline: float) -> bytes:
        while True:
            newline = self._buffer.find(b"\n")
            if newline >= 0:
                line = bytes(self._buffer[:newline])
                del self._buffer[: newline + 1]
                return line
            if len(self._buffer) >= MAX_LINE_LENGTH:
                raise ValueError("gateway response exceeds the maximum line length")

            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("timed out waiting for an Ethernet ECU response")
            self._socket.settimeout(remaining)
            try:
                chunk = self._socket.recv(min(1024, MAX_LINE_LENGTH - len(self._buffer)))
            except socket.timeout as error:
                raise TimeoutError(
                    "timed out waiting for an Ethernet ECU response"
                ) from error
            if not chunk:
                raise ConnectionError("gateway closed the Ethernet connection")
            self._buffer.extend(chunk)
