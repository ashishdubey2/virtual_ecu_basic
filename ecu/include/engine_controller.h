#pragma once

#include <cstdint>

struct EngineInput {
    std::uint16_t rpm;
    std::uint8_t throttle_percent;
    std::int8_t coolant_temperature_c;
};

enum class EngineState : std::uint8_t {
    Off = 0,
    Running = 1,
    Fault = 2,
};

enum EngineFault : std::uint8_t {
    NoFault = 0,
    CoolantOverTemperature = 1U << 0,
    InvalidThrottle = 1U << 1,
    InvalidRpm = 1U << 2,
};

struct EngineOutput {
    std::uint16_t calculated_rpm;
    EngineState state;
    std::uint8_t fault_status;
};

class EngineController {
public:
    EngineOutput update(const EngineInput& input) const;
};
