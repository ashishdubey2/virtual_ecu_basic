"""High-level helpers for exercising the virtual engine ECU."""

from __future__ import annotations

from typing import Protocol

from .can_interface import EngineResponse, INPUT_CAN_ID, OUTPUT_CAN_ID


class EngineInterface(Protocol):
    def send_can(
        self,
        can_id: int = INPUT_CAN_ID,
        *,
        rpm: int,
        throttle: int,
        coolant_temperature: int = 85,
    ) -> None: ...

    def wait_for_can(
        self,
        can_id: int = OUTPUT_CAN_ID,
        *,
        timeout: float | None = None,
    ) -> EngineResponse: ...


class EcuController:
    """Send a protocol input and synchronously collect its ECU response."""

    def __init__(self, interface: EngineInterface) -> None:
        self.interface = interface

    def exchange(
        self,
        *,
        rpm: int = 0,
        throttle: int = 0,
        coolant_temperature: int = 85,
        timeout: float | None = None,
    ) -> EngineResponse:
        self.interface.send_can(
            INPUT_CAN_ID,
            rpm=rpm,
            throttle=throttle,
            coolant_temperature=coolant_temperature,
        )
        return self.interface.wait_for_can(OUTPUT_CAN_ID, timeout=timeout)
