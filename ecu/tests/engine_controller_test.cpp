#include "engine_controller.h"

#include <cstdlib>
#include <iostream>
#include <string>

namespace {
void expect(bool condition, const std::string& message)
{
    if (!condition) {
        std::cerr << "FAIL: " << message << '\n';
        std::exit(EXIT_FAILURE);
    }
}
}

int main()
{
    const EngineController controller;

    const auto off = controller.update({0, 0, 85});
    expect(off.calculated_rpm == 0, "zero RPM remains zero");
    expect(off.state == EngineState::Off, "zero RPM and throttle means off");
    expect(off.fault_status == NoFault, "normal temperature has no fault");

    const auto running = controller.update({2000, 40, 85});
    expect(running.calculated_rpm == 2000, "valid RPM is reported");
    expect(running.state == EngineState::Running, "nonzero RPM means running");
    expect(running.fault_status == NoFault, "valid input has no fault");

    const auto hot = controller.update({2000, 40, 111});
    expect(hot.calculated_rpm == 0, "faulted engine reports zero RPM");
    expect(hot.state == EngineState::Fault, "over-temperature sets fault state");
    expect(hot.fault_status == CoolantOverTemperature,
           "over-temperature sets fault bit 0");

    const auto invalid = controller.update({8001, 101, 111});
    expect(invalid.state == EngineState::Fault, "invalid values set fault state");
    expect(invalid.fault_status ==
               (CoolantOverTemperature | InvalidThrottle | InvalidRpm),
           "all applicable fault bits are reported");

    const auto throttle_only = controller.update({0, 1, 85});
    expect(throttle_only.state == EngineState::Running,
           "nonzero throttle means running");

    std::cout << "All engine controller tests passed.\n";
    return EXIT_SUCCESS;
}
