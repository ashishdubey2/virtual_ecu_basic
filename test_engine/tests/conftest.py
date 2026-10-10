from __future__ import annotations

import os

import pytest

from test_engine.can_interface import CanInterface
from test_engine.ecu_controller import EcuController


@pytest.fixture(scope="session")
def ecu() -> EcuController:
    interface_name = os.environ.get("VIRTUAL_ECU_CAN_INTERFACE", "vcan0")
    timeout = float(os.environ.get("VIRTUAL_ECU_TIMEOUT", "1.0"))
    try:
        interface = CanInterface(interface_name, timeout=timeout)
    except OSError as error:
        pytest.skip(f"SocketCAN interface {interface_name!r} is unavailable: {error}")
    try:
        yield EcuController(interface)
    finally:
        interface.close()
