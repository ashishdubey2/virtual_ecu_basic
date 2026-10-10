#include "engine_controller.h"

namespace {
constexpr std::int8_t kMaximumCoolantTemperatureC = 110;
constexpr std::uint16_t kMaximumRpm = 8000;
constexpr std::uint8_t kMaximumThrottlePercent = 100;
}  // namespace

EngineOutput EngineController::update(const EngineInput& input) const
{
    std::uint8_t faults = NoFault;
    if (input.coolant_temperature_c > kMaximumCoolantTemperatureC) {
        faults |= CoolantOverTemperature;
    }
    if (input.throttle_percent > kMaximumThrottlePercent) {
        faults |= InvalidThrottle;
    }
    if (input.rpm > kMaximumRpm) {
        faults |= InvalidRpm;
    }

    if (faults != NoFault) {
        return {0, EngineState::Fault, faults};
    }

    const auto state = (input.rpm > 0 || input.throttle_percent > 0)
                           ? EngineState::Running
                           : EngineState::Off;
    return {input.rpm, state, NoFault};
}
