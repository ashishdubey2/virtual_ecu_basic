# Virtual ECU Basic

A small C++ virtual engine controller for demonstrating ECU software and
SocketCAN-based virtual testing on Linux. The ECU listens on `vcan0` by default;
an alternate CAN interface can be passed as its first argument.

## CAN protocol

The ECU accepts standard CAN data frames with ID `0x100` and exactly four data
bytes:

| Byte(s) | Meaning | Encoding |
| --- | --- | --- |
| 0-1 | Input RPM | Unsigned 16-bit, big-endian |
| 2 | Throttle | Unsigned percentage, `0`-`100` |
| 3 | Coolant temperature | Signed 8-bit degrees Celsius (two's complement) |

For valid input, the output reports the input RPM as calculated RPM. The engine
is `Off` when both RPM and throttle are zero, otherwise it is `Running`. A
coolant temperature above 110 C, throttle above 100%, or RPM above 8000 sets a
fault and forces calculated RPM to zero.

The ECU responds with a standard CAN data frame on ID `0x200`, also with four
bytes:

| Byte(s) | Meaning | Encoding |
| --- | --- | --- |
| 0-1 | Calculated RPM | Unsigned 16-bit, big-endian |
| 2 | Engine state | `0` off, `1` running, `2` fault |
| 3 | Fault status | Bit 0 coolant over-temperature; bit 1 invalid throttle; bit 2 invalid RPM |

Frames with an input ID but an unexpected length are reported to standard
error; valid frames with out-of-range values receive a fault response.

## Build and test

Requirements: Linux, CMake 3.16 or newer, a C++17 compiler, and `can-utils` for
the CAN demo. Install these with your distribution's package manager if needed.

From the repository root, configure and build the ECU:

```sh
cmake -S ecu -B build
cmake --build build
```

Run the unit tests:

```sh
ctest --test-dir build --output-on-failure
```

## Run the virtual ECU with `vcan0`

Create and enable the virtual CAN interface. These commands may require
`sudo`; the `vcan` kernel module must be available. Run the `ip link add`
command only the first time you create `vcan0` (it reports an error if the
interface already exists).

```sh
sudo modprobe vcan
sudo ip link add dev vcan0 type vcan
sudo ip link set up vcan0
```

Open three terminals from the repository root:

**Terminal 1 — start the ECU** and leave it running:
```sh
./build/virtual_ecu
```

**Terminal 2 — listen for ECU responses:**
```sh
candump vcan0,200:7FF
```

**Terminal 3 — send a test input** (RPM 2000, throttle 40%, coolant 85 C):
```sh
cansend vcan0 100#07D02855
```

`cansend` is normally silent when transmission succeeds. Look in Terminal 2
for a response similar to:

```text
vcan0  200   [4]  07 D0 01 00
```

This is CAN ID `0x200`: calculated RPM 2000 (`07 D0`), engine state `1`
(running), and fault status `0` (no faults). Stop the ECU with Ctrl+C in
Terminal 1. If no response appears, make sure the ECU is running without an
error and that `vcan0` is up (`ip link show vcan0`).

The executable can use another configured SocketCAN interface, for example
`./build/virtual_ecu can0`. Remove `vcan0` when finished with
`sudo ip link del vcan0`.

This first version implements the SocketCAN interface only; the optional TCP
endpoint can be added later without changing the CAN protocol.

## Python integration tests

The `test_engine/` package provides pytest integration tests for the CAN
protocol. Start `vcan0` as described above, then start `./build/virtual_ecu`
in another terminal. Install pytest in the Python environment and run:

```sh
source <virtual_env_folder>/bin/activate
python -m pip install -r requirements-dev.txt
python -m pytest test_engine/tests
```

Pytest writes a self-contained HTML report to `pytest-report.html` in the
repository root on every run. Open it in a browser to review the test summary,
individual outcomes, and detailed failure tracebacks and captured output.

The tests use `vcan0` by default and wait up to one second for each ECU
response. Override these settings with `VIRTUAL_ECU_CAN_INTERFACE` and
`VIRTUAL_ECU_TIMEOUT` (in seconds). If the configured SocketCAN interface
does not exist or is unavailable, pytest skips the integration tests.

`EthernetInterface` is provided for a future TCP gateway, not the current ECU
executable. It expects newline-delimited JSON requests containing `can_id`,
`rpm`, `throttle`, and `coolant_temperature`, and responses containing
`can_id`, `rpm`, `state`, and `fault`.
