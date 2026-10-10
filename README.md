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

## Build

Requirements: Linux, CMake 3.16 or newer, and a C++17 compiler.

```sh
cmake -S ecu -B build
cmake --build build
ctest --test-dir build --output-on-failure
```

## Run with `vcan0`

Create and enable the virtual CAN interface (the `ip` commands may require
`sudo`; `vcan` may need to be available as a kernel module):

```sh
sudo modprobe vcan
sudo ip link add dev vcan0 type vcan
sudo ip link set up vcan0
```

Start the ECU:

```sh
./build/virtual_ecu
```

With `can-utils` installed, open one terminal to monitor CAN:

```sh
candump vcan0
```

In another terminal, send RPM 2000, throttle 40%, and coolant 85 C (`0x0050`,
`0x28`, `0x55`):

```sh
cansend vcan0 100#07D02855
```

The response on ID `0x200` should be `200#07D00100`. Stop the ECU with Ctrl+C.
The executable can use another configured SocketCAN interface, for example
`./build/virtual_ecu can0`. Remove the virtual interface when finished with
`sudo ip link del vcan0`.

This first version implements the SocketCAN interface only; the optional TCP
endpoint can be added later without changing the CAN protocol.
