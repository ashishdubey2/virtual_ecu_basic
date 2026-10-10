"""SocketCAN client for the virtual ECU's documented four-byte protocol."""

from __future__ import annotations

import socket
import struct
import time
from dataclasses import dataclass

INPUT_CAN_ID = 0x100
OUTPUT_CAN_ID = 0x200
CAN_SFF_MASK = 0x7FF
CAN_EFF_RTR_FLAGS_MASK = 0xC0000000
CAN_RAW_FILTER = 1
CAN_RAW = 1
CAN_FRAME = struct.Struct("=IB3x8s")
CAN_FILTER = struct.Struct("=II")
PAYLOAD_LENGTH = 4


@dataclass(frozen=True)
class EngineResponse:
    rpm: int
    state: int
    fault: int

    @property
    def calculated_rpm(self) -> int:
        return self.rpm

    @property
    def fault_status(self) -> int:
        return self.fault


class CanInterface:
    """Send engine inputs and receive ECU responses on a SocketCAN interface."""

    def __init__(self, interface: str = "vcan0", timeout: float = 1.0) -> None:
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        self.interface = interface
        self.timeout = timeout
        self._socket = socket.socket(socket.PF_CAN, socket.SOCK_RAW, CAN_RAW)
        try:
            self._socket.setsockopt(
                socket.SOL_CAN_RAW,
                CAN_RAW_FILTER,
                CAN_FILTER.pack(
                    OUTPUT_CAN_ID,
                    CAN_SFF_MASK | CAN_EFF_RTR_FLAGS_MASK,
                ),
            )
            self._socket.bind((interface,))
        except Exception:
            self._socket.close()
            raise

    def close(self) -> None:
        self._socket.close()

    def __enter__(self) -> CanInterface:
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

        payload = bytes(
            (
                rpm >> 8,
                rpm & 0xFF,
                throttle,
                coolant_temperature & 0xFF,
            )
        )
        frame = CAN_FRAME.pack(can_id, PAYLOAD_LENGTH, payload.ljust(8, b"\0"))
        bytes_sent = self._socket.send(frame)
        if bytes_sent != CAN_FRAME.size:
            raise OSError(f"incomplete CAN frame write: {bytes_sent} bytes")

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
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError(
                    f"timed out waiting for CAN 0x{OUTPUT_CAN_ID:X} "
                    f"on {self.interface}"
                )
            self._socket.settimeout(remaining)
            try:
                frame = self._socket.recv(CAN_FRAME.size)
            except socket.timeout as error:
                raise TimeoutError(
                    f"timed out waiting for CAN 0x{OUTPUT_CAN_ID:X} "
                    f"on {self.interface}"
                ) from error

            received_id, length, data = CAN_FRAME.unpack(frame)
            received_id &= CAN_SFF_MASK
            if received_id != can_id:
                continue
            if length != PAYLOAD_LENGTH:
                raise ValueError(
                    f"CAN 0x{can_id:X} response has {length} bytes; "
                    f"expected {PAYLOAD_LENGTH}"
                )
            return EngineResponse(
                rpm=(data[0] << 8) | data[1],
                state=data[2],
                fault=data[3],
            )


def send_can(
    interface: CanInterface,
    *,
    can_id: int = INPUT_CAN_ID,
    rpm: int,
    throttle: int,
    coolant_temperature: int = 85,
) -> None:
    """Convenience wrapper matching the engine test call style."""
    interface.send_can(
        can_id,
        rpm=rpm,
        throttle=throttle,
        coolant_temperature=coolant_temperature,
    )


def wait_for_can(
    interface: CanInterface,
    can_id: int = OUTPUT_CAN_ID,
    *,
    timeout: float | None = None,
) -> EngineResponse:
    """Wait for an ECU response using the engine test call style."""
    return interface.wait_for_can(can_id, timeout=timeout)
